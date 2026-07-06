
Nagini is an automatic verifier for statically typed Python programs, based on the `Viper <http://viper.ethz.ch>`_ verification infrastructure. Nagini is being developed at the `Programming Methodology Group <https://www.pm.inf.ethz.ch/research/nagini.html>`_ at ETH Zurich.

Our CAV 2018 tool paper describing Nagini can be found `here <http://pm.inf.ethz.ch/publications/getpdf.php?bibname=Own&id=EilersMueller18.pdf>`_, and a more detailed description of its encoding can be found in `Marco Eilers' thesis <https://pm.inf.ethz.ch/publications/Eilers2022.pdf>`_. Also see `the Wiki <https://github.com/marcoeilers/nagini/wiki>`_ for the documentation of Nagini's specification language. See the `changelog <CHANGELOG.md>`_ for the version history.

Dependencies (Ubuntu Linux)
===================================

1.  Install Java 11 or newer (64 bit) and a Python version between Python 3.12 and 3.14 (64 bit).

2.  Install the the required libraries, in particular, python3.x-dev.

3.  For usage with Viper's verification condition generation backend Carbon, you will also need to install Boogie (version 2.15.9).

Dependencies (Windows)
==========================

1.  Install Java 11 or newer (64 bit) and a Python version between Python 3.12 and 3.14 (64 bit).

2.  Install the required version of either Visual C++ Build Tools or Visual Studio.

3.  For usage with Viper's verification condition generation backend Carbon, you will also need to install Boogie (version 2.15.9).

Getting Started
===============

Execute the following commands (on Windows, you may have to use ``cmd`` and not PowerShell):

1.  Create a virtual environment::

        virtualenv --python=python3.14 <env>
        
2.  Activate it::

        source env/bin/activate

    on Linux, or::

        env\Scripts\activate

    on Windows.
        
3.  Install Nagini::

        pip install nagini
        # or with optional dependencies for server mode and testing:
        pip install "nagini[server,test]"

    Alternatively, to get the most up-to-date version, install from source::

        git clone https://github.com/marcoeilers/nagini.git
        cd nagini
        pip install .
        # or with optional dependencies for server mode and testing:
        pip install ".[server,test]"

4.  Optionally, try running some tests::

        pytest -v -p no:faulthandler src/nagini_translation/tests.py --silicon --minimal

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
                    Sets the path to the required Viper binary ('viperserver.jar').
                    A single jar bundles both the Silicon and Carbon backends, so it
                    is used regardless of the selected backend. You can either use the
                    provided binary packages installed by default or compile your own
                    from source (see below).
                    Expects either a single path or a colon- (Unix) or semicolon-
                    (Windows) separated list of paths. Alternatively, the environment
                    variable 'VIPERSERVERJAR' can be set, or 'VIPERJAVAPATH' for a
                    full explicit classpath.
                        
To see all possible command line options, invoke ``nagini`` without arguments.

Server Mode / Faster Verification Mode
======================================

Nagini has to do a significant amount of work on startup, and has to start a JVM to run Viper.
To avoid some of that startup work and speed up Viper's runtime, Nagini has a server mode.
To use it,

0. Install pyzmq::

        pip install "nagini[server]"

1. Start a Nagini server::

        nagini --server <otherArgs> dummyFile.py

   Note that all required arguments, including ``JAVA_HOME`` and other potentially required
   environment variables, have to be set here. The dummy file does not need to exist, it is
   never read, but some file name has to be supplied.

2. Wait a few seconds to allow the server to start up. It prints a message like ``Server started successfully on <address>`` when it is ready.

3. While the server is running, run a client to instruct the server to verify a specific file::

        nagini_client path/to/file.py

Model Context Protocol (MCP) Server
===================================

Nagini ships an MCP server that exposes verification to AI agents and MCP-capable
editors (e.g. Claude Code, Claude Desktop, Cursor) over stdio. Through it, an agent
can verify entire files, individual methods, or inline snippets and receive
structured diagnostics (error positions, messages, and optional counterexamples).

1. Install Nagini with the MCP dependencies::

        pip install "nagini[mcp]"

   As with normal command-line use, a Java installation is required. The Z3 and
   Viper JAR binaries needed for verification are bundled with Nagini, so you do
   not need to supply them separately. If Java is not found automatically, set the
   ``JAVA_HOME`` environment variable to point to your Java installation.

