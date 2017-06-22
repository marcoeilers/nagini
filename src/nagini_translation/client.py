import argparse
import zmq

from nagini_translation.lib.constants import DEFAULT_CLIENT_SOCKET


context = zmq.Context()

socket = context.socket(zmq.REQ)
socket.connect(DEFAULT_CLIENT_SOCKET)

parser = argparse.ArgumentParser()
parser.add_argument(
        'python_file',
        help='Python file to verify')

args = parser.parse_args()

socket.send_string(args.python_file)
response = socket.recv_string()

print(response)