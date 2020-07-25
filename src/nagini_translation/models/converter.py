"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

from nagini_translation.lib.constants import RESULT_NAME
from nagini_translation.lib.program_nodes import PythonMethod, PythonType, GenericType, PythonField, PythonClass, OptionalType
from nagini_translation.lib.util import int_to_string, UnsupportedException
from collections import OrderedDict
from typing import Dict, Tuple, Union


ISSUBTYPE = 'issubtype<Bool>'
UNBOX_INT = 'int___unbox__%limited'
UNBOX_BOOL = 'bool___unbox__%limited'
UNBOX_PSEQ = 'PSeq___sil_seq__%limited'
TYPEOF = 'typeof<PyType>'
SNAP_TO = '$SortWrappers.'
SEQ_LENGTH = 'seq_ref_length<Int>'
SEQ_INDEX = 'seq_ref_index<Ref>'
SET_CARD = 'Set_card'
DICT_GET = 'dict_get_helper<Ref>'

UNIT = '$Snap.unit'


class ScalaIteratorWrapper:
    def __init__(self, iterator):
        self.iterator = iterator

    def __next__(self):
        if self.iterator.hasNext():
            return self.iterator.next()
        else:
            raise StopIteration


class ScalaIterableWrapper:
    def __init__(self, iterable):
        self.iterable = iterable

    def __iter__(self):
        return ScalaIteratorWrapper(self.iterable.toIterator())


class Model:
    def __init__(self, input_store, current_store, old_heap, heap):
        self.input_store = input_store
        self.current_store = current_store
        self.old_heap = old_heap
        self.heap = heap

    def __str__(self):
        if self.current_store:
            store_string = '\n  ' + (',\n  '.join(['{} -> {}'.format(k, v) for k, v in self.current_store.items()]))
        else:
            store_string = ' Empty.'
        if self.heap:
            heap_string = '\n  ' + (',\n  '.join(['{} -> {{ {} }}'.format(o, ', '.join(['{} -> {}'.format(f, v)
                                                                                        for f, v in parts.items()]))
                                                  for o, parts in self.heap.items()]))
        else:
            heap_string = ' Empty.'
        if self.input_store is not None and self.old_heap is not None:
            if self.input_store:
                ostore_string = '\n  ' + (',\n  '.join(['{} -> {}'.format(k, v) for k, v in self.input_store.items()]))
            else:
                ostore_string = ' Empty.'
            if self.old_heap:
                oheap_string ='\n  ' + (',\n  '.join(['{} -> {{ {} }}'.format(o, ', '.join(['{} -> {}'.format(f, v)
                                                                                            for f,v in parts.items()]))
                                                      for o, parts in self.old_heap.items()]))
            else:
                oheap_string = ' Empty.'

            return 'Old store:{0}\nOld heap:{1}\nCurrent store:{2}\nCurrent heap:{3}\n'.format(ostore_string, oheap_string,
                                                                                               store_string, heap_string)
        return 'Store:{0}\nHeap:{1}\n'.format(store_string, heap_string)


class NoFittingValueException(Exception):
    pass


def get_func_value(model, name, args):
    args = tuple([' '.join(a.split()) for a in args])
    entry = model[name]
    if args == () and isinstance(entry, str):
        return entry
    res = entry.get(args)
    if res is not None:
        return res
    return model[name].get('else')


def get_func_values(model, name, args):
    args = tuple([' '.join(a.split()) for a in args])
    options = [(k[len(args):], v) for k, v in model[name].items() if k != 'else' and k[:len(args)] == args]
    els= model[name].get('else')
    return options, els


def get_parts(jvm, val):
    parser = getattr(getattr(jvm.viper.silver.verifier, 'ModelParser$'), 'MODULE$')
    res = []
    for part in ScalaIterableWrapper(parser.getApplication(val)):
        res.append(part)
    return res

def translate_sort(jvm, s):
    terms = jvm.viper.silicon.state.terms
    def get_sort_object(name):
        return getattr(terms, 'sorts$' + name + '$')
    def get_sort_class(name):
        return getattr(terms, 'sorts$' + name)

    if isinstance(s, get_sort_class('Set')):
        return 'Set<{}>'.format(translate_sort(jvm, s.elementsSort()))
    elif isinstance(s, get_sort_object('Ref')):
        return '$Ref'
    elif isinstance(s, get_sort_object('Snap')):
        return '$Snap'
    elif isinstance(s, get_sort_object('Perm')):
        return '$Perm'
    elif isinstance(s, get_sort_class('Seq')):
        return 'Seq<{}>'.format(translate_sort(jvm, s.elementsSort()))
    else:
        return str(s)


