# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from typing import Sized


class Whatever(Sized):
    def __len__(self) -> int:
        return 15