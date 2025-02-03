"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import ast
import imp
import os
import sys
import types

from astor import to_source
from nagini_contracts.transformer import transform_ast

class ContractsImporter(object):
    """
    Import hook for use on `sys.meta_path`.
    """

    def __init__(self):
        self._cache = {}

    def find_module(self, name, path=None):
        try:
            lastname = name.split('.')[-1]
            # print("find_module", name, path)
            self._cache[name] = imp.find_module(lastname, path), path
        except ImportError:
            return None
        return self

    def load_module(self, name):
        # print("load_module", name)
        try:
            (fd, fn, info), path = self._cache[name]
        except KeyError:
            # can that happen?
            raise ImportError(name)
        if info[2] == imp.PY_SOURCE:
            newpath = None
            filename = fn
            with fd:
                code = fd.read()
        elif info[2] == imp.PY_COMPILED:
            newpath = None
            filename = fn[:-1]
            with open(filename, 'U') as f:
                code = f.read()
        elif info[2] == imp.PKG_DIRECTORY:
            filename = os.path.join(fn, '__init__.py')
            newpath = [fn]
            with open(filename, 'U') as f:
                code = f.read()
        else:
            return imp.load_module(name, fd, fn, info)
        try:
            module = types.ModuleType(name)
            module.__file__ = filename
            if newpath:
                module.__path__ = newpath
            tree = ast.parse(code)
            # print("Before Transformation:\n%s" % to_source(tree))
            transformed_ast = transform_ast(tree)
            # print("After Transformation:\n%s" % to_source(transformed_ast))
            code = compile(transformed_ast, filename, 'exec')
            sys.modules[name] = module
            exec(code, module.__dict__)
            return module
        except Exception:
            raise ImportError('cannot import %s' % (name))


def install_hook():
    print("Installing import hook.")
    sys.meta_path.insert(0, ContractsImporter())


def remove_hook():
    print("Removing import hook.")
    sys.meta_path[:] = [importer for importer in sys.meta_path if
                        not isinstance(importer, ContractsImporter)]
