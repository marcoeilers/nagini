import ast


class Cache:

    def __init__(self):
        self.nodes = {}

    def reset(self) -> None:
        self.nodes = {}

    def __getitem__(self, item: str) -> ast.AST:
        return self.nodes[item]

    def __setitem__(self, key: str, value: ast.AST) -> None:
        self.nodes[key] = value

cache = Cache()