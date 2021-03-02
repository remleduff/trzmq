import trio
import trzmq
import zmq

async def req(s, lock, n):
    i = 1
    while True:
        topic = b"ZMQ-Test"
        message = f"Hello {i}".encode()
        async with lock:
            await s.send(b"%b %b" % (topic, message))
            print(f"{n} Sent: {topic} {message}")
            reply = await s.recv()
            print(f"{n} Got response: {reply}")
        i += 1
        await trio.sleep(1)
        if n == 1 and i > 30:
            s.close()
            break

async def rep():
    await trio.sleep(10)

    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.setsockopt(zmq.SNDHWM, 2)
    socket.bind("tcp://0.0.0.0:5556")

    s = trzmq.Socket(socket)
    i = 1
    while True:
        msg = await s.recv()
        await s.send(b'Reply to: ' + msg)
        if i > 30:
            s.close()
            break

async def printer():
    while True:
        print("Still alive")
        await trio.sleep(1)

async def run():
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.setsockopt(zmq.SNDHWM, 5)
    socket.connect("tcp://0.0.0.0:5556")

    s = trzmq.Socket(socket)
    lock = trio.Lock()
    async with trio.open_nursery() as nursery:
        nursery.start_soon(req, s, lock, 1)
        nursery.start_soon(req, s, lock, 2)
        nursery.start_soon(rep)
        nursery.start_soon(printer)


trio.run(run)
