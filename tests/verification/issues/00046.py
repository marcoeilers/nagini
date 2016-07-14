#:: IgnoreFile(/py2viper/issue/46/)
from py2viper_contracts.contracts import *

def test_list_3(r: List[int]) -> None:
    Requires(Forall(r, lambda i: (i > 0, [])))

    a = 3
