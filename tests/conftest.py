"""Pytest bootstrap: make the repo root importable.

Prevents the failure where "pytest" collects tests/ (a plain directory, no
__init__.py) and only tests/ lands on sys.path, so "import data_analyzer"
raises ModuleNotFoundError depending on the directory pytest was started from.
"""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)
