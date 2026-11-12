#!/usr/bin/env python3
"""Load a FRESH copy of the pristine saved model into a NEW NES simulation, apply weights.json, verify every pair by read-back.
Usage (from anywhere):  PYTHONPATH=<PythonClient> <venv>/bin/python apply.py
Writes apply_report.json (contains the new sim id used by recall_test.py)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import recipe_core
r = recipe_core.apply_main(os.path.dirname(os.path.abspath(__file__)))
sys.exit(0 if r['ok'] else 1)
