from typing import Tuple, Union, Optional, List, Dict
from nagini_contracts.contracts import *

GInt = int
MarkGhost(GInt)
GintList = List[GInt]
MarkGhost(GintList)

global_var: int = 0

def bar(i: int, gi: GInt) -> Tuple[int, GInt]: # OK
    res: GInt = gi + i  # OK
    (i, j) = k = 0,0
    j = i + 2           # OK
    gi += 1             # OK
    # i, gi = i+1, gi+1 # Throw invalid.ghost.assign
    # j += gi           # Throw invalid.ghost.assign

    return j, res       # OK
    # return gi, res    # Throw invalid.ghost.return
    # return i, j       # OK
    # return 0, 0       # OK

def simple(i: int, gi: GInt) -> int:
    return i

def simple2() -> List[Tuple[List[int],int]]:    # OK
    return []

def simple3() -> GInt:
    # Do something with potential side-effects
    return 0

def reg_call() -> Tuple[Tuple[int, int], Tuple[GInt, GInt]]: # OK
    i = simple(0, 0)                    # OK
    gi: GInt = foo(0)                   # OK

    # i = foo(0)                        # Throw invalid.ghost.assign
    # gi, i = ghost_simple(0)           # Throw invalid.ghost.assign
    gj: GInt = 0
    gk: GInt = 0
    # (gi,gj), (gk,i) = ghost_return()  # Throw invalid.ghost.assign

    # gi = ghost_simple(simple3())      # Throw invalid.ghost.call

    # i = simple(gi=0, i=gi)            # Throw invalid.ghost.call
    i = simple(gi=gi, i=0)              # OK

    return (i,1), (gi, gj)

# def mixed_return() -> Tuple[GInt, int]: #Throw invalid.ghost.annotation
#     pass

# def variadic(pos: int, *args: int, kw: str) -> int: # TODO: Properly support
#     return 0

def unpacking(i: int) -> None:
    gi: GInt = 0
    # j = bar(0,0)                          # Throw invalid.ghost.assign
    i, gi = bar(0, 0)                       # OK
    gtuple: Tuple[GInt, GInt] = bar(0,0)    # OK

    gk: GInt = 0
    r, (gi,gk) = reg_call()                 # OK
    # (i, gi), gtuple = reg_call()          # Throw invalid.ghost.assign

    i, j = r                                # OK
    gi, gk = r                              # OK
    # i, gi = r                             # Throw invalid.ghost.assign

    d: Dict[str,int] = {'i': 0, 'gi': 1}
    glist: GintList = [0, 1]                # OK
    i = simple(*r)                          # OK
    # i = simple(*gtuple)                   # Throw invalid.ghost.call
    # i = simple(*glist)                    # Throw invalid.ghost.call
    # i = simple(**d)

    # r, (gi, i) = reg_call()               # Throw invalid.ghost.assign

    # (i, glist[0]), (gi,gk) = reg_call()   # Throw invalid.ghost.assign

    # i = variadic(0, kw="")


# def pos_kw_only(pos1: int, pos2:int, /, any: int, *, kw: int) -> None:
#     pass

class RegClass:         # OK
    static = 0
    
    def __init__(self, i: int) -> None:
        self.fld = i
    
    @property
    def prop(self) -> int:              # OK
        return self.fld * 2
    
    @prop.setter
    def prop(self, i: int) -> None:     # OK
        self.fld = i // 2

    def simple(self) -> int:
        return 0

    def dot_notation(self) -> None:
        loc = RegClass.static           # OK
        loc = self.static               # OK
        loc = self.fld                  # OK

        loc = self.simple()             # OK
        
        strlst = "one two".split(" ")   # OK

def futureRef() -> 'GStr':
    gstr: GStr = "Valid"
    return gstr         # OK

GStr = str
MarkGhost(GStr)

# def returnAnn() -> Union[Optional[GStr], Union[int, str]]: # Throw invalid.ghost.annotation
    # return 0

# def varArgsAnn(*vars: int, **kwargs: GInt) -> None: # Throw invalid.ghost.annotation
#     pass

