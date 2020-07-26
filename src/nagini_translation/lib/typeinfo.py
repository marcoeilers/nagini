"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import logging
import mypy.build
import os

from mypy.build import BuildSource
from nagini_translation.lib import config
from nagini_translation.lib.constants import IGNORED_IMPORTS, LITERALS
from nagini_translation.mypy_patches.visitor import TraverserVisitor
# from mypy.traverser import TraverserVisitor

from nagini_translation.lib.util import (
    construct_lambda_prefix,
)
from typing import List, Optional


logger = logging.getLogger('nagini_translation.lib.typeinfo')


def col(node) -> Optional[int]:
    """
    Returns the column in a mypy mypy AST node, if any.
    """
    if hasattr(node, 'column'):
        return node.column
    return None


class TypeException(Exception):
    def __init__(self, messages):
        self.messages = messages


class TypeVisitor(TraverserVisitor):
    def __init__(self, type_map, path, ignored_lines, real_path):
        self.prefix = []
        self.all_types = {}
        self.alt_types = {}
        self.type_map = type_map
        self.path = path
        self.ignored_lines = ignored_lines
        self.type_aliases = {}
        self.type_vars = {}
        self.real_path = real_path

    def _is_result_call(self, node: mypy.nodes.Node) -> bool:
        """Checks if call is either ``Result`` or ``RaisedException``."""
        if isinstance(node, mypy.nodes.CallExpr):
            if node.callee.name == 'Result':
                return True
            if node.callee.name == 'RaisedException':
                return True
        return False

    def visit_decorator(self, node: mypy.nodes.Decorator):
        self.visit_func_def(node.func)

    def visit_member_expr(self, node: mypy.nodes.MemberExpr):
        rectype = self.type_of(node.expr)
        if (not self._is_result_call(node.expr) and
                not isinstance(node.expr, mypy.nodes.IndexExpr) and
                not isinstance(rectype, mypy.types.CallableType) and
                not isinstance(rectype, str) and
                not isinstance(rectype, mypy.types.AnyType) and
                not isinstance(rectype, mypy.types.TypeVarType)):
            if isinstance(rectype, mypy.types.UnionType):
                # Collext all non-None elements of the union,
                # taking nested unions into account.
                utypes = [rectype]
                uindex = 0
                types = []
                while uindex < len(utypes):
                    for i in utypes[uindex].items:
                        if isinstance(i, mypy.types.UnionType):
                            utypes.append(i)
                        elif not isinstance(i, mypy.types.NoneTyp):
                            types.append(i)
                    uindex += 1
            else:
                types = [rectype]
            for t in types:
                if isinstance(t, mypy.types.AnyType):
                    if t.type_of_any == mypy.types.TypeOfAny.from_error:
                        continue
                if isinstance(t, mypy.types.TypeType):
                    continue
                if not hasattr(t, 'type'):
                    t = t.partial_fallback   # 'TupleType' object has no attribute 'type'
                if isinstance(t, mypy.types.Instance) and t.type.fullname.startswith('builtins.'):
                    continue
                self.set_type(t.type.fullname.split('.') + [node.name],
                              self.type_of(node),
                              node.line, col(node))
        super().visit_member_expr(node)

    def visit_del_stmt(self, node: mypy.nodes.DelStmt):
        pass

    def visit_try_stmt(self, node: mypy.nodes.TryStmt):
        for var in node.vars:
            if var is not None:
                self.set_type(self.prefix + [var.name], self.type_of(var),
                              var.line, col(var))
        super().visit_try_stmt(node)

    def visit_assignment_stmt(self, node: mypy.nodes.AssignmentStmt):
        if (isinstance(node.rvalue, mypy.nodes.IndexExpr) and
                isinstance(node.rvalue.analyzed, mypy.nodes.TypeAliasExpr)):
            # If it's a type alias, process it as such.
            key = tuple(self.prefix + [node.lvalues[0].name])
            self.type_aliases[key] = node.rvalue.analyzed.type
        elif (isinstance(node.rvalue, mypy.nodes.CallExpr) and
                isinstance(node.rvalue.analyzed, mypy.nodes.TypeVarExpr)):
            key = tuple(self.prefix + [node.rvalue.analyzed._name])
            self.type_vars[key] = (node.rvalue.analyzed.upper_bound,
                                   node.rvalue.analyzed.values)
        else:
            super().visit_assignment_stmt(node)

    def visit_name_expr(self, node: mypy.nodes.NameExpr):
        is_alias = False
        if node.name == '_':
            return
        for i in range(len(self.prefix)):
            key = tuple(self.prefix[:i] + [node.name])
            if key in self.type_aliases:
                is_alias = True
                break
        if (node.name not in LITERALS and not is_alias):
            name_type = self.type_of(node)
            if not isinstance(name_type, mypy.types.CallableType):
                self.set_type(self.prefix + [node.name], name_type,
                              node.line, col(node))

    def visit_star_expr(self, node: mypy.nodes.StarExpr):
        self.visit(node.expr)

    def visit_func_def(self, node: mypy.nodes.FuncDef):
        oldprefix = self.prefix
        self.prefix = self.prefix + [node.name]
        functype = self.type_of(node)
        self.set_type(self.prefix, functype, node.line, col(node), True)
        for arg in node.arguments:
            self.set_type(self.prefix + [arg.variable.name],
                          arg.variable.type, arg.line, col(arg))
        super().visit_func_def(node)
        self.prefix = oldprefix

    def visit_lambda_expr(self, node: mypy.nodes.LambdaExpr):
        oldprefix = self.prefix
        prefix_string = construct_lambda_prefix(node.line, col(node))
        self.prefix = self.prefix + [prefix_string]
        for arg in node.arguments:
            self.set_type(self.prefix + [arg.variable.name],
                          arg.variable.type, arg.line, col(arg))
        self.visit(node.body)
        self.prefix = oldprefix

    def visit_class_def(self, node: mypy.nodes.ClassDef):
        oldprefix = self.prefix
        self.prefix = self.prefix + [node.name]
        super().visit_class_def(node)
        self.prefix = oldprefix

    def startswith(self, l1, l2):
        return len(l2) <= len(l1) and all(l1[i] == ele for i, ele in enumerate(l2))

    def set_type(self, fqn, type, line, col, return_type=False):
        if self.real_path is not None:
            if self.startswith(fqn, self.real_path):
                fqn = ['__main__'] + fqn[len(self.real_path):]
        if return_type and isinstance(type, mypy.types.CallableType):
            type = type.ret_type
        if not type or isinstance(type, mypy.types.AnyType):
            if line in self.ignored_lines:
                return
            else:
                error = ' error: Encountered Any type. Type annotation missing?'
                msg = ':'.join([self.path, str(line), error])
                raise TypeException([msg])
        key = tuple(fqn)
        if key in self.all_types:
            if not self.type_equals(self.all_types[key], type):
                # Type change after isinstance
                if key not in self.alt_types:
                    self.alt_types[key] = {}
                self.alt_types[key][(line, col)] = type
                return
        self.all_types[key] = type

    def type_equals(self, t1, t2):
        if str(t1) == str(t2):
            return True
        if (isinstance(t1, mypy.types.FunctionLike) and
                isinstance(t2, mypy.types.FunctionLike)):
            if self.type_equals(t1.ret_type, t2.ret_type):
                all_eq = True
                for arg1, arg2 in zip(t1.arg_types, t2.arg_types):
                    all_eq = all_eq and self.type_equals(arg1, arg2)
                return all_eq
        return t1 == t2

    def visit_call_expr(self, node: mypy.nodes.CallExpr):
        if (isinstance(node.callee, mypy.nodes.NameExpr) and
                node.callee.fullname in ('typing.cast', 'typing.NamedTuple')):
            return
        if isinstance(node.callee, mypy.nodes.SuperExpr):
            return
        for a in node.args:
            self.visit(a)
        self.visit(node.callee)

    def type_of(self, node):
        if hasattr(node, 'node') and isinstance(node.node, mypy.nodes.MypyFile):
            return node.fullname
        if hasattr(node, 'node') and isinstance(node.node, mypy.nodes.TypeInfo):
            return node.fullname
        if isinstance(node, mypy.nodes.FuncDef):
            if node.type:
                return node.type
        if isinstance(node, mypy.nodes.NameExpr):
            key = (node.name,)
            if key in self.all_types:
                return self.all_types[key]
        elif isinstance(node, mypy.nodes.CallExpr):
            if node.callee.name == 'Result':
                key = tuple(self.prefix)
                for i in range(len(key)):
                    if key[i].startswith('lambda'):
                        key = key[:i]
                        break
                type = self.all_types[key]
                return type
        if node in self.type_map:
            result = self.type_map[node]
            return result
        elif hasattr(node, 'fullname'):
            fullname = node.fullname.split('.')
            if self.real_path is not None:
                if self.startswith(fullname, self.real_path):
                    fullname = ['__main__'] + fullname[len(self.real_path):]
            if tuple(fullname) in self.type_vars:
                result = self.type_vars[tuple(fullname)]
                return result
        msg = self.path + ':' + str(node.get_line()) + ': error: '
        if isinstance(node, mypy.nodes.FuncDef):
            msg += 'Encountered Any type. Type annotation missing?'
        else:
            msg += 'dead.code'
        raise TypeException([msg])

    def visit_comparison_expr(self, o: mypy.nodes.ComparisonExpr):
        # Weird things seem to happen with is-comparisons, so we ignore those.
        if 'is' not in o.operators and 'is not' not in o.operators:
            super().visit_comparison_expr(o)


