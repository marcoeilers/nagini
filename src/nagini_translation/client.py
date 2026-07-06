"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import argparse
import json
import zmq

from nagini_translation.lib.constants import DEFAULT_CLIENT_SOCKET


def main():
    context = zmq.Context()

    socket = context.socket(zmq.REQ)
    socket.connect(DEFAULT_CLIENT_SOCKET)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        'python_file',
        help='Python file to verify')
    parser.add_argument(
        '--select',
        default=None,
        help='select specific methods or classes to verify, separated by commas')

    args = parser.parse_args()

    request = {'file': args.python_file}
    if args.select:
        request['select'] = args.select
    socket.send_string(json.dumps(request))
    response = socket.recv_string()

    print(response)


if __name__ == '__main__':
    main()
