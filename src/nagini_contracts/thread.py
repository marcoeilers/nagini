from typing import Callable, Tuple, Any


class Thread:
    """
    A stub for threads with a similar interface as threading.Thread.
    Clients must give the constructor a target method; subclassing and overriding
    the run method is currently not supported.
    """
    def __init__(self, group: object=None, target: Callable=None, name: str=None,
                 args: Tuple=None, kwargs: object=None, daemon: bool=None) -> None :
        pass

    def start(self, *method_list : Callable) -> None:
        """
        Starts this thread; requires a permission to start it.
        method_list must include a reference to the actual target method of this thread
        that was passed to it upon creation.
        """
        pass

    def join(self, *method_list : Callable) -> None:
        """
        Joins this thread, requires a permission to do so. If a ThreadPost permission is
        held and the thread's actual target method is included in method_list, this will
        inhale the thread's postcondition.
        """
        pass


def getMethod(t: Thread) -> Callable:
    """Return the target method of a thread."""
    pass


def getArg(t: Thread, i: int) -> object:
    """Return the ith argument passed to the thread object upon creation."""
    pass


def getOld(t: Thread, o: object) -> object:
    """
    Return the value of expression o when thread t was started.
    o must be an expression mentioned in an old-expression in the postcondition of the
    thread's target method, in which references to parameter i of the target method are
    replaces by arg(i) (see below).
    """
    pass


def arg(i: int) -> Any:
    """Used to reference method parameters in getOld() calls."""
    pass


def MayJoin(t: Thread) -> bool:
    """
    A permission to join thread t.
    Threads may be joined if they promise to terminate.
    """
    pass


def MayStart(t: Thread) -> bool:
    """A permission to start a newly created thread. Can only be used once."""
    pass


def ThreadPost(t: Thread) -> bool:
    """
    A permission to get the postcondition of thread t after joining it.
    If only a fractional amount of permission to ThreadPost(t) is held when joining,
    only that fractional amount of the postcondition will be inhaled.
    """
    pass
