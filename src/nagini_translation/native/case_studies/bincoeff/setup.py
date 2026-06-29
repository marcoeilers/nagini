from setuptools import setup, Extension

# Build the verified compute_bincoeff as an importable CPython extension:
#   python setup.py build_ext --inplace
setup(
    name="bincoeff_native",
    version="0.1",
    ext_modules=[Extension("bincoeff_native", ["bincoeff_module.c"])],
)
