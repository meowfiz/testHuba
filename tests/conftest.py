"""Put the repository root on sys.path so tests can import data_analyzer."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
