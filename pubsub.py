
import trzmq
import trio
import zmq


async def pub(n):
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.connect("tcp://0.0.0.0:5556")

    s = trzmq.Socket(socket)
    i = 1
    while True:
        topic = b"ZMQ-Test"
        message = f"Hello, from {n}: {i}..."
        await s.send(b"%b %b" % (topic, message.encode()))
        print("%s %s" % (topic, message))
        i += 1
        await trio.sleep(1)


async def sub():
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.bind("tcp://0.0.0.0:5556")
    socket.setsockopt_string(zmq.SUBSCRIBE, '')
    s = trzmq.Socket(socket)
    while True:
        string = await s.recv()
        print(string)


async def run():
    async with trio.open_nursery() as nursery:
        nursery.start_soon(sub)
        nursery.start_soon(pub, 1)
        nursery.start_soon(pub, 2)


trio.run(run)
