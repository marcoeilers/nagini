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
        sol1 = sol.replace("\r", "").replace("\n", "").replace(" ", "").replace("\t", "")
        res1 = res.replace("\r", "").replace("\n", "").replace(" ", "").replace("\t", "")
        if (res1 == sol1):
            print(""+(Fore.GREEN+"PASSED")+Style.RESET_ALL)
        else:
            print((Fore.RED+"FAILED")+Style.RESET_ALL, end="")
            differences = list(difflib.ndiff(res.splitlines(), sol.splitlines()))
            print("\n\t" + "\n\t".join(filter(lambda x: x.startswith("+") or x.startswith("-") or x.startswith("?"), differences)))
            print()

for filename in os.listdir('nagini_translation/native/tests'):
    if filename.startswith("test_"):
        print("Running test for file: " + filename)
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
        print("  ENV" + (20 - len("ENV")) * " ", end="")
        if (result.stderr==""):
            separated=result.stdout.split("/*--END OF ENV--*/\n")
            handle_diff(ast.get_docstring(tree), separated[0])
            if (len(separated) > 1):
                fun = separated[1] or None
                for i, f in enumerate(functions):
                    print("  "+f.name + (20 - len(f.name)) * " ", end="")
                    handle_diff(ast.get_docstring(f), fun.split("\n/*----*/\n")[i])
        else:
            print(Fore.RED+"FAILED"+Style.RESET_ALL)
            print(result.stderr)
file.close()
print("All tests completed.")