def evaluate_term(jvm, term, model):
    if isinstance(term, getattr(jvm.viper.silicon.state.terms, 'Unit$')):
        return '$Snap.unit'
    if isinstance(term, jvm.viper.silicon.state.terms.IntLiteral):
        return str(term)
    if isinstance(term, jvm.viper.silicon.state.terms.Null):
        return model['$Ref.null']
    if isinstance(term, jvm.viper.silicon.state.terms.Var):
        key = str(term)
        if key not in model:
            raise NoFittingValueException
        return model[key]
    elif isinstance(term, jvm.viper.silicon.state.terms.App):
        fname = str(term.applicable().id()) + '%limited'
        if fname not in model:
            fname = str(term.applicable().id())
            if fname not in model:
                fname = fname.replace('[', '<').replace(']', '>')
        args = []
        for arg in ScalaIterableWrapper(term.args()):
            args.append(evaluate_term(jvm, arg, model))
        res = get_func_value(model, fname, tuple(args))
        return res
    if isinstance(term, jvm.viper.silicon.state.terms.Combine):
        p0_val = evaluate_term(jvm, term.p0(), model)
        p1_val = evaluate_term(jvm, term.p1(), model)
        return '($Snap.combine ' + p0_val + ' ' + p1_val + ')'
    if isinstance(term, jvm.viper.silicon.state.terms.First):
        sub = evaluate_term(jvm, term.p(), model)
        if sub.startswith('($Snap.combine '):
            return get_parts(jvm, sub)[1]
    elif isinstance(term, jvm.viper.silicon.state.terms.Second):
        sub = evaluate_term(jvm, term.p(), model)
        if sub.startswith('($Snap.combine '):
            return get_parts(jvm, sub)[2]
    elif isinstance(term, jvm.viper.silicon.state.terms.SortWrapper):
        sub = evaluate_term(jvm, term.t(), model)
        from_sort_name = translate_sort(jvm, term.t().sort())
        to_sort_name = translate_sort(jvm, term.to())
        return get_func_value(model, SNAP_TO + from_sort_name + 'To' + to_sort_name, (sub,))
    elif isinstance(term, jvm.viper.silicon.state.terms.PredicateLookup):
        lookup_func_name = '$PSF.lookup_' + term.predname()
        toSnapTree = getattr(jvm.viper.silicon.state.terms, 'toSnapTree$')
        obj = getattr(toSnapTree, 'MODULE$')
        snap = obj.apply(term.args())
        psf_value = evaluate_term(jvm, term.psf(), model)
        snap_value = evaluate_term(jvm, snap, model)
        return get_func_value(model, lookup_func_name, (psf_value, snap_value))
    raise Exception(str(term))



