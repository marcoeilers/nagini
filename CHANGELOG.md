# Nagini Changelog

## v1.3.0 (June 2026)

### New features

- **Python 3.12–3.14 support**: Nagini now targets Python 3.12 and newer (3.13 and 3.14 are also supported). Python versions older than 3.12 are no longer supported. (#300)
- **`match` statement support**: `match`/`case` statements are now supported in both impure and pure functions. Most pattern types (value, OR, sequence, mapping, class, wildcard, capture) are handled, with class patterns with keyword arguments currently unsupported. (#301, #302)
- **Branch condition reporting**: When using the Silicon backend, error messages now include the branch conditions that led to the error — the set of conditions along the execution path that the verifier was exploring when it found the failure. (#298)
- **Bytearray and PByteSeq**: Added support for `bytearray` and a corresponding pure ghost type `PByteSeq`. (#299)
- **`IntEnum` support**: Classes subclassing `IntEnum` are now supported. (#299)
- **Bit shift operators**: Left (`<<`) and right (`>>`) shift operators are now supported for integers. (#299)
- **`int.bit_length()`**: Added support for the `int.bit_length()` method. (#299)
- **String format expressions**: Basic support for string format operations. (#299)
- **Relative imports**: `from .module import X` style relative imports are now supported. (#280)
- **Constructor calls with type arguments**: Calls like `ParseResult[bool](True)` (generic constructor with explicit type argument) are now supported. (#264)
- **Subclassing `int`**: Soundly supports subclasses of `int`. Subclassing other builtin types remains unsupported. (#262)
- **Better quantifier triggers for collections**: Improved trigger selection for `Forall` quantifiers over lists, sequences, and similar collection types, reducing incompleteness issues. (#289)

### Fixes

- Fixed imprecise ADT type information in certain cases. (#288)
- Fixed several crashes and translation errors. (#265, #267, #268, #272, #274, #277, #279, #283, #291)
- Fixed `Reveal()` annotations being incorrectly attached to type conversion wrappers rather than the actual function call. (#303)

### Infrastructure and dependencies

- Migrated packaging from `setup.py` to `pyproject.toml`. (#300)
- Updated `jpype1` from 1.5.0 to 1.7.0. (#300)
- Updated `mypy` from 0.900 to 1.5.0. (#300)
- Updated `toposort` from 1.5 to 1.10. (#300)
- Updated `z3-solver` to 4.16.0.0 on ARM. (#300)
- Updated `pytest` from 7.0.0 to 9.0.3. (#300)
- Removed `astunparse` and `typed-ast` dependencies. (#300)

---

## v1.2.0 (November 2025)

### New features

- **Python 3.9–3.12 multi-version support**: Nagini now supports Python 3.9, 3.10, 3.11, and 3.12 (previously only 3.9 was officially supported). CI tests run against multiple Python versions. (#256)
- **Opaque pure functions**: Pure functions can now be marked `@Opaque`. Callers only learn the function's postcondition by default; they must wrap the call in `Reveal(...)` to unfold the function's definition. (#240)
- **`Assert` and `Unfold` in pure functions**: The `Assert(e)` and `Unfold(P(...))` contract statements can now be used inside pure functions, translating to Viper's `asserting` and `unfolding` expressions. (#248)
- **Postconditions with lambdas**: `Ensures(T, lambda r: P(r))` is now accepted as an alternative to `Ensures(P(Result()))`. This form is fully type-checkable by mypy and executable without runtime errors. (#228)
- **`@Inline` decorator**: Methods and functions can be marked `@Inline` to request that Nagini inline their bodies at call sites rather than treating them modularly. (#215)
- **Proper string encoding**: Strings are now encoded as sequences of characters in Viper, enabling stronger reasoning about string contents. (#225)
- **Optional obligation encoding**: The obligation encoding (for reasoning about threads, locks, and IO operations) is now only activated when the program actually uses these features. A `--force-obligations` flag is available to override this. (#230)
- **Using Viper's Chopper for dependency analysis**: Nagini's custom dependency tracking between methods and functions has been replaced by Viper's built-in Chopper, which is more precise. (#250)
- **Power operator** (`**`): The `**` operator is now supported for integers, with special-case handling for constant exponents to improve SMT automation. (#213, #217)
- **Ellipsis** (`...`): The `...` literal is now accepted. (#257)
- **Longer tuple support**: Tuples up to length 9 are now supported (previously limited to length 4). A clear error is given for longer tuples. (#259)
- **Resource bounds with Silicon**: Verification is now run with resource bounds instead of timeouts by default when using the Silicon's backend. (#251)
- **Viper 25.02**: Updated to the Viper 25.02 release. (#226)

### Fixes

- Fixed crash on dynamically indexed tuples. (#227)
- Fixed crash when calling an unsupported method or function. (#233)
- Fixed statically-bound calls to interface methods being incorrectly treated as dynamic dispatch. (#243)
- Fixed global constant functions not being marked as terminating. (#244)
- Fixed incorrect field vs. property ordering that could cause crashes. (#236)
- Fixed `MayCreate` and built-in predicates being usable in impure positions. (#239)

---

## v1.1.1 (October 2024)

### Fixes

- Updated `jpype1` to version 1.2.1 which has pre-built wheels for Python 3.9 on Windows and avoids compilation issues on that platform. (#210)
- Added basic Windows CI tests and fixed automatic Z3 executable path detection on Windows. (#211)

---

## v1.1.0 (October 2024)

This release includes a large number of features and fixes accumulated since v0.9.0, as well as the first official support for Python 3.9.

### Language and verification features

- **Python 3.9 support**: Nagini now supports Python 3.9 (as well as the previously supported Python 3.8). (#167)
- **Abstract predicates**: Predicates can now be declared abstract (without a body), allowing callers to use them without Nagini knowing their definition. (#163)
- **Bitwise operators**: `&`, `|`, and `^` are now supported for both booleans and bounded integers. The encoding uses the SMT bitvector theory and requires a declared bit-width bound. (#208)
- **Reflected arithmetic magic methods**: `__radd__`, `__rsub__`, `__rmul__`, etc. are now supported, enabling custom right-hand-side operator overloading. (#183)
- **Unary operator magic methods**: `__neg__`, `__pos__`, `__abs__` etc. are now supported, also fixing a bug with negative float literals. (#184)
- **Inplace arithmetic magic methods**: `__iadd__`, `__isub__`, etc. are now supported. (#188)
- **Float encoding options**: A new `--float-encoding` command-line flag accepts `real` (model floats as mathematical reals) or `ieee32` (use SMT IEEE floating point theory). The default remains uninterpreted floats. (#160)
- **Float model extended**: The real-number float model now handles `float('inf')`, `float('-inf')`, and `float('nan')`. A new `isNaN()` contract function is available. (#192)
- **`ResultT(t)` contract function**: `ResultT(T)` is a typed alternative to `Result()` in postconditions, allowing mypy to type-check postconditions that mention the return value without using `Any`. (#205)
- **New dict encoding**: Dictionaries are now encoded using Viper's native map type, improving completeness and counterexample quality. (#154)
- **Counterexamples for generic classes**: Counterexample extraction now works correctly for generic classes. (#154)
- **`Refute` and `Decreases` contract functions**: Added `Refute(e)` (assert that `e` is not provable) and `Decreases(e)` (termination measure). (#154)
- **`ToMS` and `Forall_n` contract functions**: Added `ToMS` (convert to multiset) and `Forall_n` (quantifier over `n` variables). (#154)
- **`viper_arg` support**: Arguments can be passed directly to the Viper backend via `viper_arg`. (#154)
- **`sorted()` and `sum()` builtins**: Added support for the `sorted()` and `sum()` builtin functions. (#172)
- **`range()` with one argument**: `range(n)` is now supported in addition to `range(start, stop)`. (#171)
- **Correct exit codes**: Nagini now exits with an appropriate non-zero exit code when verification fails. (#178)
- **Better error messages for built-in functions**: Precondition violation messages for built-in functions include source location information via Viper annotations. (#174)
- **Better tuple equality**: Tuple equality is now defined in terms of component-wise object equality, and object equality is axiomatized to be transitive and symmetric. (#165, #173, #179)
- **Tracking static field assignments**: Static field and global variable assignments are now correctly tracked, fixing incorrect `Final` detection. (#162)
- **Fix `__truediv__`**: Fixed inconsistent use of `__div__` vs `__truediv__` (Python 3 uses the latter for `/`). (#190)
- **Fix union subtype axiom**: Fixed an unsoundness where union subtype checking was incorrect for union types on the left-hand side. (#197)
- **Viper data collection**: Added a `--submit-for-evaluation` option to submit programs to the Viper data collection server. (#180)
- **Viper 24.01 update**: Updated the bundled Viper backends. (#154, #166)

---

## v0.9.0 (May 2021)

### New features

- **Security information flow (SIF) analysis**: Added support for verifying possibilistic and probabilistic noninterference properties using a dedicated `--sif` command-line flag. SIF verification uses a product program encoding and a specialized Silicon backend extension. (#145, #146)
- **Counterexamples**: When verification fails, Nagini can now produce counterexamples showing concrete values for program variables that cause the failure. Use `--counterexample` to enable. Counterexamples are supported for most built-in types and can include global variables.
- **SIF counterexamples**: Counterexample extraction also works when using the `--sif` mode.
- **Updated Viper version**: Updated to a newer Viper release with various improvements.

---

## v0.8.x (2017–2020)

The 0.8.x series represents the primary development period of Nagini, during which the core language support and most of the fundamental verification features were built. The series spans versions 0.8 through 0.8.6. Key features introduced during this period:

### Concurrency

- **Thread support**: Nagini supports creating, starting, and joining threads using a `Thread` stub class and corresponding contract functions. Verification checks wait-level and obligation contracts for thread operations. (#103)
- **Lock invariants**: Locks can have invariants defined by overriding the `invariant` predicate in a subclass of `Lock`. (#104)

### Data types and language features

- **Algebraic Data Types (ADTs)**: Python classes can be used as ADTs and are translated to Viper using classical axiomatization. (#114)
- **Properties**: Property getters (translated as pure functions) and setters (translated as methods) are fully supported. (#81)
- **Generic classes and methods**: Generic classes with type parameters work correctly, including generic methods. (#77)
- **Dynamic field creation**: Fields can be added to objects outside the constructor. Permissions to create or set fields are tracked via `MayCreate` and `MaySet` contract functions. Field deletion is also supported. (#90)
- **Union types**: Method calls and attribute accesses on variables with union or optional types are handled by case-splitting on the actual type. (#94, #100)
- **List comprehensions**: Simple list comprehensions are supported. (#79)
- **`enumerate()` builtin**: The `enumerate()` function is supported in for-loops. (#135)
- **Let-expressions**: `Let(e, lambda x: body)` is supported. (#135)
- **Global program**: Top-level statements are collected into a single synthetic method that captures global initialization. (#96)

### Ghost types and permissions

- **Pure sequences** (`PSeq`): A purely functional sequence type for use in specifications.
- **Pure sets** (`PSet`): A purely functional set type. (#106)
- **Pure multisets** (`PMultiset`): A purely functional multiset type. (#138)
- **Abstract read permissions**: Support for abstract read permission amounts. (#137)
- **Wildcard permissions**: Permission amounts in function contracts are automatically interpreted as wildcard amounts; `Rd()` can be used explicitly. (#79)

### IO and specification features

- **IO contracts**: Nagini supports specifying and verifying I/O behavior using IO operation contracts. A built-in `eval_io` operation enables conditionally-triggered transitions. (#83)
- **`ignore-global` flag**: A command-line flag to skip verification of top-level statements. (#109)
- **`--select` flag**: Selective verification — choose a subset of methods, functions, or classes to verify; dependencies are included as stubs. (#78)
- **Client/server mode**: A long-running server process keeps the JVM warm for faster repeated verification, intended for IDE integration. (#84)
- **Quantifier triggers**: Manually specified and auto-generated triggers are supported for universal quantifiers. (#135)
- **Definedness checking**: Nagini checks that local variables are defined on every use and that fields are initialized before access in constructors. (#89)
- **Postconditions in constructors**: Postconditions may be written at the end of a method body, which is useful for constructors. (#88)
