import ast

DEFAULT_CLIENT_SOCKET = "tcp://localhost:5555"
DEFAULT_SERVER_SOCKET = "tcp://*:5555"


LITERALS = ['True', 'False', 'None']

BUILTINS = ['cast',
            'isinstance',
            'bool',
            'len',
            'str',
            'set',
            'super',
            'range',
            'type']

BUILTIN_PREDICATES = ['list_pred', 'set_pred', 'dict_pred']

FUNCTION_DOMAIN_NAME = 'Function'

MAY_SET_PRED = '_MaySet'

IS_DEFINED_FUNC = '_isDefined'

CHECK_DEFINED_FUNC = '_checkDefined'

ARBITRARY_BOOL_FUNC = '_int_to_bool'

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
    MAY_SET_PRED,
    IS_DEFINED_FUNC,
    CHECK_DEFINED_FUNC,
    FUNCTION_DOMAIN_NAME,
    ARBITRARY_BOOL_FUNC,
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
    'unique']

LEGAL_MAGIC_METHODS = {
    '__eq__',
    '__ne__',
    '__gt__',
    '__ge__',
    '__lt__',
    '__le__',
    '__add__',
    '__sub_',
    '__mul__',
    '__floordiv__',
    '__mod__',
    '__init__',
    '__enter__',
    '__exit__',
    '__str__',
    '__len__',
    '__bool__',
}

RESULT_NAME = '_res'

ERROR_NAME = '_err'

END_LABEL = '__end'

LIST_TYPE = 'list'

RANGE_TYPE = 'range'

SEQ_TYPE = 'Sequence'

TUPLE_TYPE = 'tuple'

UNION_TYPE = 'Union'

DICT_TYPE = 'dict'

SET_TYPE = 'set'

STRING_TYPE = 'str'

BYTES_TYPE = 'bytes'

INT_TYPE = 'int'

BOOL_TYPE = 'bool'

PRIMITIVE_PREFIX = '__prim__'

PRIMITIVE_INT_TYPE = PRIMITIVE_PREFIX + INT_TYPE

PRIMITIVE_BOOL_TYPE = PRIMITIVE_PREFIX + BOOL_TYPE

PRIMITIVE_SEQ_TYPE = PRIMITIVE_PREFIX + SEQ_TYPE

OBJECT_TYPE = 'object'

CALLABLE_TYPE = 'Callable'

PRIMITIVES = {PRIMITIVE_INT_TYPE, PRIMITIVE_BOOL_TYPE, PRIMITIVE_SEQ_TYPE, CALLABLE_TYPE}

BOXED_PRIMITIVES = {INT_TYPE, BOOL_TYPE, CALLABLE_TYPE}

MYPY_SUPERCLASSES = {
    'Sized',
}

EVAL_IO_SIGNATURE = ('eval_io', 'func', 'arg', 'result')

IGNORED_IMPORTS = {'_importlib_modulespec',
                   'abc',
                   'builtins',
                   'nagini_contracts',
                   'nagini_contracts.contracts',
                   'nagini_contracts.io',
                   'nagini_contracts.obligations',
                   'sys',
                   'types',
                   'typing',
                   }

OPERATOR_FUNCTIONS = {
    ast.Add: '__add__',
    ast.Sub: '__sub__',
    ast.Mult: '__mul__',
    ast.FloorDiv: '__floordiv__',
    ast.Mod: '__mod__',
}
