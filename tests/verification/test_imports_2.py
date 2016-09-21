from py2viper_contracts.contracts import *
from resources.test_import_2_file_1 import test_func
# Import('resources/test_import_2_file_1.py')


def test_method_2(a: int) -> int:
    Ensures(test_func())
    return 17
