
Nagini is an automatic verifier for statically typed Python programs, based on the `Viper <http://viper.ethz.ch>`_ verification infrastructure. Nagini is being developed at the `Chair of Programming Methodology <http://www.pm.inf.ethz.ch/>`_ at ETH Zurich as part of the `VerifiedSCION <http://www.pm.inf.ethz.ch/research/verifiedscion.html>`_ project.

Our CAV 2018 tool paper describing Nagini can be found `here <http://pm.inf.ethz.ch/publications/getpdf.php?bibname=Own&id=EilersMueller18.pdf>`_. See `here <https://github.com/marcoeilers/nagini/wiki>`_ for the documentation of Nagini's specification language. 

You can try a (rather slow) online version of Nagini `here <http://viper.ethz.ch/nagini-examples>`_.

For use with the PyCharm IDE, try the `Nagini PyCharm plugin <https://github.com/marcoeilers/nagini-pycharm>`_.

Getting Started (Ubuntu Linux only)
===================================

0.  Install Java 8 (64 bit), Mercurial, Git and Python 3.6 (64 bit, newer versions should work but are currently untested) and the required libraries::

        sudo apt-get install python3-dev libzmq3-dev

    For usage with the Viper's verification condition generation backend Carbon, you will also need to install the Mono runtime.

1.  Clone repository::

        git clone https://github.com/marcoeilers/nagini.git

2.  Download and extract `ViperToolsLinux <http://viper.ethz.ch/downloads/ViperToolsLinux.zip>`_ to the nagini directory
3.  Set paths to Viper (adjust paths if necessary)::

        export SILICONJAR=backends/silicon.jar
        export CARBONJAR=backends/carbon.jar
        export Z3_EXE=z3/bin/z3
        export BOOGIE_EXE=boogie/Binaries/Boogie.exe

4.  Install dependencies and run tests::

        cd nagini
        make test

    If it fails with the error::

        subprocess.CalledProcessError: Command '['curl', 'https://pypi.python.org/packages/source/s/setuptools/setuptools-20.2.2.zip', '--silent', '--output', '/tmp/bootstrap-mbuvyhif/setuptools-20.2.2.zip']' returned non-zero exit status 77
        make: *** [bin/buildout] Error 1

    Try to set::

        export CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt


Getting Started on Windows
==================

1.  Install Java (64 bit), Mercurial, Git and Python 3.5 (64 bit), s.t. java, hg, git and python are all available from the command line.

2.  Install either Visual C++ Build Tools 2015 (http://go.microsoft.com/fwlink/?LinkId=691126) or Visual Studio 2015. For the latter, make sure to choose the option "Common Tools for Visual C++ 2015" in the setup (see https://blogs.msdn.microsoft.com/vcblog/2015/07/24/setup-changes-in-visual-studio-2015-affecting-c-developers/ for an explanation).

3.  In CMD, do the following::

        git clone https://github.com/marcoeilers/nagini.git
        cd nagini
        mkdir -p .virtualenv
        wget -c https://pypi.python.org/packages/d4/0c/9840c08189e030873387a73b90ada981885010dd9aea134d6de30cd24cb8/virtualenv-15.1.0.tar.gz#md5=44e19f4134906fe2d75124427dc9b716 -O .virtualenv\archive.tar.gz
        tar -xvf .virtualenv\archive.tar.gz
        mv virtualenv-* .virtualenv\source
        python3 .virtualenv\source\virtualenv.py env
        env\Scripts\pip.exe install -r requirements.txt
        env\Scripts\pip.exe install -e .

4.  Download and extract `ViperToolsWin <http://viper.ethz.ch/downloads/ViperToolsWin.zip>`_ to the nagini directory

5.  In CMD, do the following (adjust the paths if you have extracted ViperToolsWin somewhere else)::

        set SILICONJAR=backends\silicon.jar
        set CARBONJAR=backends\carbon.jar
        set Z3_EXE=z3\bin\z3.exe
        set BOOGIE_EXE=boogie\Binaries\Boogie.exe

6.  To run the tests, do the following::

        env\Scripts\pytest.exe --all-tests --all-verifiers -v src\nagini_translation\tests.py


Command Line Usage
==================

To verify a specific file from the nagini directory, run::

    ./env/bin/nagini [OPTIONS] path-to-file.py

on Linux or ::

    env\Scripts\nagini.exe [OPTIONS] path-to-file.py

on Windows.

The following command line options are available::

    ``--verifier``      
                    Possible options are ``silicon`` and ``carbon``. Selects the Viper backend
                    to use for verification. Default: ``silicon``.

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
parameters mentioned above to instruct Nagini to use your custom 


Documentation
=============

To build HTML documentation, use::

    make docs

The documentation is outputted to ``docs/build/html/index.html``.

To run doctests::

    make doctest

Troubleshooting
=======================

1.  On Windows: During the setup, you get an error like ``Microsoft Visual C++ 14.0 is required.`` or ``Unable to fnd vcvarsall.bat``: 

    Python cannot find the required Visual Studio 2015 C++ installation, make sure you have either installed the Build Tools or checked the "Common Tools" option in your regular VS 2015 installation (see above).

2.  While running the tests or verifying a single file, you get a stack trace ending with something like ``TypeError: Package viper.silver.ast.LocalVarDecl is not Callable``:

    The verifier cannot find the Viper .jar files. You either did not set the required environment variables (SILICONJAR etc., see above) or use the respective command line options for bin\nagini.exe, or the paths you supplied are invalid, or do not point to silicon.jar and carbon.jar.

3.  While running the tests or verifying a single file, you get a stack trace containing the string "Z3_EXE" or "BOOGIE_EXE":

    Same problem as the previous one, but the paths for Boogie and/or Z3 are either not set or invalid.

4.  While running the tests or verifying a single file, you get a stack trace ending with something like ``No matching overloads found``:

    The version of Viper you're using does not match your version of Nagini. Try updating both to the newest version.

5.  When using Carbon, Boogie crashes:

    The Boogie binaries in ViperToolsWin don't seem to work on all systems; in this case, compile Boogie from scratch and set the Boogie path point to the new (or an existing) Boogie installation.

Build Status
============

.. image:: https://pmbuilds.inf.ethz.ch/buildStatus/icon?job=nagini&style=plastic
   :alt: Build Status
   :target: https://pmbuilds.inf.ethz.ch/job/nagini
