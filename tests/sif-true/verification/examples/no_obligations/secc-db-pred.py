# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

"""
Example adapted from https://bitbucket.org/covern/secc/src/master/examples/case-studies/
"""

from nagini_contracts.contracts import *
from typing import List, Tuple, Optional


class Elem:
    def __init__(self, key: int, value: int) -> None:
        self.key = key
        self.value = value
        self.next = None  # type: Optional[Elem]

"""
/* An array of elems of length n storing  arbitrary values.
 * Describes the empty heap region if n <= 0 */
_(predicate ar(elem_t *a, int n)
  n > 0 ==> exists int k, int v. &a->key |-> k && &a->value |-> v && ar(a + 1, n - 1))

/* An key/value array all of whose values have the security level associated
 * with their key. */
_(predicate ar_sec(elem_t *a, int n)
  n > 0 ==> exists int k, int v. &a->key |-> k && &a->value |-> v && k :: low && v :: label(k) && ar_sec(a + 1, n - 1))
"""

@Pure
@ContractOnly
def global_label() -> int:
    pass

@Predicate
def ar(a: Optional[Elem], n: int) -> bool:
    return Implies(n > 0,
                   Acc(a.key) and Acc(a.value) and Acc(a.next) and ar(a.next, n - 1))



@Predicate
def ar_sec(a: Optional[Elem], n: int) -> bool:
    return Implies(n > 0,
                   Acc(a.key) and Acc(a.value) and Acc(a.next) and Low(a.key) and Implies(a.key > global_label(), Low(a.value))
                   and ar_sec(a.next, n-1))

@Pure
def ar_sec_last(a: Optional[Elem], n: int) -> Optional[Elem]:
    Requires(n >= 0)
    Requires(ar_sec(a, n))
    return Unfolding(ar_sec(a, n), a if n == 0 else ar_sec_last(a.next, n - 1))

"""
void ar_sec_snoc(elem_t *a, int n)
_(requires n >= 0)
_(requires n :: low)
_(requires ar_sec(a,n))
  _(requires exists int k, int v. &(a+n)->key |-> k && &(a+n)->value |-> v && k :: low && v :: label(k))
_(ensures ar_sec(a,n+1))
_(lemma)
{
  if (n == 0){
    _(unfold ar_sec(a,n))
    _(fold ar_sec(a+1,0))
    _(fold ar_sec(a,1))
  }else{
    _(unfold ar_sec(a,n))
    _(apply ar_sec_snoc(a+1,n-1);)
    _(fold ar_sec(a,n+1))
  }
}
"""

def ar_sec_snoc(a: Optional[Elem], n: int) -> None:
    Requires(n >= 0)
    Requires(type(n) == int)
    Requires(Low(n))
    Requires(ar_sec(a, n))
    Requires(Acc(ar_sec_last(a, n).key) and Acc(ar_sec_last(a, n).value) and Acc(ar_sec_last(a, n).next))
    Requires(Low(ar_sec_last(a, n).key) and Implies(ar_sec_last(a, n).key > global_label(), Low(ar_sec_last(a, n).value)))
    Ensures(ar_sec(a, n + 1))
    Ensures(ar_sec_last(a, n + 1) is Old(ar_sec_last(a, n).next))
    if n == 0:
        Unfold(ar_sec(a, n))
        Fold(ar_sec(a.next, 0))
        Fold(ar_sec(a, 1))
    else:
        Unfold(ar_sec(a, n))
        ar_sec_snoc(a.next, n-1)
        Fold(ar_sec(a, n+1))

"""
void ar_sec_join(elem_t *a, int n, int m)
_(requires n >= 0 && m >= 0)
_(requires n :: low && m :: low)
_(requires ar_sec(a,n) && ar_sec(a+n,m))
_(ensures ar_sec(a,n+m))
_(lemma)
{
  if (n == 0){
    _(unfold ar_sec(a,n))
  }else{
    _(unfold ar_sec(a,n))
    _(apply ar_sec_join(a+1,n-1,m);)
    _(fold ar_sec(a,n+m))
  }
}
"""

def ar_sec_join(a: Optional[Elem], n: int, m: int) -> None:
    Requires(n >= 0 and m >= 0)
    Requires(type(n) == int)
    Requires(type(m) == int)
    Requires(Low(n) and Low(m))
    Requires(ar_sec(a, n) and ar_sec(ar_sec_last(a, n), m))
    Ensures(ar_sec(a, n + m))
    if n == 0:
        Assert(ar_sec_last(a, n) is a)
        Assert(n + m is m)
        Unfold(ar_sec(a, n))

    else:
        Unfold(ar_sec(a, n))
        ar_sec_join(a.next, n-1, m)
        Fold(ar_sec(a, n+m))

