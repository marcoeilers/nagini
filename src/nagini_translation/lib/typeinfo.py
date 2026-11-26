"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import logging
import mypy.build
import os
import re
import tokenize

from mypy.build import BuildSource
from mypy.checkexpr import has_any_type
from mypy.plugin import Plugin
from mypy.type_visitor import TypeQuery
from mypy.typevars import fill_typevars_with_any
from nagini_translation.lib import phases
from nagini_translation.lib.constants import IGNORED_IMPORTS, LITERALS
from nagini_translation.mypy_patches.visitor import TraverserVisitor

from nagini_translation.lib.util import (
    char_columns,
    construct_lambda_prefix,
)
from typing import Dict, List, NamedTuple, Optional


logger = logging.getLogger('nagini_translation.lib.typeinfo')


class HasTypeObject(TypeQuery[bool]):
    """Whether a type has a part that is a class seen as its constructor."""

    def strategy(self, items: List[bool]) -> bool:
        return any(items)

    def visit_callable_type(self, t: mypy.types.CallableType) -> bool:
        return t.is_type_obj() or super().visit_callable_type(t)

    def visit_overloaded(self, t: mypy.types.Overloaded) -> bool:
        return t.is_type_obj() or super().visit_overloaded(t)


# A message of mypy or of the type collector; only mypy's has the column and
# the end position. The file group is non-greedy so a Windows drive letter
# (``C:\...``) or a ``: error:`` inside the message is not mistaken for the
# separators.
MESSAGE = re.compile(
    r"^(?P<file>.*?):(?P<line>\d+)"
    r"(?::(?P<col>\d+)(?::(?P<end_line>\d+):(?P<end_col>\d+))?)?"
    r": (?P<severity>error|note): (?P<msg>.*)$")


class ContractPlugin(Plugin):
    """
    Gives Result() the return type of the function whose contract it is in
    and RaisedException() the exception type of the Exsures it is in.
    """

    CONTRACTS = 'nagini_contracts.contracts.'

    def __init__(self, options) -> None:
        super().__init__(options)
        self.raised = None

    def get_function_signature_hook(self, fullname: str):
        # called before the arguments of the call are checked
        if fullname == self.CONTRACTS + 'Exsures':
            return self._enter_exsures
        return None

    def get_function_hook(self, fullname: str):
        return {
            self.CONTRACTS + 'Result': self._result_type,
            self.CONTRACTS + 'RaisedException': self._raised_type,
            self.CONTRACTS + 'Exsures': self._leave_exsures,
        }.get(fullname)

    def _result_type(self, ctx) -> mypy.types.Type:
        function = next((scope for scope in reversed(ctx.api.scope.stack)
                         if isinstance(scope, mypy.nodes.FuncDef)), None)
        signature = function and mypy.types.get_proper_type(function.type)
        if isinstance(signature, mypy.types.CallableType):
            return signature.ret_type
        return ctx.default_return_type

    def _enter_exsures(self, ctx) -> mypy.types.CallableType:
        exception = ctx.args[0][0] if ctx.args and ctx.args[0] else None
        info = getattr(exception, 'node', None)
        self.raised = (fill_typevars_with_any(info)
                       if isinstance(info, mypy.nodes.TypeInfo) else None)
        return ctx.default_signature

    def _raised_type(self, ctx) -> mypy.types.Type:
        return self.raised or ctx.default_return_type

    def _leave_exsures(self, ctx) -> mypy.types.Type:
        self.raised = None
        return ctx.default_return_type


class TypeException(Exception):
    def __init__(self, messages):
        self.messages = messages


class LocatedTypeError(NamedTuple):
    """An error of a TypeException: 0-based columns, and the end (exclusive)
    if mypy gave one."""
    file: str
    line: int
    col: int
    end_line: Optional[int]
    end_col: Optional[int]
    msg: str


