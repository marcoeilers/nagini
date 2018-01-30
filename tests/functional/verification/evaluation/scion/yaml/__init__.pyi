from nagini_contracts.contracts import *
from typing import Dict


def dump(d: Dict[str, object]) -> str:
    Requires(Acc(dict_pred(d), 1 / 10))
    Ensures(Acc(dict_pred(d), 1 / 10))
    ...