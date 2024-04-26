from nagini_contracts.contracts import *

############################################
##  Basic tests                           ##
############################################

class A():
  def __add__(self, other: 'B') -> 'A':
    return A()

class B():
  pass

def basic_add_test() -> None:  
  r1 = A() + B()  


# __add__ of left operand takes priority
class C():
  def __add__(self, other: 'D') -> 'C':
    return C()
  
class D():
  def __add__(self, other: 'C') -> 'D':
    Requires(False)
    assert False

def basic_add_test_2() -> None:  
  r2 = C() + D()


# __add__ prefered over __radd__
class E():
  def __add__(self, other: 'E') -> 'E':
    return E()
  
  def __radd__(self, other: 'E') -> 'E':
    Requires(False)
    assert False

def add_and_radd_test() -> None:  
  r3 = E() + E()


# Left operand takes precedence over right operand
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

def left_operand_precedence_test() -> None:
  r4 = F() + G()


# If left operand has no matching __add__, check for __radd__ on right operand
class H():
  pass

class I():
  def __radd__(self, other: 'H') -> 'I':
    return I()

def basic_radd_test() -> None:  
  r5 = H() + I()


class F1():
  def __radd__(self, other: 'G1') -> 'F1':
    Requires(False)
    assert False

class G1():
  def __radd__(self, other: 'F1') -> 'F1':
    return F1()

def basic_radd_test_2() -> None:
  r41 = F1() + G1()


class H1():
  def __add__(self, other: int) -> 'H1':
    Requires(False)
    assert False

class I1(H1):
  def __radd__(self, other: 'H1') -> 'H1':
    return I1()

def incompatible_add_test() -> None:  
  r51 = H1() + I1()


############################################
##  Subtyped operands                     ##
############################################

# If operand inherits magic functions from supertype
# without overriding them, treat operand as usual
class J():
  def __add__(self, other: int) -> 'J':
    Requires(False)
    assert False
  
  def __radd__(self, other: int) -> 'J':
    return J()
  
class K(J):
  pass

def basic_subclass_test() -> None:
  r6 = 2 + K()

class L():
  def __add__(self, other: int) -> 'L':
    return L()
  
  def __radd__(self, other: int) -> 'L':
    Requires(False)
    assert False
  
class M(L):
  pass
def basic_subclass_test_2() -> None:
  r7 = M() + 2

class P():
  def __add__(self, other: 'P') -> 'P':
    return P()
  
  def __radd__(self, other: 'P') -> 'P':
    Requires(False)
    assert False
  
class Q(P):
  pass

def basic_subclass_test_3() -> None:
  r9 = P() + Q()

class R():
  pass
  
class S(R):
  def __radd__(self, other: 'R') -> 'R':
    return R()

def basic_subclass_test_4() -> None:
  r10 = R() + S()


# If right operand is subtype of left operand, and
# right operand provides its own implementation of
# __radd__, prefer this reflected function before
# __add__ from left operand
class N():
  def __add__(self, other: 'N') -> 'N':
    Requires(False)
    assert False
  
  def __radd__(self, other: 'N') -> 'N':
    Requires(False)
    assert False
  
class O(N):
  def __radd__(self, other: 'N') -> 'N':
    return O()
  
def overridden_radd_test() -> None:
  r8 = N() + O()

class T():
  pass

class U(T):
  def __radd__(self: 'U', other: 'U') -> 'U':
    Requires(False)
    assert False
  
class V(U):
  def __radd__(self: 'V', other: 'T') -> 'V':
    return self

def overridden_radd_test_2() -> None:
  r11 = U() + V()

class W():
  pass

class X(W):
  def __add__(self: 'X', other: 'X') -> 'X':
    Requires(False)
    assert False

  def __radd__(self: 'X', other: 'X') -> 'X':
    Requires(False)
    assert False
  
class Y(X):
  def __radd__(self: 'Y', other: 'W') -> 'Y':
    return self

def overridden_radd_test_3() -> None:
  r12 = X() + Y()


class IntContainer():
  def __init__(self, i: int) -> None:
    self.i = i
    Ensures(Acc(self.i) and self.i == i)

  def __add__(self, other: 'IntContainer') -> 'IntContainer':
    Requires(Acc(self.i, 1/2) and Acc(other.i, 1/2))
    Ensures(Acc(self.i, 1/2) and Acc(other.i, 1/2))
    Ensures(Acc(Result().i) and Result().i == self.i + other.i)
    return IntContainer(self.i + other.i)
  

def failure() -> None:
  a = IntContainer(42)
  b = IntContainer(15)
  c = a + b

  assert c.i == 57
  #:: ExpectedOutput(assert.failed:assertion.false)
  assert c.i == 42

class Failure():
  def __add__(self, other: 'Failure') -> 'Failure':
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert False

def failure_2() -> None:
  a = Failure() + Failure()


class Z():
  def __init__(self, i: int) -> None:
    self.i = i
    Ensures(Acc(self.i) and self.i == i)

  def __add__(self, other: 'Z') -> 'Z':
    Requires(Acc(self.i, 1/2) and Acc(other.i, 1/2))
    Ensures(Acc(self.i, 1/2) and Acc(other.i, 1/2))
    Ensures(Acc(Result().i))
    return Z(0)

  def __radd__(self, other: 'Z') -> 'Z':
    Requires(Acc(self.i, 1/2) and Acc(other.i, 1/2))
    Ensures(Acc(self.i, 1/2) and Acc(other.i, 1/2))
    Ensures(Acc(Result().i))
    return Z(0)

class ZZ(Z):
  def __radd__(self, other: Z) -> 'ZZ':
    Requires(Acc(self.i, 1/2) and Acc(other.i, 1/2))
    Ensures(Acc(self.i, 1/2) and Acc(other.i, 1/2))
    Ensures(Acc(Result().i) and Result().i == self.i + other.i)
    return ZZ(self.i + other.i)

def failure_3() -> None:
  a = Z(42) + ZZ(42)

  assert a.i == 84
  #:: ExpectedOutput(assert.failed:assertion.false)
  assert a.i == 0
  