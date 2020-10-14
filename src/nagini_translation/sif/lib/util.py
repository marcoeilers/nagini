"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

from typing import Optional

from nagini_translation.lib.context import Context
from nagini_translation.lib.program_nodes import MethodType
from nagini_translation.lib.typedefs import DomainFuncApp
from nagini_translation.translators.type_domain_factory import TypeDomainFactory

def configure_mpp_transformation(jvm, ctrl_opt: bool, seq_opt: bool,
                                 act_opt: bool, func_opt: bool, all_low: bool) -> None:
    """
    Configure which optimizations to apply in MPP transformation.
    - ctrl_opt: only generate those control variables which are needed.
    - seq_opt:  bunch together statements which are executed under the same condition without
                interference with the other execution.
    - act_opt:  at the beginning of each method add an 'assume p1' statement.
    - func_opt: only apply the _checkDefined and _isDefined functions in the first execution.
    """
    transformer_object = getattr(getattr(jvm.viper.silver.sif, 'SIFExtendedTransformer$'), 'MODULE$')
    transformer_object.optimizeControlFlow(ctrl_opt)
    transformer_object.optimizeSequential(seq_opt)
    transformer_object.optimizeRestrictActVars(act_opt)
    transformer_object.generateAllLowFuncs(all_low)
    if func_opt:
        transformer_object.addPrimedFuncAppReplacement(
            "_checkDefined", "first_arg")
        transformer_object.addPrimedFuncAppReplacement(
            "_isDefined", "true")
    else:
        transformer_object.clearPrimedFuncAppReplacement()

def _to_scala_set(jvm, inset: set):
    seq = jvm.scala.collection.mutable.ArraySeq(len(inset))
    for i, elem in enumerate(inset):
        seq.update(i, elem)
    return seq.toSet()

def set_all_low_methods(jvm, names: set) -> None:
    scala_set = _to_scala_set(jvm, names)
    getattr(getattr(jvm.viper.silver.sif, 'SIFExtendedTransformer$'), 'MODULE$').setAllLowMethods(scala_set)

def set_preserves_low_methods(jvm, names: set) -> None:
    scala_set = _to_scala_set(jvm, names)
    getattr(getattr(jvm.viper.silver.sif, 'SIFExtendedTransformer$'), 'MODULE$').setPreservesLowMethods(scala_set)

def set_equality_comp_functions(jvm, names: set) -> None:
    if not names:
        return
    names_seq = jvm.scala.collection.mutable.ArraySeq(len(names))
    for i, elem in enumerate(names):
        names_seq.update(i, (elem, elem))
    hash_map = names_seq.toMap()
    jvm.viper.silver.sif.SIFExtendedTransformer.equalityCompFunctions = hash_map

def in_postcondition_of_dyn_bound_call(type_factory: TypeDomainFactory,
                                       ctx: Context) -> Optional[DomainFuncApp]:
    """
    Determine if we are in a postcondition of a dynamically bound method. If so return the
    function application representing the type of self. Else return None.
    """
    if (ctx.current_class and
            ctx.current_function.method_type == MethodType.normal and
            ctx.obligation_context.is_translating_posts):
        return type_factory.typeof(
            next(iter(ctx.actual_function.args.values())).ref(), ctx)
    return None

def in_override_check(ctx: Context) -> bool:
    exceptional_positions = ['inheritance', 'override']
    return any(map(lambda tuple: tuple[0] in exceptional_positions, ctx.position))
