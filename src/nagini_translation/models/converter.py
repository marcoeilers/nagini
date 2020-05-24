from nagini_translation.lib.constants import RESULT_NAME
from nagini_translation.lib.program_nodes import PythonMethod, PythonType, GenericType, PythonField
from nagini_translation.lib.util import UnsupportedException
from collections import OrderedDict
from typing import Dict, List, Tuple, Union


ISSUBTYPE = 'issubtype<Bool>'

UNBOX_INT = 'int___unbox__%limited'
UNBOX_BOOL = 'bool___unbox__%limited'
TYPEOF = 'typeof<PyType>'
SNAP_TO = '$SortWrappers.$SnapTo'
SEQ_LENGTH = 'seq_ref_length<Int>'
SEQ_INDEX = 'seq_ref_index<Ref>'
SET_CARD = 'Set_card'
DICT_GET = 'dict_get_helper<Ref>'

UNIT = '$Snap.unit'


class Model:
    def __init__(self, input_store, current_store, old_heap, heap):
        self.input_store = input_store
        self.current_store = current_store
        self.old_heap = old_heap
        self.heap = heap

    def __str__(self):
        ostore_string = ',\n  '.join(['{} -> {}'.format(k, v) for k, v in self.input_store.items()])
        store_string = ',\n  '.join(['{} -> {}'.format(k, v) for k, v in self.current_store.items()])
        oheap_string = ',\n  '.join(['{} -> {{ {} }}'.format(o, ', '.join(['{} -> {}'.format(f, v)
                                                                           for f,v in parts.items()]))
                                     for o, parts in self.old_heap.items()])
        heap_string = ',\n  '.join(['{} -> {{ {} }}'.format(o, ', '.join(['{} -> {}'.format(f, v)
                                                                          for f,v in parts.items()]))
                                    for o, parts in self.heap.items()])
        return 'Old store:\n  {0}\nOld heap:\n  {1}\nCurrent store:\n  {2}\nCurrent heap:\n  {3}\n'.format(ostore_string,
                                                                                                           oheap_string,
                                                                                                           store_string,
                                                                                                           heap_string)

def get_func_value(model, name, args):
    args = tuple([' '.join(a.split()) for a in args])
    res = model[name].get(args)
    if res is not None:
        return res
    return model[name].get('else')

def get_func_values(model, name, args):
    args = tuple([' '.join(a.split()) for a in args])
    options = [(k[len(args):], v) for k, v in model[name].items() if k != 'else' and k[:len(args)] == args]
    els= model[name].get('else')
    return options, els

