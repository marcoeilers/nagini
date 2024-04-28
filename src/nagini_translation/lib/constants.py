"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import ast

DEFAULT_CLIENT_SOCKET = "tcp://localhost:5555"
DEFAULT_SERVER_SOCKET = "tcp://*:5555"


LITERALS = ['True', 'False', 'None']

BUILTINS = ['cast',
            'int',
            'float',
            'isinstance',
            'bool',
            'len',
            'str',
            'set',
            'super',
            'range',
            'type',
            'list',
            'enumerate']

THREADING = ['Thread']

BUILTIN_PREDICATES = ['list_pred', 'set_pred', 'dict_pred', 'MayStart', 'ThreadPost']

FUNCTION_DOMAIN_NAME = 'Function'

MAY_SET_PRED = '_MaySet'

IS_DEFINED_FUNC = '_isDefined'

ASSERTING_FUNC = '_asserting'

NAME_QUANTIFIER_VAR = '_name'

COMBINE_NAME_FUNC = '_combine'

GLOBAL_IS_DEFINED_FUNC = '_isDefinedG'

CHECK_DEFINED_FUNC = '_checkDefined'

GLOBAL_CHECK_DEFINED_FUNC = '_checkDefinedG'

ARBITRARY_BOOL_FUNC = '_int_to_bool'

JOINABLE_FUNC = '_joinable'

THREAD_POST_PRED = '_thread_post'

THREAD_START_PRED = '_thread_start'

THREAD_DOMAIN = 'Thread'

METHOD_ID_DOMAIN = 'ThreadingID'

GET_ARG_FUNC = 'getArg'

GET_OLD_FUNC = 'getOld'

GET_METHOD_FUNC = 'getMethod'

GLOBAL_VAR_FIELD = '_val'

NAME_DOMAIN = '_Name'

COMBINED_NAME_ACCESSOR = '_get_combined_name'

COMBINED_PREFIX_ACCESSOR = '_get_combined_prefix'

SINGLE_NAME = '_single'

INTERNAL_NAMES = [
    'FuncTriple',
    'ft_get1',
    'ft_get2',
    'ft_get2',
    'ft_create',
    'A1',
    'A2',
    'A3',
    'PyType',
    'extends_',
    'issubtype',
    'isnotsubtype',
    'typeof',
    'get_type_arg1',
    'get_type_arg2',
    'get_type_nargs0',
    'get_type_nargs1',
    'issubtype_transitivity',
    'issubtype_reflexivity',
    'extends_implies_subtype',
    'issubtype_exclusion',
    'issubtype_exclusion_2',
    'issubtype_exclusion_propagation',
    'Thread',
    JOINABLE_FUNC,
    THREAD_POST_PRED,
    THREAD_START_PRED,
    METHOD_ID_DOMAIN,
    GET_ARG_FUNC,
    GET_OLD_FUNC,
    GET_METHOD_FUNC,
    MAY_SET_PRED,
    IS_DEFINED_FUNC,
    CHECK_DEFINED_FUNC,
    FUNCTION_DOMAIN_NAME,
    ARBITRARY_BOOL_FUNC,
    GLOBAL_VAR_FIELD,
    NAME_QUANTIFIER_VAR,
    COMBINE_NAME_FUNC,
    NAME_DOMAIN,
    COMBINED_NAME_ACCESSOR,
    COMBINED_PREFIX_ACCESSOR,
    SINGLE_NAME,
    '_is_single',
    '_is_combined',
    'm',     # the following are used in various
    'X',     # places in the resources/... files.
    'Y',
    'id',
    't',
    'g',
    'x',
    'n',
    'n1',
    'n2',
    'Low',
    'key',
    'guard',
    'value'
]

VIPER_KEYWORDS = [
    'result',
    'Int',
    'Perm',
    'Bool',
    'Ref',
    'Rational',
    'true',
    'false',
    'null',
    'import',
    'method',
    'function',
    'predicate',
    'program',
    'domain',
    'axiom',
    'var',
    'returns',
    'field',
    'define',
    'wand',
    'requires',
    'ensures',
    'invariant',
    'fold',
    'unfold',
    'inhale',
    'exhale',
    'new',
    'assert',
    'assume',
    'package',
    'apply',
    'elseif',
    'goto',
    'label',
    'fresh',
    'constraining',
    'Seq',
    'Set',
    'Multiset',
    'union',
    'intersection',
    'setminus',
    'subset',
    'unfolding',
    'in',
    'folding',
    'applying',
    'packaging',
    'old',
    'lhs',
    'let',
    'forall',
    'exists',
    'forperm',
    'acc',
    'wildcard',
    'write',
    'none',
    'epsilon',
    'perm',
    'unique',
    'range',
    'domain',
    'Map']

