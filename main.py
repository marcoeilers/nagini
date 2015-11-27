from typeinfo import *
from translator import *
from verifier import *
from jvmaccess import *
import ast
import astpp


def main() -> None:
    path = sys.argv[1]
    try:
        viperjar = sys.argv[2]
    except IndexError:
        viperjar = '/viper/git/silicon_qp/target/scala-2.11/silicon-quantified-permissions.jar'
    try:
        mypydir = sys.argv[3]
    except IndexError:
        mypydir = '/home/marco/.local/bin/mypy'
    ti = TypeInfo()
    typecorrect = ti.init(path, mypydir)
    if typecorrect:
        print("Type check successful")
        file = open(path, 'r')
        text = file.read()
        file.close()
        parseresult = ast.parse(text)
        print(astpp.dump(parseresult))
        bridge = Jpype(viperjar)
        translator = Translator(bridge, path, ti)
        prog = translator.translate_module(parseresult)
        print("Generated Silver program:")
        print(prog)
        verifier = Verifier(bridge, path)
        vresult = verifier.verify(prog)
        print(vresult)
    else:
        print("Type check failed")

if __name__ == '__main__':
    main()