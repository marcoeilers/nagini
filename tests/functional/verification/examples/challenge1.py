from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate
from typing import List, Tuple, Dict, Optional


class Point:
    def __init__(self, x: int, y: int, z: int) -> None:
        Requires(MustTerminate(1))
        self.x = x
        self.y = y
        self.z = z
        Ensures(Acc(self.x) and self.x is x and Acc(self.y) and self.y is y and Acc(self.z) and self.z is z)

    def add(self, other: 'Point') -> None:
        Requires(Acc(point_pred(other), 1 / 20))
        Requires(Acc(point_pred(self), 1))
        Requires(MustTerminate(1))
        Ensures(Acc(point_pred(other), 1 / 20))
        Ensures(Acc(point_pred(self), 1))

        Unfold(Acc(point_pred(self), 1))
        Unfold(Acc(point_pred(other), 1 / 20))
        self.x += other.x
        self.y += other.y
        self.z += other.z
        Fold(Acc(point_pred(self), 1))
        Fold(Acc(point_pred(other), 1 / 20))

X_VAL = 0
Y_VAL = 1
Z_VAL = 2

@Predicate
def point_pred(p: Point) -> bool:
    return (
        Acc(p.x) and Acc(p.y) and Acc(p.z)
    )


@Pure
def xs(p: List[Point]) -> PSeq[int]:
    Requires(Acc(list_pred(p), 1 / 2000) and len(p) > 0)
    Requires(Forall2(int, int, lambda i, j: (Implies(type(i) is int and type(j) is int and i is not j and i >= 0 and i < len(p) and j >= 0 and j < len(p),
                                                     p[i] is not p[j]),
                                             [[p[i], p[j]]])))
    Requires(Forall(int, lambda i: (Implies(type(i) is int and i >= 0 and i < len(p), Acc(point_pred(p[i]), 1 / 2000)), [[p[i]]])))
    return xs_rec(p, 0)


@Pure
def xs_rec(p: List[Point], start: int) -> PSeq[int]:
    Requires(Acc(list_pred(p), 1 / 2000) and len(p) > 0)
    Requires(start >= 0 and start < len(p) and type(start) is int)
    Requires(Forall2(int, int, lambda i, j: (Implies(type(i) is int and type(j) is int and i is not j and i >= start and i < len(p) and j >= start and j < len(p),
                                                     p[i] is not p[j]),
                                             [[p[i], p[j]]])))
    Requires(Forall(int, lambda i: (Implies(type(i) is int and i >= start and i < len(p), Acc(point_pred(p[i]), 1 / 2000)), [[p[i]]])))
    Ensures(len(Result()) == len(p) - start)

    if start == len(p) - 1:
        return PSeq(Unfolding(Acc(point_pred(p[start]), 1/2000), p[start].x))
    else:
        return PSeq(Unfolding(Acc(point_pred(p[start]), 1 / 2000), p[start].x)) + xs_rec(p, start + 1)


def lemma_xs_rec(p: List[Point], start: int) -> None:
    Requires(Acc(list_pred(p), 1 / 1600) and len(p) > 0)
    Requires(start >= 0 and start < len(p) and type(start) is int)
    Requires(Forall2(int, int, lambda i, j: (Implies(type(i) is int and type(j) is int and i is not j and i >= 0 and i < len(p) and j >= 0 and j < len(p),
                                                     p[i] is not p[j]),
                                             [[p[i], p[j]]])))
    Requires(Forall(int, lambda i: (Implies(type(i) is int and i >= 0 and i < len(p), Acc(point_pred(p[i]), 1 / 1600)), [[p[i]]])))
    Requires(MustTerminate(len(p) - start))
    Ensures(Acc(list_pred(p), 1 / 1600))
    Ensures(Forall2(int, int, lambda i, j: (Implies(type(i) is int and type(j) is int and i is not j and i >= 0 and i < len(p) and j >= 0 and j < len(p),
                                                     p[i] is not p[j]),
                                             [[p[i], p[j]]])))
    Ensures(Forall(int, lambda i: (Implies(type(i) is int and i >= 0 and i < len(p), Acc(point_pred(p[i]), 1 / 1600)), [[p[i]]])))
    Ensures(Forall(int, lambda i: (Implies(type(i) is int and i >= 0 and i < Old(len(p)) - start,
                                           Old(xs_rec(p, start)[i]) is Old(Unfolding(Acc(point_pred(p[start + i]), 1 / 1600),
                                                                                  p[start + i].x))),
                                   [[Old(xs_rec(p, start)[i])]])))
    Assert(Old(xs_rec(p, start)[0]) is Old(Unfolding(Acc(point_pred(p[start]), 1 / 1600), p[start].x)))
    if start == len(p) - 1:
        pass
    else:
        Assert(Forall(int, lambda i: (Implies(i > 0 and i < Old(len(p)) - start,
                                              Old(xs_rec(p, start)[i]) is Old(xs_rec(p, start + 1)[i - 1])),
                                      [[Old(xs_rec(p, start)[i])]])))
        lemma_xs_rec(p, start + 1)


@Pure
def ys(p: List[Point]) -> PSeq[int]:
    Requires(Acc(list_pred(p), 1 / 2000) and len(p) > 0)
    Requires(Forall2(int, int, lambda i, j: (Implies(type(i) is int and type(j) is int and i is not j and i >= 0 and i < len(p) and j >= 0 and j < len(p),
                                                     p[i] is not p[j]),
                                             [[p[i], p[j]]])))
    Requires(Forall(int, lambda i: (Implies(type(i) is int and i >= 0 and i < len(p), Acc(point_pred(p[i]), 1 / 2000)), [[p[i]]])))
    return ys_rec(p, 0)


