"""
Copyright (c) 2026 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

"""Python-level frontend for Silicon's verification debugger.

Silicon can keep the symbolic state and the verifier of a failed verification
alive and let a user interrogate them: what was assumed, what could not be
proved, what the store and heap look like. Because Nagini runs ViperServer in
the same JVM, it can drive that machinery directly, rather than through
ViperServer's LSP layer.

Everything Silicon reports is phrased in Viper, though, and a Nagini user has
never seen the Viper program. This module therefore also translates what the
debugger shows back to the Python level; see :mod:`nagini_translation.debug`
for that part.
"""


import logging
import threading

from typing import Any, Dict, List, Optional

from nagini_translation.debug_backtranslation import Backtranslator
from nagini_translation.debug_input import (
    DebugExpressionTranslator,
    ExpressionInputError,
)
from nagini_translation.lib.constants import INTERNAL_NAMES, RESULT_NAME
from nagini_translation.lib.errors import error_manager
from nagini_translation.lib.errors.manager import Item
from nagini_translation.lib.jvmaccess import JVM
from nagini_translation.lib.program_nodes import PythonMethod, PythonModule
from nagini_translation.main import TranslationArtifacts
from nagini_translation.verifier import build_silicon_debug_backend_args
from nagini_translation.viper_server import get_viper_server_manager


#: How far to descend into the assumption forest. Silicon nests every
#: assumption under the operation that produced it, and the lower levels are
#: almost entirely the encoding's own bookkeeping.
_MAX_ASSUMPTION_DEPTH = 4

#: Groups Silicon labels with a description of its own machinery. They say
#: nothing at the Python level: a `let` binding, for instance, is an artifact of
#: how a subexpression was evaluated, and the subexpression itself is shown
#: anyway.
_INTERNAL_DESCRIPTIONS = frozenset({
    'letvar assignment', 'pcDeltaExp', 'quantifiedExp', 'Heap Triggers',
    'Reference Disjointness', 'Snapshot', 'Snapshots', 'Empty snapshot',
    'Snapshot Equations',
})


class DebugSessionError(Exception):
    """A debug session could not be started or a command could not be run."""


class DebugFailure:
    """One of the verification failures a session can be opened for."""

    def __init__(self, index: int, message: str, position: Optional[str],
                 member_name: Optional[str], debuggable: bool) -> None:
        self.index = index
        self.message = message
        self.position = position
        self.member_name = member_name
        self.debuggable = debuggable

    def to_dict(self) -> dict:
        return {
            'index': self.index,
            'message': self.message,
            'position': self.position,
            'member': self.member_name,
            'debuggable': self.debuggable,
        }


class NaginiDebugSession:
    """A live debug session for one translated Nagini program.

    The session pins a lot of state: the JVM objects of the translation (so
    that the Viper nodes Silicon reports can still be related to the Python
    program they came from), the error-manager tables of that translation, and
    a Silicon instance that owns a prover process and the symbolic state of
    every failing branch. It must therefore be closed explicitly.

    Not thread-safe: the underlying ``SiliconDebugSession`` owns a prover and
    mutable symbolic state, so callers have to serialize their commands.
    """

    def __init__(self, jvm: JVM, artifacts: TranslationArtifacts,
                 items: Dict[str, Item], rules: Dict[str, Any],
                 silicon, session, sif: bool = False) -> None:
        self.jvm = jvm
        self.artifacts = artifacts
        self.modules = artifacts.modules
        self.prog = artifacts.prog
        self.translator = artifacts.translator
        self.viper_ast = artifacts.viper_ast
        self.items = items
        self.rules = rules
        self.sif = sif
        self._silicon = silicon
        self._session = session
        self._closed = False
        self._sil_names = None          # type: Optional[Dict[str, tuple]]
        self._field_names = None        # type: Optional[Dict[str, str]]
        self._backtranslator = None     # type: Optional[Backtranslator]
        self._expression_translator = None  # type: Optional[DebugExpressionTranslator]
        #: Ids of the assumptions the user added, which are never filtered.
        self._user_added = set()

    # -----------------------------------------------------------------------
    # Lifecycle
    # -----------------------------------------------------------------------

    @classmethod
    def start(cls, jvm: JVM, path: str, bv_size: int = 8,
              base_dir: str = None, selected: set = None,
              counterexample: bool = True, viper_args: List[str] = None,
              sif: bool = False, float_encoding: str = None,
              ignore_global: bool = False) -> 'NaginiDebugSession':
        """Translate ``path`` and verify it with debugging enabled.

        ``selected`` restricts the *verification* the way Nagini's ``--select``
        does. It makes a debug run much faster, but the chopped program is not
        the one the user's diagnostics came from, and expressions the user
        enters later can only mention what survived the chopping.
        """
        from nagini_translation.main import translate_full

        artifacts = translate_full(path, jvm, bv_size, selected=selected or set(),
                                   base_dir=base_dir, sif=sif,
                                   ignore_global=ignore_global,
                                   float_encoding=float_encoding,
                                   counterexample=counterexample)
        if artifacts is None:
            raise DebugSessionError('The program does not typecheck.')

        # Take ownership of the error information of *this* translation: the
        # session outlives the next translation, which would otherwise clear it.
        items, rules = error_manager.detach()

        manager = get_viper_server_manager(jvm)
        manager.start()
        args = build_silicon_debug_backend_args(viper_args or [],
                                                counterexample=counterexample)
        try:
            silicon = manager.submit_for_debugging(artifacts.prog, path or 'nagini_program', args)
        except Exception as e:
            raise DebugSessionError('The debug verification could not be run: {}'.format(e))

        session = silicon.debugSession()
        if session is None or not session.isDefined():
            _stop_silicon(silicon)
            raise DebugSessionError(
                'Silicon did not produce a debug session. This usually means the program '
                'verified, so there is nothing to debug.')
        session = session.get()
        result = cls(jvm, artifacts, items, rules, silicon, session, sif=sif)
        if not result.failures:
            result.close()
            raise DebugSessionError('The program verified; there is nothing to debug.')
        return result

    def close(self) -> None:
        """Release the prover process and the symbolic state kept alive."""
        if self._closed:
            return
        self._closed = True
        try:
            self._session.close()
        except Exception:
            logging.exception('Error while closing the Silicon debug session.')
        _stop_silicon(self._silicon)
        self._silicon = None
        self._session = None

    @property
    def closed(self) -> bool:
        return self._closed

    def __enter__(self) -> 'NaginiDebugSession':
        return self

    def __exit__(self, *args) -> None:
        self.close()

    # -----------------------------------------------------------------------
    # Queries
    # -----------------------------------------------------------------------

    @property
    def failures(self) -> List[DebugFailure]:
        """The verification failures of the debug run, at the Python level."""
        self._check_open()
        infos = self._to_list(self._session.failures())
        # `DebugFailureInfo.pos` is already rendered as a string; the Viper node
        # that still carries our identifier is only on the reason.
        reasons = self._to_list(self._session.failureReasons())
        result = []
        for info, reason in zip(infos, reasons):
            item = self._item_at(reason.offendingNode().pos())
            result.append(DebugFailure(
                index=int(info.index()),
                message=self._failure_message(item, info),
                position=self._position_string(item),
                member_name=self._python_member_name(info),
                debuggable=bool(info.debuggable())))
        return result

    def open_failure(self, index: int) -> None:
        """Make the failure with the given index the one being debugged."""
        self._check_open()
        self._report(self._session.openObligation(index))
        self._user_added.clear()

    def obligation_model(self) -> dict:
        """The current proof obligation, rendered at the Python level."""
        obl = self.obligation
        if obl is None:
            raise DebugSessionError('There is no proof obligation to inspect.')
        reason = obl.originalErrorReason()
        item = self._item_at(reason.offendingNode().pos())
        self.backtranslator.current_terms = self._current_terms(obl)
        self.backtranslator.field_terms = self._field_terms(obl)
        self.backtranslator.location_values = self._location_values(obl)
        return {
            'error': {
                'message': self._failure_message(item, reason),
                'position': self._position_string(item),
            },
            'member': self._member_of(obl).name if self._member_of(obl) else None,
            # The proof goal has the same shape as an assumption; clients treat
            # the two identically.
            'assertion': self._assumption_node(obl.eAssertion()),
            'store': self._store_entries(obl),
            'heap': self._heap_entries(obl),
            'branchConditions': self._branch_conditions(obl),
            'assumptions': self._assumptions(obl),
        }

    def _heap_entries(self, obl) -> List[dict]:
        """The permissions held, and the value behind each of them.

        Which is also what identifies the symbols the assumptions use for field
        values: the verifier calls the value of `c.value` something like
        `Cell_value@21`, and the only thing that says whose field that is, is
        the heap chunk it belongs to.
        """
        result = []
        for chunk in self._to_list(obl.s().h().values()):
            entry = self._chunk_entry(chunk)
            if entry is not None:
                result.append(entry)
        return result

    def _chunk_entry(self, chunk) -> Optional[dict]:
        location = self._chunk_location(chunk)
        if location is None:
            return None
        snap = getattr(chunk, 'snap', None)
        perm = getattr(chunk, 'permExp', None)
        return {
            'location': location,
            'permission': self._permission_string(perm() if perm else None),
            # Only a field holds a value worth naming. A predicate's snapshot is
            # a tree of the values everything under it holds, which says nothing
            # a Python user could use.
            'holds': (_simplify_term(str(snap()))
                      if snap is not None and self._is_field(chunk) else None),
            'internal': _is_internal_location(location),
        }

    def _is_field(self, chunk) -> bool:
        return self._chunk_field_name(chunk) is not None

    def _chunk_field_name(self, chunk) -> Optional[str]:
        """The Python attribute a chunk is about, if it is a field chunk."""
        return self._sil_name_to_field_name().get(str(chunk.id()))

    def _chunk_location(self, chunk) -> Optional[str]:
        """The Python expression a heap chunk is about, e.g. ``c.value``."""
        args = getattr(chunk, 'argsExp', None)
        args = args() if args else None
        if args is None or not args.isDefined():
            return None
        arguments = [self._render_exp(a) for a in self._to_list(args.get())]
        if not arguments or any(a is None for a in arguments):
            return None
        name = str(chunk.id())
        field = self._sil_name_to_field_name().get(name)
        if field is not None and len(arguments) == 1:
            return '{}.{}'.format(arguments[0], field)
        # A predicate: Nagini generates one per class for its fields, and one
        # per user-defined predicate.
        return '{}({})'.format(name, ', '.join(arguments))

    def _permission_string(self, perm_exp) -> Optional[str]:
        """How much permission is held, in Viper's terms.

        Permission amounts have no Python spelling -- Nagini writes them as the
        second argument of ``Acc`` -- so they are reported as they are, only
        simplified so that the arithmetic the verifier accumulated does not
        show through.
        """
        if perm_exp is None or not perm_exp.isDefined():
            return None
        return str(self.backtranslator.simplify(perm_exp.get()))

    def _assumptions(self, obl, include_internal: bool = False) -> List[dict]:
        """Everything the verifier assumed on the way to the failing state."""
        result = []
        for debug_exp in self._to_list(obl.assumptionsExp()):
            node = self._assumption_node(debug_exp)
            if node['internal'] and not include_internal:
                continue
            result.append(node)
        return result

    def _assumption_node(self, debug_exp, depth: int = 0) -> dict:
        """One assumption, with its children, at the Python level."""
        rendered = self.backtranslator.render_debug_exp(
            debug_exp, force=int(debug_exp.id()) in self._user_added)
        children = []
        # The assumption forest is deep and largely made up of the encoding's
        # own bookkeeping, so only descend while something is still readable.
        if depth < _MAX_ASSUMPTION_DEPTH:
            for child in self._to_list(debug_exp.children()):
                node = self._assumption_node(child, depth + 1)
                if not node['internal']:
                    children.append(node)
        node_id = int(debug_exp.id())
        added = node_id in self._user_added
        description = self._description(debug_exp)
        internal = (not added
                    and (bool(debug_exp.isInternal())
                         or description in _INTERNAL_DESCRIPTIONS
                         or (rendered.internal and not children)))
        return {
            'id': node_id,
            'added': added,
            # Silicon groups the assumptions of one operation under a node that
            # carries only a description ("Loop invariant", "Joined path
            # conditions"). That description is the only label such a node has.
            'python': rendered.text or description,
            'kind': rendered.kind if rendered.text else 'group',
            'position': rendered.position,
            'description': description,
            'viper': self._viper_string(debug_exp),
            'internal': internal,
            'children': children,
        }

    def _description(self, debug_exp) -> Optional[str]:
        description = debug_exp.description()
        if description is None or not description.isDefined():
            return None
        return str(description.get())

    def _viper_string(self, debug_exp) -> Optional[str]:
        final = debug_exp.finalExp()
        if final is not None and final.isDefined():
            return str(final.get())
        return None

    @property
    def backtranslator(self) -> Backtranslator:
        if self._backtranslator is None:
            self._backtranslator = Backtranslator(
                self.jvm, self.prog, self.items, self._sil_name_to_variable(),
                self._sil_name_to_field_name())
        return self._backtranslator

    def _sil_name_to_field_name(self) -> Dict[str, str]:
        """A map from generated Viper field names back to Python ones."""
        if self._field_names is None:
            self._field_names = {}
            for module in self.modules:
                for cls in module.classes.values():
                    for name, field in cls.fields.items():
                        if getattr(field, 'sil_name', None):
                            self._field_names[field.sil_name] = name
        return self._field_names

    def _field_terms(self, obl) -> Dict[str, tuple]:
        """What each field-value symbol stands for, as ``term -> (text, current)``.

        The verifier gives the value of a field a symbol of its own, named after
        the field but not after the object: `c.value` and `d.value` both become
        `Cell_value@k`. Only the heap says which is which, so the chunks are
        what makes an assumption about a field readable at all. Earlier values
        are looked up in the heaps that were kept at the points they were
        snapshotted.
        """
        terms = {}

        def record(heap, current):
            for chunk in self._to_list(heap.values()):
                snap = getattr(chunk, 'snap', None)
                if snap is None:
                    continue
                location = self._chunk_location(chunk)
                if location is None:
                    continue
                key = _simplify_term(str(snap()))
                if current or key not in terms:
                    terms[key] = (location, current)

        record(obl.s().h(), True)
        for entry in self._to_list(obl.s().oldHeaps().toSeq()):
            record(entry._2(), False)
        return terms

    def _location_values(self, obl) -> Dict[tuple, str]:
        """What each location held in each state, as ``(label, key) -> term``.

        This is what decides whether saying *which* state an expression was
        evaluated in tells the reader anything: it does when the location held
        something else there, and not otherwise. The key identifies a location
        by the verifier's own terms, so no back-translation is needed to
        compare two states.
        """
        values = {}

        def record(label, heap):
            for chunk in self._to_list(heap.values()):
                snap = getattr(chunk, 'snap', None)
                key = self._location_key(chunk)
                if snap is not None and key is not None:
                    values[(label, key)] = _simplify_term(str(snap()))

        record('', obl.s().h())
        for entry in self._to_list(obl.s().oldHeaps().toSeq()):
            record(str(entry._1()), entry._2())
        return values

    def _location_key(self, chunk) -> Optional[str]:
        field = self._chunk_field_name(chunk)
        if field is None:
            return None
        args = [_simplify_term(str(a)) for a in self._to_list(chunk.args())]
        return '{}|{}'.format(str(chunk.id()), ','.join(args))

    def _current_terms(self, obl) -> Dict[str, str]:
        """What each Python name stands for in the state being debugged.

        Nagini gives a method's parameters a local copy that the body assigns
        to, so one Python name can have two Viper variables: the value the
        method was called with, and the value now. The local copy is the one the
        name means, and any other value has to be marked as such when shown.
        """
        variables = self._sil_name_to_variable()
        terms = {}
        for entry in self._to_list(obl.s().g().values()):
            sil_name = str(entry._1().name())
            known = variables.get(sil_name)
            if known is None:
                continue
            var, is_arg = known
            name = self._plain_name(var)
            if is_arg and name in terms:
                continue        # the local copy wins
            terms[name] = _simplify_term(str(entry._2()._1()))
        return terms

    def _store_entries(self, obl) -> List[dict]:
        """The symbolic store, with Viper names mapped back to Python ones."""
        variables = self._sil_name_to_variable()
        result = []
        for entry in self._to_list(obl.s().g().values()):
            variable, value = entry._1(), entry._2()
            sil_name = str(variable.name())
            exp = value._2()
            rendered = None
            if exp is not None and exp.isDefined() and not self._is_variable(exp.get()):
                # A variable whose value is just another symbol says nothing
                # here; `holds` already relates the two, and what it was
                # assigned appears among the assumptions.
                rendered = self._render_exp(exp.get())
            name = self._store_entry_name(sil_name, variables)
            result.append({
                'variable': name,
                'silName': sil_name,
                'value': rendered,
                # Which of the values in the assumptions this name stands for.
                # The assumptions have to distinguish the value before and after
                # an assignment, and this is what relates the two.
                'holds': _simplify_term(str(value._1())),
                'term': str(value._1()),
                # Nagini introduces variables that have no counterpart in the
                # Python program (the error variable, the obligation encoding,
                # ...). `show_in_ce` is the flag it already uses to decide what
                # is worth showing a user in a counterexample.
                'internal': (variables.get(sil_name) is None
                             or not variables[sil_name][0].show_in_ce),
            })
        return result

    def _is_variable(self, exp) -> bool:
        return isinstance(exp, self.jvm.viper.silver.ast.AbstractLocalVar)

    @staticmethod
    def _plain_name(var) -> str:
        """What an expression mentioning this variable would call it."""
        return 'Result()' if var.name == RESULT_NAME else var.name

    def _store_entry_name(self, sil_name: str, variables: dict) -> str:
        """How to call a store entry at the Python level.

        A method parameter appears twice: once as the Viper parameter, which
        keeps the value the method was called with, and once as the local copy
        the body assigns to. They have the same Python name, so the parameter is
        marked as the value on entry to keep them apart.
        """
        known = variables.get(sil_name)
        if known is None:
            return sil_name
        var, is_arg = known
        name = self._plain_name(var)
        if is_arg and any(v.name == var.name and not arg
                          for v, arg in variables.values()):
            return '{} (on entry)'.format(name)
        return name

    def _branch_conditions(self, obl) -> List[dict]:
        """The branch conditions that led to the failing state."""
        result = []
        for pair in self._to_list(obl.branchConditionExps()):
            # `_1` is the condition over source variables, `_2` the same with
            # the values of the state substituted in; `_1` is what carries our
            # identifiers, so it is the one to back-translate.
            if self.backtranslator.is_internal_fact(pair._1()):
                continue
            rendered = self._render_condition(pair._1())
            if rendered is None or rendered == 'True':
                continue
            result.append({'condition': rendered, 'viper': str(pair._2())})
        return result

    def _render_condition(self, exp) -> Optional[str]:
        """Back-translate a branch condition, respecting its polarity.

        Taking the else branch is recorded as the negation of the condition, and
        Silicon builds that negation with the position of the condition itself,
        so a plain lookup would report the then branch.
        """
        negated = False
        if (isinstance(exp, self.jvm.viper.silver.ast.Not)
                and exp.pos() == exp.exp().pos()):
            negated = True
            exp = exp.exp()
        rendered = self._render_exp(exp)
        if rendered is None or not negated:
            return rendered
        return 'not ({})'.format(rendered)

    def _render_exp(self, exp) -> Optional[str]:
        """The Python form of a Viper expression, or None if it has none."""
        return self.backtranslator.render(exp).text

    def _sil_name_to_variable(self) -> Dict[str, tuple]:
        """A map from generated Viper variable names to ``(PythonVar, is_arg)``.

        Note that ``PythonMethod.locals`` is keyed by the *generated* name, so
        the Python name has to be read off the variable itself.
        """
        if self._sil_names is None:
            self._sil_names = {}

            def record(var, is_arg):
                if getattr(var, 'sil_name', None):
                    self._sil_names[var.sil_name] = (var, is_arg)

            for module in self.modules:
                for method in _all_methods(module):
                    for var in method.args.values():
                        record(var, True)
                    for var in method.locals.values():
                        record(var, False)
                    if method.result is not None:
                        record(method.result, False)
                for var in module.global_vars.values():
                    record(var, False)
        return self._sil_names

    def _member_of(self, obl) -> Optional[PythonMethod]:
        """The Python method the obligation's state belongs to."""
        member = obl.s().currentMember()
        if member is None or not member.isDefined():
            return None
        sil_name = str(member.get().name())
        for module in self.modules:
            method = _find_method_by_sil_name(module, sil_name)
            if method is not None:
                return method
        return None

    def prove(self) -> bool:
        """Ask the prover whether the current proof obligation holds."""
        self._check_open()
        result = self._report(self._session.prove())
        proved = result.proved()
        return bool(proved.get()) if proved is not None and proved.isDefined() else False

    def reset(self) -> None:
        """Discard everything the user changed about the current obligation."""
        self._check_open()
        self._report(self._session.reset())
        self._user_added.clear()

    def add_assumption(self, expression: str, free: bool = True) -> None:
        """Assume a Python expression in the state being debugged.

        With ``free`` set the expression is taken on faith; otherwise it has to
        follow from what is already assumed, and is rejected if it does not.
        """
        before = self._assumption_ids()
        self._report(self._session.addAssumptionExp(
            self._translate_input(expression), free))
        # Remember what the user added. It has to be shown whatever it says --
        # `type(i1) == int` is an assumption about the encoding, which would
        # otherwise be filtered as noise, but a user who asks for it means it.
        self._user_added |= self._assumption_ids() - before

    def _assumption_ids(self) -> set:
        obl = self.obligation
        if obl is None:
            return set()
        return {int(a.id()) for a in self._to_list(obl.assumptionsExp())}

    def assert_expression(self, expression: str) -> bool:
        """Ask whether a Python expression holds in the state being debugged."""
        result = self._report(self._session.assertExp(self._translate_input(expression)))
        proved = result.proved()
        return bool(proved.get()) if proved is not None and proved.isDefined() else False

    def _translate_input(self, expression: str):
        """Translate a user-entered Python expression to Viper."""
        obl = self.obligation
        if obl is None:
            raise DebugSessionError('There is no proof obligation to add to.')
        item = self._item_at(obl.originalErrorReason().offendingNode().pos())
        try:
            return self.expression_translator.translate(expression, item)
        except ExpressionInputError as e:
            raise DebugSessionError(str(e))

    @property
    def expression_translator(self) -> DebugExpressionTranslator:
        if self._expression_translator is None:
            self._expression_translator = DebugExpressionTranslator(
                self.translator, self.viper_ast, self.modules, sif=self.sif)
        return self._expression_translator

    def remove_assumptions(self, ids: List[int]) -> None:
        self._check_open()
        from nagini_translation.lib.util import list_to_seq
        seq = list_to_seq([self.jvm.java.lang.Integer(i) for i in ids], self.jvm)
        self._report(self._session.removeAssumptions(seq))

    # -----------------------------------------------------------------------
    # Internals
    # -----------------------------------------------------------------------

    @property
    def obligation(self):
        """The current ``ProofObligation``, or None if none is open."""
        self._check_open()
        obl = self._session.currentProofObligation()
        return obl.get() if obl is not None and obl.isDefined() else None

    def _check_open(self) -> None:
        if self._closed:
            raise DebugSessionError('This debug session has been closed.')

    def _report(self, result):
        """Turn a ``DebugCommandResult`` into an exception if it failed."""
        if not result.ok():
            messages = [str(m.text()) for m in self._to_list(result.messages())]
            raise DebugSessionError(
                _explain_failure('; '.join(messages)
                                 or 'The debugger command failed.'))
        return result

    def _to_list(self, seq) -> list:
        result = []
        iterator = seq.toIterator()
        while iterator.hasNext():
            result.append(iterator.next())
        return result

    def _item_at(self, pos) -> Optional[Item]:
        """The Python information recorded for a Viper position, if any."""
        if pos is None:
            return None
        try:
            if not hasattr(pos, 'id'):
                return None
            return self.items.get(pos.id())
        except Exception:
            return None

    def _failure_message(self, item: Optional[Item], fallback) -> str:
        """The Python expression a failure is about, or Viper's own message.

        ``fallback`` is anything with a readable message: a ``DebugFailureInfo``
        or an ``ErrorReason``.
        """
        if item is not None:
            from nagini_translation.lib.util import pprint
            return item.reason_string or pprint(item.node)
        if hasattr(fallback, 'readableMessage'):
            return str(fallback.readableMessage())
        return str(fallback.message())

    def _position_string(self, item: Optional[Item]) -> Optional[str]:
        if item is None or not hasattr(item.node, 'lineno'):
            return None
        return '{}:{}'.format(item.node.lineno, item.node.col_offset)

    def _python_member_name(self, info) -> Optional[str]:
        """The Python name of the member a failure occurred in.

        Silicon reports the Viper member name, which is the ``sil_name`` Nagini
        generated, so it has to be looked up in the module graph.
        """
        member = info.memberName()
        if member is None or not member.isDefined():
            return None
        sil_name = str(member.get())
        for module in self.modules:
            method = _find_method_by_sil_name(module, sil_name)
            if method is not None:
                return method.name
        return sil_name


