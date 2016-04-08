import ast

from py2viper_translation.abstract_translator import (
    CommonTranslator,
    TranslatorConfig,
    Expr,
    StmtAndExpr,
    Stmt
)
from py2viper_translation.analyzer import (
    PythonClass,
    PythonMethod,
    PythonVar,
    PythonTryBlock
)
from py2viper_translation.util import InvalidProgramException
from toposort import toposort_flatten
from typing import List, Tuple, Optional, Union, Dict, Any

class PredicateTranslator(CommonTranslator):

    def translate_predicate(self, pred: PythonMethod,
                            ctx) -> 'ast.silver.Predicate':
        """
        Translates pred to a Silver predicate.
        """
        if pred.type.name != 'bool':
            raise InvalidProgramException(pred.node, 'invalid.predicate')
        assert ctx.current_function is None
        ctx.current_function = pred
        args = []
        for arg in pred.args:
            args.append(pred.args[arg].decl)
        body = self.translate_exprs(pred.node.body, pred, ctx)
        ctx.current_function = None
        return self.viper.Predicate(pred.sil_name, args, body,
                                    self.to_position(pred.node, ctx),
                                    self.noinfo(ctx))

    def translate_predicate_family(self, root: PythonMethod,
            preds: List[PythonMethod], ctx) -> 'ast.silver.Predicate':
        """
        Translates the methods in preds, whose root (which they all override)
        is root, to a family-predicate in Silver.
        """
        dependencies = {}
        for pred in preds:
            value = {pred.overrides} if pred.overrides else set()
            dependencies[pred] = value
        sorted = toposort_flatten(dependencies)

        name = root.sil_name
        args = []
        self_var_ref = root.args[next(iter(root.args))].ref
        for arg in root.args:
            args.append(root.args[arg].decl)
        body = None
        assert not ctx.var_aliases
        for instance in sorted:
            ctx.var_aliases = {}
            assert not ctx.current_function
            if instance.type.name != 'bool':
                raise InvalidProgramException(instance.node,
                                              'invalid.predicate')
            ctx.current_function = instance
            for root_name, current_name in zip(root.args.keys(),
                                               instance.args.keys()):
                root_var = root.args[root_name]
                ctx.var_aliases[current_name] = root_var
            if len(instance.node.body) != 1:
                raise InvalidProgramException(instance.node,
                                              'invalid.predicate')
            stmt, current = self.translate_expr(instance.node.body[0], ctx)
            if stmt:
                raise InvalidProgramException(instance.node,
                                              'invalid.predicate')
            has_type = self.type_factory.has_type(self_var_ref, instance.cls,
                                                  ctx)
            implication = self.viper.Implies(has_type, current,
                self.to_position(instance.node, ctx), self.noinfo(ctx))
            ctx.current_function = None
            if body:
                body = self.viper.And(body, implication,
                    self.to_position(root.node, ctx), self.noinfo(ctx))
            else:
                body = implication
        ctx.var_aliases = None
        return self.viper.Predicate(name, args, body,
                                    self.to_position(root.node, ctx),
                                    self.noinfo(ctx))