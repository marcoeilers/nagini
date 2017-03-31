import ast

from nagini_translation.lib.typedefs import Expr
from typing import List, Optional


class ExprCache:
    """
    Container for the results of an already translated expression.
    """
    def __init__(self):
        self._results = []
        self._idx = 0

    def next(self) -> Optional[Expr]:
        """
        Returns the next result expr or None if there are no more available.
        """
        res = None
        if self._idx < len(self._results):
            res = self._results[self._idx]
            self._idx += 1

        return res

    def add_result(self, result: Expr):
        self._results.append(result)

    def __len__(self) -> int:
        return len(self._results)


class ExprCacheMixin:
    """
    A mixin that can be used by translators that want to cache translation
    results.
    """
    def __init__(self):
        # Map of already translated expressions.
        self._translated_exprs = {}  # Map[ast.AST, ExprCache]

    def _try_cache(self, node: ast.AST) -> Expr:
        if node in self._translated_exprs:
            expr = self._translated_exprs[node].next()
            if not len(self._translated_exprs[node]):
                del self._translated_exprs[node]
            return expr
        return None

    def _cache_results(self, node: ast.AST, results: List[Expr]):
        cache = ExprCache()
        for res in results:
            cache.add_result(res)
        self._translated_exprs[node] = cache