@Pure
def ys_rec(p: List[Point], start: int) -> PSeq[int]:
    Requires(Acc(list_pred(p), 1 / 2000) and len(p) > 0)
    Requires(start >= 0 and start < len(p) and type(start) is int)
    Requires(Forall2(int, int, lambda i, j: (Implies(type(i) is int and type(j) is int and i is not j and i >= start and i < len(p) and j >= start and j < len(p),
                                                     p[i] is not p[j]),
                                             [[p[i], p[j]]])))
    Requires(Forall(int, lambda i: (Implies(type(i) is int and i >= start and i < len(p), Acc(point_pred(p[i]), 1 / 2000)), [[p[i]]])))
    Ensures(len(Result()) == len(p) - start)

    if start == len(p) - 1:
        return PSeq(Unfolding(Acc(point_pred(p[start]), 1/2000), p[start].y))
    else:
        return PSeq(Unfolding(Acc(point_pred(p[start]), 1 / 2000), p[start].y)) + ys_rec(p, start + 1)


def lemma_ys_rec(p: List[Point], start: int) -> None:
    Requires(Acc(list_pred(p), 1 / 1600) and len(p) > 0)
    Requires(start >= 0 and start < len(p) and type(start) is int)
    Requires(Forall2(int, int, lambda i, j: (Implies(type(i) is int and type(j) is int and i is not j and i >= 0 and i < len(p) and j >= start and j < len(p),
                                                     p[i] is not p[j]),
                                             [[p[i], p[j]]])))
    Requires(Forall(int, lambda i: (Implies(type(i) is int and i >= 0 and i < len(p), Acc(point_pred(p[i]), 1 / 1600)), [[p[i]]])))
    Requires(MustTerminate(len(p) - start))
    Ensures(Acc(list_pred(p), 1 / 1600))
    Ensures(Forall2(int, int, lambda i, j: (Implies(type(i) is int and type(j) is int and i is not j and i >= 0 and i < len(p) and j >= start and j < len(p),
                                                     p[i] is not p[j]),
                                             [[p[i], p[j]]])))
    Ensures(Forall(int, lambda i: (Implies(type(i) is int and i >= 0 and i < len(p), Acc(point_pred(p[i]), 1 / 1600)), [[p[i]]])))
    Ensures(Forall(int, lambda i: (Implies(i >= 0 and i < Old(len(p)) - start,
                                           Old(ys_rec(p, start)[i]) is Old(Unfolding(Acc(point_pred(p[start + i]), 1 / 1600),
                                                                                  p[start + i].y))),
                                   [[Old(ys_rec(p, start)[i])]])))
    Assert(Old(ys_rec(p, start)[0]) is Old(Unfolding(Acc(point_pred(p[start]), 1 / 1600), p[start].y)))
    if start == len(p) - 1:
        pass
    else:
        Assert(Forall(int, lambda i: (Implies(i > 0 and i < Old(len(p)) - start,
                                              Old(ys_rec(p, start)[i]) is Old(ys_rec(p, start + 1)[i - 1])),
                                      [[Old(ys_rec(p, start)[i])]])))
        lemma_ys_rec(p, start + 1)

@Pure
def zs(p: List[Point]) -> PSeq[int]:
    Requires(Acc(list_pred(p), 1 / 2000) and len(p) > 0)
    Requires(Forall2(int, int, lambda i, j: (Implies(type(i) is int and type(j) is int and i is not j and i >= 0 and i < len(p) and j >= 0 and j < len(p),
                                                     p[i] is not p[j]),
                                             [[p[i], p[j]]])))
    Requires(Forall(int, lambda i: (Implies(type(i) is int and i >= 0 and i < len(p), Acc(point_pred(p[i]), 1 / 2000)), [[p[i]]])))
    return zs_rec(p, 0)


@Pure
def zs_rec(p: List[Point], start: int) -> PSeq[int]:
    Requires(Acc(list_pred(p), 1 / 2000) and len(p) > 0)
    Requires(start >= 0 and start < len(p) and type(start) is int)
    Requires(Forall2(int, int, lambda i, j: (Implies(type(i) is int and type(j) is int and i is not j and i >= start and i < len(p) and j >= start and j < len(p),
                                                     p[i] is not p[j]),
                                             [[p[i], p[j]]])))
    Requires(Forall(int, lambda i: (Implies(type(i) is int and i >= start and i < len(p), Acc(point_pred(p[i]), 1 / 2000)), [[p[i]]])))
    Ensures(len(Result()) == len(p) - start)

    if start == len(p) - 1:
        return PSeq(Unfolding(Acc(point_pred(p[start]), 1/2000), p[start].z))
    else:
        return PSeq(Unfolding(Acc(point_pred(p[start]), 1 / 2000), p[start].z)) + zs_rec(p, start + 1)


def lemma_zs_rec(p: List[Point], start: int) -> None:
    Requires(Acc(list_pred(p), 1 / 1600) and len(p) > 0)
    Requires(start >= 0 and start < len(p) and type(start) is int)
    Requires(Forall2(int, int, lambda i, j: (Implies(type(i) is int and type(j) is int and i is not j and i >= 0 and i < len(p) and j >= start and j < len(p),
                                                     p[i] is not p[j]),
                                             [[p[i], p[j]]])))
    Requires(Forall(int, lambda i: (Implies(type(i) is int and i >= 0 and i < len(p), Acc(point_pred(p[i]), 1 / 1600)), [[p[i]]])))
    Requires(MustTerminate(len(p) - start))
    Ensures(Acc(list_pred(p), 1 / 1600))
    Ensures(Forall2(int, int, lambda i, j: (Implies(type(i) is int and type(j) is int and i is not j and i >= 0 and i < len(p) and j >= start and j < len(p),
                                                     p[i] is not p[j]),
                                             [[p[i], p[j]]])))
    Ensures(Forall(int, lambda i: (Implies(type(i) is int and i >= 0 and i < len(p), Acc(point_pred(p[i]), 1 / 1600)), [[p[i]]])))
    Ensures(Forall(int, lambda i: (Implies(i >= 0 and i < Old(len(p)) - start,
                                           Old(zs_rec(p, start)[i]) is Old(Unfolding(Acc(point_pred(p[start + i]), 1 / 1600),
                                                                                  p[start + i].z))),
                                   [[Old(zs_rec(p, start)[i])]])))
    Assert(Old(zs_rec(p, start)[0]) is Old(Unfolding(Acc(point_pred(p[start]), 1 / 1600), p[start].z)))
    if start == len(p) - 1:
        pass
    else:
        Assert(Forall(int, lambda i: (Implies(i > 0 and i < Old(len(p)) - start,
                                              Old(zs_rec(p, start)[i]) is Old(zs_rec(p, start + 1)[i - 1])),
                                      [[Old(zs_rec(p, start)[i])]])))
        lemma_zs_rec(p, start + 1)

