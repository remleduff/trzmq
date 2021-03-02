# publisher

import trzmq
import trio
import zmq

async def run():
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.connect("tcp://0.0.0.0:5556")

    s = trzmq.Socket(socket)
    i = 1
    while True:
        topic = b"ZMQ-Test"
        message = "Hello, NORM " + str(i) + "..."
        await s.send(b"%b %b" % (topic, message.encode()))
        print("%s %s" % (topic, message))
        i += 1
        await trio.sleep(1)

trio.run(run)
