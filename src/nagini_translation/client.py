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
                '--write-viper-to-file',
                default=None,
                help='write generated Viper program to specified file')
        parser.add_argument(
                '-v', '--verbose',
                action='store_true',
                default=None,
                help='increase output verbosity')
        parser.add_argument(
                '--show-viper-errors',
                action='store_true',
                default=None,
                help='show Viper-level error messages if no Python errors are available')
        parser.add_argument(
                '--select',
                default=None,
                help='select specific methods or classes to verify, separated by commas')
        parser.add_argument(
                '--counterexample',
                action='store_true',
                default=None,
                help='return a counterexample for every verification error if possible')
        parser.add_argument(
                '--viper-arg',
                default=None,
                help='Arguments to be forwarded to Viper, separated by commas')

        args = parser.parse_args()

        # Build request: always include python_file, only include other args
        # if explicitly provided (non-None), so the server uses its own defaults.
        request = {'python_file': args.python_file}
        for key, value in vars(args).items():
                if key != 'python_file' and value is not None:
                        request[key] = value

        socket.send_string(json.dumps(request))
        response = socket.recv_string()

        print(response)

if __name__ == '__main__':
    main()