def control_flow(i: int, gi: GInt) -> None:
    if i == 0: 
        i = 1           # OK
        gi = 0          # OK
    
    if gi == 0:
        gi = 0          # OK
        # i = 0         # Throw invalid.ghost.assign

    while i < 2:
        i += 1          # OK
        gi += 1         # OK

    while gi < 5:
        gi += 1         # OK
        # i += 1        # Throw invalid.ghost.assign
    
    if i > 0:
        i += 1          # OK
        if gi != 5:
            gi = 0      # OK
        else:
            if i >= 2:
                gi = 6  # OK
                # i = 2 # Throw invalid.ghost.assign
    
    i += 1              # OK

    lst = [0,0]
    for x in lst:
        i += x          # OK
        gi += x         # OK
    
    glst: GintList = lst
    for y in glst:
        gi += y         # OK
        # i += y        # Throw invalid.ghost.assign
    
    lst2 = [(0,0), (1,1)]
    a: GInt = 0         # OK
    # for a,b in lst2:  # Throw invalid.ghost.For
    #     pass

    # assert gi >= 0    # Throw "Use the Assert contract function when working with ghost elements"

    while i < 5:
        i += 1
        if i == 4:
            break
        continue

    while i > 0:
        i -= 1
        if gi == 6:
            pass
            # break     # Throw invalid.ghost.break
    
    while i < 5:
        i += 1
        if gi == 6:
            gi -= 1
            # continue  # Throw invalid.ghost.continue
        lst.append(i)
    
    # if len(glst) > 0:
    #     gi = glst[0]

class NoInit(RegClass):  # OK

    def give_zero(self) -> int:
        return 0

def find_init() -> None:
    cls = NoInit(0)      # OK

    gi: GInt = 0
    # cls = NoInit(gi)   # Throw invalid.ghost.call

def comprehensions(lst: List[int]) -> None:
    newLst = [item * 2 for item in lst]                 # OK

    gi: GInt = 3
    # newLst = [item * gi for item in lst]              # Throw invalid.ghost.assign

    # newLst = [ghost_simple3(item) for item in lst]    # Throw invalid.ghost.assign

@Ghost
def foo(gi: int) -> int:                # OK
    gh_cls = GhostClass()
    gi = gh_cls.ghost_func(gi)          # OK
    # gi = simple(0,0)                  # Throw invalid.ghost.call

    global global_var
    # global_var = 1                    # Throw invalid.ghost.assign
    # del global_var                    # Throw invalid.ghost.delete

    glist: GintList = [0, 1]            # OK
    # glist[0] = 2                      # Throw invalid.ghost.assign
    # glist[0], gi = ghost_simple(gi)   # Throw invalid.ghost.assign

    if glist[0] != 2:
        pass
        # raise NotImplementedError     # Throw invalid.ghost.raise
    
    # assert glist[0] != 2              # Throw "Use the Assert contract function when working with ghost elements"

    # gi = ghost_simple(simple3())      # Throw invalid.ghost.call

    gi = ghost_simple2([0, 1, ghost_simple(0), 3])              # OK
    # gi = ghost_simple2([0, 1, ghost_simple(simple3()), 3])    # Throw invalid.ghost.call

    return gi                           # OK

@Ghost
def ghost_simple(i: int) -> int:
    return i

@Ghost
def ghost_simple2(l: List[int]) -> int:
    return l[0]

@Ghost
@Pure
def ghost_simple3(i: int) -> int:
    return i+2

@Ghost
def ghost_return() -> Tuple[Tuple[int, int], Tuple[GInt, int]]:
    return (0,1), (2,3)

@Ghost
class GhostClass:       # OK
    def __init__(self) -> None:
        pass

    def ghost_func(self, i: int) -> int:
        pass

@Ghost                  # OK with decorator, otherwise throw invalid.ghost.classDef
class SubClass(GhostClass): 
    pass


# --Test Importing--

from z_import_test.import_test import GBool as ImportedGBool, ghost_func
import z_import_test.import_test as imp_test

GBool = bool
MarkGhost(GBool)

def imports(b:GBool) -> ImportedGBool:
    return b        # OK

def imports2(b:GBool) -> imp_test.GBool:
    return b          # OK

@Ghost
def imported_func() -> None:
    gi = 0
    loc = ghost_func(gi)      # OK


# --Test Extractions--
def small_mixed_tuple() -> Tuple[int, GInt]:
    return 0,1

def extraction() -> None:
    # i = simple(*small_mixed_tuple())          # Throw invalid.ghost.starred
    # glst: List[GInt] = [*small_mixed_tuple()] # Throw invalid.ghost.starred

    ga: GInt = 0
    gb: GInt = 0
    ga, gb = small_mixed_tuple()
    # i = simple(0, simple3())                  # Throw invalid.ghost.call
    i = simple(0, ga)
    i = simple(gi=gb, i=0)
    pass
