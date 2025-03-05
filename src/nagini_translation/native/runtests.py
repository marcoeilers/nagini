import os
import subprocess
import ast
import difflib
from colorama import Fore, Style

hline=("\n"+50*"="+"\n")
# iterate over files contained in ./tests directory and starting with test_
for filename in os.listdir('nagini_translation/native/tests'):
    if filename.startswith("test_"):
        print("Running test for file: " + filename + (30 - len(filename)) * " ", end="")
        filepath = 'nagini_translation/native/tests/' + filename
        result = subprocess.run('python3 nagini_translation/main.py --skip-verification ' +
                                filepath, cwd="./", shell=True, capture_output=True, text=True)
        with open(filepath, "r", encoding="utf-8") as file:
            tree = ast.parse(file.read(), filename=filepath)
        functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        function_sols = ["" if ast.get_docstring(f)==None else ast.get_docstring(f) for f in functions]
        solution = "\n".join(function_sols)
        print(""+((Fore.GREEN+"PASSED") if result.stdout == solution else (Fore.RED+"FAILED"))+Style.RESET_ALL)
        #print(hline+result.stdout+"\n"+hline+solution+hline)
        if(result.stdout != solution):
            differences=difflib.ndiff(result.stdout.splitlines(), solution.splitlines())
            print("\n".join(differences))
file.close()
print("All tests completed.")
