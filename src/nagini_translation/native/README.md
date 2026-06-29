# Cross-Language Verification between Python and C

This directory contains the prototype toolchain accompanying the paper
*"Towards Cross-Language Verification between Python and C"* (ISoLA). It extends
Nagini so that, for Python functions marked `@Native` (i.e. implemented in C via
the CPython C API), it **generates VeriFast contracts** for the corresponding C
function from the function's Nagini specification. The generated contracts are
expressed against a VeriFast formalization of (a subset of) the CPython C API,
which lives in this directory. The C implementations of the case studies are
then verified against those generated contracts with VeriFast.

The verification rests on a reference-counting encoding in which `pyobj_hasval`
(the paper's `hasVal`) is pure, duplicable value knowledge and a separate,
non-duplicable `hasRef(o, owned)` predicate tracks ownership of a single
reference (`owned == true` for an owned/new reference, `false` for a borrowed
one). See `PythonAPI/defs/vfdefs/VFdefs.c` for the predicate definitions.

## Generating C specifications with Nagini

A function is marked for C-contract generation with the `@ContractOnly` and
`@Native` decorators and given a Nagini pre-/postcondition, e.g.

```python
@ContractOnly
@Native
def py_max(a: int, b: int) -> int:
    Requires(LONG_MIN() < a and a < LONG_MAX())
    Requires(LONG_MIN() < b and b < LONG_MAX())
    Ensures(Result() is (a if a > b else b))
```

Running Nagini on a file containing such functions verifies the Python side and
prints, to standard output, a shared *environment* block (VeriFast fixpoints and
predicates for the module's classes and `@Pure` functions) followed by one C
function signature with a `requires`/`ensures` contract per `@Native` function:

```
nagini path/to/file.py
```

To only generate the contracts (skipping the Viper verification of the Python
code), pass `--skip-verification`:

```
nagini --skip-verification path/to/file.py
```

The block before `/*--END OF ENV--*/` is the shared environment; each subsequent
block (ending in `/*----*/`) is one C function's generated contract.

## The CPython C API formalization

The VeriFast specification of the CPython C API lives in [`PythonAPI/`](PythonAPI/):

| File | Contents |
|------|----------|
| `PythonAPI/vfpy.c` | Entry point: `#include`s all of the below. Case studies include this file. |
| `PythonAPI/defs/vfdefs/VFdefs.c` | Core predicates and lemmas: `pyobj_hasval`, `hasRef`, `pyobj_hasattr`, `pyobj_hascontent`, `PyExc`, the exception class hierarchy, and the tuple-borrow machinery (`borrowRefs`/`returnRefs`, `bigstar`). |
| `PythonAPI/refcount.c` | `Py_INCREF` / `Py_DECREF`. |
| `PythonAPI/pylong_methods.c`, `pyfloat_methods.c`, `pybool_methods.c` | Numeric-object functions (`PyLong_AsLong`, `PyLong_FromLong`, …). |
| `PythonAPI/pyobject_methods.c` | Generic object functions, incl. attribute access (`PyObject_GetAttrString`, `PyObject_SetAttrString`, …). |
| `PythonAPI/pytuple_methods.c` | Tuple functions (`PyTuple_GetItem`, …) and the tuple-borrow ghost operations. |
| `PythonAPI/pylist_methods.c` | List functions (`PyList_GetItem`, `PyList_GetItemRef`, `PyList_SET_ITEM`, …). |
| `PythonAPI/pyerr_methods.c` | Error/exception functions (`PyErr_Occurred`, `PyErr_Clear`, `PyErr_SetString`, …). |
| `PythonAPI/gil.c` | GIL functions (`requires false`: releasing the GIL is unsound under the borrowed-reference model). |

## Case studies

Each case study in [`case_studies/`](case_studies/) is a directory containing a
`<name>.py` (the Nagini specification of the `@Native` function) and a
`<name>.c` (the C implementation, with the generated contract and proof
annotations) that verifies against the API formalization above.

| Directory | `@Native` function | What it exercises |
|-----------|--------------------|-------------------|
| `paper_example/` | `py_max` | **The running example of the paper** (Listing 1.1, specified in Listing 1.3). |
| `bincoeff/` | `compute_bincoeff` | **The GMPY2 / MPZ case study of the paper** (Sec. 5): a binomial-coefficient function computed with GMP's `mpz` integers. `mpz_include.c` holds the trusted `mpz` specification. |
| `attr_extraction/` | `replace_and_get` | Reading and writing object attributes. |
| `list_extraction/` | `list_extraction` | Reading an element out of a list (returning a new reference via `PyList_GetItemRef`). |
| `first_last_3_swap/` | `first_last_swap` | Swapping a value between an object attribute and a list element (list mutation with `PyList_SET_ITEM`). |

### Verifying a case study with VeriFast

The toolchain was developed against **VeriFast 25.06**. From a case-study
directory, most case studies verify with:

```
verifast -c <name>.c
```

The paper example additionally needs an LP64 data model (so that `long` is
64-bit and `LONG_MAX`/`LONG_MIN` match the spec bounds) and permission for
provably-unreachable defensive code (the input checks of Listing 1.1, which the
precondition makes dead). The required options are recorded in the file header;
verify it with:

```
verifast -read_options_from_source_file -allow_dead_code -c paper_example.c
```
