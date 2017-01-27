a = b = e

make sure stmt executed only once.


a, (b, c), *args, d = e with e being fixed length or not

from py2viper_contracts.contracts import *


class A:
    pass


def m() -> None:
    t = (1, [4, 12], 'asd', A())
    d, (g, h), *e = t
    assert d == 1
    assert len(e) == 2
    assert e[0] == 'asd'
    assert g == 4
    assert h == 12
    assert e[1] == 'asd'

# def m2() -> None:
#     t = [[1], [4, 12], ['asd'], [A()]]  # type: List[List[object]]
#     d, (g, h), *e = t
#     assert d == 1
#     assert len(e) == 2
#     assert e[0] == 'asd'
#     assert g == 4
#     assert h == 12
#     assert e[1] == 'asd'

def m3() -> None:
    l1 = [1]  # type: List[object]
    l2 = [4, 12]  # type: List[object]
    l3 = ['asd']  # type: List[object]
    l4 = [A()]  # type: List[object]
    t = [l1, l2, l3, l4]
    # t = [[1], [4, 12], ['asd'], [A()]]  # type: List[List[object]]
    # t = [[object()], [4, object()], [object()], [object()]]  # type: List[List[object]]
    d, (g, h), *e, z = t
    assert d[0] == 1
    assert len(e) == 1
    assert e[0] == 'asd'
    assert g == 4
    assert h == 12
    assert False

def m4() -> None:
    a = [("asd", A())]
    for b, *c in a:
       z = len(c)