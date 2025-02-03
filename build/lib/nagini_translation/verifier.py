"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""


from abc import ABCMeta
from enum import Enum
from typing import List
from nagini_translation.lib import config
from nagini_translation.lib.errors import error_manager
from nagini_translation.lib.jvmaccess import (
    getobject,
    JVM
)
from nagini_translation.lib.util import list_to_seq


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
        if not jvm.is_known_class(jvm.viper.silver.plugin, 'ARPPlugin'):
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

    def __init__(self, jvm: JVM, filename: str, viper_args: List[str], counterexample: bool):
        self.jvm = jvm
        self.silver = jvm.viper.silver
        if not jvm.is_known_class(jvm.viper.silicon, 'Silicon'):
            raise Exception('Silicon backend not found on classpath.')
        reporter = getobject(jvm.java, jvm.viper.silver.reporter, 'NoopReporter')
        self.silicon = jvm.viper.silicon.MinimalSiliconFrontendAPI(reporter)
        args = [
            '--assumeInjectivityOnInhale',
            '--z3Exe', config.z3_path,
            '--disableCatchingExceptions',
            '--exhaleMode=2',
            '--alternativeFunctionVerificationOrder',
            '--disableDefaultPlugins',
            '--plugin=viper.silver.plugin.standard.refute.RefutePlugin:'
            'viper.silver.plugin.standard.termination.TerminationPlugin:'
            'viper.silver.plugin.standard.predicateinstance.PredicateInstancePlugin',
            *(['--counterexample=native', '--proverArgs=model.partial=true'] if counterexample else []),
            *viper_args,
        ]
        args_seq = list_to_seq(args, jvm, jvm.java.lang.String)
        self.silicon.initialize(args_seq)

    def verify(self, modules, prog: 'silver.ast.Program', arp=False, sif=False) -> VerificationResult:
        """
        Verifies the given program using Silicon
        """
        result = self.silicon.verify(prog)
        if arp:
            result = get_arp_plugin(self.jvm).map_result(result)
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

    def __init__(self, jvm: JVM, filename: str, viper_args: List[str]):
        self.silver = jvm.viper.silver
        if not jvm.is_known_class(jvm.viper.carbon, 'CarbonVerifier'):
            raise Exception('Carbon backend not found on classpath.')
        if config.boogie_path is None:
            raise Exception('Boogie not found.')
        reporter = getobject(jvm.java, jvm.viper.silver.reporter, 'NoopReporter')
        self.carbon = jvm.viper.carbon.MinimalCarbonFrontendAPI(reporter)
        args = [
            '--assumeInjectivityOnInhale',
            '--boogieExe', config.boogie_path,
            '--z3Exe', config.z3_path,
            '--disableDefaultPlugins',
            '--plugin=viper.silver.plugin.standard.refute.RefutePlugin:'
            'viper.silver.plugin.standard.termination.TerminationPlugin:'
            'viper.silver.plugin.standard.predicateinstance.PredicateInstancePlugin',
            *viper_args
        ]
        args_seq = list_to_seq(args, jvm, jvm.java.lang.String)
        self.carbon.initialize(args_seq)
        self.jvm = jvm

    def verify(self, modules, prog: 'silver.ast.Program', arp=False, sif=False) -> VerificationResult:
        """
        Verifies the given program using Carbon
        """
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