# from lib.packet.host_addr import HostAddrBase
from typing import Optional
from nagini_contracts.contracts import *


class ISD_AS:
    LEN = 4
    def __init__(self, raw: Optional[str] = None) -> None: ...
    def to_int(self) -> int: ...


# class SCIONAddr(object):
#     def __init__(self) -> None:  # pragma: no cover
#         self.isd_as = None  # type: Optional[ISD_AS]
#         self.host = None  # type: Optional[HostAddrBase]
#
#     @Predicate
#     def State(self) -> bool:
#         return Acc(self.isd_as) and Acc(self.host)
#
#     @Pure
#     def matches(self, raw: bytes, offset: int) -> bool:
#         return True
#
#     @classmethod
#     def from_values(cls, isd_as: Optional[ISD_AS], host: Optional[HostAddrBase]) -> 'SCIONAddr':  # pragma: no cover
#         ...