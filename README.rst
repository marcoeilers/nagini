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

1.  Install Java (64 bit), Mercurial, Git and Python 3.6 (64 bit), s.t. java, hg, git and python are all available from the command line.

2.  Install Visual C++ Build Tools 2015: http://go.microsoft.com/fwlink/?LinkId=691126

3.  Do the following::

        hg clone -b win-setup https://bitbucket.org/viperproject/py2viper-translation
        cd py2viper-translation
        mkdir deps
        hg clone https://bitbucket.org/viperproject/py2viper-contracts deps\py2viper-contracts
        python bootstrap.py
        bin\buildout.exe

4.  Download and extract `ViperToolsWin <http://viper.ethz.ch/downloads/ViperToolsWin.zip>`_ to the py2viper-translation directory

5.  Do the following::

        set SILICONJAR=ViperToolsWin\backends\silicon.jar
        set CARBONJAR=ViperToolsWin\backends\carbon.jar
        set Z3_EXE=ViperToolsWin\z3\bin\z3.exe
        set Z3_EXE=ViperToolsWin\boogie\Binaries\Boogie.exe

6.  To run the tests, do the following::

        bin\py.test --all-tests --all-verifiers -v src/py2viper_translation/tests.py

7.  To verify a specific file, run e.g.::

        bin\py2viper.exe --verifier silicon tests\functional\verification\examples\test_student_enroll_preds.py

Build Status
============

.. image:: https://pmbuilds.inf.ethz.ch/buildStatus/icon?job=nagini&style=plastic
   :alt: Build Status
   :target: https://pmbuilds.inf.ethz.ch/job/nagini