#!/usr/bin/env python3
"""Run the recall tests on the sim created by apply.py (full cue, 2/3-cell cues, cross-pattern mixes) and a
control on a second fresh copy with NO pruning/programming. Writes recall_results.json and demo_data.json."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import recipe_core
recipe_core.recall_main(os.path.dirname(os.path.abspath(__file__)), control=('--no-control' not in sys.argv))