@Pure
def values(p: List[Point], coord: int) -> PSeq[int]:
    Requires(coord in (X_VAL, Y_VAL, Z_VAL))
    Requires(Acc(list_pred(p), 1 / 2000) and len(p) > 0)
    Requires(Forall2(int, int, lambda i, j: (Implies(type(i) is int and type(j) is int and i is not j and i >= 0 and i < len(p) and j >= 0 and j < len(p),
                                                     p[i] is not p[j]),
                                             [[p[i], p[j]]])))
    Requires(Forall(int, lambda i: (Implies(type(i) is int and i >= 0 and i < len(p), Acc(point_pred(p[i]), 1 / 2000)), [[p[i]]])))
    if coord == X_VAL:
        return xs(p)
    elif coord == Y_VAL:
        return ys(p)
    else:
        return zs(p)


@Predicate
def min_max_properties(p: List[Point], coord: int, min: int, max: int) -> bool:
    return (
            (coord in (X_VAL, Y_VAL, Z_VAL)) and
            (Acc(list_pred(p), 1 / 200) and len(p) > 0) and
            (Forall2(int, int, lambda i, j: (Implies(type(i) is int and type(j) is int and i is not j and i >= 0 and i < len(p) and j >= 0 and j < len(p),
                                                     p[i] is not p[j]),
                                             [[p[i], p[j]]]))) and
            (Forall(int, lambda i: (Implies(type(i) is int and i >= 0 and i < len(p), Acc(point_pred(p[i]), 1 / 200)), [[p[i]]]))) and
            (min in values(p, coord) and max in values(p, coord) and
             Forall(int, lambda i: (Implies(i >= 0 and i < len(p),
                                            values(p, coord)[i] <= max and values(p, coord)[i] >= min),
                                    [[values(p, coord)[i]]])))
    )

def lemma_min_max(p: List[Point], coord: int, min: int, max: int, i: int, pt: Point) -> None:
    Requires(min_max_properties(p, coord, min, max))
    Requires(Acc(list_pred(p), 1/200) and i >= 0 and i < len(p))
    Requires(Acc(point_pred(pt), 1/200))
    Requires(pt is p[i])
    Requires(MustTerminate(len(p) + 1))
    Ensures(Acc(point_pred(pt), 1 / 200))
    Ensures(Implies(coord == X_VAL, Unfolding(Acc(point_pred(pt), 1 / 200), pt.x >= min and pt.x <= max)))
    Ensures(Implies(coord == Y_VAL, Unfolding(Acc(point_pred(pt), 1 / 200), pt.y >= min and pt.y <= max)))
    Ensures(Implies(coord == Z_VAL, Unfolding(Acc(point_pred(pt), 1 / 200), pt.z >= min and pt.z <= max)))

    Ensures(Acc(list_pred(p), 1/200))
    Ensures(min_max_properties(p, coord, min, max))

    Assume(SplitOn(coord == X_VAL, falseSplit=SplitOn(coord == Y_VAL)))

    Unfold(min_max_properties(p, coord, min, max))
    if coord == X_VAL:
        Assert(values(p, coord)[i] is xs_rec(p, 0)[i])
        Unfold(Acc(point_pred(pt), 1 / 200))
        before = xs_rec(p, 0)[i]
        lemma_xs_rec(p, 0)
        Assert(pt.x is before)
        Assert(pt.x >= min and pt.x <= max)
        Fold(Acc(point_pred(pt), 1 / 200))
    elif coord == Y_VAL:
        Assert(values(p, coord)[i] is ys_rec(p, 0)[i])
        Unfold(Acc(point_pred(pt), 1 / 200))
        before = ys_rec(p, 0)[i]
        lemma_ys_rec(p, 0)
        Assert(pt.y is before)
        Assert(pt.y >= min and pt.y <= max)
        Fold(Acc(point_pred(pt), 1 / 200))
    else:
        Assert(values(p, coord)[i] is zs_rec(p, 0)[i])
        Unfold(Acc(point_pred(pt), 1 / 200))
        before = zs_rec(p, 0)[i]
        lemma_zs_rec(p, 0)
        Assert(pt.z is before)
        Assert(pt.z >= min and pt.z <= max)
        Fold(Acc(point_pred(pt), 1 / 200))
    Fold(min_max_properties(p, coord, min, max))

def triple_min_max(p: List[Point]) -> Tuple[int, int, int, int, int, int]:
    Requires(Acc(list_pred(p), 3 / 200) and len(p) > 0)
    Requires(Forall2(int, int, lambda i, j: (Implies(type(i) is int and type(j) is int and i is not j and i >= 0 and i < len(p) and j >= 0 and j < len(p),
            p[i] is not p[j]),
            [[p[i], p[j]]])))
    Requires(Forall(int, lambda i: (Implies(type(i) is int and i >= 0 and i < len(p), Acc(point_pred(p[i]), 3 / 200)), [[p[i]]])))
    Requires(MustTerminate(len(p) + 2))
    Ensures(min_max_properties(p, X_VAL, Result()[0], Result()[1]))
    Ensures(min_max_properties(p, Y_VAL, Result()[2], Result()[3]))
    Ensures(min_max_properties(p, Z_VAL, Result()[4], Result()[5]))
    Ensures(Result()[0] <= Result()[1])
    Ensures(Result()[2] <= Result()[3])
    Ensures(Result()[4] <= Result()[5])

    x_min, x_max = find_min_max(p, X_VAL)
    y_min, y_max = find_min_max(p, Y_VAL)
    z_min, z_max = find_min_max(p, Z_VAL)
    return x_min, x_max, y_min, y_max, z_min, z_max