SUCCESS = 0
FAILURE = 1

"""
int lookup(elem_t *elems, int len, int key, int *valueOut)
  _(requires ar_sec(elems,len))
  _(requires len :: low)
  _(requires key :: low)
  _(requires len >= 0)
  _(requires exists int oldOut. valueOut |-> oldOut)
  _(ensures exists int out. valueOut |-> out)
  _(ensures result == SUCCESS ==> out :: label(key))
  _(ensures result == FAILURE ==> out == oldOut)
  _(ensures result == SUCCESS || result == FAILURE)
  _(ensures ar_sec(elems,len))
{
  int i = 0;
  elem_t *p = elems;
  int ret = FAILURE;
  _(fold ar_sec(elems,0))
  while (i < len && ret == FAILURE)
    _(invariant i >= 0 && i <= len)
    _(invariant ret :: low && i :: low)
    _(invariant ret == SUCCESS ==> exists int v. valueOut |-> v && v :: label(key)) 
    _(invariant ret == FAILURE ==> valueOut |-> oldOut)
    _(invariant ret == SUCCESS || ret == FAILURE)
    _(invariant ret >= SUCCESS && ret <= FAILURE)
    _(invariant ar_sec(p,len-i))
    _(invariant ar_sec(elems,i))
    _(invariant p == elems + i)
    {
    _(unfold ar_sec(p,len - i))
    if (p->key == key){
      *valueOut = p->value;
      ret = SUCCESS;
    }
    p++;
    _(apply ar_sec_snoc(elems,i);)    
    i++;
  }
  _(apply ar_sec_join(elems,i,len-i);)
  return ret;
}
"""

@Predicate
def dummy(i: int) -> bool:
    return Low(i) and Implies(i > 0, dummy(i - 1))

def lookup(elems: Optional[Elem], len: int, key: int) -> Tuple[int, int]:
    Requires(dummy(15))
    Requires(ar_sec(elems, len))
    Requires(Low(len) and Low(key))
    Requires(len >= 0)
    Requires(type(len) == int)
    Ensures(ar_sec(elems, len))
    Ensures(Implies(Result()[0] == SUCCESS, Implies(key > global_label(), Low(Result()[1]))))
    Ensures(Implies(Result()[0] == FAILURE, Result()[1] == -1))
    Ensures(Result()[0] == SUCCESS or Result()[0] == FAILURE)
    Assume(type(len) == int)
    i = 0
    p = elems
    Fold(ar_sec(elems, 0))
    while i < len:
        Invariant(type(i) == int)
        Invariant(i >= 0 and i <= len)
        Invariant(Low(i) and LowExit())
        Invariant(ar_sec(p, len-i))
        Invariant(ar_sec(elems, i))
        Invariant(ar_sec_last(elems, i) is p)
        Invariant(dummy(15))
        #Invariant(Acc(list_pred(elems)) and Low(len(elems)))
        #Invariant(Forall(int, lambda j: (Implies(j >= 0 and j < len(elems), Acc(elems[j].key) and Acc(elems[j].value) and Low(elems[j].key) and Implies(elems[j].key is key, Low(elems[j].value))), [[elems[j]]])))
        #Assert(ar_sec(p, len - i))
        Unfold(dummy(15))
        Unfold(ar_sec(p, len-i))
        if p.key is key:
            res = p.value
            Fold(ar_sec(p, len-i))
            Assume(False)
            return (SUCCESS, res)
        p = p.next
        ar_sec_snoc(elems, i)
        i += 1
        Fold(dummy(15))
    ar_sec_join(elems, i, len - i)
    return (FAILURE, -1)


# def binsearch(elems: List[Elem], from_: int, l: int, key: int) -> Tuple[int, int]:
#     Requires(Acc(list_pred(elems)))
#     Requires(Low(l) and Low(key) and Low(from_))
#     Requires(0 <= from_ and from_ + l <= len(elems))
#     Requires(Forall(int, lambda i: (Implies(i >= 0 and i < len(elems), Acc(elems[i].key) and Acc(elems[i].value) and Low(elems[i].key) and Implies(elems[i].key is key, Low(elems[i].value))), [[elems[i]]])))
#     Ensures(Acc(list_pred(elems)))
#     Ensures(Forall(int, lambda i: (Implies(i >= 0 and i < len(elems), Acc(elems[i].key) and Acc(elems[i].value) and Low(elems[i].key) and Implies(elems[i].key is key, Low(elems[i].value))), [[elems[i]]])))
#     Ensures(Implies(Result()[0] == SUCCESS, Low(Result()[1])))
#     Ensures(Implies(Result()[0] == FAILURE, Result()[1] == -1))
#     Ensures(Result()[0] == SUCCESS or Result()[0] == FAILURE)
#
#     if l <= 0:
#         return FAILURE, -1
#
#     mid = l // 2
#
#     e = elems[from_ + mid]
#     k = e.key
#     if k is key:
#         return SUCCESS, elems[from_ + mid].value
#     else:
#         if l == 1:
#             return FAILURE, -1
#         #Assume(SplitOn(k > key))
#         if k > key:
#             return binsearch(elems, from_, mid - 1, key)
#         else:
#             return binsearch(elems, from_ + mid + 1, l - (mid + 1), key)

