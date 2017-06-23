nagini_contracts
===============



### [contracts.py](./contracts.py)


This is where we define the functions needed to give a semantic to a contract : we need both wrappers and functions. Since those and the expressions they contain should not be evaluated, we'll remove them from the AST.


### [obligations.py](./obligations.py)


There are encoded some important obligations as contracts, needed to encode a proper lock.


### [lock.py](./lock.py)


An actual lock encoding as contracts.



### [io.py](./io.py)


<!--- TODO, I don't understand what that's for. -->


### [io_builtins.py](./io_builtins.py)


<!---TODO, same as io.py -->


### [transformer.py](./transformer.py)


Contains transform_ast : a method to cleanse the AST of all statements related to ghost variables and functions.
To do so, we use three [NodeVisitors](https://docs.python.org/2/library/ast.html#ast.NodeVisitor) and a [NodeTransformers](https://docs.python.org/2/library/ast.html#ast.NodeTransformer) which respectively :
- Collects the names of every ghost variable and every ghost function
- Collects all statements involving those ghost variables and functions.
- Collects all empty bodied methods.
- Given a list of statements, modify the AST to remove all the statements in that list.

transform_ast(tree)  collects all the statements involving ghost variables and functions, and removes them from the tree. 
Then it also removes all code blocks who were emptied by that process.


### [importer.py](./importer.py)

This contains a hook (which can be installed through install_hook) which modifies how modules should be imported. Indeed, to verify a program, it must be annotated but so do all the functions from all the modules it uses. Those must then be modified in consequences.
