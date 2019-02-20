
Nagini is an automatic verifier for statically typed Python programs, based on the `Viper <http://viper.ethz.ch>`_ verification infrastructure. Nagini is being developed at the `Chair of Programming Methodology <http://www.pm.inf.ethz.ch/>`_ at ETH Zurich as part of the `VerifiedSCION <http://www.pm.inf.ethz.ch/research/verifiedscion.html>`_ project.

Our CAV 2018 tool paper describing Nagini can be found `here <http://pm.inf.ethz.ch/publications/getpdf.php?bibname=Own&id=EilersMueller18.pdf>`_. See `the Wiki <https://github.com/marcoeilers/nagini/wiki>`_ for the documentation of Nagini's specification language. 

You can try a (rather slow) online version of Nagini `on this website <http://viper.ethz.ch/nagini-examples>`_.

For use with the PyCharm IDE, try the `Nagini PyCharm plugin <https://github.com/marcoeilers/nagini-pycharm>`_.

Dependencies (Ubuntu Linux)
===================================

1.  Install Java 8 (64 bit), Mercurial, Git and Python 3.6 (64 bit, newer versions should work but are currently untested) and the required libraries::

        sudo apt-get install python3-dev libzmq3-dev

    For usage with the Viper's verification condition generation backend Carbon, you will also need to install the Mono runtime.

2.  Download and extract `ViperToolsLinux <http://viper.ethz.ch/downloads/ViperToolsLinux.zip>`_

Dependencies (Windows)
==========================

1.  Install Java (64 bit), Mercurial, Git and Python 3.5 (64 bit), s.t. java, hg, git and python are all available from the command line.

2.  Install either Visual C++ Build Tools 2015 (http://go.microsoft.com/fwlink/?LinkId=691126) or Visual Studio 2015. For the latter, make sure to choose the option "Common Tools for Visual C++ 2015" in the setup (see https://blogs.msdn.microsoft.com/vcblog/2015/07/24/setup-changes-in-visual-studio-2015-affecting-c-developers/ for an explanation).

3.  Download and extract `ViperToolsWin <http://viper.ethz.ch/downloads/ViperToolsWin.zip>`_

Getting Started
===============

1.  Create a virtual environment::

        virtualenv --python=python3 <env>
        
2.  Install Nagini::

    ./<env>/bin/pip install nagini


Command Line Usage
==================

To verify a specific file from the nagini directory, run::

    ./<env>/bin/nagini [OPTIONS] path-to-file.py


The options ``--z3`` and ``--viper-jar-path`` are mandatory and must point to a Z3 executable and a JAR file containing the desired Viper backend. E.g., to use the Symbolic Execution backend (Silicon) from the provided Viper Tools file, call ::

    ./<env>/bin/nagini --z3 <viperTools>/z3/bin/z3 --viper-jar-path <viperTools>/backends/silicon.jar path-to-file.py

The following command line options are available::

    ``--verifier``      
                    Selects the Viper backend to use for verification.
                    Possible options are ``silicon`` (for Symbolic Execution) and ``carbon`` 
                    (for Verification Condition Generation based on Boogie).  
                    Default: ``silicon``.

    ``--select``        
                    Select which functions/methods/classes to verify. Expects a comma-
                    separated list of names.

    ``--z3``            
                    Sets the path of the Z3 executable. Always required. Alternatively, the
                    ``Z3_EXE`` environment variable can be set.
                    
    ``--boogie``        
                    Sets the path of the Boogie executable. Required if the Carbon backend
                    is selected. Alternatively, the ``BOOGIE_EXE`` environment variable can be
                    set.

    ``--viper-jar-path``    
                    Sets the path to the required Viper binaries (``silicon.jar`` or
                    ``carbon.jar``). Only the binary for the selected backend is
                    required. You can either use the provided binary packages
                    (see above) or compile your own from source (see below).
                    Expects either a single path or a colon- (Unix) or semicolon-
                    (Windows) separated list of paths. Alternatively, the environment
                    variables ``SILICONJAR``, ``CARBONJAR`` or ``VIPERJAR`` can be set.
                        
To see all possible command line options, invoke ``./bin/nagini`` without arguments.


Alternative Viper Versions
==========================

To use a more recent or custom version of the Viper infrastructure, follow the
`instructions here <https://bitbucket.org/viperproject/documentation/wiki/Home>`_. Look for
``sbt assembly`` to find instructions for packaging the required JAR files. Use the
parameters mentioned above to instruct Nagini to use your custom Viper version.


Troubleshooting
=======================

1.  On Windows: During the setup, you get an error like ``Microsoft Visual C++ 14.0 is required.`` or ``Unable to fnd vcvarsall.bat``: 

    Python cannot find the required Visual Studio 2015 C++ installation, make sure you have either installed the Build Tools or checked the "Common Tools" option in your regular VS 2015 installation (see above).

2.  While verifying a file, you get a stack trace ending with something like ``No matching overloads found``:

    The version of Viper you're using does not match your version of Nagini. Try updating both to the newest version.

3.  When using the Carbon backend, Boogie crashes:

    The Boogie binaries in ViperToolsWin don't seem to work on all systems; in this case, compile Boogie from scratch and set the Boogie path point to the new (or an existing) Boogie installation.

Build Status
============

.. image:: https://pmbuilds.inf.ethz.ch/buildStatus/icon?job=nagini&style=plastic
   :alt: Build Status
   :target: https://pmbuilds.inf.ethz.ch/job/nagini
