from typing import List


def get_odd_collatz(n: int) -> List[int]:
    #:: ExpectedOutput(invalid.program:partial.type)
    ans, x = [], n
    while x != 1:
        if x % 2 == 1:
            ans.append(x)
        x = x // 2 if x % 2 == 0 else x * 3 + 1
    ans.append(1)
    return sorted(ans)
