"""
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

"""
Monkey-patches member access resolution for union types so that no error
message is generated when accessing members of optional types, and type
inference and checking can proceed normally.
"""
import mypy.checkmember

from functools import wraps


def remove_none(f):
    @wraps(f)
    def wrapper(*args, **varargs):
        if isinstance(args[1], mypy.types.UnionType):
            args = list(args)
            members = [t for t in args[1].items
                       if not isinstance(t, mypy.types.NoneTyp)]
            new_type = mypy.types.UnionType.make_simplified_union(members)
            args[1] = new_type
            args = tuple(args)
        res = f(*args, **varargs)
        return res
    return wrapper

patched_access = remove_none(mypy.checkmember.analyze_member_access)
mypy.checkmember.analyze_member_access = patched_access
