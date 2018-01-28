"""
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import ast

from abc import ABCMeta
from collections import OrderedDict
from enum import Enum
from nagini_translation.lib import config
from nagini_translation.lib.errors import error_manager
from nagini_translation.lib.jvmaccess import JVM
from typing import Optional


class ViperVerifier(Enum):
    silicon = 'silicon'
    carbon = 'carbon'


class VerificationResult(metaclass=ABCMeta):
    pass


class Success(VerificationResult):
    """
    Encodes a verification success
    """

    def __bool__(self):
        return True

    def to_string(self, ide_mode: bool) -> str:
        return "Verification successful"


class Failure(VerificationResult):
    """
    Encodes a verification failure and provides access to the errors
    """

    def __init__(
            self, errors: 'silver.verifier.AbstractError',
            jvm: Optional[JVM] = None):
        self.errors = error_manager.convert(errors, jvm)

    def __bool__(self):
        return False

    def to_string(self, ide_mode: bool) -> str:
        all_errors = [error.string(ide_mode) for error in self.errors]
        unique_errors = []
        for e in all_errors:
            if e not in unique_errors:
                unique_errors.append(e)
        return "Verification failed\nErrors:\n" + '\n'.join(unique_errors)


class Silicon:
    """
    Provides access to the Silicon verifier
    """

    def __init__(self, jvm: JVM, filename: str):
        self._jvm = jvm
        self.silver = jvm.viper.silver
        self.silicon = jvm.viper.silicon.Silicon()
        args = jvm.scala.collection.mutable.ArraySeq(4)
        args.update(0, '--z3Exe')
        args.update(1, config.z3_path)
        args.update(2, '--disableCatchingExceptions')
        args.update(3, filename)
        self.silicon.parseCommandLine(args)
        self.silicon.start()
        self.ready = True

    def verify(self, prog: 'silver.ast.Program') -> VerificationResult:
        """
        Verifies the given program using Silicon
        """
        if not self.ready:
            self.silicon.restart()
        result = self.silicon.verify(prog)
        self.ready = False
        if isinstance(result, self.silver.verifier.Failure):
            it = result.errors().toIterator()
            errors = []
            while it.hasNext():
                errors += [it.next()]
            return Failure(errors, self._jvm)
        else:
            return Success()

    def __del__(self):
        self.silicon.stop()


class Carbon:
    """
    Provides access to the Carbon verifier
    """

    def __init__(self, jvm: JVM, filename: str):
        self.silver = jvm.viper.silver
        self.carbon = jvm.viper.carbon.CarbonVerifier()
        args = jvm.scala.collection.mutable.ArraySeq(5)
        args.update(0, '--boogieExe')
        args.update(1, config.boogie_path)
        args.update(2, '--z3Exe')
        args.update(3, config.z3_path)
        args.update(4, filename)
        self.carbon.parseCommandLine(args)
        self.carbon.start()
        self.ready = True

    def verify(self, prog: 'silver.ast.Program') -> VerificationResult:
        """
        Verifies the given program using Carbon
        """
        if not self.ready:
            self.carbon.restart()
        result = self.carbon.verify(prog)
        self.ready = False
        if isinstance(result, self.silver.verifier.Failure):
            it = result.errors().toIterator()
            errors = []
            while it.hasNext():
                errors += [it.next()]
            return Failure(errors)
        else:
            return Success()
