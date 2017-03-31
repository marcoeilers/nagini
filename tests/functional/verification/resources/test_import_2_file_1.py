from nagini_contracts.contracts import *
from resources.test_import_2_file_2 import test_func


def test_method(a: int) -> int:
    Ensures(test_func())
    return 17
