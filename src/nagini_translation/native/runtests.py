import os
import subprocess
import ast
import difflib
from colorama import Fore, Style

# iterate over files contained in ./tests directory and starting with test_


def handle_diff(sol, res):
    if (sol == None):
        print(Fore.RED+"EMPTY"+Style.RESET_ALL)
    else:
        print(""+((Fore.GREEN+"PASSED") if res ==
            sol else (Fore.RED+"FAILED"))+Style.RESET_ALL)
        if (res != sol):
            differences = list(difflib.ndiff(res.splitlines(), sol.splitlines()))
            #return "\n\t" + "\n\t".join(differences)
            print("\n\t" + "\n\t".join(filter(lambda x: x.startswith("+") or x.startswith("-") or x.startswith("?"), differences)))


for filename in os.listdir('nagini_translation/native/tests'):
    if filename.startswith("test_"):
        print("Running test for file: " + filename, end="")
        filepath = 'nagini_translation/native/tests/' + filename
        with open(filepath, "r", encoding="utf-8") as file:
            tree = ast.parse(file.read(), filename=filepath)
        functions = [node for node in ast.walk(
            tree) if isinstance(node, ast.FunctionDef) and any(
                isinstance(
                    decorator, ast.Name) and decorator.id == "ContractOnly"
                for decorator in node.decorator_list
        )]
        result = subprocess.run('python3 nagini_translation/main.py --skip-verification ' +
                                filepath, cwd="./", shell=True, capture_output=True, text=True)
        print("\n  ENV" + (20 - len("ENV")) * " ", end="")
        handle_diff(ast.get_docstring(tree), result.stdout.split("/*--END OF ENV--*/")[0])
        if (len(result.stdout.split("/*--END OF ENV--*/")) > 1):
            fun = result.stdout.split("/*--END OF ENV--*/")[1] or None
            for i, f in enumerate(functions):
                print("\n  "+f.name + (20 - len(f.name)) * " ", end="")
                handle_diff(ast.get_docstring(f), fun.split("/*----*/")[i])
        print()
file.close()
print("All tests completed.")