def find_min_max(p: List[Point], coord: int) -> Tuple[int, int]:
    Requires(coord in (X_VAL, Y_VAL, Z_VAL))
    Requires(Acc(list_pred(p), 1/200) and len(p) > 0)
    Requires(Forall2(int, int, lambda i, j: (Implies(type(i) is int and type(j) is int and i is not j and i >= 0 and i < len(p) and j >= 0 and j < len(p),
                                                     p[i] is not p[j]),
                                             [[p[i], p[j]]])))
    Requires(Forall(int, lambda i: (Implies(type(i) is int and i >= 0 and i < len(p), Acc(point_pred(p[i]), 1 / 200)), [[p[i]]])))
    Requires(MustTerminate(len(p) + 1))
    Ensures(min_max_properties(p, coord, Result()[0], Result()[1]))
    Ensures(Result()[0] <= Result()[1])

    Assume(SplitOn(coord == X_VAL, falseSplit=SplitOn(coord == Y_VAL)))

    j = 0
    min = None  # type: Optional[int]
    max = None  # type: Optional[int]

    seq = values(p, coord)
    while j < len(p):
        Invariant(Acc(list_pred(p), 1 / 200) and len(seq) == len(p))
        Invariant(j >= 0 and j <= len(p) and type(j) is int)
        Invariant(Forall2(int, int, lambda i, k: (Implies(type(i) is int and type(k) is int and i is not k and i >= 0 and i < len(p) and k >= 0 and k < len(p),
                                                          p[i] is not p[k]),
                                                  [[p[i], p[k]]])))
        Invariant(Forall(int, lambda i: (Implies(type(i) is int and i >= 0 and i < len(p), Acc(point_pred(p[i]), 1 / 200)), [[p[i]]])))
        Invariant(values(p, coord) is seq)
        Invariant(Implies(j == 0, min is None and max is None))
        Invariant(Implies(j > 0, min is not None and max is not None))
        Invariant(Implies(j > 0, min in seq and max in seq))
        Invariant(Implies(j > 0, Forall(int, lambda i: (Implies(i >= 0 and i < j,
                                                         seq[i] <= max and seq[i] >= min),
                                                 [[seq[i]]]))))
        Invariant(Implies(j > 0, min <= max))
        Invariant(MustTerminate(len(p) + 1 - j))

        cp = p[j]
        Unfold(Acc(point_pred(cp), 1/400))
        if coord == X_VAL:
            cur = cp.x
        elif coord == Y_VAL:
            cur = cp.y
        else:
            cur = cp.z
        Fold(Acc(point_pred(cp), 1/400))

        Assert(values(p, coord) is seq)
        if coord == X_VAL:
            lemma_xs_rec(p, 0)
        elif coord == Y_VAL:
            lemma_ys_rec(p, 0)
        else:
            lemma_zs_rec(p, 0)
        Assert(cur is seq[j])
        Assert(cur in seq)

        if min is None or cur < min:
            min = cur
        if max is None or cur > max:
            max = cur

        j += 1
    Fold(min_max_properties(p, coord, min, max))
    return min, max


def create_point_map(x_dim: int, y_dim: int, z_dim: int) -> Dict[Tuple[int, int, int], Point]:
    Requires(x_dim > 0 and y_dim > 0 and z_dim > 0)
    Requires(MustTerminate(2))
    Ensures(dict_pred(Result()))
    Ensures(Forall6(int, int, int, int, int, int,
                      lambda x1, x2, x3, y1, y2, y3: (Implies((x1 != y1 or x2 != y2 or x3 != y3) and (x1, x2, x3) in Result() and (y1, y2, y3) in Result(),
                                                              Result()[(x1, x2, x3)] is not Result()[(y1, y2, y3)]),
                                                      [[Result()[(x1, x2, x3)], Result()[(y1, y2, y3)]]])))
    Ensures(Forall3(int, int, int,
                      lambda x, y, z: ((type(x) is int and type(y) is int and type(
                              z) is int and x >= 0 and x < x_dim and y >= 0 and y < y_dim and z >= 0 and z < z_dim) ==
                                       ((x, y, z) in Result()),
                                       [[(x, y, z) in Result()]])))
    Ensures(Forall3(int, int, int, lambda x, y, z: (Implies((x, y, z) in Result(),
                                                            point_pred(Result()[(x, y, z)])
                                                            ), [[(x, y, z) in Result()]])))

    res = {}  # type: Dict[Tuple[int, int, int], Point]
    i = 0
    while i < x_dim:
        Invariant(dict_pred(res))
        Invariant(i >= 0 and i <= x_dim and type(i) is int)
        Invariant(Forall6(int, int, int, int, int, int,
                          lambda x1, x2, x3, y1, y2, y3: (Implies((x1 != y1 or x2 != y2 or x3 != y3) and (x1, x2, x3) in res and (y1, y2, y3) in res,
                                                                  res[(x1, x2, x3)] is not res[(y1, y2, y3)]),
                                                          [[res[(x1, x2, x3)], res[(y1, y2, y3)]]])))
        Invariant(Forall3(int, int, int,
                          lambda x, y, z: ((type(x) is int and type(y) is int and type(
                              z) is int and x >= 0 and x < i and y >= 0 and y < y_dim and z >= 0 and z < z_dim) ==
                                           ((x, y, z) in res),
                                           [[(x, y, z) in res]])))
        Invariant(Forall3(int, int, int, lambda x, y, z: (Implies((x, y, z) in res,
                                                            point_pred(res[(x, y, z)])
                                                            ), [[(x, y, z) in res]])))
        Invariant(MustTerminate(x_dim + 1 - i))

        j = 0
        while j < y_dim:
            Invariant(dict_pred(res))
            Invariant(j >= 0 and j <= y_dim and type(j) is int)
            Invariant(Forall6(int, int, int, int, int, int,
                              lambda x1, x2, x3, y1, y2, y3: (Implies((x1 != y1 or x2 != y2 or x3 != y3) and (x1, x2, x3) in res and (y1, y2, y3) in res,
                                                                      res[(x1, x2, x3)] is not res[(y1, y2, y3)]),
                                                              [[res[(x1, x2, x3)], res[(y1, y2, y3)]]])))
            Invariant(Forall3(int, int, int,
                              lambda x, y, z: ((type(x) is int and type(y) is int and type(
                                  z) is int and x >= 0 and z >= 0 and z < z_dim and y >= 0 and y < y_dim and (
                                                            (x == i and y < j) or (x < i))) ==
                                               ((x, y, z) in res),
                                               [[(x, y, z) in res]])))
            Invariant(Forall3(int, int, int, lambda x, y, z: (
            Implies((x, y, z) in res,
                    point_pred(res[(x, y, z)])
                    ), [[(x, y, z) in res]])))
            Invariant(MustTerminate(y_dim + 1 - j))

            k = 0
            while k < z_dim:
                Invariant(dict_pred(res))
                Invariant(k >= 0 and k <= z_dim and type(k) is int)
                Invariant(Forall6(int, int, int, int, int, int, lambda x1, x2, x3, y1, y2, y3: (Implies((x1 != y1 or x2 != y2 or x3 != y3) and (x1, x2, x3) in res and (y1, y2, y3) in res,
                                                                                                        res[(x1, x2, x3)] is not res[(y1, y2, y3)]),
                                                                                                [[res[(x1, x2, x3)], res[(y1, y2, y3)]]])))
                Invariant(Forall3(int, int, int,
                                  lambda x, y, z: (
                                      Implies(type(x) is int and type(y) is int and type(
                                          z) is int and x >= 0 and x < x_dim and y >= 0 and y < y_dim and z >= 0 and z < z_dim and (
                                                          ((y < j and x == i) or x < i) or (
                                                              y == j and x == i and z < k)),
                                              ((x, y, z) in res)),
                                      [[(x, y, z)]])))
                Invariant(Forall3(int, int, int,
                                  lambda x, y, z: (
                                      Implies((x, y, z) in res, (type(x) is int and type(y) is int and type(
                                          z) is int and x >= 0 and x < x_dim and y >= 0 and y < y_dim and z >= 0 and z < z_dim and (
                                                                             ((y < j and x == i) or x < i) or (
                                                                                 y == j and x == i and z < k)))),
                                      [[(x, y, z)]])))
                Invariant(Forall3(int, int, int, lambda x, y, z: (
                    Implies((x, y, z) in res,
                            point_pred(res[(x, y, z)])
                            ), [[(x, y, z) in res]])))
                Invariant(MustTerminate(z_dim + 1 - k))

                p = Point(0, 0, 0)
                Assume(Forall3(int, int, int, lambda x, y, z: (Implies((x, y, z) in res, res[(x, y, z)] is not p),
                                                               [[res[(x, y, z)]]])))
                res[(i, j, k)] = p
                Fold(point_pred(p))
                k += 1
            j += 1
        i += 1
    return res


