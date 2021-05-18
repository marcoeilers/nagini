"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

"""
A singleton configuration object.

>>> from nagini_translation.lib import config
>>> config.classpath is None
False
>>> config.z3_path is None
False
>>> config.mypy_path is None
False

"""


import configparser
import glob
import os
import sys

import nagini_translation.resources


class SectionConfig:
    """A base class for configuration sections."""

    def __init__(self, config, section_name) -> None:
        self.config = config
        if section_name not in self.config:
            self.config[section_name] = {}
        self._info = self.config[section_name]


class ObligationConfig(SectionConfig):
    """Obligation translation configuration."""

    def __init__(self, config) -> None:
        super().__init__(config, 'Obligations')

    @property
    def disable_all(self):
        """Disable all obligation related checks."""
        return self._info.getboolean('disable_all', False)

    @disable_all.setter
    def disable_all(self, val):
        """Disable all obligation related checks."""
        self._info['disable_all'] = str(val)

    @property
    def disable_measure_check(self):
        """Replace obligation measure checks with ``True``."""
        return self._info.getboolean(
            'disable_measure_check', self.disable_all)

    @property
    def disable_measures(self):
        """Completely disable obligation measures."""
        return self._info.getboolean(
            'disable_measures', self.disable_all)

    @property
    def disable_method_body_leak_check(self):
        """Disable leak check at the end of method body."""
        return self._info.getboolean(
            'disable_method_body_leak_check', self.disable_all)

    @property
    def disable_loop_body_leak_check(self):
        """Disable leak check at the end of loop body."""
        return self._info.getboolean(
            'disable_loop_body_leak_check', self.disable_all)

    @property
    def disable_call_context_leak_check(self):
        """Disable leak check at the caller side."""
        return self._info.getboolean(
            'disable_call_context_leak_check', self.disable_all)

    @property
    def disable_loop_context_leak_check(self):
        """Disable leak check at the loop surrounding context."""
        return self._info.getboolean(
            'disable_loop_context_leak_check', self.disable_all)

    @property
    def disable_termination_check(self):
        """Disable all termination checks.

        Also replaces all ``MustTerminate`` with ``True``.
        """
        return self._info.getboolean(
            'disable_termination_check', self.disable_all)

    @property
    def disable_must_invoke(self):
        """Replace all ``token`` with ``ctoken``."""
        return self._info.getboolean(
            'disable_must_invoke', self.disable_all)

    @property
    def disable_waitlevel_check(self):
        """Disable all waitlevel checks."""
        return self._info.getboolean(
            'disable_waitlevel_check', self.disable_all)


class TestConfig(SectionConfig):
    """Testing configuration."""

    def __init__(self, config) -> None:
        super().__init__(config, 'Tests')

        ignore_tests_value = self._info.get('ignore_tests')
        if not ignore_tests_value:
            self.ignore_tests = set([])
        else:
            patterns = ignore_tests_value.strip().splitlines()
            self.ignore_tests = set([i for pattern in patterns for i in glob.glob(pattern)])

        verifiers_value = self._info.get('verifiers')
        if not verifiers_value:
            self.verifiers = []
        else:
            self.verifiers = verifiers_value.strip().split()

        tests_value = self._info.get('tests')
        if not tests_value:
            self.tests = []
        else:
            self.tests = tests_value.strip().split()


class FileConfig:
    """Configuration stored in the config file."""

    def __init__(self, config_file) -> None:
        self.config = configparser.ConfigParser()
        self.config.read(config_file)
        self.obligation_config = ObligationConfig(self.config)
        self.test_config = TestConfig(self.config)


def resources_folder():
    resources = os.path.dirname(nagini_translation.resources.__file__)
    return resources


