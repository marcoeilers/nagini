from nagini_contracts.contracts import *

class A():
  def __add__(self, other: 'B') -> 'A':
    return A()

class B():
  pass
  
r1 = A() + B()

class C():
  def __add__(self, other: 'D') -> 'C':
    return C()
  
class D():
  def __add__(self, other: 'C') -> 'D':
    Requires(False)
    assert False
  
r2 = C() + D()

class E():
  def __add__(self, other: 'E') -> 'E':
    return E()
  
  def __radd__(self, other: 'E') -> 'E':
    Requires(False)
    assert False
  
r3 = E() + E()

class F():
  def __add__(self, other: 'G') -> 'F':
    return F()
  
  def __radd__(self, other: 'G') -> 'F':
    Requires(False)
    assert False
  
class G():
  def __add__(self, other: 'F') -> 'F':
    Requires(False)
    assert False
  
  def __radd__(self, other: 'F') -> 'F':
    Requires(False)
    assert False

r4 = F() + G()

class H():
  pass

class I():
  def __radd__(self, other: 'H') -> 'I':
    return I()
  
r5 = H() + I()

class J():
  def __add__(self, other: int) -> 'J':
    Requires(False)
    assert False
  
  def __radd__(self, other: int) -> 'J':
    return J()
  
class K(J):
  pass

r6 = 2 + K()

class L():
  def __add__(self, other: int) -> 'L':
    return L()
  
  def __radd__(self, other: int) -> 'L':
    Requires(False)
    assert False
  
class M(L):
  pass

r7 = M() + 2

class N():
  def __add__(self, other: 'N') -> 'N':
    Requires(False)
    assert False
  
  def __radd__(self, other: 'N') -> 'N':
    Requires(False)
    assert False
  
class O(N):
  def __radd__(self, other: 'N') -> 'O':
    return O()
  
r8 = N() + O()

class P():
  def __add__(self, other: 'P') -> 'P':
    return P()
  
  def __radd__(self, other: 'P') -> 'P':
    Requires(False)
    assert False
  
class Q(P):
  pass

r9 = P() + Q()
