"""
Copyright (c) 2026 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

"""Back-translation of the debugger's Viper expressions to Python.

The debugger shows the expressions Silicon recorded while verifying, and those
are Viper expressions over the encoding Nagini produced -- not something a
Python user has ever seen. This module turns them back into Python.

Nagini gives every Viper node it builds a position carrying a unique
identifier, and :class:`~nagini_translation.lib.errors.manager.ErrorManager`
remembers which Python expression each identifier came from, so most of the
work is a lookup. The complication is that Silicon does not only report the
expressions Nagini built: it also *composes* new ones (conjoining several,
making one conditional on a branch condition, substituting arguments into a
callee's contract), and it builds those by copying the position -- and hence
the identifier -- of one of the parts. ``Utils.BigAnd``, for instance, gives a
conjunction the position of its first conjunct, so looking the identifier up
would report a single conjunct as if it were the whole conjunction.

The identifier alone is therefore not enough: an expression is only accepted as
"this is what the user wrote" if it is also structurally the node Nagini built
for that identifier. Everything else is either recomposed from its parts or
recognised as an internal artifact of the encoding and hidden.

(A cleaner solution would be for Silicon to mark the nodes it synthesizes, so
they could be recognised positively rather than by elimination. This module is
written so that it could be swapped in behind :meth:`Backtranslator._resolve`.)
"""


import ast as python_ast

from typing import Dict, List, Optional

from nagini_translation.lib.constants import (
    ASSERTING_FUNC,
    ASSUMING_FUNC,
    CHECK_DEFINED_FUNC,
    FUNCTION_DOMAIN_NAME,
    INTERNAL_NAMES,
    IS_DEFINED_FUNC,
    MAY_SET_PRED,
    PRIMITIVE_PREFIX,
    RESULT_NAME,
)
from nagini_translation.lib.errors.manager import Item
from nagini_translation.lib.util import pprint


#: Names of Viper functions, domains and predicates that only exist to encode
#: Python semantics. An assumption that is built entirely from these says
#: nothing to a Python user.
_INTERNAL_NAMES = frozenset(INTERNAL_NAMES) | frozenset({
    IS_DEFINED_FUNC, CHECK_DEFINED_FUNC, IS_DEFINED_FUNC + 'G',
    CHECK_DEFINED_FUNC + 'G', MAY_SET_PRED, FUNCTION_DOMAIN_NAME,
    ASSUMING_FUNC, ASSERTING_FUNC,
    # The obligation encoding.
    '_cthread', '_residue', '_current_wait_level', '_cwl', '_caller_measures',
    '_method_measures', '_loop_measures', '_loop_check_before',
    '_loop_termination_flag', '_loop_original_must_terminate',
    'Measure$', 'Measure$create', 'Measure$check',
    'MustTerminate', 'MustReleaseBounded', 'MustReleaseUnbounded',
    'Level', 'WaitLevel$', 'WaitLevel',
})

_INTERNAL_PREFIXES = (PRIMITIVE_PREFIX, 'issubtype', 'typeof', 'Measure$',
                      'WaitLevel$', '_loop_', '_thread_')

#: The domain Nagini encodes Python's type hierarchy in.
_TYPE_DOMAIN = 'PyType'

#: Functions that stand for their own first argument: Nagini wraps and unwraps
#: primitive values constantly, and guards every read of a local with a
#: definedness check. They are noise around a value, not structure, so they are
#: peeled rather than hidden.
_VALUE_WRAPPERS = ('___box__', '___unbox__', '___sil_seq__',
                   CHECK_DEFINED_FUNC, CHECK_DEFINED_FUNC + 'G')

#: Functions and predicates whose *truth* is bookkeeping. Unlike the wrappers
#: above these appear as whole assumptions, and there is nothing to say about
#: them at the Python level. ``_isDefined(99)`` in particular does correspond to
#: a Python statement -- the assignment that made the variable defined -- so it
#: would resolve, and has to be excluded explicitly rather than by elimination.
_INTERNAL_FACTS = frozenset({
    IS_DEFINED_FUNC, IS_DEFINED_FUNC + 'G', MAY_SET_PRED,
    'issubtype', 'isnotsubtype', 'typeof', 'extends_',
})

#: Viper functions Nagini generates for Python operators, and how to write them
#: back. Only needed for expressions Silicon composed -- anything Nagini built
#: itself is recovered from the error manager verbatim -- but that is common
#: enough that leaving them as `list___getitem__(l, 0)` would show a Nagini user
#: the encoding they never wrote.
#:
#: Keyed by the Python special method, which is how the generated name ends:
#: `list___getitem__` is `list` and `__getitem__` run together.
_BINARY_OPERATORS = {
    '__gt__': '>', '__lt__': '<', '__ge__': '>=', '__le__': '<=',
    '__eq__': '==', '__ne__': '!=', '__add__': '+', '__sub__': '-',
    '__mul__': '*', '__floordiv__': '//', '__mod__': '%', '__div__': '/',
    '__truediv__': '/', '__pow__': '**', '__and__': 'and', '__or__': 'or',
    '__is__': 'is', '__lshift__': '<<', '__rshift__': '>>', '__xor__': '^',
}

#: Special methods that are not infix operators.
_BINARY_TEMPLATES = {
    '__getitem__': '{0}[{1}]',
    '__contains__': '{1} in {0}',
}

_UNARY_TEMPLATES = {
    '__len__': 'len({0})', '__str__': 'str({0})', '__bool__': 'bool({0})',
    '__int__': 'int({0})', '__float__': 'float({0})', '__abs__': 'abs({0})',
    '__neg__': '-{0}', '__pos__': '+{0}', '__invert__': '~{0}',
    '__not__': 'not {0}',
}


class Rendered:
    """One back-translated expression.

    ``kind`` says how much can be trusted:

    ``source``
        the expression is one the user wrote, recovered verbatim;
    ``composed``
        Silicon built this out of several expressions; ``text`` is a rendering
        of the parts, which are also available as ``children``;
    ``internal``
        nothing about this is meaningful at the Python level.
    """

    def __init__(self, text: Optional[str], kind: str,
                 children: List['Rendered'] = None,
                 position: Optional[dict] = None) -> None:
        self.text = text
        self.kind = kind
        self.children = children or []
        # A composed expression has no position of its own, but pointing at the
        # first part it was built from is better than pointing at nothing.
        self.position = position or next(
            (c.position for c in self.children if c.position), None)

    @property
    def internal(self) -> bool:
        return self.kind == 'internal'

    def to_dict(self) -> dict:
        result = {'text': self.text, 'kind': self.kind}
        if self.position:
            result['position'] = self.position
        if self.children:
            result['children'] = [c.to_dict() for c in self.children]
        return result

    def __repr__(self) -> str:
        return 'Rendered({!r}, {})'.format(self.text, self.kind)


INTERNAL = Rendered(None, 'internal')


class Backtranslator:
    """Turns the Viper expressions of a debug session back into Python."""

    def __init__(self, jvm, prog, items: Dict[str, Item],
                 sil_names: Dict[str, tuple] = None,
                 field_names: Dict[str, str] = None) -> None:
        self.jvm = jvm
        self.ast = jvm.viper.silver.ast
        self.prog = prog
        self.items = items
        self.sil_names = sil_names or {}
        self.field_names = field_names or {}
        #: The symbolic value each Python name currently stands for, as
        #: ``name -> "silName@version"``. A value from an earlier point of the
        #: execution has a different one, which is what makes it necessary to
        #: say so rather than print the plain name.
        self.current_terms = {}     # type: Dict[str, str]
        #: What each field-value symbol stands for, as ``term -> (text, current)``;
        #: see :meth:`NaginiDebugSession._field_terms`.
        self.field_terms = {}       # type: Dict[str, tuple]
        #: What each location held in each state, as ``(label, key) -> term``;
        #: see :meth:`NaginiDebugSession._location_values`.
        self.location_values = {}   # type: Dict[tuple, str]
        self._show_versions = False
        self._candidates = None     # type: Optional[Dict[str, list]]
        self._simplifier = None

    # -----------------------------------------------------------------------
    # Entry points
    # -----------------------------------------------------------------------

    def render(self, exp, final=None) -> Rendered:
        """Back-translate a Viper expression.

        ``final`` is the same expression after evaluation, if available. Which
        of the two to use is not a matter of taste:

        ``exp`` is phrased over the variables of the program, so it is the one
        that can be matched against what Nagini built, and it yields the user's
        own words. But it says nothing about *when*: after ``x += 2``, both
        sides of the recorded equality are called ``x``, and printing it gives
        the nonsense ``x == x + 2``.

        ``final`` has the values of the state substituted in, so the two sides
        are distinguishable -- but everything is renamed, so nothing matches.

        So the two are walked together, and the choice is made per
        sub-expression: the user's own words are used for every part that still
        means what it says, and only the parts that refer to another point in
        time are spelled out. See :meth:`_render`.
        """
        if exp is None and final is None:
            return INTERNAL
        # Whether to write versions out at all is decided once for the whole
        # expression: a mix of marked and unmarked names reads as if the
        # unmarked ones were somehow more current than they are.
        self._show_versions = self._needs_versions(final if final is not None else exp)
        try:
            return self._render(exp if exp is not None else final,
                                final if exp is not None else None)
        finally:
            self._show_versions = False

    def _needs_versions(self, node) -> bool:
        """Whether ``node`` mentions a value other than a variable's current one."""
        if node is None:
            return False
        stack = [node]
        while stack:
            current = stack.pop()
            if isinstance(current, self.ast.LocalVarWithVersion):
                if self._is_stale(str(current.name())):
                    return True
            elif isinstance(current, self.ast.DebugLabelledOld):
                # Only a state from somewhere other than where the expression is
                # written says anything; see `_state_label`.
                if self._state_label(current, current.exp()) is not None:
                    return True
            if hasattr(current, 'subnodes'):
                iterator = current.subnodes().toIterator()
                while iterator.hasNext():
                    stack.append(iterator.next())
        return False

    def _is_stale(self, versioned_name: str) -> bool:
        """Whether ``silName@version`` is not what its Python name means now."""
        base = versioned_name.split('@')[0]
        name = self._variable_name(base)
        if name is None:
            return False
        current = self.current_terms.get(name)
        return current is not None and current != versioned_name

    def render_debug_exp(self, debug_exp, force: bool = False) -> Rendered:
        """Back-translate one ``DebugExp``: an assumption or the proof goal.

        ``force`` skips the check for facts that belong to the encoding. An
        assumption the user asked for has to be shown whatever it says: writing
        ``type(i1) == int`` produces exactly such a fact, and dropping it would
        look like the debugger had ignored the request.
        """
        original = _option(debug_exp.originalExp())
        final = _option(debug_exp.finalExp())
        if original is None:
            # Assumptions that only carry a description are Silicon's own
            # bookkeeping ("Snapshot", "Inverse Function Axioms", ...).
            return INTERNAL
        if not force and self.is_internal_fact(original):
            return INTERNAL
        return self.render(original, final)

    def is_internal_fact(self, exp) -> bool:
        """Whether an assumption says something only the encoding cares about.

        Two cases. Some facts are about a construct of the encoding directly
        (``_isDefined``, ``issubtype``, permission to a ``_MaySet`` predicate);
        these have to be recognised explicitly, because they *do* correspond to
        a Python statement -- the assignment that made the variable defined --
        and would otherwise be reported as that statement. The rest is caught by
        elimination: if everything an assumption is built from belongs to the
        encoding, there is nothing in it for a Python user.
        """
        root = exp
        while isinstance(root, self.ast.Not):
            root = root.exp()
        if isinstance(root, (self.ast.FuncApp, self.ast.DomainFuncApp)):
            if str(root.funcname()) in _INTERNAL_FACTS:
                return True
        names = self._names_in(exp)
        return bool(names) and all(_is_internal_name(n) for n in names)

    def _names_in(self, exp) -> List[str]:
        """The function, domain function and predicate names used in ``exp``.

        The wrappers that stand for their own argument are left out: they say
        nothing about what an assumption is *about*, and counting them would
        make ``Result() == _checkDefined(c)`` -- a fact about two variables the
        user declared -- look like pure encoding.
        """
        ast = self.ast
        names = []
        stack = [exp]
        while stack:
            node = stack.pop()
            if (isinstance(node, (ast.FuncApp, ast.DomainFuncApp))
                    and str(node.funcname()).endswith(_VALUE_WRAPPERS)):
                pass
            elif isinstance(node, ast.DomainFuncApp):
                # Every function of the type domain (`int()`, `list(T)`, ...)
                # belongs to the encoding, whatever it is called.
                names.append(_TYPE_DOMAIN if str(node.domainName()) == _TYPE_DOMAIN
                             else str(node.funcname()))
            elif isinstance(node, ast.FuncApp):
                names.append(str(node.funcname()))
            elif isinstance(node, ast.PredicateAccess):
                names.append(str(node.predicateName()))
            if hasattr(node, 'subnodes'):
                iterator = node.subnodes().toIterator()
                while iterator.hasNext():
                    stack.append(iterator.next())
        return names

    # -----------------------------------------------------------------------
    # The core: identifier lookup, guarded by a structural check
    # -----------------------------------------------------------------------

    def _render(self, exp, final=None) -> Rendered:
        """Back-translate ``exp``, using ``final`` for what state it refers to.

        The two are walked together so that the decision can be made per
        sub-expression rather than for the expression as a whole: an assumption
        may be the user's own words apart from one variable that stands for an
        earlier value, and only that variable needs saying so.
        """
        exp, final, label = self._align(exp, final)
        if exp is None:
            return INTERNAL
        item = self._resolve(exp)
        if item is not None and not self._needs_versions(final):
            return self._at(Rendered(item.reason_string or pprint(item.node),
                                     'source', position=_position_of(item)), label)
        composed = self._compose(exp, final)
        if composed is not None:
            return self._at(composed, label)
        return INTERNAL

    def _align(self, exp, final):
        """Bring the two forms into correspondence.

        Peels the wrappers off both, takes any state label off the evaluated
        form, and gives up on the pairing when the two no longer have the same
        shape -- which happens when the debugger simplified one of them.
        """
        exp = self._peel(exp)
        final = self._peel(final) if final is not None else None
        label = None
        while isinstance(final, self.ast.DebugLabelledOld):
            label = label or self._state_label(final, exp)
            final = self._peel(final.exp())
        if final is not None and not self._same_shape(exp, final):
            final = None
        return exp, final, label

    def _same_shape(self, exp, final) -> bool:
        """Whether the two nodes are each other's counterpart."""
        if exp is None:
            return False
        # A variable and the symbol it was replaced by are exactly the pairing
        # this is all about, and they are different classes.
        if isinstance(exp, self.ast.AbstractLocalVar):
            return isinstance(final, self.ast.AbstractLocalVar)
        return exp.getClass().getName() == final.getClass().getName()

    def _state_label(self, node, exp) -> Optional[str]:
        """Where the state a labelled expression was evaluated in comes from.

        Silicon labels every heap it snapshots, including the one an expression
        is evaluated in where it stands, so most of these labels say nothing.
        The one that does is where the location held something else there --
        which is the case at ``c.value -= 8``, where both the old and the new
        value are written on the same line and mentioning the line is the only
        thing that tells them apart.
        """
        label = str(node.oldLabel())
        where = _debug_label_location(label)
        if where is None:
            return None
        key = self._location_key(exp)
        if key is not None:
            there = self.location_values.get((label.split('#')[0], key))
            here = self.location_values.get(('', key))
            return None if there is not None and there == here else where
        # Not a location we can compare; fall back to whether the state was
        # taken somewhere other than where the expression is written.
        line = _line_of(exp) if exp is not None else None
        if line is not None and where == 'line {}'.format(line):
            return None
        return where

    def _location_key(self, exp) -> Optional[str]:
        """The key :meth:`NaginiDebugSession._location_values` uses, for a read."""
        if not isinstance(exp, self.ast.FieldAccess):
            return None
        receiver = exp.rcv()
        if not isinstance(receiver, self.ast.AbstractLocalVar):
            return None
        return '{}|{}'.format(str(exp.field().name()), str(receiver.name()))

    def _at(self, rendered: Rendered, label: Optional[str]) -> Rendered:
        if label is None or rendered.text is None:
            return rendered
        return Rendered('{}@{}'.format(rendered.text, label), rendered.kind,
                        children=rendered.children, position=rendered.position)

    def _peel(self, exp):
        """Strip the wrappers that stand for their own argument."""
        while isinstance(exp, (self.ast.FuncApp, self.ast.DomainFuncApp)):
            name = str(exp.funcname())
            if not name.endswith(_VALUE_WRAPPERS):
                return exp
            args = _seq_to_list(exp.args())
            if not args:
                return exp
            exp = args[0]
        return exp

    def _resolve(self, exp) -> Optional[Item]:
        """The Python expression ``exp`` came from, if it really came from one.

        Returns None when the identifier on ``exp`` was inherited from another
        node rather than earned, which is how a synthesized node is recognised.
        """
        item = self._item_at(exp)
        if item is None:
            return None
        for candidate in self.candidates.get(exp.pos().id(), ()):
            if self._same_node(candidate, exp):
                return item
        return None

    def _same_node(self, candidate, exp) -> bool:
        """Whether ``exp`` is the node Nagini built, modulo simplification.

        Viper's nodes are case classes whose position and info sit in a second
        parameter list, so equality already ignores them; the only systematic
        difference is that the debugger simplifies everything it stores.
        """
        try:
            if candidate.equals(exp):
                return True
            return self._simplify(candidate).equals(exp)
        except Exception:
            return False

    def simplify(self, node):
        """Fold away the arithmetic the verifier accumulated in an expression."""
        return self._simplify(node)

    def _simplify(self, node):
        if self._simplifier is None:
            from nagini_translation.lib.jvmaccess import getobject
            self._simplifier = getobject(self.jvm.java,
                                         self.jvm.viper.silver.ast.utility,
                                         'Simplifier')
        return self._simplifier.simplify(node, True)

    @property
    def candidates(self) -> Dict[str, list]:
        """The Viper nodes Nagini built, indexed by position identifier.

        Not a one-to-one mapping: a single ``to_position`` call is threaded
        through several constructors (a comprehension builds a dozen nodes from
        one position), and the wrappers that box primitive values deliberately
        reuse their operand's position. Any of the recorded nodes counts as a
        match.
        """
        if self._candidates is None:
            self._candidates = {}
            stack = [self.prog]
            while stack:
                node = stack.pop()
                if hasattr(node, 'pos'):
                    pos = node.pos()
                    if hasattr(pos, 'id'):
                        self._candidates.setdefault(pos.id(), []).append(node)
                iterator = node.subnodes().toIterator()
                while iterator.hasNext():
                    stack.append(iterator.next())
        return self._candidates

    # -----------------------------------------------------------------------
    # Composition: expressions Silicon built out of several source expressions
    # -----------------------------------------------------------------------

    def _compose(self, exp, final=None) -> Optional[Rendered]:
        """Rebuild a synthesized expression from parts that do resolve.

        ``final`` is the counterpart of ``exp`` in the evaluated form, or None
        when the two could not be paired; each case hands the matching part of
        it down, so that a variable leaf knows which of its values is meant.
        """
        ast = self.ast

        if isinstance(exp, ast.And):
            return self._nary(self._spine(exp, final, ast.And), ' and ')
        if isinstance(exp, ast.Or):
            return self._nary(self._spine(exp, final, ast.Or), ' or ')
        if isinstance(exp, ast.Implies):
            return self._binary(exp, final, 'Implies({0}, {1})')
        if isinstance(exp, ast.EqCmp):
            return self._binary(exp, final, self._equality_template(exp, '==', 'is'))
        if isinstance(exp, ast.NeCmp):
            return self._binary(exp, final, self._equality_template(exp, '!=', 'is not'))
        if isinstance(exp, ast.Not):
            return self._unary(exp.exp(), _side(final, 'exp'), 'not ({0})')
        if isinstance(exp, ast.CondExp):
            return self._conditional(exp, final)
        if isinstance(exp, ast.OldExp):
            # A plain `old`, which is what Nagini emits for `Old(...)`.
            return self._unary(exp.exp(), _side(final, 'exp'), 'Old({0})')
        if isinstance(exp, (ast.Forall, ast.Exists)):
            return self._quantifier(exp, final)
        if isinstance(exp, ast.FieldAccess):
            return self._field_access(exp, final)
        if isinstance(exp, ast.FieldAccessPredicate):
            return self._permission(exp, final)
        if isinstance(exp, (ast.FuncApp, ast.DomainFuncApp)):
            return self._call(exp, final)
        if isinstance(exp, ast.AbstractLocalVar):
            return self._variable_at(exp, final)
        literal = self._literal(exp)
        if literal is not None:
            return literal
        return None

    def _equality_template(self, exp, value_operator: str, identity_operator: str) -> str:
        """Whether an equality was written as ``==`` or as ``is``.

        Nagini translates both to the same Viper node, so the difference exists
        only in the Python source, and an `is` reported as `==` is a different
        claim. An expression that matches what Nagini built keeps its own words
        and never reaches this; it is the ones that have to be rebuilt -- those
        the verifier recorded only in evaluated form -- that would otherwise
        lose the distinction.

        Reading it off the position is safe even where matching the node is
        not: a comparison the verifier synthesized points at something that is
        not an `is` in the source, and then the default is kept.
        """
        item = self._item_at(exp)
        node = item.node if item is not None else None
        if (isinstance(node, python_ast.Compare) and len(node.ops) == 1
                and isinstance(node.ops[0], (python_ast.Is, python_ast.IsNot))):
            return '{{0}} {} {{1}}'.format(identity_operator)
        return '{{0}} {} {{1}}'.format(value_operator)

    def _item_at(self, exp) -> Optional[Item]:
        """What was recorded for a node's position, without checking the node.

        Unlike :meth:`_resolve` this does not establish that the node really is
        the one Nagini built, so it may only be used for things that are
        properties of the source rather than of the expression.
        """
        pos = exp.pos() if hasattr(exp, 'pos') else None
        if pos is None or not hasattr(pos, 'id'):
            return None
        return self.items.get(pos.id())

    def _spine(self, exp, final, cls) -> list:
        """Flatten a left-nested binary operator into its paired operands."""
        result = []
        stack = [(exp, final)]
        root = True
        while stack:
            node, node_final = stack.pop()
            # The root is always taken apart -- we are only here because it
            # could not be rendered as a whole, so returning it unchanged would
            # ask for it to be rendered as a whole again. Below the root, a
            # conjunction the user wrote stays one unit; only the ones the
            # verifier built out of several are flattened.
            flatten = isinstance(node, cls) and (root or self._resolve(node) is None)
            root = False
            if flatten:
                stack.append((node.right(), _side(node_final, 'right')))
                stack.append((node.left(), _side(node_final, 'left')))
            else:
                result.append((node, node_final))
        return result

    def _nary(self, operands, separator: str) -> Optional[Rendered]:
        children = [self._render(o, f) for o, f in operands]
        useful = [c for c in children if not c.internal]
        if not useful:
            return None
        text = separator.join(c.text for c in useful) if all(
            c.text for c in useful) else None
        if len(useful) == 1:
            return useful[0]
        return Rendered(text, 'composed', children=useful)

    def _binary(self, exp, final, template: str) -> Optional[Rendered]:
        return self._apply(template, [(exp.left(), _side(final, 'left')),
                                      (exp.right(), _side(final, 'right'))])

    def _unary(self, operand, operand_final, template: str) -> Optional[Rendered]:
        return self._apply(template, [(operand, operand_final)])

    def _apply(self, template: str, operands) -> Optional[Rendered]:
        """Render the operands and put them into ``template``."""
        rendered = [self._render(o, f) for o, f in operands]
        if all(r.internal for r in rendered):
            return None
        text = (template.format(*[r.text for r in rendered])
                if all(r.text for r in rendered) else None)
        return Rendered(text, 'composed',
                        children=[r for r in rendered if not r.internal])

    def _conditional(self, exp, final) -> Optional[Rendered]:
        parts = [self._render(exp.cond(), _side(final, 'cond')),
                 self._render(exp.thn(), _side(final, 'thn')),
                 self._render(exp.els(), _side(final, 'els'))]
        if all(p.internal for p in parts):
            return None
        text = ('{} if {} else {}'.format(parts[1].text, parts[0].text, parts[2].text)
                if all(p.text for p in parts) else None)
        return Rendered(text, 'composed',
                        children=[p for p in parts if not p.internal])

    def _quantifier(self, exp, final) -> Optional[Rendered]:
        body = self._render(exp.exp(), _side(final, 'exp'))
        if body.internal:
            return None
        keyword = 'Forall' if isinstance(exp, self.ast.Forall) else 'Exists'
        names = []
        iterator = exp.variables().toIterator()
        while iterator.hasNext():
            names.append(self._variable_name(str(iterator.next().name())))
        text = ('{}({}, {})'.format(keyword, ', '.join(names), body.text)
                if body.text else None)
        return Rendered(text, 'composed', children=[body])

    def _permission(self, exp, final) -> Optional[Rendered]:
        """Permission to a field, which Nagini spells ``Acc``."""
        location = self._render(exp.loc(), _side(final, 'loc'))
        if location.internal or location.text is None:
            return None
        return Rendered('Acc({})'.format(location.text), 'composed',
                        children=[location], position=location.position)

    def _call(self, exp, final) -> Optional[Rendered]:
        """A call to one of the functions Nagini's encoding generates."""
        name = str(exp.funcname())
        args = _seq_to_list(exp.args())
        final_args = (_seq_to_list(final.args())
                      if final is not None and hasattr(final, 'args') else [])
        if len(final_args) != len(args):
            final_args = [None] * len(args)
        operands = list(zip(args, final_args))

        template = _operator_template(name, len(args))
        if template is not None:
            return self._apply(template, operands)

        if (isinstance(exp, self.ast.DomainFuncApp)
                and str(exp.domainName()) == _TYPE_DOMAIN):
            return self._type_expression(name, operands)

        if _is_internal_name(name):
            return None

        # A call Nagini generated for a Python-level function: the Viper name is
        # the generated one, so report the Python name if we can find it.
        rendered = [self._render(a, f) for a, f in operands]
        if any(r.internal or not r.text for r in rendered):
            return None
        return Rendered('{}({})'.format(_python_function_name(name),
                                        ', '.join(r.text for r in rendered)),
                        'composed', children=rendered)

    def _type_expression(self, name: str, operands) -> Optional[Rendered]:
        """A fact about Python's type hierarchy, written the way Python does.

        Nagini encodes types as a domain: a class is a nullary function, the
        type of a value is ``typeof``, and ``isinstance`` is a subtype check.
        These are normally hidden as encoding noise, but they surface when the
        user asks about a type themselves.
        """
        if not operands:
            # A class: `int()` is the type `int`.
            return Rendered(name, 'composed')
        if name == 'typeof' and len(operands) == 1:
            return self._apply('type({0})', operands)
        if name in ('issubtype', 'isnotsubtype') and len(operands) == 2:
            # `issubtype(typeof(x), C())` is how `isinstance(x, C)` is encoded.
            subject, expected = operands
            negated = name == 'isnotsubtype'
            inner = _side_of_typeof(subject[0], self.ast)
            if inner is not None:
                rendered = self._apply('isinstance({0}, {1})',
                                       [(inner, None), expected])
            else:
                rendered = self._apply('issubclass({0}, {1})', [subject, expected])
            if rendered is None or not negated or rendered.text is None:
                return rendered
            return Rendered('not {}'.format(rendered.text), rendered.kind,
                            children=rendered.children)
        return None

    def _variable_at(self, exp, final) -> Rendered:
        """A variable, and which of its values is meant.

        Silicon renames a variable on every assignment, so the symbol in the
        evaluated form says which value this is. Dropping that would state a
        fact about the current value that only holds for an earlier one, so it
        is reported whenever the expression refers to more than one point in
        time; the Variables section says what each plain name stands for now,
        which is what makes the marks readable.
        """
        versioned = final if isinstance(final, self.ast.LocalVarWithVersion) else exp
        name = str(versioned.name())
        base, _, version = name.partition('@')
        # The value of a field is a symbol of its own; the heap says which
        # object's field it belongs to.
        field = self.field_terms.get(name)
        if field is not None:
            text, current = field
            if current or not self._show_versions or not version:
                return Rendered(text, 'composed')
            return Rendered('{}@{}'.format(text, version), 'composed')
        rendered = self._variable(base)
        if not version or rendered.text is None or not self._show_versions:
            return rendered
        return Rendered('{}@{}'.format(rendered.text, version), rendered.kind,
                        position=rendered.position)

    def _field_access(self, exp, final) -> Optional[Rendered]:
        receiver = self._render(exp.rcv(), _side(final, 'rcv'))
        field = self.field_names.get(str(exp.field().name()))
        if receiver.internal or receiver.text is None or field is None:
            return None
        return Rendered('{}.{}'.format(receiver.text, field), 'composed',
                        children=[receiver], position=receiver.position)

    def _variable(self, sil_name: str) -> Rendered:
        name = self._variable_name(sil_name)
        if name is None:
            return INTERNAL
        return Rendered(name, 'source')

    def _variable_name(self, sil_name: str) -> Optional[str]:
        known = self.sil_names.get(sil_name)
        if known is not None:
            name = known[0].name
            return 'Result()' if name == RESULT_NAME else name
        # Silicon also introduces variables for the value a field holds after an
        # assignment. Which object's field that is cannot be recovered, but the
        # field name is better than the generated one.
        field = self.field_names.get(sil_name)
        if field is not None:
            return '.{}'.format(field)
        return None if _is_internal_name(sil_name) else sil_name

    def _literal(self, exp) -> Optional[Rendered]:
        ast = self.ast
        if isinstance(exp, ast.IntLit):
            return Rendered(str(exp.i()), 'source')
        if isinstance(exp, ast.BoolLit):
            return Rendered('True' if exp.value() else 'False', 'source')
        if isinstance(exp, ast.NullLit):
            return Rendered('None', 'source')
        return None

def _option(value):
    """Unwrap a Scala ``Option``."""
    if value is None or not value.isDefined():
        return None
    return value.get()


def _seq_to_list(seq) -> list:
    result = []
    iterator = seq.toIterator()
    while iterator.hasNext():
        result.append(iterator.next())
    return result


def _position_of(item: Item) -> Optional[dict]:
    node = item.node
    if not hasattr(node, 'lineno') or node.lineno is None:
        return None
    return {
        'line': node.lineno,
        'column': node.col_offset,
        'endLine': getattr(node, 'end_lineno', None),
        'endColumn': getattr(node, 'end_col_offset', None),
    }


def _debug_label_location(label: str) -> Optional[str]:
    """The source location encoded in one of Silicon's debug old-labels.

    They look like ``debug@3#l:12.5``, built from the position of the Viper node
    the state was snapshotted at. Since every position Nagini produces is a
    position in the *Python* file, that is a Python line and column.
    """
    _, _, location = label.partition('#l:')
    if not location:
        return None
    line, _, _column = location.partition('.')
    return 'line {}'.format(line) if line.isdigit() else location


def _is_internal_name(name: str) -> bool:
    return (name in _INTERNAL_NAMES
            or name.startswith(_INTERNAL_PREFIXES))


def _side_of_typeof(node, ast):
    """The value whose type is taken, if ``node`` is a ``typeof``."""
    if (isinstance(node, ast.DomainFuncApp)
            and str(node.funcname()) == 'typeof'):
        args = _seq_to_list(node.args())
        if len(args) == 1:
            return args[0]
    return None


def _side(node, accessor: str):
    """The counterpart of a sub-expression in the evaluated form, if paired."""
    if node is None:
        return None
    method = getattr(node, accessor, None)
    if method is None:
        return None
    try:
        return method()
    except Exception:
        return None


def _line_of(exp) -> Optional[int]:
    """The line of the Python expression a Viper node came from."""
    try:
        pos = exp.pos()
        return int(pos.line()) if hasattr(pos, 'line') else None
    except Exception:
        return None


def _operator_template(name: str, arity: int) -> Optional[str]:
    """How to write a generated Viper function as Python, if it is an operator.

    Nagini names these ``<type>___<special method>``, so `list___getitem__` is
    recognised by the `__getitem__` its name ends with.
    """
    if arity == 2:
        for suffix, operator in _BINARY_OPERATORS.items():
            if name.endswith(suffix):
                return '{{0}} {} {{1}}'.format(operator)
        for suffix, template in _BINARY_TEMPLATES.items():
            if name.endswith(suffix):
                return template
    elif arity == 1:
        for suffix, template in _UNARY_TEMPLATES.items():
            if name.endswith(suffix):
                return template
    return None


def _python_function_name(sil_name: str) -> str:
    """A readable name for a generated Viper function.

    Nagini prefixes methods with their class and appends a counter to keep
    names unique; neither is interesting to the user.
    """
    name = sil_name
    if '___' in name:
        name = name.split('___')[-1]
    return name
