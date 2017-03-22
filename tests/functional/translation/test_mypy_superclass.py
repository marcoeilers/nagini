from typing import Sized


class Whatever(Sized):
    def __len__(self) -> int:
        return 15