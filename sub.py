# subscriber

import trio
import trzmq
import zmq

async def run():
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.bind("tcp://0.0.0.0:5556")
    socket.setsockopt_string(zmq.SUBSCRIBE, '')
    s = trzmq.Socket(socket)
    while True:
        string = await s.recv()
        print(string)

trio.run(run)
