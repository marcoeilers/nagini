
Nagini is an automatic verifier for statically typed Python programs, based on the `Viper <http://viper.ethz.ch>`_ verification infrastructure. Nagini is being developed at the `Programming Methodology Group <https://www.pm.inf.ethz.ch/research/nagini.html>`_ at ETH Zurich.

Our CAV 2018 tool paper describing Nagini can be found `here <http://pm.inf.ethz.ch/publications/getpdf.php?bibname=Own&id=EilersMueller18.pdf>`_, and a more detailed description of its encoding can be found in `Marco Eilers' thesis <https://pm.inf.ethz.ch/publications/Eilers2022.pdf>`_. Also see `the Wiki <https://github.com/marcoeilers/nagini/wiki>`_ for the documentation of Nagini's specification language. 

Dependencies (Ubuntu Linux)
===================================

Install Java 11 or newer (64 bit) and Python 3.9 (64 bit, other versions likely *will not work*) and the required libraries.
For usage with Viper's verification condition generation backend Carbon, you will also need to install Boogie (version 2.15.9).

Dependencies (Windows)
==========================

1.  Install Java 11 or newer (64 bit) and Python 3.9 (64 bit, other versions likely *will not work*).

2.  Install the required version of either Visual C++ Build Tools or Visual Studio. 


Getting Started
===============

1.  Create a virtual environment::

        virtualenv --python=python3 <env>
        
2.  Activate it::

        source env/bin/activate
        
3.  Install Nagini::

        pip install nagini

    Alternatively, to get the most up-to-date version, install from source; this will require manually getting and compiling Viper (most likely the most recent development version)::

        git clone https://github.com/marcoeilers/nagini.git
        cd nagini
        pip install .

4.  Optionally, try running the tests::

        pytest src/nagini_translation/tests.py --silicon

Command Line Usage
==================

To verify a specific file from the nagini directory, run::

    nagini [OPTIONS] path-to-file.py


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
                    Enable verification of secure information flow. v can be true for ordinary 
                    non-interference (for sequential programs only), poss for possiblistic 
                    non-intererence (for concurrent programs) or prob for probabilistic non-
                    interference (for concurrent programs).

    --z3           
                    Sets the path of the Z3 executable. Alternatively, the
                    'Z3_EXE' environment variable can be set.
                    
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

