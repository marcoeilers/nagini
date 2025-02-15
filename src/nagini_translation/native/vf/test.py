import nagini_translation.native.vf.pymodules as vfpy
import nagini_translation.native.vf.standard.literal as lit
import nagini_translation.native.vf.standard.expr as expr
import nagini_translation.native.vf.standard as vf

def main():
    pred = vfpy.PyObj_HasVal(lit.Ptr(), expr.ImmediateLiteral(lit.Int()));