import os
import sys

import matplotlib

# The modules under test import pyplot at module level; CI has no display.
matplotlib.use('Agg')

# Challenge code imports its helpers relative to src/components
# (e.g. `from common import Spatial`, `from NES_interfaces import KGTRecords`).
COMPONENTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src', 'components'))
sys.path.insert(0, COMPONENTS_DIR)
