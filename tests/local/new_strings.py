# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


def main() -> None:
    my_string = "abcde" + "f"
    Assert(my_string == "abcdef")
    Assert(my_string != "foobar")
    my_string2 = ""
    Assert(my_string2 == "")
    # Assert(my_string[:3] == "abc")


if __name__ == "__main__":
    main()



