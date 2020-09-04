"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

from collections import OrderedDict
from nagini_translation.models.converter import Converter, evaluate_term, ScalaIterableWrapper, NoFittingValueException


class Extractor:

    def extract_counterexample(self, jvm, pymethod, ce, modules):
        scala_store = ce.store()
        store = OrderedDict()
        for entry in ScalaIterableWrapper(scala_store):
            store[entry._1()] = entry._2()
        scala_model = ce.model()
        model = OrderedDict()
        for entry in ScalaIterableWrapper(scala_model.entries()):
            self.extract_model_entry(entry, jvm, model)

        heap = OrderedDict()
        for chunk in ScalaIterableWrapper(ce.heap()):
            self.extract_chunk(chunk, jvm, modules, model, heap)

        oheap = OrderedDict()
        if ce.oldHeap().isDefined():
            for chunk in ScalaIterableWrapper(ce.oldHeap().get()):
                self.extract_chunk(chunk, jvm, modules, model, oheap)

        converter = Converter(pymethod, model, store, heap, oheap, jvm, modules)
        result = converter.generate_inputs()
        if hasattr(ce, 'second'):
            second_exec_result = self.extract_counterexample(jvm, pymethod, ce.second(), modules)
            result = 'First execution:\n' + str(result) + '\nSecond execution:\n' + str(second_exec_result)
        return result

    def extract_model_entry(self, entry, jvm, target):
        name = entry._1()
        value = entry._2()
        if isinstance(value, jvm.viper.silver.verifier.SingleEntry):
            target[name] = value.value()
        else:
            entry_val = OrderedDict()
            for option in ScalaIterableWrapper(value.options()):
                option_value = option._2()
                option_key = ()
                for option_key_entry in ScalaIterableWrapper(option._1()):
                    option_key += (option_key_entry,)
                entry_val[option_key] = option_value
            entry_val['else'] = value.els()
            target[name] = entry_val

    def extract_chunk(self, chunk, jvm, modules, model, target):
        if not isinstance(chunk, jvm.viper.silicon.state.BasicChunk):
            print('WARNING: Found non-basic heap chunk type; quantified chunks are currently not supported and will '
                  'not be shown in counterexamples.')
            return
        resource_id = str(chunk.resourceID())
        if not resource_id in ('FieldID', 'PredicateID'):
            return
        if resource_id == 'FieldID':
            self.extract_field_chunk(chunk, jvm, modules, model, target)
        else:
            self.extract_predicate_chunk(chunk, modules, target)

    def extract_field_chunk(self, chunk, jvm, modules, model, target):
        field_name = str(chunk.id())
        recv_val = chunk.args().toIterator().next()
        try:
            value = evaluate_term(jvm, chunk.snap(), model)
            value = ' '.join(value.split())
        except NoFittingValueException:
            value = None
        if field_name in ('__iter_index', '__previous', '__container'):
            return
        if field_name in ('list_acc', 'set_acc', 'dict_acc', 'dict_acc2', '_val', 'MustReleaseBounded', 'MustReleaseUnbounded'):
            # Special handling,
            pyfield = field_name
        else:
            pyfield = [f for mod in modules for c in mod.classes.values() for f in c.python_class.fields.values()
                       if f.sil_name == field_name][0]

        target[(recv_val, pyfield)] = value

    def extract_predicate_chunk(self, chunk, modules, target):
        pred_name = str(chunk.id())
        if pred_name in ('MustTerminate', 'MustInvokeBounded', 'MustInvokeUnbounded', '_MaySet', '_thread_start', '_thread_post'):
            pypred = pred_name
        else:
            pypreds = [p for mod in modules for p in mod.predicates.values()
                       if p.sil_name == pred_name]
            if not pypreds:
                pypreds = [p for mod in modules for c in mod.classes.values() for p in c.predicates.values()
                           if p.sil_name == pred_name]
                if not pypreds:
                    pypreds = [o for mod in modules for o in mod.io_operations.values()
                               if o.sil_name == pred_name]
            pypred = pypreds[0]
        pred_args = []
        for pred_arg in ScalaIterableWrapper(chunk.args()):
            pred_args.append(pred_arg)

        target[(tuple(pred_args), pypred)] = None
