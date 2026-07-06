"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import jpype
import logging


def configure_java_logging() -> None:
    """Raise the JVM's logback root level so the Viper backends don't flood output.

    ``viperserver.jar`` ships no ``logback.xml`` (unlike the old standalone
    ``silicon.jar``/``carbon.jar``), so logback would otherwise fall back to its
    default configuration, which logs at DEBUG to the console. That floods
    stdout/stderr with internal Silicon/ViperServer traces and can corrupt the
    JSON-RPC stream of an LSP/MCP frontend. We raise the root level to WARN
    programmatically instead. Nagini's own output uses Python logging and is
    unaffected. Safe to call repeatedly, and a no-op if logback is not present.
    """
    try:
        logger_factory = jpype.JClass('org.slf4j.LoggerFactory')
        level = jpype.JClass('ch.qos.logback.classic.Level')
        logback_logger = jpype.JClass('ch.qos.logback.classic.Logger')
        root = jpype.JObject(logger_factory.getLogger('ROOT'), logback_logger)
        root.setLevel(level.WARN)
    except Exception:
        logging.debug('Could not adjust JVM (logback) log level.', exc_info=True)


class JVM:
    """
    Encapsulates access to a JVM
    """

    def __init__(self, classpath: str):
        # Only one JVM can exist per process; reuse it if one is already running
        # (e.g. started by another component or the test harness).
        if not jpype.isJVMStarted():
            jpype.startJVM(jpype.getDefaultJVMPath(),
                           '-Djava.class.path=' + classpath, '-Xss32m',
                           convertStrings=True)
        # Suppress the default DEBUG-level logback console output that
        # viperserver.jar would otherwise produce (no bundled logback.xml).
        configure_java_logging()
        self.java = jpype.JPackage('java')
        self.scala = jpype.JPackage('scala')
        self.viper = jpype.JPackage('viper')
        self.fastparse = jpype.JPackage('fastparse')
        # The JVM (logback, and ViperServer's hard-coded println of the journal
        # path / "shutting down..." messages) writes to System.out. That noise
        # would pollute Nagini's own stdout — which carries the verification
        # result on the CLI and the JSON-RPC stream of a stdio LSP/MCP frontend,
        # and is parsed by the test framework. Route all JVM System.out to
        # System.err; Nagini's own output uses Python stdout and is unaffected.
        try:
            self.java.lang.System.setOut(self.java.lang.System.err)
        except Exception:
            logging.exception('Could not redirect JVM stdout.')

    def get_proxy(self, supertype, instance):
        return jpype.JProxy(supertype, inst=instance)

    def get_array(self, t, n):
        return jpype.JArray(t)(n)

    def is_known_class(self, package_object, class_name) -> bool:
        return hasattr(package_object, class_name)


def getobject(java, package, name):
    return java.lang.Class.forName(str(package) + "." + name + "$").getDeclaredField('MODULE$').get(None)

def getclass(java, package, name):
    return jpype.JClass(java.lang.Class.forName(str(package) + "." + name))
