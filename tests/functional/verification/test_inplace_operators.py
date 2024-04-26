from nagini_contracts.contracts import *

def primitive_tests() -> None:
  a = 42

  a += 42
  assert a == 84

  a -= 42
  assert a == 42

  a *= 2
  assert a == 84

class A():
  def __init__(self, i: int) -> None:
    self.i = i
    Ensures(Acc(self.i))
    Ensures(self.i == i)

  def __add__(self, other: 'A') -> 'A':
    Requires(False)
    assert False

  def __iadd__(self, other: 'A') -> 'A':
    Requires(Acc(self.i) and Implies(self is not other, Acc(other.i, 1/2)))
    Ensures(Acc(self.i) and Implies(self is not other, Acc(other.i, 1/2)))
    Ensures(Implies(self is not other, self.i == Old(self.i) + other.i))
    Ensures(Implies(self is other, self.i == Old(self.i) + Old(self.i)))
    Ensures(self is Result())
    self.i += other.i
    return self
  
  def __sub__(self, other: 'A') -> 'A':
    Requires(Acc(self.i, 1/2) and Acc(other.i, 1/2))
    Ensures(Acc(self.i, 1/2) and Acc(other.i, 1/2))
    Ensures(Acc(Result().i) and Result().i == self.i - other.i)
    return A(self.i - other.i)
  
def overloaded_op_test() -> None:
  a = A(42)
  b = A(42)

  # Test inplace implementation
  a += b
  assert a.i == 84

  # Test fallback to normal implementation
  a -= b
  assert a.i == 42

  a += a
  assert a.i == 84

def failure() -> None:
  a = A(42)

  a += a
  #:: ExpectedOutput(assert.failed:assertion.false)
  assert a.i == 42

def failure2() -> None:
  a = A(42)

  a += A(42)

  a = a - a

  #:: ExpectedOutput(assert.failed:assertion.false)
  assert a.i != 0
