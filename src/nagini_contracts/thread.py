"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

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
    """
    Return the ith element passed to the thread constructor in the ``args`` parameter,
    unless the thread target passed to the constructor contained a receiver object, in
    which case this will return the (i+1)th argument element from the ``args`` tuple
    and the receiver object is treated as the argument with index zero.

    t = Thread(target=foo, args=(x, y, z))  # getArg(t, 0) == x, getArg(t, 2) == z
    t = thread(target=o.bar, args=(x, y, z))  # getArg(t, 0) == o, getArg(t, 1) == x
    """
    pass


def getOld(t: Thread, o: object) -> object:
    """
    Return the value of expression o when thread t was started.
    o must be an expression mentioned in an old-expression in the postcondition of the
    thread's target method, in which references to parameter i of the target method are
    replaces by arg(i) (see below).
    """
    pass


def getARP(t: Thread) -> float:
    """
    Returns the permission value of abstract read permissions passed to thread t.
    """
    pass


def arg(i: int) -> Any:
    """Used to reference method parameters in getOld() calls."""
    pass


def Joinable(t: Thread) -> bool:
    """
    Represents that thread t is joinable.
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
    Holding some permission to ThreadPost for a thread implies that the thread
    is joinable; it is not necessary to write ThreadPost and Joinable.
    """
    pass
