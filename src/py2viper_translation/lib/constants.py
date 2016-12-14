import ast

LITERALS = ['True', 'False', 'None']

BUILTINS = ['cast',
            'isinstance',
            'bool',
            'len',
            'set',
            'super',
            'range',
            'type']

BUILTIN_PREDICATES = ['list_pred', 'set_pred', 'dict_pred']

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

RESULT_NAME = '_res'

ERROR_NAME = '_err'

END_LABEL = '__end'

LIST_TYPE = 'list'

RANGE_TYPE = 'range'

TUPLE_TYPE = 'tuple'

UNION_TYPE = 'Union'

DICT_TYPE = 'dict'

SET_TYPE = 'set'

STRING_TYPE = 'str'

INT_TYPE = 'int'

BOOL_TYPE = 'bool'

OBJECT_TYPE = 'object'

PRIMITIVES = [] # [INT_TYPE, BOOL_TYPE]

IGNORED_IMPORTS = {'_importlib_modulespec',
                   'abc',
                   'builtins',
                   'py2viper_contracts',
                   'py2viper_contracts.contracts',
                   'py2viper_contracts.io',
                   'py2viper_contracts.obligations',
                   'sys',
                   'threading',
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
