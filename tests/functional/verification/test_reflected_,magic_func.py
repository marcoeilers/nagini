from nagini_contracts.contracts import *

############################################
##  Basic tests                           ##
############################################

class A():
  def __add__(self, other: 'B') -> 'A':
    return A()

class B():
  pass
  
r1 = A() + B()


# __add__ of left operand takes priority
class C():
  def __add__(self, other: 'D') -> 'C':
    return C()
  
class D():
  def __add__(self, other: 'C') -> 'D':
    Requires(False)
    assert False
  
r2 = C() + D()


# __add__ prefered over __radd__
class E():
  def __add__(self, other: 'E') -> 'E':
    return E()
  
  def __radd__(self, other: 'E') -> 'E':
    Requires(False)
    assert False
  
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

r4 = F() + G()


# If left operand has no matching __add__, check for __radd__ on right operand
class H():
  pass

class I():
  def __radd__(self, other: 'H') -> 'I':
    return I()
  
r5 = H() + I()


class F1():
  def __radd__(self, other: 'G1') -> 'F1':
    Requires(False)
    assert False

class G1():
  def __radd__(self, other: 'F1') -> 'F1':
    return F1()

r41 = F1() + G1()


class H1():
  def __add__(self, other: int) -> 'H1':
    Requires(False)
    assert False

class I1(H1):
  def __radd__(self, other: 'H1') -> 'H1':
    return I1()
  
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

class P():
  def __add__(self, other: 'P') -> 'P':
    return P()
  
  def __radd__(self, other: 'P') -> 'P':
    Requires(False)
    assert False
  
class Q(P):
  pass

r9 = P() + Q()

class R():
  pass
  
class S(R):
  def __radd__(self, other: 'R') -> 'R':
    return R()

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

r12 = X() + Y()