def type_error(message: str, main_file: str = '__main__') -> Optional[LocatedTypeError]:
    """The error that the given message of a TypeException reports, if it is
    one, with main_file as the file of the checked module."""
    match = MESSAGE.match(message)
    if not match or match['severity'] != 'error':
        return None
    return LocatedTypeError(
        main_file if match['file'] == '__main__' else match['file'],
        int(match['line']),
        int(match['col']) - 1 if match['col'] else 0,
        int(match['end_line']) if match['end_line'] else None,
        int(match['end_col']) if match['end_col'] else None,
        match['msg'])


class TypeVisitor(TraverserVisitor):
    def __init__(self, type_map, path, ignored_lines, real_path, source=''):
        self.char_column = char_columns(source)
        self.prefix = []
        self.all_types = {}
        self.alt_types = {}
        self.ghost_names = {}
        self.type_map = type_map
        self.expr_types = {}
        self.path = path
        self.ignored_lines = ignored_lines
        self.type_aliases = {}
        self.type_vars = {}
        self.real_path = real_path

    def col(self, node) -> Optional[int]:
        """The column of a mypy AST node, if any, as the analyzer has it."""
        if hasattr(node, 'column'):
            return self.char_column(node.line, node.column)
        return None

    def _is_result_call(self, node: mypy.nodes.Node) -> bool:
        """Checks if call is either ``Result`` or ``RaisedException``."""
        if isinstance(node, mypy.nodes.CallExpr) and isinstance(node.callee, mypy.nodes.NameExpr):
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
                    if hasattr(t, 'partial_fallback'):
                        t = t.partial_fallback
                    elif hasattr(t, 'fallback'):
                        t = t.fallback
                    else:
                        continue
                if isinstance(t, mypy.types.Instance) and t.type.fullname.startswith('builtins.'):
                    continue
                self.set_type(t.type.fullname.split('.') + [node.name],
                              self.type_of(node),
                              node.line, self.col(node))
        super().visit_member_expr(node)

    def visit_del_stmt(self, node: mypy.nodes.DelStmt):
        pass

    def visit_try_stmt(self, node: mypy.nodes.TryStmt):
        for var in node.vars:
            if var is not None:
                self.set_type(self.prefix + [var.name], self.type_of(var),
                              var.line, self.col(var))
        super().visit_try_stmt(node)

    def visit_assignment_stmt(self, node: mypy.nodes.AssignmentStmt):
        analyzed = getattr(node.rvalue, "analyzed", None)
        if isinstance(analyzed, mypy.nodes.TypeAliasExpr):
            key = tuple(self.prefix + [node.lvalues[0].name])
            self.type_aliases[key] = analyzed.node.target
        elif isinstance(analyzed, mypy.nodes.TypeVarExpr):
            key = tuple(self.prefix + [analyzed.name])
            self.type_vars[key] = (analyzed.upper_bound, analyzed.values)
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
            # References to functions are not recorded, but a class object is
            # also typed as a callable (its constructor), and those are
            # ordinary values that do need a recorded type.
            is_function_ref = (isinstance(name_type, mypy.types.CallableType) and
                               not name_type.is_type_obj())
            if not is_function_ref:
                self.set_type(self.prefix + [node.name], name_type,
                              node.line, self.col(node))

    def visit_star_expr(self, node: mypy.nodes.StarExpr):
        self.visit(node.expr)

    def visit_func_def(self, node: mypy.nodes.FuncDef):
        oldprefix = self.prefix
        self.prefix = self.prefix + [node.name]
        functype = self.type_of(node)
        self.set_type(self.prefix, functype, node.line, self.col(node), True)
        for arg in node.arguments:
            self.set_type(self.prefix + [arg.variable.name],
                          arg.variable.type, arg.line, self.col(arg))
        super().visit_func_def(node)
        self.prefix = oldprefix

    def visit_lambda_expr(self, node: mypy.nodes.LambdaExpr):
        oldprefix = self.prefix
        prefix_string = construct_lambda_prefix(node.line, self.col(node))
        self.prefix = self.prefix + [prefix_string]
        for arg in node.arguments:
            self.set_type(self.prefix + [arg.variable.name],
                          arg.variable.type, arg.line, self.col(arg))
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
            if (str(type) != str(self.all_types[key]) and
                    any(isinstance(t, mypy.types.Overloaded)
                        for t in (type, self.all_types[key]))):
                error = ' error: Overloaded function or method {} is used at different types.'.format(fqn[-1])
                raise TypeException([':'.join([self.path, str(line), error])])
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
        if isinstance(node.callee, mypy.nodes.NameExpr) and node.callee.name == 'ResultT':
            return
        if isinstance(node.callee, mypy.nodes.NameExpr) and node.callee.name == 'MarkGhost':
            # Verify MarkGhost call and collect ghost names
            if len(node.args) != 1:
                msg = self.path + ':' + str(node.line) + ': error: MarkGhost may only define one ghost name at a time.'
                raise TypeException([msg])
            ghost_type = node.args[0]
            if not isinstance(ghost_type.node, mypy.nodes.TypeAlias):
                msg = self.path + ':' + str(node.line) + ': error: MarkGhost takes only Type aliases.'
                raise TypeException([msg])
            if not self.path in self.ghost_names:
                self.ghost_names[self.path] = set()
            curr_set = self.ghost_names[self.path]
            if ghost_type.name in curr_set:
                msg = self.path + ':' + str(node.line) + ': error: MarkGhost may only define ghost names once.'
                raise TypeException([msg])
            curr_set.add(ghost_type.name)
        if (isinstance(node.callee, mypy.nodes.RefExpr) and
                isinstance(node.callee.node, mypy.nodes.TypeInfo)):
            self.record_expr_type(node)
        for a in node.args:
            self.visit(a)
        self.visit(node.callee)

    def visit_list_expr(self, node: mypy.nodes.ListExpr):
        self.record_expr_type(node)
        super().visit_list_expr(node)

    def visit_set_expr(self, node: mypy.nodes.SetExpr):
        self.record_expr_type(node)
        super().visit_set_expr(node)

    def visit_dict_expr(self, node: mypy.nodes.DictExpr):
        self.record_expr_type(node)
        super().visit_dict_expr(node)

    def visit_tuple_expr(self, node: mypy.nodes.TupleExpr):
        self.record_expr_type(node)
        super().visit_tuple_expr(node)

    def record_expr_type(self, node: mypy.nodes.Expression):
        """
        Records mypy's type for a collection literal or a constructor call,
        whose type arguments mypy infers from the context (an annotation, the
        callee's parameter, an enclosing literal) as well as the elements.
        A type mypy made of classes seen as their constructors is not recorded.
        """
        expr_type = self.type_map.get(node)
        if (expr_type is not None and not has_any_type(expr_type)
                and not expr_type.accept(HasTypeObject())):
            self.expr_types[(node.line, self.col(node))] = expr_type

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
            # Note: do not fall back to a previously recorded type for the
            # qualified name here. mypy's own type for this node reflects
            # narrowing by isinstance, whereas the recorded one is whatever the
            # name had at its first occurrence, so preferring it would stop alt
            # types from ever being collected.
        if node in self.type_map:
            result = self.type_map[node]
            return result
        if hasattr(node, 'node') and isinstance(node.node, mypy.nodes.TypeAlias):
            return node.fullname
        elif hasattr(node, 'fullname'):
            fullname = node.fullname.split('.')
            if self.real_path is not None:
                if self.startswith(fullname, self.real_path):
                    fullname = ['__main__'] + fullname[len(self.real_path):]
            if tuple(fullname) in self.type_vars:
                result = self.type_vars[tuple(fullname)]
                return result
        msg = self.path + ':' + str(node.line) + ': error: '
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
        self.expr_types = {}
        self.files = {}
        self.sources = {}
        self.type_aliases = {}
        self.type_vars = {}
        self.ghost_names = {}
        self.module_name = None
        self.imports = None  # name -> path of the modules the checked file imports

    def _create_options(self, strict_optional: bool):
        """
        Creates an Options object for mypy and activates strict optional typing
        based on the given argument.
        As long as mypy actually ignores these options, this will also set
        the STRICT_OPTIONAL flag in the experimental module to the given value.
        """
        result = mypy.options.Options()
        result.strict_optional = strict_optional
        result.show_traceback = True
        # Emit "file:line:col:end_line:end_col: error: msg" so that reported type
        # errors carry a real source range (start and end) instead of only a
        # line, matching the format Nagini produces for verification errors.
        # show_error_end implies show_column_numbers.
        result.show_column_numbers = True
        result.show_error_end = True
        result.export_types = True
        result.preserve_asts = True
        result.warn_no_return = False
        # mypy's nodes are matched with those of Python's parser by position
        result.native_parser = False
        # Since we run mypy twice with different options, we use different cache dirs for different configurations,
        # otherwise Mypy throws away the cache every time.
        result.cache_dir = '.mypy_cache_strict' if strict_optional else '.mypy_cache_nonstrict'
        return result

    def _build(self, filename: str, module_name: str, base_dir: str, options):
        """
        Runs mypy on the given file. Nagini reads the typed ASTs of the file
        and of everything it transitively imports, and mypy builds those in
        full only for the sources of a build whose text it is given: a module
        it loads from its cache has no AST, and one it finds among the
        installed packages is checked only as far as its interface needs. So
        the file is built alone to learn what it imports, and then together
        with those modules, each where mypy found it.
        """
        if self.imports is None:
            result = self._mypy(filename, module_name, base_dir, options, {})
            self.imports = self._import_paths(result)
            if not self.imports:
                return result
        result = self._mypy(filename, module_name, base_dir, options, self.imports)
        if self._import_paths(result) != self.imports:
            raise Exception('mypy builds of %s differ in what it imports.' % filename)
        return result

    def _import_paths(self, result) -> Dict[str, str]:
        """Name -> path of the modules the main module of the given mypy build
        imports, see _imported."""
        paths = {name: result.graph[name].path
                 for name in self._imported(result)[1:]}
        return {name: path for name, path in paths.items()
                if path and os.path.isfile(path)}

    def _mypy(self, filename: str, module_name: str, base_dir: str, options,
              imports: Dict[str, str]):
        sources = [self._source(filename, module_name, base_dir)]
        sources += [self._source(path, name, base_dir)
                    for name, path in imports.items()]
        return mypy.build.build(sources, options,
                                extra_plugins=[ContractPlugin(options)])

    def _source(self, path: str, module_name: str, base_dir: str) -> BuildSource:
        with tokenize.open(path) as f:
            text = self.sources[os.path.abspath(path)] = f.read()
        return BuildSource(path, module_name, text, base_dir=base_dir)

    def _char_positions(self, message: str) -> str:
        """The given message of mypy with the columns of its position, UTF-8
        byte offsets, as character offsets."""
        match = MESSAGE.match(message)
        source = match and self.sources.get(os.path.abspath(match['file']))
        if not source or not match['col']:
            return message
        char_column = char_columns(source)
        position = '%s:%d' % (
            match['line'], char_column(int(match['line']), int(match['col']) - 1) + 1)
        if match['end_col']:
            position += ':%s:%d' % (
                match['end_line'],
                char_column(int(match['end_line']), int(match['end_col'])))
        return '%s:%s: %s: %s' % (match['file'], position, match['severity'],
                                  match['msg'])

    def _imported(self, result) -> List[str]:
        """The main module of the given mypy build and every module it
        transitively imports, except IGNORED_IMPORTS and what only those
        import."""
        names = [next(iter(result.graph))]
        for name in names:
            state = result.graph[name]
            for dep_name in state.dep_line_map:
                # a module loaded from the cache also lists the modules its
                # types refer to
                if (state.priorities.get(dep_name) != mypy.build.PRI_INDIRECT
                        and dep_name in result.graph
                        and dep_name not in IGNORED_IMPORTS
                        and dep_name not in names):
                    names.append(dep_name)
        return names

    def check(self, filename: str, base_dir: str = None,
              confirm: bool = True) -> bool:
        """
        Typechecks the given file and collects all type information needed for
        the translation to Viper. With ``confirm``, any errors of the first
        strict build are confirmed by a second non-strict one.
        """

        def report_errors(errors: List[str]) -> None:
            for error in errors:
                logger.info(error)
            raise TypeException([self._char_positions(e) for e in errors])

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
        self.module_name = module_name
        try:
            options_strict = self._create_options(True)

            with phases.phase('typecheck.strict'):
                res_strict = self._build(filename, module_name, base_dir,
                                         options_strict)

            # An implicit-None return incompatibility exists only under
            # strict-optional overapproximation: with strict_optional=False,
            # None is compatible with every return type, so this error class
            # ALWAYS vanishes in the confirmation build below. A batch
            # consisting solely of such errors needs no confirmation build —
            # this skips a full second mypy pass on the common
            # agent-in-development file shape.
            confirmable = [e for e in res_strict.errors
                           if 'implicitly returns "None"' not in e]
            if confirmable and confirm:
                # Run mypy a second time with strict optional checking disabled,
                # s.t. we don't get overapproximated none-related errors.
                options_non_strict = self._create_options(False)
                with phases.phase('typecheck.nonstrict'):
                    res_non_strict = self._build(filename, module_name, base_dir,
                                                 options_non_strict)
                if res_non_strict.errors:
                    report_errors(res_non_strict.errors)
            with phases.phase('typecheck.visit'):
                self._collect(res_strict, module_name)
            return True
        except mypy.errors.CompileError as e:
            report_errors(e.messages)

    def _collect(self, result, module_name: str) -> None:
        """Collects the type information of the main file of the given mypy
        build and of everything it transitively imports."""
        relevant_files = [(name, result.graph[name]) for name in self._imported(result)]

        for name, file_graph in relevant_files:
            file = file_graph.tree
            real_name = None
            if name == module_name:
                real_name = name.split('.')
                name = '__main__'
            self.files[name] = file.path
            visitor = TypeVisitor(result.types, name,
                                  file.ignored_lines, real_name,
                                  self.sources.get(os.path.abspath(file.path), ''))
            visitor.prefix = name.split('.')
            visitor.visit(file)
            self.all_types.update(visitor.all_types)
            self.alt_types.update(visitor.alt_types)
            for (line, column), expr_type in visitor.expr_types.items():
                self.expr_types[(name, line, column)] = expr_type
            self.type_aliases.update(visitor.type_aliases)
            self.type_vars.update(visitor.type_vars)
            self.ghost_names.update(visitor.ghost_names)

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

    def get_expr_type(self, module: str, line: int, column: int):
        """
        Looks up the recorded type of the collection literal or constructor
        call at the given position of the given module, if any.
        """
        return self.expr_types.get((module, line, column))

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

    def is_literal_type(self, type: mypy.types.Type) -> bool:
        return isinstance(type, mypy.types.LiteralType)

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

    def is_overloaded_type(self, type: mypy.types.Type) -> bool:
        return isinstance(type, mypy.types.Overloaded)

    def is_type_alias_type(self, type: mypy.types.Type) -> bool:
        return isinstance(type, mypy.types.TypeAliasType)

    def is_partial_type(self, type: mypy.types.Type) -> bool:
        return isinstance(type, mypy.types.PartialType)

    def is_uninhabited_type(self, type: mypy.types.Type) -> bool:
        return isinstance(type, mypy.types.UninhabitedType)

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

    def is_literal_type(self, type: mypy.types.Type) -> bool:
        return isinstance(type, mypy.types.LiteralType)
