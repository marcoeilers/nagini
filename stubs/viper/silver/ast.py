from typing import Any, List

class Node:
    pass

class IdentifierPosition:
    def file(self) -> Any:
        pass
    def start(self) -> Any:
        pass
    def end(self) -> Any:
        pass
    def id(self) -> str:
        pass

class Info:
    pass

class NoInfo(Info):
    pass

class SimpleInfo(Info):
    def __init__(self, comment: List[str]) -> None:
        self.comment = comment
