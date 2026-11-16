"""
Copyright (c) 2026 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""


"""
Compression of recorded SMT state: the backend's session logs and bundles
(``--smtStateDir``) become zstd files (``name.zst``, read with ``zstd -dc``).

    python -m nagini_translation.smt_archive DIR...   compress what is left raw under DIR
"""


import os
import sys

import zstandard


RAW_SUFFIXES = ('.smt2', '.txt')
LEVEL = 3


def compress_file(path: str) -> None:
    """Replace ``path`` by ``path.zst``; the raw file goes once the compressed
    one is complete."""
    tmp = path + '.zst.tmp'
    with open(path, 'rb') as src, open(tmp, 'wb') as dst:
        zstandard.ZstdCompressor(level=LEVEL).copy_stream(src, dst)
    os.replace(tmp, path + '.zst')
    os.remove(path)


def compress_dir(smtstate_dir: str) -> int:
    """Compress the raw files of one SMT state dir; returns how many."""
    n = 0
    for name in sorted(os.listdir(smtstate_dir)):
        path = os.path.join(smtstate_dir, name)
        if name.endswith(RAW_SUFFIXES) and os.path.isfile(path):
            compress_file(path)
            n += 1
    return n


def compress_tree(root: str) -> int:
    """Compress every raw file of the SMT state dirs under ``root``: archived
    attempts' ``smtstate`` and the ``.smtstate-*`` dirs verifications that were
    killed left behind."""
    n = 0
    for parent, dirs, _ in os.walk(root):
        for d in dirs:
            if d == 'smtstate' or d.startswith('.smtstate-'):
                n += compress_dir(os.path.join(parent, d))
    return n


def main() -> None:
    for root in sys.argv[1:]:
        print('{}: compressed {} file(s)'.format(root, compress_tree(root)))


if __name__ == '__main__':
    main()
