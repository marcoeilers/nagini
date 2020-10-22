from nagini_contracts.contracts import *
from typing import List


def encrypt(cipher: List[int], plain: int, key: int) -> bool:
    Requires(list_pred(cipher) and len(cipher) == 0)
    Ensures(list_pred(cipher) and len(cipher) == 1)
    Ensures(Low(Result()))
    Ensures(Implies(not Result(), Low(cipher[0])))
    cipher.append(plain + key)
    Declassify(plain + key)
    return False


def decrypt(plain: List[int], cipher: int, key: int) -> bool:
    Requires(Low(cipher))
    Requires(list_pred(plain) and len(plain) == 1)
    Ensures(list_pred(plain) and len(plain) == 1)
    Ensures(Implies(Result(), Low(plain[0])))
    Ensures(Low(Result()))
    plain[0] = cipher - key
    return False


def secure(plaintext: int, key: int) -> int:
    Ensures(Low(Result()))
    ciphertext = []  # type: List[int]
    res = encrypt(ciphertext, plaintext, key)
    if res:
        ciphertext[0] = 0
    else:
        copy = [plaintext]
        if decrypt(copy, ciphertext[0], key):
            ciphertext = copy
    return ciphertext[0]