#
# def sum_all(elems: List[Elem], key: int) -> int:
#     Requires(Acc(list_pred(elems)))
#     Requires(Low(len(elems)) and Low(key))
#     Requires(Forall(int, lambda i: (Implies(i >= 0 and i < len(elems), Acc(elems[i].key) and Acc(elems[i].value) and Low(elems[i].key) and Implies(elems[i].key is key, Low(elems[i].value))), [[elems[i]]])))
#     Ensures(Acc(list_pred(elems)))
#     Ensures(Forall(int, lambda i: (Implies(i >= 0 and i < len(elems), Acc(elems[i].key) and Acc(elems[i].value) and Low(elems[i].key) and Implies(elems[i].key is key, Low(elems[i].value))), [[elems[i]]])))
#     Ensures(Low(Result()))
#
#     sum = 0
#     i = 0
#     while i < len(elems):
#         Invariant(Acc(list_pred(elems)) and Low(len(elems)))
#         Invariant(i >= 0 and i <= len(elems))
#         Invariant(Low(sum) and Low(i))
#         Invariant(Forall(int, lambda j: (Implies(j >= 0 and j < len(elems), Acc(elems[j].key) and Acc(elems[j].value) and Low(elems[j].key) and Implies(elems[j].key is key, Low(elems[j].value))), [[elems[j]]])))
#
#         if elems[i].key is key:
#             sum += elems[i].value
#         i += 1
#     return sum
#
#
# def sum_all_rec(elems: List[Elem], from_: int, l: int, key: int, init: int) -> int:
#     Requires(Acc(list_pred(elems)))
#     Requires(Low(l) and Low(key) and Low(from_) and Low(init))
#     Requires(0 <= from_ and from_ + l <= len(elems))
#     Requires(Forall(int, lambda i: Implies(i >= 0 and i < len(elems), Acc(elems[i].key) and Acc(elems[i].value) and Low(elems[i].key) and Implies(elems[i].key is key, Low(elems[i].value)))))
#     Ensures(Acc(list_pred(elems)))
#     Ensures(Forall(int, lambda i: Implies(i >= 0 and i < len(elems), Acc(elems[i].key) and Acc(elems[i].value) and Low(elems[i].key) and Implies(elems[i].key is key, Low(elems[i].value)))))
#     Ensures(Low(Result()))
#
#     if l > 0:
#         e = elems[from_]
#         if e.key is key:
#             return sum_all_rec(elems, from_ + 1, l - 1, key, init + e.value)
#         else:
#             return sum_all_rec(elems, from_ + 1, l - 1, key, init)
#     else:
#         return init
#
#
# def remove_all(elems: List[Elem], key: int) -> None:
#     Requires(Acc(list_pred(elems)))
#     Requires(Low(len(elems)) and Low(key))
#     Requires(Forall(int, lambda i: (Implies(i >= 0 and i < len(elems), Acc(elems[i].key) and Acc(elems[i].value) and Low(elems[i].key) and Implies(elems[i].key is key, Low(elems[i].value))), [[elems[i]]])))
#     Ensures(Acc(list_pred(elems)))
#     Ensures(Forall(int, lambda i: (Implies(i >= 0 and i < len(elems), Acc(elems[i].key) and Acc(elems[i].value) and Low(elems[i].key) and Implies(elems[i].key is key, Low(elems[i].value))), [[elems[i]]])))
#
#     i = 0
#     while i < len(elems):
#         Invariant(Acc(list_pred(elems)) and Low(len(elems)))
#         Invariant(i >= 0 and i <= len(elems))
#         Invariant(Low(i))
#         Invariant(Forall(int, lambda j: (Implies(j >= 0 and j < len(elems), Acc(elems[j].key) and Acc(elems[j].value) and Low(elems[j].key) and Implies(elems[j].key is key, Low(elems[j].value))), [[elems[j]]])))
#
#         if elems[i].key is key:
#             elems[i].value = 0
#         i += 1
