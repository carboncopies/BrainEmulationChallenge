#!/usr/bin/env python3
"""
Byte-compile every Python file in the repo so syntax errors fail CI.

Files listed in KNOWN_BROKEN already fail to compile on main. They are
reported but do not fail the job, so that any *new* breakage still does.
Remove an entry once its file is fixed (the job fails if a listed file
starts compiling, so the list cannot go stale).
"""

import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

SKIP_DIRS = {'.git', 'venv', '.venv', 'PythonClient', 'graphify', 'graphify-out', '__pycache__'}

KNOWN_BROKEN = {
    # Unresolved `git stash pop` conflict markers committed in d7faad9.
    'src/models/xor_scnm/dashboard.py',
    'src/models/xor_scnm/dashboard_scoring.py',
    # 2023 prototypes that have never compiled.
    'src/components/NES_interfaces/NES_AMPA_Receptor.py',
    'src/components/NES_interfaces/NMDA_Receptor.py',
    'src/components/prototyping/NMDA_Receptor.py',
    'src/models/e3_aifinch/aifinch_vbp1_acquisition.py',
}


def python_files():
    for dirpath, dirnames, filenames in os.walk(REPO_ROOT):
        # Don't follow symlinked dirs (src/components/*/BrainGenix -> PythonClient).
        dirnames[:] = sorted(
            d for d in dirnames
            if d not in SKIP_DIRS and not os.path.islink(os.path.join(dirpath, d))
        )
        for name in sorted(filenames):
            if name.endswith('.py'):
                yield os.path.relpath(os.path.join(dirpath, name), REPO_ROOT)


def main():
    new_errors = []
    now_fixed = []
    checked = 0
    for rel in python_files():
        checked += 1
        with open(os.path.join(REPO_ROOT, rel), 'rb') as f:
            source = f.read()
        try:
            compile(source, rel, 'exec', dont_inherit=True)
            if rel in KNOWN_BROKEN:
                now_fixed.append(rel)
        except (SyntaxError, ValueError) as e:
            if rel in KNOWN_BROKEN:
                print('KNOWN BROKEN (ignored): %s' % rel)
            else:
                new_errors.append((rel, '%s: %s' % (type(e).__name__, e)))

    print('Checked %d files.' % checked)
    for rel, msg in new_errors:
        print('\nSYNTAX ERROR: %s\n%s' % (rel, msg))
    for rel in now_fixed:
        print('\n%s compiles now; remove it from KNOWN_BROKEN in %s' % (rel, os.path.relpath(__file__, REPO_ROOT)))
    return 1 if new_errors or now_fixed else 0


if __name__ == '__main__':
    sys.exit(main())
