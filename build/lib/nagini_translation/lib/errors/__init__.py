"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

"""Code for handling errors.

This includes:

1.  Converting Silver level errors to Nagini errors.
2.  Creating human readable error messages.
"""


from nagini_translation.lib.errors.manager import manager as error_manager
from nagini_translation.lib.errors.rules import Rules
