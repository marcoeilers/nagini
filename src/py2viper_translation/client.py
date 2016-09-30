import argparse
import zmq
import sys

parser = argparse.ArgumentParser()
parser.add_argument('python_file')
args = parser.parse_args()

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect('tcp://127.0.0.1:5555')
socket.send_string(args.python_file)
msg = socket.recv_string()
for part in msg.splitlines():
    print(part)
    sys.stdout.flush()
