from typing import Dict, List, Union

def test_implicit_function_call_1(o: Union[List[int], Dict[int, int]]) -> int:
    return o[0]

def test_implicit_method_call_1(o: Union[List[int], Dict[int, int]]) -> None:
    o[0] = 5
