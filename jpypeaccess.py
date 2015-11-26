import jpype

class Jpype:
    def __init__(self, classpath):
        jpype.startJVM(jpype.getDefaultJVMPath(), '-Djava.class.path=' + classpath)
        self.java = jpype.JPackage('java')
        self.scala = jpype.JPackage('scala')
        self.viper = jpype.JPackage('viper')