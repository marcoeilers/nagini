# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from resources.test_import_2_file_1 import test_func


def test_method_2(a: int) -> int:
    Ensures(test_func())
    return 17
