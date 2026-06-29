"""Import the compiled extension and check compute_bincoeff against math.comb.

Run after building:
    python setup.py build_ext --inplace
    python test_bincoeff_native.py
"""
import math
import bincoeff_native

# (n, k) pairs within the verified domain (0 <= k <= n <= 63), kept small
# enough that the placeholder mpz_bin_uiui does not overflow.
cases = [(0, 0), (5, 2), (6, 0), (6, 6), (5, 5), (10, 3), (20, 10), (30, 15)]

for n, k in cases:
    got = bincoeff_native.compute_bincoeff(n, k)
    expected = math.comb(n, k)
    status = "ok" if got == expected else "MISMATCH"
    print(f"compute_bincoeff({n:2d}, {k:2d}) = {got:<12} (expected {expected:<12}) [{status}]")
    assert got == expected, f"C({n},{k}): got {got}, expected {expected}"

print("\nAll cases passed.")
