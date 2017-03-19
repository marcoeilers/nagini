def cond(a: int) -> bool:
    return a > 5

def main() -> None:
    a = 10
    #:: ExpectedOutput(invalid.program:purity.violated)
    while cond(a):
        a = a - 1
