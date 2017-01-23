Getting Started (Ubuntu Linux only)
===================================

1.  `Install Viper <https://bitbucket.org/viperproject/documentation/wiki/Home#markdown-header-binary-packages-ubuntu-linux-only>`_.
2.  Clone repository::

        hg clone https://bitbucket.org/viperproject/py2viper-translation

3.  Install dependencies and run tests::

        make test

If fails with error::

    subprocess.CalledProcessError: Command '['curl', 'https://pypi.python.org/packages/source/s/setuptools/setuptools-20.2.2.zip', '--silent', '--output', '/tmp/bootstrap-mbuvyhif/setuptools-20.2.2.zip']' returned non-zero exit status 77
    make: *** [bin/buildout] Error 1

Try to set::

    export CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

Documentation
=============

To build HTML documentation, use::

    make docs

The documentation is outputted to ``docs/build/html/index.html``.

To run doctests::

    make doctest

Running on Windows
==================

1.  Install Java (64 bit), Mercurial, Git and Python 3.5 (64 bit), s.t. java, hg, git and python are all available from the command line.

2.  Install either Visual C++ Build Tools 2015 (http://go.microsoft.com/fwlink/?LinkId=691126) or Visual Studio 2015. For the latter, make sure to choose the option "Common Tools for Visual C++ 2015" in the setup (see https://blogs.msdn.microsoft.com/vcblog/2015/07/24/setup-changes-in-visual-studio-2015-affecting-c-developers/ for an explanation).

3.  In CMD, do the following::

        hg clone -b win-setup https://bitbucket.org/viperproject/py2viper-translation
        cd py2viper-translation
        hg clone https://bitbucket.org/viperproject/py2viper-contracts deps\py2viper-contracts
        python bootstrap.py
        bin\buildout.exe

4.  Download and extract `ViperToolsWin <http://viper.ethz.ch/downloads/ViperToolsWin.zip>`_ to the py2viper-translation directory

5.  In CMD, do the following (adjust the paths if you have extracted ViperToolsWin somewhere else)::

        set SILICONJAR=backends\silicon.jar
        set CARBONJAR=backends\carbon.jar
        set Z3_EXE=z3\bin\z3.exe
        set BOOGIE_EXE=boogie\Binaries\Boogie.exe

6.  To run the tests, do the following::

        bin\py.test --all-tests --all-verifiers -v src/py2viper_translation/tests.py

7.  To verify a specific file, run e.g.::

        bin\py2viper.exe --verifier silicon tests\functional\verification\examples\test_student_enroll_preds.py

    To see more options (e.g. for supplying paths to Viper, Boogie and Z3 without using environment variables), invoke ``bin\py2viper.exe`` without arguments.

Windows Troubleshooting
=======================

1.  While running ``bin\buildout.exe``, you get an error like ``Microsoft Visual C++ 14.0 is required.`` or ``Unable to fnd vcvarsall.bat``: 

    Python cannot find the required Visual Studio 2015 C++ installation, make sure you have either installed the Build Tools or checked the "Common Tools" option in your regular VS 2015 installation (see above).

2.  While running the tests or verifying a single file, you get a stack trace ending with something like ``TypeError: Package viper.silver.ast.LocalVarDecl is not Callable``:

    The verifier cannot find the Viper .jar files. You either did not set the required environment variables (SILICONJAR etc., see above) or use the respective command line options for bin\py2viper.exe, or the paths you supplied are invalid, or do not point to silicon.jar and carbon.jar.

3.  While running the tests or verifying a single file, you get a stack trace containing the string "Z3_EXE" or "BOOGIE_EXE":

    Same problem as the previous one, but the paths for Boogie and/or Z3 are either not set or invalid.

4.  When using Carbon, Boogie crashes:

    The Boogie binaries in ViperToolsWin don't seem to work on all systems; in this case, compile Boogie from scratch and set the Boogie path point to the new (or an existing) Boogie installation.

Build Status
============

.. image:: https://pmbuilds.inf.ethz.ch/buildStatus/icon?job=nagini&style=plastic
   :alt: Build Status
   :target: https://pmbuilds.inf.ethz.ch/job/nagini