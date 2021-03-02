import zmq
import socket
import trio

__all__ = ["Socket"]

class Socket:
    def __init__(self, zmq_sock):
        self._zmq_sock = zmq_sock

        # The current ZMQ_EVENTS
        self._zmq_events = None
        self._wake_events = {zmq.POLLIN: trio.Event(), zmq.POLLOUT: trio.Event()}

        # the ZMQ_FD fd
        # fromfd dups it, which is what we want, b/c the Python socket object
        # will close the fd when it's destroyed. This may or may not actually
        # be a socket, but it's definitely selectable. So on Windows it has to
        # be a socket handle, and on Unix it's some sort of file descriptor,
        # and in both cases that's what the socket module expects. And all
        # we're going to do is to call wait_readable() and close() on it,
        # which are operations that are defined for all fds on Unix.
        self._someone_is_watching_trigger = False

        self._update_events()

    def close(self):
        # XX zmq.sugar.Socket has some subtlety around shadow sockets
        self._zmq_sock.close()

    def _wake(self, flag):
        self._wake_events[flag].set()
        self._wake_events[flag] = trio.Event()

    def _update_events(self, wake_all=False):
        self._events = self._zmq_sock.getsockopt(zmq.EVENTS)
        if wake_all or self._events & zmq.POLLIN:
            self._wake(zmq.POLLIN)
        if wake_all or self._events & zmq.POLLOUT:
            self._wake(zmq.POLLOUT)

    @trio.lowlevel.enable_ki_protection
    async def _wait_for(self, flag):
        if self._events & flag:
            await trio.lowlevel.checkpoint()
            return

        if not self._someone_is_watching_trigger:
            self._someone_is_watching_trigger = True
            try:
                while not self._events & flag:
                    await trio.lowlevel.wait_readable(self._zmq_sock.fd)
                    self._update_events()
            finally:
                self._someone_is_watching_trigger = False
        else:
            # Someone else is watching the socket, so we just need to
            # wait to be woken up.
            await self._wake_events[flag].wait()

    # XX needs conflict detection
    # ...or does it? each send() call is atomic, like a DGRAM socket.
    async def send(self, data, flags=0, copy=True, track=False):
        flags |= zmq.NOBLOCK
        while True:
            await self._wait_for(zmq.POLLOUT)
            try:
                return self._zmq_sock.send(data, flags, copy, track)
            except zmq.Again:
                pass
            finally:
                self._update_events()

    # XX needs conflict detection, maybe?
    async def recv(self, flags=0, copy=True, track=False):
        flags |= zmq.NOBLOCK
        while True:
            await self._wait_for(zmq.POLLIN)
            try:
                return self._zmq_sock.recv(flags, copy, track)
            except zmq.Again:
                pass
            finally:
                self._update_events()

