import trio
import trzmq
import zmq

async def req():
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.setsockopt(zmq.SNDHWM, 2)
    socket.connect("tcp://0.0.0.0:5556")

    s = trzmq.Socket(socket)
    i = 1
    while True:
        topic = b"ZMQ-Test"
        message = f"Hello {i}".encode()
        await s.send(b"%b %b" % (topic, message))
        print("Sent: %s %s" % (topic, message))
        reply = await s.recv()
        print("Got response: %s" % reply)
        i += 1
        await trio.sleep(1)

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

async def printer():
    while True:
        print("Still alive")
        await trio.sleep(1)

async def run():
    async with trio.open_nursery() as nursery:
        nursery.start_soon(req)
        nursery.start_soon(rep)
        nursery.start_soon(printer)


trio.run(run)
