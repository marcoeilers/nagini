import ast


class Cache:

    def __init__(self):
        self._nodes = {}

    def reset(self) -> None:
        self._nodes = {}

    def __getitem__(self, item: str) -> ast.AST:
        return self._nodes[item]

    def __setitem__(self, key: str, value: ast.AST) -> None:
        self._nodes[key] = value

    def __contains__(self, key: str) -> bool:
        return key in self._nodes

cache = Cache()