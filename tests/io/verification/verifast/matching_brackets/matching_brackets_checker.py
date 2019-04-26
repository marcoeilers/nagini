# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import (
    Old,
    Acc,
    ContractOnly,
    Ensures,
    Requires,
    Result,
    Assert,
)
from nagini_contracts.io_contracts import *
from nagini_contracts.io_builtins import (
    no_op_io,
    NoOp,
)
from nagini_contracts.obligations import (
    MustTerminate,
)
from verifast.stdio_simple import (
    stdin,
    stdout,
    write_char_io,
    putchar,
    read_char_io,
    getchar,
)
from typing import Tuple, Optional


@IOOperation
def brackets_io(
        t_read1: Place,
        read1: str,
        read5: str = Result(),
        valid: bool = Result(),
        t_read5: Place = Result()) -> bool:
    return IOExists11(
               bool, bool, bool, bool,
               str, str, str, str,
               Place, Place, Place)(
        lambda success1, success2, subvalid1, subvalid2,
               read2, read3, read4, read5,
               t_read2, t_read3, t_read4: (
            (
                read_char_io(t_read1, stdin, read2, success1, t_read2) and
                brackets_io(t_read2, read2, read3, subvalid1, t_read3) and
                read_char_io(t_read3, stdin, read4, success2, t_read4) and
                brackets_io(t_read4, read4, read5, subvalid2, t_read5) and
                valid == (subvalid1 and read3 is ')' and subvalid2)
            ) if read1 is '('
            else (
                no_op_io(t_read1, t_read5) and
                read5 is read1 and
                valid == (read1 is None or read1 is ')')
            )
        )
    )


class Matcher:

    def __init__(self) -> None:
        Requires(MustTerminate(1))
        Ensures(Acc(self.c))
        self.c = None   # type: Optional[str]

    def pop_read_ahead(self, t1: Place) -> Tuple[Place, Optional[str]]:
        IOExists3(str, bool, Place)(
            lambda new_char, success, t2: (
                Requires(
                    Acc(self.c) and
                    token(t1, 2) and
                    read_char_io(t1, stdin, new_char, success, t2)
                ),
                Ensures(
                    Acc(self.c) and
                    self.c is new_char and
                    Old(self.c) is Result()[1] and
                    token(t2) and
                    t2 == Result()[0]
                )
            )
        )
        c_copy = self.c
        self.c, success, t2 = getchar(t1)
        return (t2, c_copy)

    def peek_read_ahead(self) -> Optional[str]:
        Requires(Acc(self.c, 1/2))
        Requires(MustTerminate(1))
        Ensures(Acc(self.c, 1/2) and Result() is self.c)
        return self.c

    def brackets(self, t_read1: Place) -> Tuple[Place, bool]:
        IOExists3(str, bool, Place)(
            lambda read5, valid, t_read5: (
                Requires(
                    Acc(self.c) and
                    brackets_io(t_read1, self.c, read5, valid, t_read5) and
                    token(t_read1, 3)
                ),
                Ensures(
                    Acc(self.c) and
                    self.c is read5 and
                    token(t_read5) and
                    t_read5 == Result()[0] and
                    valid == Result()[1]
                ),
            )
        )

        Open(brackets_io(t_read1, self.c))
        if self.peek_read_ahead() is '(':
            t_read2, _ = self.pop_read_ahead(t_read1)
            t_read3, brackets1 = self.brackets(t_read2)
            t_read4, c = self.pop_read_ahead(t_read3)
            should_be_close = (c is ')')
            t_read5, brackets2 = self.brackets(t_read4)
            return t_read5, (brackets1 and should_be_close and brackets2)
        else:
            i = self.peek_read_ahead()
            t_read2 = NoOp(t_read1)
            if i is None:
                return t_read2, True    # Empty string because of read EOF.
            elif self.peek_read_ahead() is ')':
                return t_read2, True    # Match empty string because read ')'.
            else:
                return t_read2, False   # No match because read invalid
                                        # character.


def main(t1: Place) -> Place:
    IOExists8(str, Place, str, bool, Place, Place, bool, bool)(
        lambda read_ahead, t_read_ahead, read_last, valid, t_brackets_end, t_end,
               success1, success2: (
            Requires(
                token(t1) and
                read_char_io(t1, stdin, read_ahead, success1, t_read_ahead) and
                brackets_io(t_read_ahead, read_ahead, read_last, valid, t_brackets_end) and
                read_last is None and
                write_char_io(t_brackets_end, stdout, ('1' if valid else '0'), success2, t_end)
            ),
            Ensures(
                token(t_end) and
                t_end == Result()
            ),
        )
    )

    m = Matcher()
    m.c, success, t2 = getchar(t1)
    t3, match = m.brackets(t2)
    if match:
        success, t4 = putchar('1', t3)
    else:
        success, t4 = putchar('0', t3)
    return t4