def create_int_map(x_dim: int, y_dim: int, z_dim: int) -> Dict[Tuple[int, int, int], int]:
    Requires(x_dim > 0 and y_dim > 0 and z_dim > 0)
    Requires(MustTerminate(2))
    Ensures(dict_pred(Result()))
    Ensures(Forall3(int, int, int,
                      lambda x, y, z: ((type(x) is int and type(y) is int and type(z) is int and x >= 0 and x < x_dim and y >= 0 and y < y_dim and z >= 0 and z < z_dim) ==
                                       ((x, y, z) in Result()),
                                       [[(x, y, z) in Result()]])))
    Ensures(Forall3(int, int, int, lambda x, y, z: (Implies(type(x) is int and type(y) is int and type(z) is int and x >= 0 and x < x_dim and y >= 0 and y < y_dim and z >= 0 and z < z_dim,
                                                            Result()[(x, y, z)] == 0
                                                            ), [[(x, y, z) in Result()]])))

    res = {}  # type: Dict[Tuple[int, int, int], int]
    i = 0
    while i < x_dim:
        Invariant(dict_pred(res))
        Invariant(i >= 0 and i <= x_dim and type(i) is int)
        Invariant(Forall3(int, int, int,
                          lambda x, y, z: ((type(x) is int and type(y) is int and type(z) is int and x >= 0 and x < i and y >= 0 and y < y_dim and z >= 0 and z < z_dim) ==
                                           ((x, y, z) in res),
                                           [[(x, y, z) in res]])))
        Invariant(Forall3(int, int, int, lambda x, y, z: (Implies((type(x) is int and type(y) is int and type(z) is int and x >= 0 and x < i and y >= 0 and y < y_dim and z >= 0 and z < z_dim),
                                                            res[(x, y, z)] == 0
                                                            ), [[res[(x, y, z)]]])))
        Invariant(MustTerminate(x_dim + 1 - i))

        j = 0
        while j < y_dim:
            Invariant(dict_pred(res))
            Invariant(j >= 0 and j <= y_dim and type(j) is int)
            Invariant(Forall3(int, int, int,
                              lambda x, y, z: ((type(x) is int and type(y) is int and type(z) is int and x >= 0 and z >= 0 and z < z_dim and y >= 0 and y < y_dim and ((x == i  and y < j) or (x < i))) ==
                                               ((x, y, z) in res),
                                               [[(x, y, z) in res]])))
            Invariant(Forall3(int, int, int, lambda x, y, z: (
            Implies((type(x) is int and type(y) is int and type(z) is int and x >= 0 and z >= 0 and z < z_dim and y >= 0 and y < y_dim and ((x == i  and y < j) or (x < i))),
                    res[(x, y, z)] == 0
                    ), [[res[(x, y, z)]]])))
            Invariant(MustTerminate(y_dim + 1 - j))

            k = 0
            while k < z_dim:
                Invariant(dict_pred(res))
                Invariant(k >= 0 and k <= z_dim and type(k) is int)
                Invariant(Forall3(int, int, int,
                                  lambda x, y, z: (
                                  Implies(type(x) is int and type(y) is int and type(z) is int and x >= 0 and x < x_dim and y >= 0 and y < y_dim and z >= 0 and z < z_dim and (((y < j and x == i) or x < i) or (y == j and x == i and z < k)),
                                  ((x, y, z) in res)),
                                  [[(x, y, z)]])))
                Invariant(Forall3(int, int, int,
                                  lambda x, y, z: (
                                  Implies((x, y, z) in res, (type(x) is int and type(y) is int and type(z) is int and x >= 0 and x < x_dim and y >= 0 and y < y_dim and z >= 0 and z < z_dim and (((y < j and x == i) or x < i) or (y == j and x == i and z < k)))),
                                  [[(x, y, z)]])))
                Invariant(Forall3(int, int, int, lambda x, y, z: (
                    Implies((type(x) is int and type(y) is int and type(z) is int and x >= 0 and x < x_dim and y >= 0 and y < y_dim and z >= 0 and z < z_dim and (((y < j and x == i) or x < i) or (y == j and x == i and z < k))),
                            res[(x, y, z)] == 0
                            ), [[(x, y, z)]])))
                Invariant(MustTerminate(z_dim + 1 - k))

                res[(i, j, k)] = 0
                k += 1
            j += 1
        i += 1
    return res


