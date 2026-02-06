"""
Copyright (c) 2025 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
import ast
from typing import List, Optional

from nagini_translation.lib.program_nodes import PythonModule
from nagini_translation.ghost.ghost_checker import TRANSPARENT_CALLS, NAGINI_DECORATORS
from nagini_translation.lib.util import get_func_name

SPEC_ONLY_DECORATORS = ['Predicate', 'IOOperation']

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

        return ast.Module(new_body, []) #TODO: Handle TypeIgnores?

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
        print(f"Unhandled node of type {type(node)}")
        return node
    
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
        new_posonly: list[ast.arg] = []
        for posonly in args.posonlyargs:
            if not posonly.is_ghost:
                new_posonly.append(posonly)

        new_args: list[ast.arg] = []
        for arg in args.args:
            if not arg.is_ghost:
                new_args.append(arg)

        new_kwonly: list[ast.arg] = []
        for kwonly in args.kwonlyargs:
            if not kwonly.is_ghost:
                new_kwonly.append(kwonly)

        new_args = ast.arguments(new_posonly, new_args, args.vararg, new_kwonly, 
                                 args.kw_defaults, args.kwarg, args.defaults) #TODO: Defaults

        # Extract each stmt
        new_body = self._extract_body(node.body, ast.Pass())

        # Remove Nagini decorators
        new_decorator_list = self._extract_decorators(node.decorator_list)

        # Remove ghosts from return annotation
        if node.returns.is_ghost:
            new_returns = ast.Constant(value=None)
        elif node.returns.contains_ghost:
            new_returns = node.returns.slice.elts[0]
        else:
            new_returns = node.returns
        
        return ast.FunctionDef(node.name, new_args, new_body, new_decorator_list, new_returns)

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
    
    def extract_Expr(self, node: ast.Expr) -> ast.AST:
        new_expr = self.extract(node.value)
        return ast.Expr(new_expr)
    
    def extract_Call(self, node: ast.Call) -> Optional[ast.AST]:
        func_name = get_func_name(node)
        if func_name in TRANSPARENT_CALLS:
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