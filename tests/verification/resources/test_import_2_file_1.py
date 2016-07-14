from py2viper_contracts.contracts import *
from resources.test_import_2_file_2 import test_func
# Import('test_import_2_file_2.py')


def test_method(a: int) -> int:
    Ensures(test_func())
    return 17
