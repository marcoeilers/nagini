"""
Copyright (c) 2025 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
import ast
import copy
import importlib
from typing import List, Optional, Set, Union

from nagini_translation.lib.program_nodes import PythonModule
from nagini_translation.ghost.ghost_checker import (
    NAGINI_IMPORT, SPEC_ONLY_DECORATORS, TRANSPARENT_CALLS, NAGINI_DECORATORS
)
from nagini_translation.lib.util import get_func_name

class ProgramExtractor:
    """
    Walks through the Python AST and removes all ghost elements.
    """
    
    def __init__(self, modules: List[PythonModule]) -> None:
        self.modules = modules
    
    def process(self) -> ast.AST:
        """
        Run extraction and return the AST with ghost elements removed.
        """
        main_module = self.modules[1]
        return self.extract_Module(main_module.node)
    
    def extract_Module(self, node: ast.Module) -> ast.AST:
        new_body = self._extract_body(node.body)
        new_body = self._restore_needed_imports(node.body, new_body)

        return ast.Module(new_body, []) #TODO: Handle TypeIgnores?

    def _restore_needed_imports(self, body: List[ast.stmt],
                                new_body: List[ast.stmt]) -> List[ast.stmt]:
        """
        Re-adds the removed imports of Nagini's contract library if the extracted
        program still refers to names defined by it. That is the case for
        specification only constructs which cannot be translated to plain Python,
        e.g. the body of a pure function which quantifies over a collection.
        """
        referenced = {node.id for node in ast.walk(ast.Module(new_body, []))
                      if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)}
        needed = [stmt for stmt in body
                  if isinstance(stmt, (ast.Import, ast.ImportFrom))
                  and stmt not in new_body and self._is_nagini_import(stmt)
                  and self._provided_names(stmt) & referenced]
        return needed + new_body

    def _is_nagini_import(self, node: Union[ast.Import, ast.ImportFrom]) -> bool:
        if isinstance(node, ast.ImportFrom):
            return node.module is not None and NAGINI_IMPORT in node.module.split('.')
        return any(NAGINI_IMPORT in alias.name.split('.') for alias in node.names)

    def _provided_names(self, node: Union[ast.Import, ast.ImportFrom]) -> Set[str]:
        """
        Returns the names which the given import statement makes available.
        """
        if isinstance(node, ast.Import):
            return {alias.asname or alias.name.split('.')[0] for alias in node.names}
        names = set()
        for alias in node.names:
            if alias.name != '*':
                names.add(alias.asname or alias.name)
                continue
            try:
                module = importlib.import_module(node.module)
            except ImportError:
                # We do not know what the import provides, so we keep it.
                return {'*'}
            exported = getattr(module, '__all__', None)
            if exported is None:
                exported = [name for name in dir(module) if not name.startswith('_')]
            names.update(exported)
        return names

    def extract(self, node: ast.AST) -> Optional[ast.AST]:
        """
        Generic visitor function for extracting statements
        """
        # Ghost statements we can remove wholesale. 
        # Similarly, purely regular statements we can replicate wholesale.
        # Only regular statements with ghost elements must be further analyzed.
        if node.is_ghost:
            return None
        elif not node.contains_ghost:
            return node
        else:
            method = 'extract_' + node.__class__.__name__
            visitor = getattr(self, method, self.generic_extract)
            return visitor(node)
    
    def generic_extract(self, node: ast.AST) -> ast.AST:
        """
        Extracts a node for which we have no dedicated visitor by extracting all
        of its children. Since the node itself is regular, none of its children
        can be ghost; they may only contain ghost elements.
        """
        new_node = copy.copy(node)
        for field, value in ast.iter_fields(node):
            if isinstance(value, list):
                new_list = []
                for item in value:
                    if self._is_extractable(item):
                        new_item = self.extract(item)
                        if new_item is not None:
                            new_list.append(new_item)
                    else:
                        new_list.append(item)
                setattr(new_node, field, new_list)
            elif self._is_extractable(value):
                new_value = self.extract(value)
                if new_value is not None:
                    setattr(new_node, field, new_value)
        return new_node

    def _is_extractable(self, node: object) -> bool:
        """
        Returns whether the given node carries ghost information. Nodes like
        operators or expression contexts do not and are copied unchanged.
        """
        return isinstance(node, ast.AST) and hasattr(node, 'is_ghost')
    
    def extract_ClassDef(self, node: ast.ClassDef) -> ast.AST:
        new_body = self._extract_body(node.body, ast.Pass())
        new_decorator_list = self._extract_decorators(node.decorator_list)
        return ast.ClassDef(node.name, node.bases, node.keywords, new_body, new_decorator_list)

    def extract_FunctionDef(self, node: ast.FunctionDef) -> Optional[ast.AST]:
        # Remove Specification only Functions
        decorators = {d.id for d in node.decorator_list if isinstance(d, ast.Name)}
        if any([dec in SPEC_ONLY_DECORATORS for dec in decorators]):
            return None
        
        # Remove ghost args
        args = node.args
        new_posonly = self._extract_args_or_defaults(args.posonlyargs)
        new_args = self._extract_args_or_defaults(args.args)
        new_kwonly = self._extract_args_or_defaults(args.kwonlyargs)
        new_kw_defaults = self._extract_args_or_defaults(args.kw_defaults)
        new_defaults = self._extract_args_or_defaults(args.defaults)

        new_arguments = ast.arguments(new_posonly, new_args, args.vararg, new_kwonly, 
                                 new_kw_defaults, args.kwarg, new_defaults)

        # Extract each stmt
        new_body = self._extract_body(node.body, ast.Pass())

        # Remove Nagini decorators
        new_decorator_list = self._extract_decorators(node.decorator_list)

        # Remove ghosts from return annotation
        if node.returns is None or not node.returns.contains_ghost:
            new_returns = node.returns
        elif node.returns.is_ghost:
            new_returns = ast.Constant(value=None)
        else:
            # A return type of the form Tuple[<regular type>, <ghost type>]:
            # only the regular part remains.
            new_returns = node.returns.slice.elts[0]


        return ast.FunctionDef(node.name, new_arguments, new_body, new_decorator_list, new_returns)

    def extract_Assign(self, node: ast.Assign) -> ast.AST:
        new_targets: List[ast.expr] = []
        for target in node.targets:
            if isinstance(target, ast.Tuple):
                new_elts: List[ast.expr] = []
                for sub_target in target.elts:
                    new_sub_target = self.extract(sub_target)
                    if new_sub_target is not None:
                        new_elts.append(new_sub_target)

                if len(new_elts) == 0:
                    new_target = None
                elif len(new_elts) == 1:
                    new_target = new_elts[0]
                else:
                    new_target = ast.Tuple(new_elts, target.ctx)
            else:
                new_target = self.extract(target)

            if new_target is not None:
                new_targets.append(new_target)

        new_value = self.extract(node.value)
        assert new_value is not None, "Value was ghost when statement is regular"

        if len(new_targets) == 0:
            # Since targets are all ghost but stmt is regular, value must be an impure call
            return ast.Expr(new_value)
        else:
            return ast.Assign(new_targets, new_value)

    def extract_AnnAssign(self, node: ast.AnnAssign) -> ast.AST:
        new_target = self.extract(node.target)
        new_value = self.extract(node.value)
        assert new_value is not None, "Value was ghost when statement is regular"

        if new_target is None:
            # Since target is ghost but stmt is regular, value must be an impure call
            return ast.Expr(new_value)
        else:
            return ast.AnnAssign(new_target,node.annotation, new_value, node.simple)

    def extract_Return(self, node: ast.Return) -> ast.AST:
        if isinstance(node.value, ast.Tuple) and len(node.value.elts) == 2:
            new_rets: List[ast.expr] = []
            for ret in node.value.elts:
                new_ret = self.extract(ret)
                if new_ret is not None:
                    new_rets.append(new_ret)
            
            if len(new_rets) == 2:
                new_value = ast.Tuple(new_rets, node.value.ctx)
            elif len(new_rets) == 1:
                new_value = new_rets[0]
            else: 
                # len(new_rets) == 0
                new_value = None
        else:
            new_value = self.extract(node.value)

        return ast.Return(new_value)

    def extract_If(self, node: ast.If) -> ast.AST:
        new_test = self.extract(node.test)
        new_body = self._extract_body(node.body, ast.Pass())
        new_orelse = self._extract_body(node.orelse)
        return ast.If(new_test, new_body, new_orelse)

    def extract_While(self, node: ast.While) -> ast.AST:
        new_test = self.extract(node.test)
        new_body = self._extract_body(node.body, ast.Pass())
        new_orelse = self._extract_body(node.orelse)
        return ast.While(new_test, new_body, new_orelse)

    def extract_For(self, node: ast.For) -> ast.AST:
        new_iter = self.extract(node.iter)
        new_body = self._extract_body(node.body, ast.Pass())
        new_orelse = self._extract_body(node.orelse)
        return ast.For(node.target, new_iter, new_body, new_orelse)

    def extract_With(self, node: ast.With) -> ast.AST:
        new_body = self._extract_body(node.body, ast.Pass())
        return ast.With(node.items, new_body)

    def extract_Try(self, node: ast.Try) -> ast.AST:
        new_body = self._extract_body(node.body, ast.Pass())
        new_handlers = [
            ast.ExceptHandler(handler.type, handler.name,
                              self._extract_body(handler.body, ast.Pass()))
            for handler in node.handlers
        ]
        new_orelse = self._extract_body(node.orelse)
        new_finalbody = self._extract_body(node.finalbody)
        return ast.Try(new_body, new_handlers, new_orelse, new_finalbody)

    def extract_AugAssign(self, node: ast.AugAssign) -> ast.AST:
        new_value = self.extract(node.value)
        assert new_value is not None, "Value was ghost when statement is regular"
        return ast.AugAssign(node.target, node.op, new_value)


    def extract_Expr(self, node: ast.Expr) -> ast.AST:
        new_expr = self.extract(node.value)
        return ast.Expr(new_expr)
    
    def extract_Call(self, node: ast.Call) -> Optional[ast.AST]:
        func_name = get_func_name(node)
        if func_name in TRANSPARENT_CALLS and len(node.args) > TRANSPARENT_CALLS[func_name]:
            idx = TRANSPARENT_CALLS[func_name]
            return self.extract(node.args[idx])
        
        # Remove ghost args
        new_args: list[ast.expr] = []
        for arg in node.args:
            new_arg = self.extract(arg)
            if new_arg is not None:
                new_args.append(new_arg)

        new_keywords: list[ast.expr] = []
        for kw in node.keywords:
            new_kw_val = self.extract(kw.value)
            if new_kw_val is not None:
                new_kw = ast.keyword(kw.arg, new_kw_val)
                new_keywords.append(new_kw)

        return ast.Call(node.func, new_args, new_keywords)
    
    def _extract_body(self, body: List[ast.stmt], if_empty: Optional[ast.AST] = None) -> List[ast.stmt]:
        new_body: List[ast.stmt] = []
        for stmt in body:
            new_stmt = self.extract(stmt)
            if new_stmt is not None:
                new_body.append(new_stmt)
        
        if len(new_body) == 0 and if_empty is not None:
            new_body.append(if_empty)
        
        return new_body
    
    def _extract_decorators(self, decorator_list: List[ast.expr]) -> List[ast.expr]:
        return [d for d in decorator_list if not (isinstance(d, ast.Name) and d.id in NAGINI_DECORATORS)]
    
    def _extract_args_or_defaults(self, args: List[Optional[Union[ast.arg, ast.expr]]]
                                  ) -> List[Optional[Union[ast.arg, ast.expr]]]:
        new_args: list[ast.arg | ast.expr | None] = []
        for arg in args:
            # Keyword defaults are None if the keyword argument has no default.
            if arg is None or not arg.is_ghost:
                new_args.append(arg)
        return new_args