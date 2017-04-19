import ast

from nagini_translation.lib.constants import BOOL_TYPE
from nagini_translation.lib.util import InvalidProgramException
from nagini_translation.lib.program_nodes import PythonMethod
from nagini_translation.translators.abstract import Context
from nagini_translation.translators.common import CommonTranslator
from toposort import toposort_flatten
from typing import List


class PredicateTranslator(CommonTranslator):

    def translate_predicate(self, pred: PythonMethod,
                            ctx: Context) -> 'ast.silver.Predicate':
        """
        Translates pred to a Silver predicate.
        """
        if not pred.type or pred.type.name != BOOL_TYPE:
            raise InvalidProgramException(pred.node, 'invalid.predicate')
        assert ctx.current_function is None
        ctx.current_function = pred
        args = []
        arg_types = self.viper.TrueLit(self.no_position(ctx), self.no_info(ctx))
        for name, arg in pred.args.items():
            args.append(arg.decl)
            arg_type = self.type_check(arg.ref(), arg.type,
                                       self.no_position(ctx), ctx)
            arg_types = self.viper.And(arg_types, arg_type,
                                       self.no_position(ctx), self.no_info(ctx))
        body = self.to_bool(self.translate_exprs(pred.node.body, pred, ctx),
                            ctx)
        body = self.viper.And(arg_types, body, self.no_position(ctx),
                              self.no_info(ctx))
        ctx.current_function = None
        return self.viper.Predicate(pred.sil_name, args, body,
                                    self.to_position(pred.node, ctx),
                                    self.no_info(ctx))

    def translate_predicate_family(self, root: PythonMethod,
                                   preds: List[PythonMethod],
                                   ctx: Context) -> 'ast.silver.Predicate':
        """
        Translates the methods in preds, whose root (which they all override)
        is root, to a family-predicate in Silver.
        """
        dependencies = {}
        for pred in preds:
            value = {pred.overrides} if pred.overrides else set()
            dependencies[pred] = value
        sorted = toposort_flatten(dependencies, False)

        name = root.sil_name
        args = []
        self_var_ref = root.args[next(iter(root.args))].ref()
        arg_types = self.viper.TrueLit(self.no_position(ctx), self.no_info(ctx))
        for arg in root.args.values():
            args.append(arg.decl)
            arg_type = self.type_check(arg.ref(), arg.type,
                                       self.no_position(ctx), ctx)
            arg_types = self.viper.And(arg_types, arg_type,
                                       self.no_position(ctx), self.no_info(ctx))
        body = None
        assert not ctx.var_aliases
        for instance in sorted:
            ctx.var_aliases = {}
            assert not ctx.current_function
            if instance.type.name != BOOL_TYPE:
                raise InvalidProgramException(instance.node,
                                              'invalid.predicate')
            ctx.current_function = instance
            ctx.module = instance.module
            for root_name, current_name in zip(root.args.keys(),
                                               instance.args.keys()):
                if root_name != next(iter(root.args.keys())):
                    root_var = root.args[root_name]
                    ctx.set_alias(current_name, root_var)
            if len(instance.node.body) != 1:
                raise InvalidProgramException(instance.node,
                                              'invalid.predicate')
            stmt, current = self.translate_expr(
                    instance.node.body[0],
                    ctx,
                    target_type=self.viper.Bool,
                    expression=True)
            if stmt:
                raise InvalidProgramException(instance.node,
                                              'invalid.predicate')
            has_type = self.type_factory.type_check(self_var_ref, instance.cls,
                                                    self.to_position(
                                                        instance.node, ctx),
                                                    ctx)
            implication = self.viper.Implies(has_type, current,
                self.to_position(instance.node, ctx), self.no_info(ctx))
            ctx.current_function = None
            if body:
                body = self.viper.And(body, implication,
                    self.to_position(root.node, ctx), self.no_info(ctx))
            else:
                body = implication
        ctx.var_aliases = {}
        body = self.viper.And(arg_types, body, self.no_position(ctx),
                              self.no_info(ctx))
        return self.viper.Predicate(name, args, body,
                                    self.to_position(root.node, ctx),
                                    self.no_info(ctx))