def test() -> None:
    plist = create_point_map(5, 6, 7)
    p = plist[(2, 3, 4)]
    Unfold(point_pred(p))


def downSample(p: List[Point], voxel_size: int) -> List[Point]:
    Requires(voxel_size > 0)
    Requires(Acc(list_pred(p), 1) and len(p) > 0)
    Requires(Forall2(int, int, lambda i, j: (Implies(type(i) is int and type(j) is int and i is not j and i >= 0 and i < len(p) and j >= 0 and j < len(p),
                                                     p[i] is not p[j]),
                                             [[p[i], p[j]]])))
    Requires(Forall(int, lambda i: (Implies(type(i) is int and i >= 0 and i < len(p), Acc(point_pred(p[i]), 1)), [[p[i]]])))
    Requires(MustTerminate(len(p) + 4))
    # x_min, x_max = find_min_max(p, X_VAL)
    # y_min, y_max = find_min_max(p, Y_VAL)
    # z_min, z_max = find_min_max(p, Z_VAL)
    x_min, x_max, y_min, y_max, z_min, z_max = triple_min_max(p)
    num_vox_x = compute_num_vox(x_max - x_min, voxel_size)
    num_vox_y = compute_num_vox(y_max - y_min, voxel_size)
    num_vox_z = compute_num_vox(z_max - z_min, voxel_size)

    voxel_map = create_point_map(num_vox_x, num_vox_y, num_vox_z)

    count_map = create_int_map(num_vox_x, num_vox_y, num_vox_z)

    non_zero_keys = first_loop(x_min, x_max, y_min, y_max, z_min, z_max, num_vox_x, num_vox_y, num_vox_z, voxel_size, voxel_map, count_map, p)

    second_loop(num_vox_x, num_vox_y, num_vox_z, count_map, voxel_map, non_zero_keys)

    res = []  # type: List[Point]
    return res


def second_loop(num_vox_x: int, num_vox_y: int, num_vox_z: int, count_map: Dict[Tuple[int, int, int], int],
                voxel_map: Dict[Tuple[int, int, int], Point], non_zero_keys: PSet[Tuple[int, int, int]]) -> None:
    i, j, k = 0, 0, 0
    pd = []  # type: List[Point]
    non_zero_processed = PSet()  # type: PSet[Tuple[int, int, int]]
    while i < num_vox_x:
        Invariant(i >= 0 and i <= num_vox_x)
        while j < num_vox_y:
            Invariant(j >= 0 and j <= num_vox_y)
            while k < num_vox_z:
                Invariant(k >= 0 and k <= num_vox_z)
                Invariant(len(pd) == len(non_zero_processed))
                Invariant(all upcoming are zero or in bla. )
                if count_map[(i, j, k)] != 0:
                    p = voxel_map[(i, j, k)]
                    p.div(count_map[(i, j, k)])
                    pd.append(p)
                k += 1
            j += 1
        i += 1
    return pd
    """
    i, j, k := 0, 0, 0;
    pd := [];
    for 0 ≤ i < num_vox_x
    for 0 ≤ j < num_vox_y
    for 0 ≤ k < num_vox_z
    if(count_array[i,j,k] 6=0)
    pd.append(voxel_array[i,j,k]/count_array[i,j,k]);
    return pd;
    """


@Predicate
def voxel_map_pred(voxel_map: Dict[Tuple[int, int, int], Point], num_vox_x: int, num_vox_y: int, num_vox_z: int) -> bool:
    return (Acc(dict_pred(voxel_map), 1 / 2) and
            (Forall6(int, int, int, int, int, int,
                     lambda x1, x2, x3, y1, y2, y3: (Implies(
                         (x1 != y1 or x2 != y2 or x3 != y3) and (x1, x2, x3) in voxel_map and (
                             y1, y2, y3) in voxel_map,
                         voxel_map[(x1, x2, x3)] is not voxel_map[(y1, y2, y3)]),
                                                     [[voxel_map[(x1, x2, x3)], voxel_map[(y1, y2, y3)]]]))) and
            (Forall3(int, int, int,
                     lambda x, y, z: ((type(x) is int and type(y) is int and type(
                         z) is int and x >= 0 and x < num_vox_x and y >= 0 and y < num_vox_y and z >= 0 and z < num_vox_z) ==
                                      ((x, y, z) in voxel_map),
                                      [[(x, y, z) in voxel_map]]))) and
            (Forall3(int, int, int, lambda x, y, z: (Implies((x, y, z) in voxel_map,
                                                             point_pred(voxel_map[(x, y, z)])
                                                             ), [[(x, y, z) in voxel_map]])))
    )


@Predicate
def count_map_pred(count_map: Dict[Tuple[int, int, int], int], num_vox_x: int, num_vox_y: int, num_vox_z: int, non_zero_keys: PSet[Tuple[int, int, int]]) -> bool:
    return (
        dict_pred(count_map) and
        (Forall3(int, int, int,
                         lambda x, y, z: ((type(x) is int and type(y) is int and type(
                             z) is int and x >= 0 and x < num_vox_x and y >= 0 and y < num_vox_y and z >= 0 and z < num_vox_z) ==
                                          ((x, y, z) in count_map),
                                          [[(x, y, z) in count_map]]))) and
               (Forall3(int, int, int,
               lambda x, y, z: (Implies((x, y, z) in count_map,
                                               (count_map[(x, y, z)] == 0 and (x, y, z) not in non_zero_keys) or (
                                                           count_map[(x, y, z)] > 0 and (x, y, z) in non_zero_keys)),

    [[(x, y, z) in count_map]])))
    )


