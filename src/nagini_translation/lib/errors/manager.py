"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

"""Error handling state is stored in singleton ``manager``."""


from collections import namedtuple, OrderedDict
from uuid import uuid1

from typing import Any, List, Optional

from nagini_translation.lib.errors.wrappers import Error
from nagini_translation.lib.errors.rules import Rules
from nagini_translation.lib.jvmaccess import JVM
from nagini_translation.models.converter import Converter, SNAP_TO, get_func_value


Item = namedtuple('Item', 'node vias reason_string')


class ErrorManager:
    """A singleton object that stores the state needed for error handling."""

    def __init__(self) -> None:
        self._items = {}                # type: Dict[str, Item]
        self._conversion_rules = {}     # type: Dict[str, Rules]

    def add_error_information(
            self, node: 'ast.Node', vias: List[Any], reason_string: str,
            conversion_rules: Rules = None) -> str:
        """Add error information to state."""
        item_id = str(uuid1())
        assert item_id not in self._items
        self._items[item_id] = Item(node, vias, reason_string)
        if conversion_rules is not None:
            self._conversion_rules[item_id] = conversion_rules
        return item_id

    def clear(self) -> None:
        """Clear all state."""
        self._items.clear()
        self._conversion_rules.clear()

    def convert(
            self,
            errors: List['AbstractVerificationError'],
            jvm: JVM,
            modules) -> List[Error]:
        """Convert Viper errors into Nagini errors.

        It does that by wrapping in ``Error`` subclasses.
        """
        new_errors = [
            self._convert_error(error, jvm, modules)
            for error in errors
        ]
        return new_errors

    def get_vias(self, node_id: str) -> List[Any]:
        """Get via information for the given ``node_id``."""
        item = self._items[node_id]
        return item.vias

    def _get_item(self, pos: 'ast.AbstractSourcePosition') -> Optional[Item]:
        if hasattr(pos, 'id'):
            node_id = pos.id()
            return self._items[node_id]
        return None

    def _get_conversion_rules(
            self, position: 'ast.AbstractSourcePosition') -> Optional[Rules]:
        if hasattr(position, 'id'):
            node_id = position.id()
            if node_id in self._conversion_rules:
                return self._conversion_rules[node_id]
        return None

    def _try_get_rules_workaround(
            self, node: 'ast.Node', jvm: Optional[JVM]) -> Optional[Rules]:
        """Try to extract rules out of ``node``.

        Due to optimizations, Silicon sometimes returns not the correct
        offending node, but an And that contains it. This method tries
        to work around this problem.

        .. todo::

            In the long term we should discuss with Malte how to solve
            this problem properly.
        """
        rules = self._get_conversion_rules(node.pos())
        if rules or not jvm:
            return rules
        if (isinstance(node, jvm.viper.silver.ast.And) or
                isinstance(node, jvm.viper.silver.ast.Implies)):
            return (self._get_conversion_rules(node.left().pos()) or
                    self._get_conversion_rules(node.right().pos()) or
                    self._try_get_rules_workaround(node.left(), jvm) or
                    self._try_get_rules_workaround(node.right(), jvm))
        return

    def transformError(self, error: 'AbstractVerificationError') -> 'AbstractVerificationError':
        """ Transform silver error to a fixpoint. """
        old_error = None
        while old_error != error:
            old_error = error
            error = error.transformedError()
        return error

    def translate_sort(self, jvm, s):
        terms = jvm.viper.silicon.state.terms
        def get_sort_object(name):
            return getattr(terms, 'sorts$' + name + '$')
        def get_sort_class(name):
            return getattr(terms, 'sorts$' + name)

        if isinstance(s, get_sort_class('Set')):
            return 'Set<{}>'.format(self.translate_sort(jvm, s.elementsSort()))
        elif isinstance(s, get_sort_object('Ref')):
            return '$Ref'
        elif isinstance(s, get_sort_class('Seq')):
            return 'Seq<{}>'.format(self.translate_sort(jvm, s.elementsSort()))
        else:
            return str(s)


    def try_evaluate(self, jvm, term, model):
        if isinstance(term, jvm.viper.silicon.state.terms.First):
            sub = self.try_evaluate(jvm, term.p(), model)
            if sub.startswith('($Snap.combine '):
                return self.get_parts(jvm, sub)[1]
        elif isinstance(term, jvm.viper.silicon.state.terms.Second):
            sub = self.try_evaluate(jvm, term.p(), model)
            if sub.startswith('($Snap.combine '):
                return self.get_parts(jvm, sub)[2]
        elif isinstance(term, jvm.viper.silicon.state.terms.Var):
            return model[term.id().name()]
        elif isinstance(term, jvm.viper.silicon.state.terms.SortWrapper):
            sub = self.try_evaluate(jvm, term.t(), model)
            sort_name = self.translate_sort(jvm, term.to())
            return get_func_value(model, SNAP_TO + sort_name, (sub,))
        raise Exception

    def get_parts(self, jvm, val):
        parser = getattr(getattr(jvm.viper.silver.verifier, 'ModelParser$'), 'MODULE$')
        res_it = parser.getApplication(val).toIterator()
        res = []
        while res_it.hasNext():
            part = res_it.next()
            res.append(part)
        return res

    def _convert_error(
            self, original_error: 'AbstractVerificationError',
            jvm: JVM, modules) -> Error:
        error = self.transformError(original_error)
        reason_pos = error.reason().offendingNode().pos()
        reason_item = self._get_item(reason_pos)
        position = error.pos()
        rules = self._try_get_rules_workaround(
            error.offendingNode(), jvm)
        if rules is None:
            rules = self._try_get_rules_workaround(
                error.reason().offendingNode(), jvm)
        if rules is None:
            rules = {}
        error_item = self._get_item(position)

        if original_error.scope().isDefined() and original_error.counterExample().isDefined():
            method_name = original_error.scope().get().name()
            pymethods = [m for mod in modules for m in mod.methods.values() if m.sil_name == method_name]
            if not pymethods:
                pymethods = [m for mod in modules for c in mod.classes.values() for m in c.methods.values()
                             if m.sil_name == method_name]
            pymethod = pymethods[0]
            scala_store = original_error.counterExample().get().store()
            store = OrderedDict()
            scala_store_iter = scala_store.toIterator()
            while scala_store_iter.hasNext():
                entry = scala_store_iter.next()
                store[entry._1()] = entry._2().toString()
            scala_model = original_error.counterExample().get().nativeModel()
            model = OrderedDict()
            scala_model_iter = scala_model.entries().toIterator()
            while scala_model_iter.hasNext():
                entry = scala_model_iter.next()
                name = entry._1()
                value = entry._2()
                if isinstance(value, jvm.viper.silver.verifier.SingleEntry):
                    model[name] = value.value()
                else:
                    entry_val = OrderedDict()
                    options_it = value.options().toIterator()
                    while options_it.hasNext():
                        option = options_it.next()
                        option_value = option._2()
                        option_key = ()
                        option_key_it = option._1().toIterator()
                        while option_key_it.hasNext():
                            option_key_entry = option_key_it.next()
                            option_key += (option_key_entry,)
                        entry_val[option_key] = option_value
                    entry_val['else'] = value.els()
                    model[name] = entry_val

            heap = OrderedDict()
            heap_it = original_error.counterExample().get().heap().toIterator()
            while heap_it.hasNext():
                chunk = heap_it.next()
                if not isinstance(chunk, jvm.viper.silicon.state.BasicChunk):
                    continue
                if not str(chunk.resourceID()) == 'FieldID':
                    continue
                field_name = str(chunk.id())
                recv_val = str(chunk.args().toIterator().next())
                value = self.try_evaluate(jvm, chunk.snap(), model)
                if field_name in ('list_acc', 'set_acc', 'dict_acc', 'dict_acc2'):
                    # Special handling,
                    pyfield = field_name
                else:
                    pyfield = [f for mod in modules for c in mod.classes.values() for f in c.fields.values()
                               if f.sil_name == field_name][0]

                heap[(recv_val, pyfield)] = ' '.join(value.split())

            oheap = OrderedDict()
            oheap_it = original_error.counterExample().get().oldHeap().toIterator()
            while oheap_it.hasNext():
                chunk = oheap_it.next()
                if not isinstance(chunk, jvm.viper.silicon.state.BasicChunk):
                    continue
                if not str(chunk.resourceID()) == 'FieldID':
                    continue
                field_name = str(chunk.id())
                if field_name in ('list_acc', 'set_acc', 'dict_acc', 'dict_acc2'):
                    # Special handling,
                    pyfield = field_name
                else:
                    pyfield = [f for mod in modules for c in mod.classes.values() for f in c.fields.values()
                               if f.sil_name == field_name][0]
                recv_val = str(chunk.args().toIterator().next())
                value = self.try_evaluate(jvm, chunk.snap(), model)
                oheap[(recv_val, pyfield)] = ' '.join(value.split())

            converter = Converter(pymethod, model, store, heap, oheap, jvm)
            # try:
            inputs = converter.generate_inputs()
            # except:
            #     inputs = None
        else:
            inputs = None

        if error_item:
            return Error(error, rules, reason_item, error_item.node,
                         error_item.vias, inputs=inputs)
        else:
            return Error(error, rules, reason_item, inputs=inputs)


manager = ErrorManager()     # pylint: disable=invalid-name
