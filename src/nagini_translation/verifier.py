"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""


from abc import ABCMeta
from enum import Enum
from nagini_translation.lib import config
from nagini_translation.lib.errors import error_manager
from nagini_translation.lib.jvmaccess import JVM


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

    def to_string(self, ide_mode: bool, show_viper_errors: bool) -> str:
        return "Verification successful"


class Failure(VerificationResult):
    """
    Encodes a verification failure and provides access to the errors
    """

    def __init__(
            self, errors: 'silver.verifier.AbstractError',
            jvm: JVM, modules, sif):
        self.errors = error_manager.convert(errors, jvm, modules, sif)

    def __bool__(self):
        return False

    def to_string(self, ide_mode: bool, show_viper_errors: bool) -> str:
        all_errors = [error.string(ide_mode, show_viper_errors) for error in self.errors]
        unique_errors = []
        for e in all_errors:
            if e not in unique_errors:
                unique_errors.append(e)
        return "Verification failed\nErrors:\n" + '\n'.join(unique_errors)


class ARPPlugin:
    """
    Provides access to the ARPPlugin
    """

    def __init__(self, jvm: JVM):
        self.jvm = jvm
        self.silver = jvm.viper.silver
        if not jvm.is_known_class(jvm.viper.silver.plugin.ARPPlugin):
            raise Exception('ARP plugin not found on classpath.')
        self.arpplugin = jvm.viper.silver.plugin.ARPPlugin()
        self.set_ignored_fields()

    def before_verify(self, prog: 'silver.ast.Program') -> 'silver.ast.Program':
        return self.arpplugin.beforeVerify(prog)

    def map_result(self, result: 'verifier.VerificationResult') -> 'verifier.VerificationResult':
        return self.arpplugin.mapVerificationResult(result)

    def set_ignored_fields(self) -> None:
        fields = self.jvm.scala.collection.mutable.ArraySeq(6)
        fields.update(0, "MustReleaseBounded")
        fields.update(1, "MustReleaseUnbounded")
        fields.update(2, "MustTerminate")
        fields.update(3, "MustInvokeBounded")
        fields.update(4, "MustInvokeUnbounded")
        fields.update(5, "MustInvokeCredit")
        self.arpplugin.setIgnoredFields(fields)


_ARP_PLUGIN = None


def get_arp_plugin(jvm: JVM) -> ARPPlugin:
    global _ARP_PLUGIN
    if not _ARP_PLUGIN:
        _ARP_PLUGIN = ARPPlugin(jvm)
    return _ARP_PLUGIN


class Silicon:
    """
    Provides access to the Silicon verifier
    """

    def __init__(self, jvm: JVM, filename: str, counterexample: bool):
        self.jvm = jvm
        self.silver = jvm.viper.silver
        if not jvm.is_known_class(jvm.viper.silicon.Silicon):
            raise Exception('Silicon backend not found on classpath.')
        self.silicon = jvm.viper.silicon.Silicon()
        nargs = 6 if counterexample else 4
        args = jvm.scala.collection.mutable.ArraySeq(nargs)
        args.update(0, '--z3Exe')
        args.update(1, config.z3_path)
        args.update(2, '--disableCatchingExceptions')
        if counterexample:
            args.update(3, '--counterexample')
            args.update(4, 'native')
        args.update(5 if counterexample else 3, filename)
        self.silicon.parseCommandLine(args)
        self.silicon.start()
        self.ready = True

    def verify(self, modules, prog: 'silver.ast.Program', arp=False, sif=False) -> VerificationResult:
        """
        Verifies the given program using Silicon
        """
        if not self.ready:
            self.silicon.restart()
        result = self.silicon.verify(prog)
        if arp:
            result = get_arp_plugin(self.jvm).map_result(result)
        self.ready = False
        if isinstance(result, self.silver.verifier.Failure):
            it = result.errors().toIterator()
            errors = []
            while it.hasNext():
                errors += [it.next()]
            return Failure(errors, self.jvm, modules, sif)
        else:
            return Success()

    def __del__(self):
        if hasattr(self, 'silicon') and self.silicon:
            self.silicon.stop()


class Carbon:
    """
    Provides access to the Carbon verifier
    """

    def __init__(self, jvm: JVM, filename: str):
        self.silver = jvm.viper.silver
        if not jvm.is_known_class(jvm.viper.carbon.CarbonVerifier):
            raise Exception('Carbon backend not found on classpath.')
        if config.boogie_path is None:
            raise Exception('Boogie not found.')
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
        self.jvm = jvm

    def verify(self, modules, prog: 'silver.ast.Program', arp=False, sif=False) -> VerificationResult:
        """
        Verifies the given program using Carbon
        """
        if not self.ready:
            self.carbon.restart()
        result = self.carbon.verify(prog)
        if arp:
            result = get_arp_plugin(self.jvm).map_result(result)
        self.ready = False
        if isinstance(result, self.silver.verifier.Failure):
            it = result.errors().toIterator()
            errors = []
            while it.hasNext():
                errors += [it.next()]
            return Failure(errors, self.jvm, modules, sif)
        else:
            return Success()
