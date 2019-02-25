"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

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