def first_loop(x_min: int, x_max: int, y_min: int, y_max: int, z_min: int, z_max: int, num_vox_x: int, num_vox_y: int, num_vox_z: int, voxel_size: int,
               voxel_map: Dict[Tuple[int, int, int], Point], count_map: Dict[Tuple[int, int, int], int], p: List[Point]) -> PSet[Tuple[int, int, int]]:
    Requires(voxel_size > 0)
    Requires(is_num_vox(x_max - x_min, voxel_size, num_vox_x))
    Requires(is_num_vox(y_max - y_min, voxel_size, num_vox_y))
    Requires(is_num_vox(z_max - z_min, voxel_size, num_vox_z))
    Requires(Acc(list_pred(p), 1 / 2) and len(p) > 0)
    Requires(Forall2(int, int, lambda i, j: (
    Implies(type(i) is int and type(j) is int and i is not j and i >= 0 and i < len(p) and j >= 0 and j < len(p),
            p[i] is not p[j]),
    [[p[i], p[j]]])))
    Requires(Forall(int, lambda i: (
    Implies(type(i) is int and i >= 0 and i < len(p), Acc(point_pred(p[i]), 1 / 2)), [[p[i]]])))
    Requires(Acc(dict_pred(voxel_map), 1 / 2) and dict_pred(count_map))
    Requires(Forall6(int, int, int, int, int, int,
                      lambda x1, x2, x3, y1, y2, y3: (Implies(
                          (x1 != y1 or x2 != y2 or x3 != y3) and (x1, x2, x3) in voxel_map and (
                              y1, y2, y3) in voxel_map,
                          voxel_map[(x1, x2, x3)] is not voxel_map[(y1, y2, y3)]),
                                                      [[voxel_map[(x1, x2, x3)], voxel_map[(y1, y2, y3)]]])))
    Requires(Forall3(int, int, int,
                      lambda x, y, z: ((type(x) is int and type(y) is int and type(
                          z) is int and x >= 0 and x < num_vox_x and y >= 0 and y < num_vox_y and z >= 0 and z < num_vox_z) ==
                                       ((x, y, z) in voxel_map),
                                       [[(x, y, z) in voxel_map]])))
    Requires(Forall3(int, int, int, lambda x, y, z: (Implies((x, y, z) in voxel_map,
                                                              point_pred(voxel_map[(x, y, z)])
                                                              ), [[(x, y, z) in voxel_map]])))
    Requires(Forall3(int, int, int,
                      lambda x, y, z: ((type(x) is int and type(y) is int and type(
                          z) is int and x >= 0 and x < num_vox_x and y >= 0 and y < num_vox_y and z >= 0 and z < num_vox_z) ==
                                       ((x, y, z) in count_map),
                                       [[(x, y, z) in count_map]])))
    Requires(Forall3(int, int, int,
                      lambda x, y, z: (Implies((x, y, z) in count_map, (count_map[(x, y, z)] == 0)),
                                       [[(x, y, z) in count_map]])))
    Requires(min_max_properties(p, X_VAL, x_min, x_max))
    Requires(min_max_properties(p, Y_VAL, y_min, y_max))
    Requires(min_max_properties(p, Z_VAL, z_min, z_max))

    Requires(MustTerminate(len(p) + 3))

    Ensures(is_num_vox(x_max - x_min, voxel_size, num_vox_x))
    Ensures(is_num_vox(y_max - y_min, voxel_size, num_vox_y))
    Ensures(is_num_vox(z_max - z_min, voxel_size, num_vox_z))
    Ensures(Acc(list_pred(p), 1 / 2) and len(p) > 0 and len(p) == Old(len(p)))
    Ensures(Forall2(int, int, lambda i, j: (
    Implies(type(i) is int and type(j) is int and i is not j and i >= 0 and i < len(p) and j >= 0 and j < len(p),
            p[i] is not p[j]),
    [[p[i], p[j]]])))
    Ensures(Forall(int, lambda i: (
    Implies(type(i) is int and i >= 0 and i < len(p), Acc(point_pred(p[i]), 1 / 2)), [[p[i]]])))
    Ensures(Acc(dict_pred(voxel_map), 1 / 2) and dict_pred(count_map))
    Ensures(Forall6(int, int, int, int, int, int,
                      lambda x1, x2, x3, y1, y2, y3: (Implies(
                          (x1 != y1 or x2 != y2 or x3 != y3) and (x1, x2, x3) in voxel_map and (
                              y1, y2, y3) in voxel_map,
                          voxel_map[(x1, x2, x3)] is not voxel_map[(y1, y2, y3)]),
                                                      [[voxel_map[(x1, x2, x3)], voxel_map[(y1, y2, y3)]]])))
    Ensures(Forall3(int, int, int,
                      lambda x, y, z: ((type(x) is int and type(y) is int and type(
                          z) is int and x >= 0 and x < num_vox_x and y >= 0 and y < num_vox_y and z >= 0 and z < num_vox_z) ==
                                       ((x, y, z) in voxel_map),
                                       [[(x, y, z) in voxel_map]])))
    Ensures(Forall3(int, int, int, lambda x, y, z: (Implies((x, y, z) in voxel_map,
                                                              point_pred(voxel_map[(x, y, z)])
                                                              ), [[(x, y, z) in voxel_map]])))
    Ensures(Forall3(int, int, int,
                      lambda x, y, z: ((type(x) is int and type(y) is int and type(
                          z) is int and x >= 0 and x < num_vox_x and y >= 0 and y < num_vox_y and z >= 0 and z < num_vox_z) ==
                                       ((x, y, z) in count_map),
                                       [[(x, y, z) in count_map]])))
    Ensures(Forall3(int, int, int,
                      lambda x, y, z: (Implies((x, y, z) in count_map,
                                               (count_map[(x, y, z)] == 0 and (x, y, z) not in non_zero_keys) or (
                                                           count_map[(x, y, z)] > 0 and (x, y, z) in non_zero_keys)),
                                       [[(x, y, z) in count_map]])))
    Ensures(min_max_properties(p, X_VAL, x_min, x_max))
    Ensures(min_max_properties(p, Y_VAL, y_min, y_max))
    Ensures(min_max_properties(p, Z_VAL, z_min, z_max))
    Ensures(len(Result()) <= len(p))

    non_zero_keys = PSet()  # type: PSet[Tuple[int, int, int]]
    i = 0
    while i < len(p):
        Invariant(is_num_vox(x_max - x_min, voxel_size, num_vox_x))
        Invariant(is_num_vox(y_max - y_min, voxel_size, num_vox_y))
        Invariant(is_num_vox(z_max - z_min, voxel_size, num_vox_z))
        Invariant(Acc(list_pred(p), 1/2) and len(p) > 0 and len(p) == Old(len(p)))
        Invariant(i >= 0 and i <= len(p) and type(i) is int)
        Invariant(Forall2(int, int, lambda i, j: (Implies(type(i) is int and type(j) is int and i is not j and i >= 0 and i < len(p) and j >= 0 and j < len(p),
                                                         p[i] is not p[j]),
                                                 [[p[i], p[j]]])))
        Invariant(Forall(int, lambda i: (Implies(type(i) is int and i >= 0 and i < len(p), Acc(point_pred(p[i]), 1/2)), [[p[i]]])))
        Invariant(Acc(dict_pred(voxel_map), 1/2) and dict_pred(count_map))
        Invariant(Forall6(int, int, int, int, int, int,
                        lambda x1, x2, x3, y1, y2, y3: (Implies(
                            (x1 != y1 or x2 != y2 or x3 != y3) and (x1, x2, x3) in voxel_map and (
                            y1, y2, y3) in voxel_map,
                            voxel_map[(x1, x2, x3)] is not voxel_map[(y1, y2, y3)]),
                                                        [[voxel_map[(x1, x2, x3)], voxel_map[(y1, y2, y3)]]])))
        Invariant(Forall3(int, int, int,
                        lambda x, y, z: ((type(x) is int and type(y) is int and type(
                            z) is int and x >= 0 and x < num_vox_x and y >= 0 and y < num_vox_y and z >= 0 and z < num_vox_z) ==
                                         ((x, y, z) in voxel_map),
                                         [[(x, y, z) in voxel_map]])))
        Invariant(Forall3(int, int, int, lambda x, y, z: (Implies((x, y, z) in voxel_map,
                                                                point_pred(voxel_map[(x, y, z)])
                                                                ), [[(x, y, z) in voxel_map]])))
        Invariant(Forall3(int, int, int,
                        lambda x, y, z: ((type(x) is int and type(y) is int and type(
                            z) is int and x >= 0 and x < num_vox_x and y >= 0 and y < num_vox_y and z >= 0 and z < num_vox_z) ==
                                         ((x, y, z) in count_map),
                                         [[(x, y, z) in count_map]])))
        Invariant(Forall3(int, int, int,
                          lambda x, y, z: (Implies((x, y, z) in count_map, (count_map[(x, y, z)] == 0 and (x, y, z) not in non_zero_keys) or (count_map[(x, y, z)] > 0 and (x, y, z) in non_zero_keys)),
                                           [[(x, y, z) in count_map]])))
        Invariant(min_max_properties(p, X_VAL, x_min, x_max))
        Invariant(min_max_properties(p, Y_VAL, y_min, y_max))
        Invariant(min_max_properties(p, Z_VAL, z_min, z_max))
        Invariant(len(non_zero_keys) <= i)
        Invariant(MustTerminate(len(p) + 1 - i))

        # Assume(False)
        pt = p[i]
        Unfold(Acc(point_pred(pt), 1/4))
        lemma_min_max(p, X_VAL, x_min, x_max, i, pt)
        lemma_min_max(p, Y_VAL, y_min, y_max, i, pt)
        lemma_min_max(p, Z_VAL, z_min, z_max, i, pt)
        Assert(pt.x >= x_min and pt.x <= x_max)
        Assert(pt.y >= y_min and pt.y <= y_max)
        Assert(pt.z >= z_min and pt.z <= z_max)
        x_floored = compute_floored(pt.x - x_min, voxel_size, x_max - x_min, num_vox_x)
        y_floored = compute_floored(pt.y - y_min, voxel_size, y_max - y_min, num_vox_y)
        z_floored = compute_floored(pt.z - z_min, voxel_size, z_max - z_min, num_vox_z)
        Fold(Acc(point_pred(pt), 1 / 4))

        Assert((x_floored, y_floored, z_floored) in voxel_map)
        Assert((x_floored, y_floored, z_floored) in count_map)

        voxel_map[(x_floored, y_floored, z_floored)].add(pt)
        count_map[(x_floored, y_floored, z_floored)] = count_map[(x_floored, y_floored, z_floored)] + 1

        i += 1
    return non_zero_keys

