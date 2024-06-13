"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import jpype


class JVM:
    """
    Encapsulates access to a JVM
    """

    def __init__(self, classpath: str):
        jpype.startJVM(jpype.getDefaultJVMPath(),
                       '-Djava.class.path=' + classpath, '-Xss32m',
                       convertStrings=True)
        self.java = jpype.JPackage('java')
        self.scala = jpype.JPackage('scala')
        self.viper = jpype.JPackage('viper')
        self.fastparse = jpype.JPackage('fastparse')

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
