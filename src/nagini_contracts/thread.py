from typing import Callable, Tuple, Any


class Thread :
    def __init__(self, group: object=None, target: Callable=None, name: str=None,
                 args: Tuple=None, kwargs: object=None, daemon: bool=None) -> None :
        pass

    def start(self, *method_list : Callable) -> None :
        pass

    def join(self, *method_list : Callable) -> None:
        pass


def getMethod(t: Thread) -> Callable:
    pass


def getArg(t: Thread, i: int) -> object:
    pass


def getOld(t: Thread, o: object) -> object:
    pass

def getARP(t: Thread) -> float:
    pass


def arg(i: int) -> Any:
    pass


def MayJoin(t: Thread) -> bool:
    pass


def MayStart(t: Thread) -> bool:
    pass


def ThreadPost(t: Thread) -> bool:
    pass