class Converter:

    def __init__(self, m: PythonMethod, model: Dict[str, Union[str, Dict[Tuple[str], str]]], store: Dict[str, str],
                 heap: Dict[Tuple[str, str], str], old_heap, jvm):
        self.method = m
        self.model = model
        self.store = store
        self.heap = heap
        self.old_heap = old_heap
        self.jvm = jvm
        self.reference_values = {}

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
            int(val)
            return True
        except:
            return False

    def generate_inputs(self):
        old_store = OrderedDict()
        store = OrderedDict()
        old_heap = OrderedDict()
        heap = OrderedDict()
        for name, var in self.method.args.items():
            if var.sil_name not in self.store:
                continue
            smt_name_or_value = self.store[var.sil_name]
            if self.is_value(smt_name_or_value, var.type):
                val = smt_name_or_value
                py_val = self.convert_value(val, var.type)
            elif smt_name_or_value in self.model:
                val = self.model[smt_name_or_value]
                py_val = self.convert_value(val, var.type)
            else:
                continue
            old_store[name] = py_val
        for name, var in list(self.method.locals.items()) + [('Result()', self.method.result)]:
            if var.sil_name not in self.store:
                continue
            smt_name_or_value = self.store[var.sil_name]
            if self.is_value(smt_name_or_value, var.type):
                val = smt_name_or_value
                py_val = self.convert_value(val, var.type)
            elif smt_name_or_value in self.model:
                val = self.model[smt_name_or_value]
                py_val = self.convert_value(val, var.type)
            else:
                continue
            display_name = 'Result()' if var.name == RESULT_NAME else var.name
            store[display_name] = py_val

        for (recv, field), value in self.heap.items():
            object_name, t = self.reference_values[self.model[recv]]
            smt_value = value
            if not isinstance(field, PythonField):
                heap[object_name] = self.convert_special_field(recv, self.heap, object_name, t, smt_value)
                continue
            py_value = self.convert_value(smt_value, field.type)
            if object_name not in heap:
                heap[object_name] = OrderedDict()
            heap[object_name][field.name] = py_value

        for (recv, field), value in self.old_heap.items():
            object_name, t = self.reference_values[self.model[recv]]
            smt_value = value
            if not isinstance(field, PythonField):
                old_heap[object_name] = self.convert_special_field(recv, self.old_heap, object_name, t, smt_value)
                continue
            py_value = self.convert_value(smt_value, field.type)
            if object_name not in old_heap:
                old_heap[object_name] = OrderedDict()
            old_heap[object_name][field.name] = py_value
        return Model(old_store, store, old_heap, heap)

    def convert_special_field(self, recv, heap, object_name, t, smt_value):
        res = OrderedDict()
        if t.python_class.name == 'list':
            length = self.get_func_value(SEQ_LENGTH, (smt_value,))
            parsed_length = self.parse_int(length)
            res['len({})'.format(object_name)] = parsed_length
            if parsed_length > 0:
                indices, els_index = self.get_func_values(SEQ_INDEX, (smt_value,))
                for ((index,), value) in indices:
                    converted_value = self.convert_value(value, t.type_args[0])
                    res['{}[{}]'.format(object_name, index)] = converted_value
                if els_index is not None and self.has_type(els_index, t.type_args[0]):
                    converted_value = self.convert_value(els_index, t.type_args[0])
                    res['{}[_]'.format(object_name)] = converted_value
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

    def convert_value(self, val, t: PythonType):
        if t.python_class.name == 'int':
            return self.convert_int_value(val)
        elif t.python_class.name == 'bool':
            return self.convert_bool_value(val)
        #elif t.python_class.name == SEQUENCE:
        #    return self.convert_list_value(val, t)
        else:
            if val in self.reference_values:
                return self.reference_values[val][0]
            else:
                actual_type = self.get_actual_type(val, t)
                i = 0
                ref_name = actual_type.python_class.name + str(i)
                while (ref_name, actual_type) in self.reference_values.values():
                    i += 1
                    ref_name = actual_type.python_class.name + str(i)
                self.reference_values[val] = (ref_name, actual_type)
                return ref_name

    def get_actual_type(self, val, t: PythonType):
        cls = t.python_class
        assert self.has_type(val, t)
        for sc in cls.direct_subclasses:
            if self.has_type(val, sc):
                return self.get_actual_type(val, sc)
        return t

    def convert_int_value(self, val):
        if self.has_type(val, 'bool'):
            return self.convert_bool_value(val)
        assert self.has_type(val, 'int')
        int_or_none = self.get_func_value(UNBOX_INT, (UNIT, val))
        if int_or_none is None:
            return self.generate_default_int()
        return self.parse_int(int_or_none)

    def convert_bool_value(self, val):
        assert self.has_type(val, 'bool')
        bool_or_none = self.get_func_value(UNBOX_BOOL, (UNIT, val))
        if bool_or_none is None:
            return self.generate_default_bool()
        return self.parse_bool(bool_or_none)

    def convert_list_value(self, val, t: PythonType):
        assert self.has_type(val, t)
        if self.has_len(val, t):
            pass
        int_or_none = self.get_func_value(UNBOX_INT, (UNIT, val))
        if int_or_none is None:
            return self.generate_default_int()
        return self.parse_int(int_or_none)

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
        type_val = self.get_type_val(t)
        val_type = self.get_func_value(TYPEOF, (val,))
        bool_or_none = self.get_func_value(ISSUBTYPE, (val_type, type_val))
        if bool_or_none is None:
            return False
        return self.parse_bool(bool_or_none)

    def parse_int(self, val):
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
