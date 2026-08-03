"""
Copyright (c) 2026 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

"""Translating expressions a user enters while debugging.

The debugger lets a user probe the state it is showing: assume something and
see what follows, or ask whether something can be proved. Silicon can do that
for a Viper expression it parses itself, but a Nagini user writes Python, so
the expression has to go through Nagini's own translation -- in the context of
the program point being debugged, so that names mean what they mean there.

Only a subset of Python is accepted. Anything whose translation would need new
Viper variables or statements is rejected rather than mistranslated, and types
come from the declarations rather than from mypy, since re-running mypy on a
fragment is not possible.
"""


import ast

from typing import Optional

from nagini_translation.lib.context import Context
from nagini_translation.lib.errors.manager import Item
from nagini_translation.lib.program_nodes import PythonMethod


class ExpressionInputError(Exception):
    """A user-entered expression could not be translated."""


class DebugExpressionTranslator:
    """Translates Python expressions in the context of a program point.

    The context is *reconstructed* from the information the error manager
    recorded, rather than captured during translation: what it needs is the
    module, the class and the method being translated, and all three follow
    from the ``PythonMethod`` stored with every position. Nagini's own
    aliasing (inside loops, comprehensions, or an inlined call) is not
    recovered, so expressions are refused at points where it would matter.
    """

    def __init__(self, translator, viper_ast, modules, sif: bool = False,
                 arp: bool = False, float_encoding: str = None) -> None:
        self.translator = translator
        self.viper = viper_ast
        self.modules = modules
        self.sif = sif
        self.arp = arp
        self.float_encoding = float_encoding

    def translate(self, expression: str, item: Optional[Item]) -> 'silver.ast.Exp':
        """Translate ``expression`` as if written at the point ``item`` is from.

        Returns a Viper expression of type ``Bool``, ready to be evaluated in
        the symbolic state of the obligation.
        """
        method = self._method_of(item)
        node = self._parse(expression, item)
        ctx = self._context_for(method)
        return self._translate_in(node, ctx, method, expression)

    # -----------------------------------------------------------------------
    # Context reconstruction
    # -----------------------------------------------------------------------

    def _method_of(self, item: Optional[Item]) -> PythonMethod:
        if item is None or not isinstance(item.py_node, PythonMethod):
            raise ExpressionInputError(
                'The method this state belongs to could not be determined, so '
                'there is no scope to interpret an expression in.')
        if item.vias:
            # The position was recorded while translating something into
            # another context (an inlined call, an inherited contract), so the
            # names in scope there are not the ones a user would write.
            raise ExpressionInputError(
                'This state comes from an inlined or inherited context, where '
                'entering expressions is not supported.')
        return item.py_node

    def _context_for(self, method: PythonMethod) -> Context:
        ctx = Context()
        ctx.module = method.module
        ctx.current_function = method
        ctx.current_class = method.cls
        ctx.sif = self.sif
        ctx.arp = self.arp
        ctx.float_encoding = self.float_encoding
        # Expressions must not produce statements; see `_translate_in`.
        ctx.allow_statements = False
        self._alias_parameters(method, ctx)
        return ctx

    def _alias_parameters(self, method: PythonMethod, ctx: Context) -> None:
        """Make a parameter's name refer to the value it has now.

        A method body never assigns to its Viper parameters: Nagini copies each
        one into a local at the start (``_create_local_vars_for_params``) and
        aliases the name to that copy for the rest of the translation. Without
        the alias, an expression a user writes about ``x`` would be about the
        value ``x`` had on entry, which is not what they mean and, in a method
        that assigns to ``x``, quietly false.
        """
        for name, arg in method.args.items():
            # `locals` is keyed by the generated name and ordered by creation,
            # and the copy is created before anything else in the body, so the
            # first local of that name is the one the parameter was aliased to.
            copy = next((var for var in method.locals.values() if var.name == name), None)
            if copy is not None and copy is not arg:
                ctx.set_alias(name, copy, arg)

    # -----------------------------------------------------------------------
    # Parsing
    # -----------------------------------------------------------------------

    def _parse(self, expression: str, item: Optional[Item]) -> ast.AST:
        try:
            parsed = ast.parse(expression, mode='eval').body
        except SyntaxError as e:
            raise ExpressionInputError('Not a valid Python expression: {}'.format(e))
        anchor = item.node if item is not None else None
        _place(parsed, anchor)
        _link_parents(parsed, getattr(anchor, '_parent', None) or anchor)
        return parsed

    # -----------------------------------------------------------------------
    # Translation
    # -----------------------------------------------------------------------

    def _translate_in(self, node: ast.AST, ctx: Context, method: PythonMethod,
                      expression: str) -> 'silver.ast.Exp':
        # Translating can create fresh local variables, which would be added to
        # the method for good even though the program Silicon is verifying is
        # already fixed and could never mention them. Anything that needs one is
        # rejected, so the method is restored afterwards either way.
        saved_locals = dict(method.locals)
        try:
            statements, result = self.translator.expr_translator.translate_expr(
                node, ctx, target_type=self.viper.Bool, impure=True)
        except ExpressionInputError:
            raise
        except Exception as e:
            raise ExpressionInputError(self._explain(e, expression, node, method))
        finally:
            added = set(method.locals) - set(saved_locals)
            for name in added:
                del method.locals[name]

        if statements:
            raise ExpressionInputError(
                'This expression cannot be evaluated on its own: translating it '
                'requires statements, which the debugger cannot run in a state '
                'that has already been verified.')
        if added:
            raise ExpressionInputError(
                'This expression needs new local variables ({}), which do not '
                'exist in the program being debugged.'.format(', '.join(sorted(added))))
        return result

    def _explain(self, error: Exception, expression: str, node: ast.AST,
                 method: PythonMethod) -> str:
        """Turn a translation failure into something a user can act on."""
        from nagini_translation.lib.util import InvalidProgramException, UnsupportedException
        unknown = _unknown_names(node, method)
        if unknown:
            return 'Not defined at this point: {}.'.format(', '.join(sorted(unknown)))
        if isinstance(error, UnsupportedException):
            return 'Nagini cannot translate this expression: {}'.format(error)
        if isinstance(error, InvalidProgramException):
            return 'This expression is not valid here: {}'.format(error.code)
        message = str(error) or type(error).__name__
        return ('The expression {!r} could not be translated ({}). Note that types '
                'narrowed by an isinstance check are not available here, since the '
                'expression is not part of the type-checked program.'
                .format(expression, message))


def _unknown_names(node: ast.AST, method: PythonMethod) -> set:
    """Names in the expression that do not exist at this program point.

    A heuristic used only to explain a failure that already happened, so it may
    miss a name; it must not claim one is missing when it is not, which is why
    everything the module can offer counts as known.
    """
    module = method.module
    bound = {name.arg for lam in ast.walk(node) if isinstance(lam, ast.Lambda)
             for name in lam.args.args}
    for comp in ast.walk(node):
        if isinstance(comp, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            for generator in comp.generators:
                bound |= {n.id for n in ast.walk(generator.target)
                          if isinstance(n, ast.Name)}
    unknown = set()
    for name in ast.walk(node):
        if not isinstance(name, ast.Name) or name.id in bound:
            continue
        if (method.get_variable(name.id) is not None
                or name.id in module.global_vars
                or name.id in module.classes
                or name.id in module.functions
                or name.id in module.methods
                or name.id in module.predicates
                or any(name.id in m.classes or name.id in m.functions
                       or name.id in m.global_vars
                       for m in module.get_included_modules())):
            continue
        unknown.add(name.id)
    return unknown


def _place(node: ast.AST, anchor: Optional[ast.AST]) -> None:
    """Give every node a position, so that it can be related to the program.

    Nagini derives the identifier it attaches to a Viper node from the position
    of the Python node, and refuses to build one at all for a node without a
    line number. The expression the user typed is not in the file, so it borrows
    the position of the one being debugged.
    """
    line = getattr(anchor, 'lineno', 1) or 1
    column = getattr(anchor, 'col_offset', 0) or 0
    for child in ast.walk(node):
        if not isinstance(child, (ast.expr, ast.stmt)):
            continue
        child.lineno = line
        child.col_offset = column
        child.end_lineno = getattr(anchor, 'end_lineno', line)
        child.end_col_offset = getattr(anchor, 'end_col_offset', column)


def _link_parents(node: ast.AST, parent: Optional[ast.AST]) -> None:
    """Set the ``_parent`` links Nagini's resolver expects.

    They are normally set by the analyzer while walking the module; a freshly
    parsed expression has none, and several places read them without checking.
    """
    node._parent = parent
    for child in ast.iter_child_nodes(node):
        _link_parents(child, node)
