from typing import Callable, Tuple


class State :
    def __init__(self) -> None:
        pass


def CREATED() -> State :
    pass


def STARTED() -> State :
    pass


def JOINED() -> State :
    pass


class Thread :
    def __init__(self, m : Callable, args : Tuple) -> None :
        self.state = CREATED()

    def start(self, *methodlist : Callable) -> None :
        pass

    def join(self, *methodlist : Callable) -> None:
        pass

    def impl(self, method : Callable) -> bool:
        pass

    def getOld(self, i : int) -> object :
        pass

    def getArg(self, i : int) -> object :
        pass

    def hasStarted(self) -> bool :
        pass