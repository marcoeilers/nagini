from typing import Dict, Optional, Sized
from nagini_contracts.contracts import *

class SCIONTime(object):
    #_custom_time = None  # type: None

    @classmethod
    def get_time(cls) -> int: ...

    @classmethod
    def set_time_method(cls, method:Optional[object]=None) -> None: ...

def load_yaml_file(file_path: str) -> Dict[str, object]:
    Ensures(Acc(dict_pred(Result())))
    ...

# class Raw(Sized):
#     def __init__(self, data: bytes, desc:str="", len_:int=None,
#                  min_:bool=False) -> None:  # pragma: no cover
#         self._data = data
#         self._desc = desc
#         self._len = len_
#         self._min = min_
#         self._offset = 0
#
#     @Pure
#     def __len__(self) -> int:
#         ...
#
#     @Predicate
#     def contents(self, data: bytes) -> bool:
#         return (Acc(self._data) and self._data == data and
#                 Acc(self._desc) and
#                 Acc(self._len) and
#                 Acc(self._min) and
#                 Acc(self._offset))
#
#
#
#
# def sleep_interval(start: float, interval: float, desc: str, quiet: bool =False) -> None:
#     ...
#
#
# def hex_str(raw: bytes) -> str:
#     ...
#
# @Pure
# def calc_padding(length: int, block_size: int) -> int:
#     Requires(block_size != 0)
#     if length % block_size:
#         return block_size - (length % block_size)
#     else:
#         return 0