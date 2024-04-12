from nagini_contracts.contracts import *

#############################################
## Test builtin types                      ##
#############################################

a = +1
assert a == 1

b = -1
assert b == -1

c = ~1
assert c == -2

d = +True
assert d == 1
assert d == True

e = +False
assert e == 0
assert e == False

f = -True
assert f == -1

g = -False
assert g == 0

h = ~True
assert h == -2

i = ~False
assert i == -1


#############################################
## Test operator overloading               ##
#############################################

class Test():
  def __init__(self, a: int) -> None:
    self.a = a
    Ensures(Acc(self.a))
    Ensures(self.a == a)

  def __pos__(self) -> 'Test':
    Requires(Acc(self.a, 1/2))
    Ensures(Acc(self.a, 1/2) and Acc(Result().a))
    Ensures(Result().a == self.a)
    return Test(self.a)

  def __neg__(self) -> 'Test':
    Requires(Acc(self.a, 1/2))
    Ensures(Acc(self.a, 1/2) and Acc(Result().a))
    Ensures(Result().a == -self.a)
    return Test(-self.a)
  
t = Test(3)
t1 = +t
t2 = -t

assert t1.a == 3
assert t2.a == -3
assert t1.a == -t2.a