#:: IgnoreFile(/py2viper/issue/3/)
from py2viper_contracts.contracts import *

def break_out() -> bool:
    while True:
        try:
            raise Exception()
        finally:
            break
