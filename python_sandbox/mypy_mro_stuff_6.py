from typing import Any, TypeVar
from functools import wraps
# from nagini_contracts.contracts import Pure

T = TypeVar('T')

def Pure(f) :
    @wraps(f)

    def wrapper(*args, **kwds):
        return f(*args, **kwds)
    return wrapper

class A:
    @Pure
    def __getattr__(self, name: str) -> Any:
        return "123"

a = A()
print(dir(a))
a.__dict__['foo'] = 'bar'
print(a.foo)
