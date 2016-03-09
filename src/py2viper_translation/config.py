"""
A singleton configuration object.
"""

import os
import sys
import glob


def _construct_classpath():
    """ Contstructs JAVA classpath.

    First tries environment variables ``VIPERJAVAPATH``, ``SILICONJAR``
    and ``CARBONJAR``. If they are undefined, then tries to use OS
    specific locations.
    """

    viper_java_path = os.environ.get('VIPERJAVAPATH')
    silicon_jar = os.environ.get('SILICONJAR')
    carbon_jar = os.environ.get('CARBONJAR')

    if viper_java_path:
        return viper_java_path

    if silicon_jar or carbon_jar:
        return os.pathsep.join(
            jar for jar in (silicon_jar, carbon_jar) if jar)

    if sys.platform.startswith('linux'):
        if os.path.isdir('/usr/lib/viper'):
            # Check if we have Viper installed via package manager.
            return os.pathsep.join(
                glob.glob('/usr/lib/viper/*.jar'))

    return None


def _get_boogie_path():
    """ Tries to detect path to Boogie executable.

    First tries the environment variable ``BOOGIE_EXE``. If it is not
    defined, then checks the OS specific directory. On Ubuntu returns a
    path only if it also finds a mono installation.
    """

    boogie_exe = os.environ.get('BOOGIE_EXE')
    if boogie_exe:
        return boogie_exe

    if sys.platform.startswith('linux'):
        if (os.path.exists('/usr/bin/boogie') and
            os.path.exists('/usr/bin/mono')):
            return '/usr/bin/boogie'


def _get_z3_path():
    """ Tries to detect path to Z3 executable.

    First tries the environment variable ``Z3_EXE``. If it is not
    defined, then checks the OS specific directories.
    """

    z3_exe = os.environ.get('Z3_EXE')
    if z3_exe:
        return z3_exe

    if sys.platform.startswith('linux'):
        if os.path.exists('/usr/bin/viper-z3'):
            # First check if we have Z3 installed together with Viper.
            return '/usr/bin/viper-z3'
        if os.path.exists('/usr/bin/z3'):
            return '/usr/bin/z3'


def _get_mypy_path():
    """ Construct MYPYPATH.

    If MYPYPATH environment variable is not defined, then sets it to
    ``py2viper-contracts`` directory.
    """

    mypy_path = os.environ.get('MYPYPATH')
    if not mypy_path:
        import py2viper_contracts
        mypy_path = os.path.dirname(os.path.dirname(
            py2viper_contracts.__file__))
    return mypy_path


classpath = _construct_classpath()
boogie_path = _get_boogie_path()
z3_path = _get_z3_path()
mypy_path = _get_mypy_path()


__all__ = [classpath, boogie_path, z3_path, mypy_path]