def _all_methods(module: PythonModule) -> List[PythonMethod]:
    """Every method and function of a module, including those of its classes."""
    result = list(module.functions.values()) + list(module.methods.values())
    for cls in module.classes.values():
        result += list(cls.functions.values()) + list(cls.methods.values())
    return result


def _find_method_by_sil_name(module: PythonModule, sil_name: str) -> Optional[PythonMethod]:
    """Find the Python method a Viper member name was generated for."""
    for method in _all_methods(module):
        if method.sil_name == sil_name:
            return method
    return None


class DebugCommandHandler:
    """Owns at most one debug session and dispatches commands to it.

    Shared by every frontend (the ZMQ server, the LSP/MCP service) so they
    cannot drift apart. There is deliberately only one session: it keeps a
    prover and the symbolic state of a failed verification alive, and Silicon
    holds the configuration of the most recently created verifier in global
    state, so a second session would silently change the meaning of the first.
    Commands are serialized for the same reason.
    """

    def __init__(self, jvm: JVM, bv_size: int = 8, sif: bool = False,
                 float_encoding: str = None) -> None:
        self.jvm = jvm
        self.bv_size = bv_size
        self.sif = sif
        self.float_encoding = float_encoding
        self.session = None     # type: Optional[NaginiDebugSession]
        self._lock = threading.Lock()

    def handle(self, command: str, params: dict) -> dict:
        """Run one command and return a JSON-ready result.

        Never raises: a failure is reported as ``{'ok': False, 'error': ...}``
        so that a server loop cannot be taken down by one bad request.
        """
        with self._lock:
            try:
                return self._handle(command, params)
            except DebugSessionError as e:
                return {'ok': False, 'error': str(e)}
            except Exception as e:
                logging.exception('Error handling debug command %r.', command)
                return {'ok': False, 'error': str(e) or type(e).__name__}

    def _handle(self, command: str, params: dict) -> dict:
        if command == 'start':
            self.close()
            selected = params.get('select')
            self.session = NaginiDebugSession.start(
                self.jvm, params['file'], bv_size=self.bv_size,
                base_dir=params.get('baseDir'),
                selected=set(selected.split(',')) if selected else None,
                counterexample=params.get('counterexample', True),
                viper_args=params.get('viperArgs'), sif=self.sif,
                float_encoding=self.float_encoding)
            return {'ok': True,
                    'failures': [f.to_dict() for f in self.session.failures]}

        if command == 'stop':
            self.close()
            return {'ok': True}

        session = self.session
        if session is None or session.closed:
            raise DebugSessionError('There is no debug session; start one first.')

        if command == 'selectFailure':
            session.open_failure(int(params['index']))
        elif command == 'prove':
            return {'ok': True, 'proved': session.prove(),
                    'obligation': session.obligation_model()}
        elif command == 'assert':
            return {'ok': True,
                    'proved': session.assert_expression(params['expression']),
                    'obligation': session.obligation_model()}
        elif command == 'addAssumption':
            session.add_assumption(params['expression'],
                                   free=params.get('free', True))
        elif command == 'removeAssumptions':
            session.remove_assumptions([int(i) for i in params['ids']])
        elif command == 'reset':
            session.reset()
        elif command == 'obligation':
            pass
        else:
            raise DebugSessionError('Unknown debug command {!r}.'.format(command))
        return {'ok': True, 'obligation': session.obligation_model()}

    def close(self) -> None:
        if self.session is not None:
            self.session.close()
            self.session = None