LEGAL_MAGIC_METHODS = {
    '__eq__',
    '__ne__',
    '__gt__',
    '__ge__',
    '__lt__',
    '__le__',

    '__add__',
    '__sub__',
    '__mul__',
    '__matmul__',
    '__truediv__',
    '__floordiv__',
    '__mod__',
    '__divmod__',
    '__pow__',
    '__lshift__',
    '__rshift__',
    '__and__',
    '__or__',
    '__xor__',
    
    '__neg__',
    '__pos__',
    '__invert__',
  

    '__radd__',
    '__rsub__',
    '__rmul__',
    '__rmatmul__',
    '__rtruediv__',
    '__rfloordiv__',
    '__rmod__',
    '__rdivmod__',
    '__rpow__',
    '__rlshift__',
    '__rrshift__',
    '__rand__',
    '__rxor__',
    '__ror__',

    '__init__',
    '__enter__',
    '__exit__',
    '__str__',
    '__len__',
    '__bool__',

    '__getitem__',
    '__setitem__',

    '__iadd__',
    '__isub__',
    '__imul__',
    '__imatmul__',
    '__itruediv__',
    '__ifloordiv__',
    '__imod__',
    '__ipow__',
    '__ilshift__',
    '__irshift__',
    '__iand__',
    '__ior__',
    '__ixor__',
}

RESULT_NAME = '_res'

ERROR_NAME = '_err'

END_LABEL = '__end'

LIST_TYPE = 'list'

RANGE_TYPE = 'range'

PSEQ_TYPE = 'PSeq'

PSET_TYPE = 'PSet'

PMSET_TYPE = 'PMultiset'

TUPLE_TYPE = 'tuple'

UNION_TYPE = 'Union'

DICT_TYPE = 'dict'

SET_TYPE = 'set'

STRING_TYPE = 'str'

BYTES_TYPE = 'bytes'

INT_TYPE = 'int'

PERM_TYPE = 'perm'

FLOAT_TYPE = 'float'

BOOL_TYPE = 'bool'

PRIMITIVE_PREFIX = '__prim__'

PRIMITIVE_INT_TYPE = PRIMITIVE_PREFIX + INT_TYPE

PRIMITIVE_PERM_TYPE = PRIMITIVE_PREFIX + PERM_TYPE

PRIMITIVE_BOOL_TYPE = PRIMITIVE_PREFIX + BOOL_TYPE

PRIMITIVE_SEQ_TYPE = PRIMITIVE_PREFIX + 'Seq'

PRIMITIVE_SET_TYPE = PRIMITIVE_PREFIX + 'Set'

PRIMITIVE_MSET_TYPE = PRIMITIVE_PREFIX + 'Multiset'


OBJECT_TYPE = 'object'

CALLABLE_TYPE = 'Callable'

PRIMITIVES = {PRIMITIVE_INT_TYPE, PRIMITIVE_BOOL_TYPE, PRIMITIVE_SEQ_TYPE,
              PRIMITIVE_SET_TYPE, CALLABLE_TYPE, PRIMITIVE_MSET_TYPE}

BOXED_PRIMITIVES = {INT_TYPE, BOOL_TYPE}

NAME_VAR = '__name__'

FILE_VAR = '__file__'

MODULE_VARS = (NAME_VAR, FILE_VAR)

MAIN_METHOD_NAME = '__main__'

MYPY_SUPERCLASSES = {
    'Sized',
}

EVAL_IO_SIGNATURE = ('eval_io', 'func', 'arg', 'result')

IGNORED_IMPORTS = {'_importlib_modulespec',
                   'abc',
                   'builtins',
                   'nagini_contracts',
                   'nagini_contracts.contracts',
                   'nagini_contracts.io_contracts',
                   'nagini_contracts.obligations',
                   'nagini_contracts.thread',
                   'sys',
                   'types',
                   'typing',
                   }

IGNORED_MODULE_NAMES = {
    '_importlib_modulespec': [],
    'abc': [],
    'builtins': [],
    'nagini_contracts': [],
    'nagini_contracts.contracts': [],
    'nagini_contracts.io_contracts': [],
    'nagini_contracts.obligations': ['BaseLock'],
    'sys': [],
    'types': [],
    'typing': [],
}

LEFT_OPERATOR_FUNCTIONS = {
    ast.Add: '__add__',
    ast.Sub: '__sub__',
    ast.Mult: '__mul__',
    ast.MatMult: '__matmul__',
    ast.Div: '__truediv__',
    ast.FloorDiv: '__floordiv__',
    ast.Mod: '__mod__',
    ast.Pow: '__pow__',
    ast.LShift: '__lshift__',
    ast.RShift: '__rshift__',
    ast.BitAnd: '__and__',
    ast.BitOr: '__or__',
    ast.BitXor: '__xor__',
}

INPLACE_OPERATOR_FUNCTIONS = {
    ast.Add: '__iadd__',
    ast.Sub: '__isub__',
    ast.Mult: '__imul__',
    ast.MatMult: '__imatmul__',
    ast.Div: '__itruediv__',
    ast.FloorDiv: '__ifloordiv__',
    ast.Mod: '__imod__',
    ast.Pow: '__ipow__',
    ast.LShift: '__ilshift__',
    ast.RShift: '__irshift__',
    ast.BitAnd: '__iand__',
    ast.BitOr: '__ior__',
    ast.BitXor: '__ixor__',
}

RIGHT_OPERATOR_FUNCTIONS = {
    ast.Add: '__radd__',
    ast.Sub: '__rsub__',
    ast.Mult: '__rmul__',
    ast.MatMult: '__rmatmul__',
    ast.Div: '__rtruediv__',
    ast.FloorDiv: '__rfloordiv__',
    ast.Mod: '__rmod__',
    ast.Pow: '__rpow__',
    ast.LShift: '__rlshift__',
    ast.RShift: '__rrshift__',
    ast.BitAnd: '__rand__',
    ast.BitOr: '__ror__',
    ast.BitXor: '__rxor__',
}