class TypeInfo:
    """
    Provides type information for all variables and functions in a given
    Python module.
    """

    def __init__(self):
        self.all_types = {}
        self.alt_types = {}
        self.files = {}
        self.type_aliases = {}
        self.type_vars = {}

    def _create_options(self, strict_optional: bool):
        """
        Creates an Options object for mypy and activates strict optional typing
        based on the given argument.
        As long as mypy actually ignores these options, this will also set
        the STRICT_OPTIONAL flag in the experimental module to the given value.
        """
        result = mypy.options.Options()
        result.strict_optional = strict_optional
        result.show_none_errors = strict_optional
        result.show_traceback = True
        result.export_types = True
        result.preserve_asts = True
        result.warn_no_return = False
        result.incremental = False
        # This is an experimental feature atm and you actually have to
        # enable it like this
        return result

    def check(self, filename: str, base_dir: str = None) -> bool:
        """
        Typechecks the given file and collects all type information needed for
        the translation to Viper
        """

        def report_errors(errors: List[str]) -> None:
            for error in errors:
                logger.info(error)
            raise TypeException(errors)

        module_name = None
        if base_dir is not None:
            relpath = os.path.relpath(filename, base_dir)
            if '..' not in relpath:
                relpath = relpath.replace('/', '.').replace('\\', '.')
                if relpath.endswith('.py'):
                    relpath = relpath[:-3]
                elif relpath.endswith('.pyi'):
                    relpath = relpath[:-4]
                module_name = relpath
        try:
            options_strict = self._create_options(True)
            res_strict = mypy.build.build(
                [BuildSource(filename, module_name, None, base_dir=base_dir)],
                options_strict
                )

            if res_strict.errors:
                # Run mypy a second time with strict optional checking disabled,
                # s.t. we don't get overapproximated none-related errors.
                options_non_strict = self._create_options(False)
                res_non_strict = mypy.build.build(
                    [BuildSource(filename, module_name, None, base_dir=base_dir)],
                    options_non_strict
                )
                if res_non_strict.errors:
                    report_errors(res_non_strict.errors)
            relevant_files = [next(iter(res_strict.graph))]
            i = 0
            while i < len(relevant_files):
                name = relevant_files[i]
                for dep_name in res_strict.graph[name].dep_line_map:
                    if dep_name in IGNORED_IMPORTS:
                        continue
                    if dep_name not in relevant_files:
                        relevant_files.append(dep_name)
                i += 1
            relevant_files = [(name, res_strict.files[name]) for name in relevant_files]
            for name, file in relevant_files:
                real_name = None
                if name == module_name:
                    real_name = name.split('.')
                    name = '__main__'
                self.files[name] = file.path
                visitor = TypeVisitor(res_strict.types, name,
                                      file.ignored_lines, real_name)
                visitor.prefix = name.split('.')
                visitor.visit(file)
                self.all_types.update(visitor.all_types)
                self.alt_types.update(visitor.alt_types)
                self.type_aliases.update(visitor.type_aliases)
                self.type_vars.update(visitor.type_vars)
            return True
        except mypy.errors.CompileError as e:
            report_errors(e.messages)

    def get_type_prefix(self, name: str) -> str:
        name = os.path.abspath(name)
        for prefix, path in self.files.items():
            path = os.path.abspath(path)
            # If we run tests, we can be in the situation that there is a nagini_contracts directory in the site-
            # packages and one in the source folder. This workaround ensures that we Nagini treats them as identical.
            if prefix.startswith('nagini_contracts'):
                if 'nagini_contracts' in name:
                    relative_name = name[name.index('nagini_contracts'):]
                    relative_path = path[path.index('nagini_contracts'):]
                    if relative_path == relative_name:
                        return prefix
            if path == name:
                return prefix
        return None

    def get_type(self, prefix: List[str], name: str):
        """
        Looks up the inferred or annotated type for the given name in the given
        prefix
        """
        key = tuple(prefix + [name])
        result = self.all_types.get(key)
        alts = self.alt_types.get(key)
        if result is None:
            if not prefix:
                return None, None
            else:
                return self.get_type(prefix[:len(prefix) - 1], name)
        else:
            return result, alts

    def get_func_type(self, prefix: List[str]):
        """
        Looks up the type of the function which creates the given context
        """
        result = self.all_types.get(tuple(prefix))
        if result is None:
            if len(prefix) == 0:
                return None
            else:
                return self.get_func_type(prefix[:len(prefix) - 1])
        else:
            if isinstance(result, mypy.types.FunctionLike):
                result = result.ret_type
            return result

    def is_normal_type(self, type: mypy.types.Type) -> bool:
        return isinstance(type, mypy.nodes.TypeInfo)

    def is_instance_type(self, type: mypy.types.Type) -> bool:
        return isinstance(type, mypy.types.Instance)

    def is_tuple_type(self, type: mypy.types.Type) -> bool:
        return isinstance(type, mypy.types.TupleType)

    def is_void_type(self, type: mypy.types.Type) -> bool:
        return isinstance(type, mypy.types.NoneTyp)

    def is_union_type(self, type: mypy.types.Type) -> bool:
        return isinstance(type, mypy.types.UnionType)

    def is_callable_type(self, type: mypy.types.Type) -> bool:
        return isinstance(type, mypy.types.CallableType)

    def is_type_type(self, type: mypy.types.Type) -> bool:
        return isinstance(type, mypy.types.TypeType)

    def is_type_alias_type(self, type: mypy.types.Type) -> bool:
        return isinstance(type, mypy.types.TypeAliasType)

    def is_any_type_from_error(self, type: mypy.types.Type) -> bool:
        if isinstance(type, mypy.types.AnyType):
            if type.type_of_any == mypy.types.TypeOfAny.from_error:
                return True
            if type.type_of_any == mypy.types.TypeOfAny.from_another_any:
                return self.is_any_type_from_error(type.source_any)
        return False

    def is_type_var(self, type: mypy.types.Type) -> bool:
        return isinstance(type, mypy.types.TypeVarType)

    def is_none_type(self, type: mypy.types.Type) -> bool:
        return isinstance(type, mypy.types.NoneTyp)