def _is_internal_location(location: str) -> bool:
    """Whether a heap entry is part of the encoding rather than the program.

    Nagini keeps permission to predicates of its own -- to record which
    attributes may still be set, which globals are defined -- alongside the
    ones the program declares. They are the ones whose names start with an
    underscore, which no Python attribute Nagini generates a field for does.
    """
    return location.split('(')[0].split('.')[-1].startswith('_')


def _simplify_term(term: str) -> str:
    """Drop the verifier id Silicon appends to a symbol name.

    Terms are ``name@version@verifierId``, but the expressions the debugger
    reports use ``name@version``, so the two have to be brought to the same
    form before they can be compared.
    """
    parts = term.split('@')
    return '@'.join(parts[:2]) if len(parts) > 2 else term


def _explain_failure(message: str) -> str:
    """Add the Python-level reason to a message Silicon phrased in Viper terms."""
    marker = 'Function name '
    if marker in message and 'not found in program' in message:
        function = message.split(marker, 1)[1].split(' ', 1)[0]
        return ('{}\n\nThe program being debugged does not contain the operation '
                '{!r}. Nagini only encodes the operations a program actually uses, '
                'so an expression can only use operations that appear somewhere in '
                'it.'.format(message, function))
    return message


def _stop_silicon(silicon) -> None:
    try:
        silicon.stop()
    except Exception:
        logging.exception('Error while stopping the debug verifier.')