class Converter:

    def __init__(self, m: PythonMethod, model: Dict[str, Union[str, Dict[Tuple[str], str]]], store: Dict[str, str],
                 heap: Dict[Tuple[str, str], str], old_heap, jvm, modules):
        self.method = m
        self.model = model
        self.store = store
        self.heap = heap
        self.old_heap = old_heap
        self.jvm = jvm
        self.reference_values = {}
        self.modules = modules

    def is_value(self, val, t):
        if t.python_class.name == 'int':
            return self.is_int_value(val)
        elif t.python_class.name == 'bool':
            return self.is_bool_value(val)
        else:
            return False

    def is_bool_value(self, val):
        return val in ('true', 'false')

    def is_int_value(self, val):
        try:
            self.parse_int(val)
            return True
        except:
            return False

    def convert_python_variable(self, name, var, target):
        try:
            if var.sil_name not in self.store:
                return
            if not var.show_in_ce:
                return
            term = self.store[var.sil_name]
            val = self.evaluate_term(term)
            display_name = 'Result()' if var.name == RESULT_NAME else var.name
            py_val = self.convert_value(val, var.type, display_name)
            target[display_name] = py_val
        except NoFittingValueException:
            pass

    def convert_python_field(self, recv, field, value, heap_contents, target, target_store):
        try:
            smt_ref_val = self.evaluate_term(recv)
            if isinstance(field, PythonField):
                receiver_type = field.cls
            else:
                global_module = self.modules[0].global_module
                if field in ('dict_acc', 'dict_acc2'):
                    receiver_type = global_module.classes['dict']
                elif field == 'list_acc':
                    receiver_type = global_module.classes['list']
                elif field == 'set_acc':
                    receiver_type = global_module.classes['set']
                elif field == '_val':
                    # This is a global variable.
                    var_sil_name = str(recv.applicable().id())
                    var_name, variable = [(name, var) for mod in self.modules for name, var in mod.global_vars.items()
                                          if var.sil_name == var_sil_name][0]
                    if value is not None:
                        py_value = self.convert_value(value, variable.type, var_name)
                    else:
                        py_value = '?'
                    target_store[var_name] = py_value
                    return
                elif field.startswith('MustRelease'):
                    lock_module = [m for m in self.modules if m.type_prefix == 'nagini_contracts.lock'][0]
                    lock_type = lock_module.classes['Lock']
                    self.get_reference_name(smt_ref_val, lock_type)
                    lock_name, _ = self.reference_values[smt_ref_val]
                    if field == 'MustReleaseUnbounded':
                        target['MustRelease({})'.format(lock_name)] = OrderedDict()
                    else:
                        target['MustRelease({}, _)'.format(lock_name)] = OrderedDict()
                    return
                else:
                    raise Exception
            self.get_reference_name(smt_ref_val, receiver_type)
            object_name, t = self.reference_values[smt_ref_val]
            smt_value = value
            if not isinstance(field, PythonField):
                target[object_name] = self.convert_special_field(recv, heap_contents, object_name, t, smt_value)
                return
            if smt_value is not None:
                py_value = self.convert_value(smt_value, field.type)
            else:
                py_value = '?'
            if object_name not in target:
                target[object_name] = OrderedDict()
            target[object_name][field.name] = py_value
        except NoFittingValueException:
            pass

    def convert_python_predicate(self, smt_args, pred, target):
        try:
            if isinstance(pred, str):
                # Special case for _MaySet, MustTerminate or MustInvoke
                contents = OrderedDict()
                if pred == 'MustTerminate':
                    target['MustTerminate(_)'] = contents
                    return
                if pred.startswith('MustInvoke'):
                    place_term = self.evaluate_term(smt_args[0])
                    place_class = self.modules[0].global_module.classes['Place']
                    place_val = self.convert_value(place_term, place_class)
                    if pred == 'MustInvokeBounded':
                        target['token({}, _)'.format(place_val)] = contents
                    else:
                        target['token({})'.format(place_val)] = contents
                    return
                if pred.startswith('_thread_'):
                    thread_term = self.evaluate_term(smt_args[0])
                    thread_module = self.modules[0].global_module
                    thread_class = thread_module.classes['Thread']
                    thread_val = self.convert_value(thread_term, thread_class)
                    if pred == '_thread_start':
                        target['MayStart({})'.format(thread_val)] = contents
                    else:
                        target['ThreadPost({})'.format(thread_val)] = contents
                    return
                if pred == '_MaySet':
                    field_name_int_term = self.evaluate_term(smt_args[1])
                    field_name_int = int(field_name_int_term)
                    field_name = int_to_string(field_name_int)
                    pyfield = [f for mod in self.modules for c in mod.classes.values()
                               for f in c.fields.values() if f.sil_name == field_name][0]
                    receiver_term = self.evaluate_term(smt_args[0])
                    receiver_val = self.convert_value(receiver_term, pyfield.cls)
                    name = "MaySet({}, '{}')".format(receiver_val, pyfield.name)
                    target[name] = OrderedDict()
                    return
                raise Exception(pred)
            args = []
            if isinstance(pred, PythonMethod):
                param_types = [f.type for f in pred.args.values()]
            else:
                param_types = [f.type for f in pred.get_parameters()]
            for arg, t in zip(smt_args, param_types):
                evaluated_arg = self.evaluate_term(arg)
                args.append(self.convert_value(evaluated_arg, t))
            if isinstance(pred, PythonMethod) and pred.cls:
                name = '{}.{}({})'.format(args[0], pred.name, ', '.join([str(a) for a in args[1:]]))
            elif isinstance(pred, PythonMethod):
                name = '{}({})'.format(pred.name, ', '.join([str(a) for a in args]))
            else:
                # IO operation
                all_args = [str(a) for a in args] + ['?' for a in pred.get_results()]
                name = '{}({})'.format(pred.name, ', '.join(all_args))
            target[name] = OrderedDict()
        except NoFittingValueException:
            pass

    def generate_inputs(self):
        old_store = OrderedDict()
        store = OrderedDict()
        old_heap = OrderedDict()
        heap = OrderedDict()
        for name, var in self.method.args.items():
            self.convert_python_variable(name, var, old_store)
        locals = list(self.method.locals.items())
        if self.method.result:
            locals += [('Result()', self.method.result)]
        for name, var in locals:
            self.convert_python_variable(name, var, store)

        for (recv, field), value in self.heap.items():
            if isinstance(recv, tuple):
                # this is a predicate
                self.convert_python_predicate(recv, field, heap)
            else:
                self.convert_python_field(recv, field, value, self.heap, heap, store)

        for (recv, field), value in self.old_heap.items():
            if isinstance(recv, tuple):
                # this is a predicate
                self.convert_python_predicate(recv, field, old_heap)
            else:
                self.convert_python_field(recv, field, value, self.old_heap, old_heap, old_store)
        if self.method.pure:
            # no old heap, no updated store.
            return Model(None, old_store, None, heap)
        return Model(old_store, store, old_heap, heap)

    def evaluate_term(self, term):
        return evaluate_term(self.jvm, term, self.model)

    def convert_sequence_value(self, val, content_type, object_name):
        res = OrderedDict()
        length = self.get_func_value(SEQ_LENGTH, (val,))
        parsed_length = self.parse_int(length)
        res['len({})'.format(object_name)] = parsed_length
        if parsed_length > 0:
            indices, els_index = self.get_func_values(SEQ_INDEX, (val,))
            for ((index,), value) in indices:
                converted_value = self.convert_value(value, content_type)
                res['{}[{}]'.format(object_name, index)] = converted_value
            if els_index is not None and self.has_type(els_index, content_type):
                converted_value = self.convert_value(els_index, content_type)
                res['{}[_]'.format(object_name)] = converted_value
        return res

    def convert_special_field(self, recv, heap, object_name, t, smt_value):
        res = OrderedDict()
        if isinstance(t, PythonClass):
            object_type = self.modules[0].global_module.classes['object']
            if t.name == 'dict':
                args = [object_type, object_type]
            else:
                args = [object_type]
            t = GenericType(t, args)
        if t.python_class.name == 'list':
            return self.convert_sequence_value(smt_value, t.type_args[0], object_name)
        elif t.python_class.name == 'set':
            length = self.get_func_value(SET_CARD, (smt_value,))
            parsed_length = self.parse_int(length)
            res['len({})'.format(object_name)] = parsed_length
        elif t.python_class.name == 'dict':
            length = self.get_func_value(SET_CARD, (smt_value,))
            parsed_length = self.parse_int(length)
            res['len({})'.format(object_name)] = parsed_length
            if parsed_length > 0:
                set_val = heap[(recv, 'dict_acc')]
                ref_val = heap[(recv, 'dict_acc2')]
                keys, els_val = self.get_func_values(DICT_GET, (set_val, ref_val))
                for ((key,), value) in keys:
                    converted_value = self.convert_value(value, t.type_args[1])
                    converted_key = self.convert_value(key, t.type_args[0])
                    res['{}[{}]'.format(object_name, converted_key)] = converted_value
                if els_val is not None and self.has_type(els_val, t.type_args[1]):
                    converted_value = self.convert_value(els_val, t.type_args[1])
                    res['{}[_]'.format(object_name)] = converted_value
        return res

    def convert_value(self, val, t: PythonType, name: str = None):
        if t.python_class.name == 'int':
            return self.convert_int_value(val)
        elif t.python_class.name == 'bool':
            return self.convert_bool_value(val)
        elif t.python_class.name == 'PSeq':
            return self.convert_pseq_value(val, t, name)
        else:
            return self.get_reference_name(val, t)

    def get_reference_name(self, val, t: PythonType):
        if val in self.reference_values:
            return self.reference_values[val][0]
        else:
            actual_type = self.get_actual_type(val, t)
            if actual_type.name == 'NoneType':
                self.reference_values[val] = ('None', actual_type)
                return 'None'
            actual_type_name = actual_type.python_class.name
            i = 0
            ref_name = actual_type_name + str(i)
            while (ref_name, actual_type) in self.reference_values.values():
                i += 1
                ref_name = actual_type_name + str(i)
            self.reference_values[val] = (ref_name, actual_type)
            return ref_name

    def get_actual_type(self, val, t: PythonType):
        cls = t.python_class
        if not self.has_type(val, cls):
            if isinstance(t, OptionalType):
                none_type = self.modules[0].global_module.classes['NoneType']
                if self.has_type(val, none_type) or '$Ref.null' in self.model and val == self.model['$Ref.null']:
                    return none_type
            raise NoFittingValueException
        for sc in cls.direct_subclasses:
            if self.has_type(val, sc):
                return self.get_actual_type(val, sc)
        return t

    def convert_pseq_value(self, val, t: PythonType, name):
        sequence = self.get_func_value(UNBOX_PSEQ, (UNIT, val))
        sequence_info = self.convert_sequence_value(sequence, t.type_args[0], name)
        return 'Sequence: {{ {} }}'.format(', '.join(['{} -> {}'.format(k, v) for k, v in sequence_info.items()]))

    def convert_int_value(self, val):
        if self.has_type(val, 'bool'):
            return self.convert_bool_value(val)
        if not self.has_type(val, 'int'):
            raise NoFittingValueException
        int_or_none = self.get_func_value(UNBOX_INT, (UNIT, val))
        if int_or_none is None:
            return self.generate_default_int()
        return self.parse_int(int_or_none)

    def convert_bool_value(self, val):
        if not self.has_type(val, 'bool'):
            raise NoFittingValueException
        bool_or_none = self.get_func_value(UNBOX_BOOL, (UNIT, val))
        if bool_or_none is None:
            return self.generate_default_bool()
        return self.parse_bool(bool_or_none)

    def convert_list_value(self, val, t: PythonType):
        if not self.has_type(val, t):
            raise NoFittingValueException
        if self.has_len(val, t):
            pass
        int_or_none = self.get_func_value(UNBOX_INT, (UNIT, val))
        if int_or_none is None:
            return self.generate_default_int()
        return self.parse_int(int_or_none)

    def get_type_vals(self, t: PythonClass):
        return self.get_func_values(t.sil_name + '<PyType>', ())

    def get_type_val(self, t: Union[str, PythonType]):
        if isinstance(t, str):
            return self.model[t + '<PyType>']
        else:
            if isinstance(t, GenericType):
                func_name = t.python_class.sil_name + '<PyType>'
                args = tuple([self.get_type_val(ta) for ta in t.type_args])
                return self.get_func_value(func_name, args)
            else:
                return self.model[t.python_class.sil_name + '<PyType>']

    def has_type(self, val, t: Union[str, PythonType]) -> bool:
        val_type = self.get_func_value(TYPEOF, (val,))
        if isinstance(t, PythonType) and t.python_class.name.startswith('__prim__'):
            return False
        if isinstance(t, PythonType) and t.python_class.name == 'tuple':
            # TODO: handle properly
            return False
        if isinstance(t, PythonType) and not isinstance(t, GenericType) and t.python_class.type_vars:
            arg_options, els = self.get_type_vals(t)
            for _,option in arg_options:
                bool_or_none = self.get_func_value(ISSUBTYPE, (val_type, option))
                if bool_or_none is None:
                    continue
                if self.parse_bool(bool_or_none):
                    return True
            bool_or_none = self.get_func_value(ISSUBTYPE, (val_type, els))
            if bool_or_none is None:
                return False
            return self.parse_bool(bool_or_none)
        try:
            type_val = self.get_type_val(t)
            if type_val == val_type:
                return True
            bool_or_none = self.get_func_value(ISSUBTYPE, (val_type, type_val))
            if bool_or_none is None:
                return False
            return self.parse_bool(bool_or_none)
        except KeyError:
            return False

    def parse_int(self, val):
        if val.startswith('(-') and val.endswith(')'):
            return - int(val[2:-1])
        return int(val)

    def parse_bool(self, val):
        if val == 'true':
            return True
        elif val == 'false':
            return False
        else:
            raise Exception(val)

    def generate_default_value(self, t: PythonType):
        if t.python_class.name == 'int':
            return self.generate_default_int()
        elif t.python_class.name == 'bool':
            return self.generate_default_bool()
        else:
            raise UnsupportedException

    def generate_default_int(self):
        return 0

    def generate_default_bool(self):
        return False

    def get_func_value(self, name, args):
        return get_func_value(self.model, name, args)

    def get_func_values(self, name, args):
        return get_func_values(self.model, name, args)
