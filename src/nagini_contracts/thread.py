from typing import Callable, Tuple, Any


class Thread :
    def __init__(self, m : Callable, args : Tuple) -> None :
        pass

    def start(self, *methodlist : Callable) -> None :
        pass

    def join(self, *methodlist : Callable) -> None:
        pass


def getArg(t: Thread, i: int) -> object:
    pass

def getOld(t: Thread, o: object) -> object:
    pass

def arg(i: int) -> Any:
    pass