2. The server is launched via the ``nagini_mcp`` entry point and communicates over
   stdio, so it is normally started by the MCP client rather than by hand. Configure
   your client to run it, passing ``JAVA_HOME`` through the environment if needed.
   For example::

        {
          "mcpServers": {
            "nagini": {
              "command": "nagini_mcp",
              "env": { "JAVA_HOME": "/path/to/your/java" }
            }
          }
        }

   Use the absolute path to the ``nagini_mcp`` executable (e.g. the one inside your
   virtual environment) if it is not on the client's ``PATH``. The server uses the
   faster in-process ViperServer backend by default and accepts the same
   configuration options as the command line (e.g. ``--verifier``); run
   ``nagini_mcp --help`` to see them.

The server exposes the following tools: ``verify_file``, ``verify_method``,
``verify_snippet``, ``configure`` (change verification options at runtime),
``cancel``, and ``flush_cache``. See the
`wiki <https://github.com/marcoeilers/nagini/wiki>`_ for information on how to write
specifications in Nagini.

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

Publications on Nagini
=======================

The following papers describe verification techniques implemented in Nagini:

- `Nagini: A Static Verifier for Python <http://pm.inf.ethz.ch/publications/getpdf.php?bibname=Own&id=EilersMueller18.pdf>`_ — Marco Eilers and Peter Müller, CAV 2018. The original tool paper presenting Nagini's design and specification language.

- `Modular Specification and Verification of Security Properties for Mainstream Languages <https://pm.inf.ethz.ch/publications/Eilers2022.pdf>`_ — Marco Eilers, PhD Thesis, ETH Zurich (2022). A detailed description of Nagini's encoding and verification approach.

- `Product Programs in the Wild: Retrofitting Program Verifiers to Check Information Flow Security <https://pm.inf.ethz.ch/publications/EilersMeierMueller21.pdf>`_ — Marco Eilers, Severin Meier, and Peter Müller, CAV 2021. Describes Nagini's support for verifying information flow security (noninterference) via product programs constructed at the Viper intermediate language level.

- `Modular Reasoning about Object Relations <https://pm.inf.ethz.ch/publications/GreutmannEilersMueller26.pdf>`_ — Micha Greutmann, Marco Eilers, and Peter Müller (2026). Presents a modular technique for verifying algebraic properties of object relations such as equality, implemented in Nagini.

Published Work Using Nagini
============================

The following papers and theses have used Nagini to verify Python programs:

- `Formally Verified ASN.1 Python Encoders and Decoders <https://ethz.ch/content/dam/ethz/special-interest/infk/chair-program-method/pm/documents/Education/Theses/Luca_Schafroth_MS_Report.pdf>`_ — Luca Schafroth, ETH Zurich Master's Thesis (2026). Formal verification of ASN.1/ACN-generated Python codecs using Nagini, proving round-trip correctness for several data types and fully verifying the BitStream runtime component.

- `A Verification-Aware Pipeline for Programmable Logic Controllers <https://www.es.mdu.se/pdf_publications/7311.pdf>`_ — Salari et al., Mälardalen University (2025). Verifies Python models of industrial IEC 61131-3 Function Block Diagram programs (from an electropneumatic brake control subsystem) generated by the PyLC+ framework.

- `VeriGuard: Enhancing LLM Agent Safety via Verified Code Generation <https://arxiv.org/pdf/2510.05156>`_ — Miculicich et al., Google (2025). Uses Nagini to formally verify behavioral policies for LLM-based AI agents, providing runtime safety guarantees for agent actions.

- `Can LLMs Enable Verification in Mainstream Programming? <https://arxiv.org/pdf/2503.14183>`_ — Shefer et al., JetBrains Research (2025). Evaluates LLMs' ability to generate verified code across Dafny, Nagini, and Verus using benchmarks derived from HumanEval.

- `An LLM Benchmark Suite for Specification Inference <https://ethz.ch/content/dam/ethz/special-interest/infk/chair-program-method/pm/documents/Education/Theses/wiwest_Masters_Thesis.pdf>`_ — William West, ETH Zurich Master's Thesis (2025). Develops a benchmark for evaluating LLMs on program verification inference tasks, including Nagini specification synthesis.

- `Large Language Models for Verified Programs <https://ethz.ch/content/dam/ethz/special-interest/infk/chair-program-method/pm/documents/Education/Theses/omkar_thesis-omkar-zade.pdf>`_ — Omkar Zade, ETH Zurich Master's Thesis (2024). Uses LLMs to automatically infer Nagini memory-safety specifications for Python programs, contributing a dataset of verified programs as a benchmark.

- `Static Verification of the SCION Router Implementation <https://ethz.ch/content/dam/ethz/special-interest/infk/chair-program-method/pm/documents/Education/Theses/Sascha_Forster_BA_report(3).pdf>`_ — Sascha Forster, ETH Zurich Bachelor's Thesis (2018). Verifies memory safety, progress, and I/O behaviour of the SCION border router's Python implementation using Nagini.
