
Nagini is an automatic verifier for statically typed Python programs, based on the `Viper <http://viper.ethz.ch>`_ verification infrastructure. Nagini is being developed at the `Programming Methodology Group <https://www.pm.inf.ethz.ch/research/nagini.html>`_ at ETH Zurich.

Our CAV 2018 tool paper describing Nagini can be found `here <http://pm.inf.ethz.ch/publications/getpdf.php?bibname=Own&id=EilersMueller18.pdf>`_, and a more detailed description of its encoding can be found in `Marco Eilers' thesis <https://pm.inf.ethz.ch/publications/Eilers2022.pdf>`_. Also see `the Wiki <https://github.com/marcoeilers/nagini/wiki>`_ for the documentation of Nagini's specification language. 

Dependencies (Ubuntu Linux)
===================================

Install Java 11 or newer (64 bit) and Python 3.9 (64 bit, other versions likely *will not work*) and the required libraries (in particular, python3.9-dev). 
Experimental support for newer Python versions is available on the branches `py310 <https://github.com/marcoeilers/nagini/tree/py310>`_, `py311 <https://github.com/marcoeilers/nagini/tree/py311>`_ and `py312 <https://github.com/marcoeilers/nagini/tree/py312>`_ but may offer significantly worse performance.
For usage with Viper's verification condition generation backend Carbon, you will also need to install Boogie (version 2.15.9).

Dependencies (Windows)
==========================

Install Java 11 or newer (64 bit) and Python 3.9 (64 bit, other versions likely *will not work*), as well as the required version of either Visual C++ Build Tools or Visual Studio if necessary.
Experimental support for newer Python versions is available on the branches `py310 <https://github.com/marcoeilers/nagini/tree/py310>`_, `py311 <https://github.com/marcoeilers/nagini/tree/py311>`_ and `py312 <https://github.com/marcoeilers/nagini/tree/py312>`_ but may offer significantly worse performance and is currently untested on Windows.
For usage with Viper's verification condition generation backend Carbon, you will also need to install Boogie (version 2.15.9).

Note that we have observed *significantly* worse performance when using Nagini on Windows on some
systems. We currently do not know why this happens, but will investigate the issue when possible.

Getting Started
===============

Execute the following commands (on Windows, you may have to use ``cmd`` and not PowerShell):

1.  Create a virtual environment::

        virtualenv --python=python3.9 <env>
        
2.  Activate it::

        source env/bin/activate

    on Linux, or::

        env\Scripts\activate

    on Windows.
        
3.  Install Nagini::

        pip install nagini

    Alternatively, to get the most up-to-date version, install from source::

        git clone https://github.com/marcoeilers/nagini.git
        cd nagini
        pip install .

4.  Optionally, try running the tests::

        pytest -v -p no:faulthandler src/nagini_translation/tests.py --silicon

Command Line Usage
==================

To verify a specific file from the nagini directory, run::

    nagini [OPTIONS] path-to-file.py

You may have to explicitly supply a path to a Z3 executable (use version 4.8.7, other versions may offer significantly worse performance) using the command line parameter ``--z3=path/to/z3``.
Additionally, you may have to set the environment variable ``JAVA_HOME`` to point to your Java installation.
See the `wiki <https://github.com/marcoeilers/nagini/wiki>`_ for information on how to write specifications in Nagini.


The following command line options are available::

    --verifier      
                    Selects the Viper backend to use for verification.
                    Possible options are 'silicon' (for Symbolic Execution) and 'carbon' 
                    (for Verification Condition Generation based on Boogie).  
                    Default: 'silicon'.

    --select        
                    Select which functions/methods/classes to verify. Expects a comma-
                    separated list of names.

    --counterexample        
                    Enable outputting counterexamples for verification errors (experimental).
                    
    --sif=v         
                    Enable verification of secure information flow. v can be 'true' for ordinary 
                    non-interference (for sequential programs only), 'poss' for possiblistic 
                    non-intererence (for concurrent programs) or 'prob' for probabilistic non-
                    interference (for concurrent programs).

    --float-encoding           
                    Selects a different encoding of floating point values. The default is to model floats
                    as abstract values and all float operations as uninterpreted functions, so that essentially 
                    nothing can be proved about them. Legal values for this option are 'real' to model floats
                    as real numbers (i.e., not modeling floating point imprecision), or 'ieee32' to model them
                    as proper IEEE 32 bit floats. The latter option unfortunately usually leads to very long
                    verification times or non-termination.
    --int-bitops-size
                    Bitwise operations on integers (e.g. 12 ^ -5) are supported only for integers which can
                    be proven to be in a specific range, namely the range of n-bit signed integers.
                    This parameter sets the value of n.
                    Default: 8.
                    
    --boogie        
                    Sets the path of the Boogie executable. Required if the Carbon backend
                    is selected. Alternatively, the 'BOOGIE_EXE' environment variable can be
                    set.

    --viper-jar-path    
                    Sets the path to the required Viper binaries ('silicon.jar' or
                    'carbon.jar'). Only the binary for the selected backend is
                    required. You can either use the provided binary packages installed
                    by default or compile your own from source (see below).
                    Expects either a single path or a colon- (Unix) or semicolon-
                    (Windows) separated list of paths. Alternatively, the environment
                    variables 'SILICONJAR', 'CARBONJAR' or 'VIPERJAR' can be set.
                        
To see all possible command line options, invoke ``nagini`` without arguments.


Server Mode / Faster Verification Mode
======================================

Nagini has to do a significant amount of work on startup, and has to start a JVM to run Viper.
To avoid some of that startup work and speed up Viper's runtime, Nagini has a server mode.
To use it,

0. Install pyzmq::

        pip install pyzmq

1. Start a Nagini server::

        nagini --server <otherArgs> dummyFile.py
   Note that all required arguments, including ``JAVA_HOME`` and other potentially required  
   environment variables, have to be set here. The dummy file does not need to exist, it is 
   never read, but some file name has to be supplied.

2. Wait a few seconds to allow the server to start up

3. While the server is running, run a client to instruct the server to verify a specific file::

        nagini_client path/to/file.py 
   

Alternative Viper Versions
==========================

To use a more recent or custom version of the Viper infrastructure, follow the
`instructions here <https://github.com/viperproject/documentation/wiki>`_. Look for
``sbt assembly`` to find instructions for packaging the required JAR files. Use the
parameters mentioned above to instruct Nagini to use your custom Viper version.


Troubleshooting
=======================

1.  On Windows: During the setup, you get an error like ``Microsoft Visual C++ 14.0 is required.`` or ``Unable to fnd vcvarsall.bat``: 

    Python cannot find the required Visual Studio C++ installation, make sure you have either installed the Build Tools or checked the "Common Tools" option in your regular Visual Studio installation (see above).

2.  While verifying a file, you get a stack trace ending with something like ``No matching overloads found``:

    The version of Viper you're using does not match your version of Nagini. Try updating both to the newest version.

3.  Nagini cannot prove trivial properties about the return values of functions: 

    This is likely due to a lack of specifications, see the discussion in the ``General Contracts`` section of the  `wiki <https://github.com/marcoeilers/nagini/wiki>`_.

