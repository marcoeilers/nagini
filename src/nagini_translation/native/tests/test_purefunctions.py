"""
    fixpoint PyClass PyClass_ObjectType(){
            return ObjectType;
    }

    //WARNING: Pure function purefunction has a predicate in its precondition. => Not translated

    fixpoint SOMETYPEPURE_purefunction1(i__ptr, i__val){
            return ((i__val > 0) ? (18 + 1) : ((i__val < 0) ? 0 : (18 * 2)));
    }

    predicate PRED_mypredicate(i__ptr, i__val) = (i__val > 0);
    /*--END OF ENV--*/
"""
from nagini_contracts.contracts import *


@Predicate
def mypredicate(i: int) -> bool:
    return i > 0


@Pure
def purefunction(i: int) -> int:
    Requires(i > 0)
    Requires(mypredicate(i))
    y = 18
    if (i > 0):
        y = y + 1
    elif (i < 0):
        return 0
    else:
        y = y * 2
        return y
    return y


@Pure
def purefunction1(i: int) -> int:
    Requires(i > 0)
    y = 18
    if (i > 0):
        y = y + 1
    elif (i < 0):
        return 0
    else:
        y = y * 2
        return y
    return y


@ContractOnly
@Native
def mytest(i: int) -> int:
    """
    """
    Requires(purefunction(i) > 0)
    Requires(purefunction1(i) > 0)
