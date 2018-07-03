"""
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

def configure_mpp_transformation(jvm, ctrl_opt: bool, seq_opt: bool,
                                 act_opt: bool, func_opt: bool) -> None:
    """
    Configure which optimizations to apply in MPP transformation.
    - ctrl_opt: only generate those control variables which are needed.
    - seq_opt:  bunch together statements which are executed under the same condition without
                interference with the other execution.
    - act_opt:  at the beginning of each method add an 'assume p1' statement.
    - func_opt: only apply the _checkDefined and _isDefined functions in the first execution.
    """
    jvm.viper.silver.sif.SIFExtendedTransformer.optimizeControlFlow(ctrl_opt)
    jvm.viper.silver.sif.SIFExtendedTransformer.optimizeSequential(seq_opt)
    jvm.viper.silver.sif.SIFExtendedTransformer.optimizeRestrictActVars(act_opt)
    if func_opt:
        jvm.viper.silver.sif.SIFExtendedTransformer.addPrimedFuncAppReplacement(
            "_checkDefined", "first_arg")
        jvm.viper.silver.sif.SIFExtendedTransformer.addPrimedFuncAppReplacement(
            "_isDefined", "true")
    else:
        jvm.viper.silver.sif.SIFExtendedTransformer.clearPrimedFuncAppReplacement()
