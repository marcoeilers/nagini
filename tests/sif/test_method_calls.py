def foo(x: int) -> int:
    return 2 * x

def bar(x: int) -> int:
    return x - 2

class A:
    def m1(self, x: int) -> int:
        return x

    def m2(self, x: int) -> bool:
        return x > 2

def main() -> None:
    x = 25 * foo(bar(5))
    a = A()
    b = a.m2(a.m1(x))
