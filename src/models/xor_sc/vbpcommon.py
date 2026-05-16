# Enable common components used by multiple models:
import argparse
from sys import path
from pathlib import Path
path.insert(0, str(Path(__file__).parent.parent.parent)+'/components')

def ParseBool(value):
    if isinstance(value, bool):
        return value

    normalized = value.lower()
    if normalized in ("true", "1", "yes", "on"):
        return True
    if normalized in ("false", "0", "no", "off"):
        return False

    raise argparse.ArgumentTypeError("Expected a boolean value")