def _construct_classpath(verifier : str = None):
    """ Contstructs JAVA classpath.

    First tries environment variables ``VIPERJAVAPATH``, ``SILICONJAR``
    and ``CARBONJAR``. If they are undefined, then tries to use OS
    specific locations.
    """

    viper_java_path = os.environ.get('VIPERJAVAPATH')
    silicon_jar = os.environ.get('SILICONJAR')
    carbon_jar = os.environ.get('CARBONJAR')
    arpplugin_jar = os.environ.get('ARPPLUGINJAR')

    if viper_java_path:
        return viper_java_path

    if silicon_jar or carbon_jar:
        return os.pathsep.join(
            jar for jar, v in ((silicon_jar, 'carbon'),
                               (carbon_jar, 'silicon'),
                               (arpplugin_jar, 'arpplugin'))
            if jar and v != verifier)

    resources = resources_folder()
    silicon = os.path.join(resources, 'backends', 'silicon.jar')
    carbon = os.path.join(resources, 'backends', 'carbon.jar')
    silver_sif = os.path.join(resources, 'backends', 'silver-sif-extension.jar')
    silicon_sif = os.path.join(resources, 'backends', 'silicon-sif-extension.jar')
    return os.pathsep.join(
        jar for jar, v in ((silicon, 'carbon'),
                           (carbon, 'silicon'),
                           (silver_sif, 'silver-sif'),
                           (silicon_sif, 'silicon-sif'))
        if jar and v != verifier)


def _get_boogie_path():
    """ Tries to detect path to Boogie executable.

    First tries the environment variable ``BOOGIE_EXE``. If it is not
    defined, then checks the OS specific directory. On Ubuntu returns a
    path only if it also finds a mono installation.
    """

    boogie_exe = os.environ.get('BOOGIE_EXE')
    if boogie_exe:
        return boogie_exe


def _get_z3_path():
    """ Tries to detect path to Z3 executable.

    First tries the environment variable ``Z3_EXE``. If it is not
    defined, then checks the OS specific directories.
    """

    z3_exe = os.environ.get('Z3_EXE')
    if z3_exe:
        return z3_exe

    script_path = os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), 'z3')
    if os.path.exists(script_path):
        return script_path

    path = os.path.join(os.path.dirname(sys.executable),
                        'z3.exe' if sys.platform.startswith('win') else 'z3')
    if os.path.exists(path):
        return path



def _get_mypy_path():
    """ Construct MYPYPATH.

    If MYPYPATH environment variable is not defined, then sets it to
    ``nagini-contracts`` directory.
    """

    mypy_path = os.environ.get('MYPYPATH')
    return mypy_path


def _get_mypy_dir():
    """ Construct MYPYDIR.

    If MYPYDIR environment variable is not defined, just returns None.
    """

    mypy_dir = os.environ.get('MYPYDIR')
    if mypy_dir:
        return os.path.dirname(mypy_dir)
    return None


def set_verifier(v: str):
    global classpath
    not_set_by_arg = classpath == _construct_classpath()
    if not_set_by_arg:
        classpath = _construct_classpath(v)


mypy_dir = _get_mypy_dir()
"""
Mypy executable dir. Initialized by calling
:py:func:`_get_mypy_dir`.
"""


classpath = _construct_classpath()
"""
JAVA class path. Initialized by calling
:py:func:`_construct_classpath`.
"""


boogie_path = _get_boogie_path()
"""
Path to Boogie executable. Initialized by calling
:py:func:`_get_boogie_path`.
"""


z3_path = _get_z3_path()
"""
Path to Z3 executable. Initialized by calling :py:func:`_get_z3_path`.
"""


mypy_path = _get_mypy_path()
"""
MYPY search path. Initialized by calling :py:func:`_get_mypy_path`.
"""


file_config = FileConfig('nagini.cfg')
"""
Configuration read from ``nagini.cfg`` file.
"""


obligation_config = file_config.obligation_config
"""
Obligation configuration.
"""


test_config = file_config.test_config
"""
Test configuration.
"""


__all__ = (
    'classpath',
    'boogie_path',
    'z3_path',
    'mypy_path',
    'mypy_dir',
    'obligation_config',
    'set_verifier',
)