@Predicate
def is_num_vox(max_min_diff: int, voxel_size: int, res: int) -> bool:
    return voxel_size > 0 and res == max_min_diff // voxel_size + 1


def compute_num_vox(max_min_diff: int, voxel_size: int) -> int:
    Requires(voxel_size > 0)
    Requires(max_min_diff >= 0)
    Requires(MustTerminate(1))
    Ensures(is_num_vox(max_min_diff, voxel_size, Result()))
    Ensures(Result() > 0)
    res = max_min_diff // voxel_size + 1
    Fold(is_num_vox(max_min_diff, voxel_size, res))
    return res

def compute_floored(diff: int, voxel_size: int, max_min_diff: int, num_vox: int) -> int:
    Requires(voxel_size > 0)
    Requires(max_min_diff >= 0)
    Requires(diff >= 0 and diff <= max_min_diff)
    Requires(is_num_vox(max_min_diff, voxel_size, num_vox))
    Requires(MustTerminate(1))
    Ensures(is_num_vox(max_min_diff, voxel_size, num_vox))
    Ensures(Result() >= 0 and Result() < num_vox)
    Ensures(type(Result()) is int)
    Unfold(is_num_vox(max_min_diff, voxel_size, num_vox))
    res = diff // voxel_size
    if diff == max_min_diff:
        pass
    elif diff == max_min_diff - 1:
        pass
    else:
        pass
    Fold(is_num_vox(max_min_diff, voxel_size, num_vox))
    return res