"""Cross-platform test runner for LongImageOCR."""

import os
import sys
import unittest
from pathlib import Path

# Add project root to sys.path dynamically
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

loader = unittest.TestLoader()
suite = loader.discover(start_dir=str(project_root / "tests"), pattern="test_*.py")

runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(suite)

if not result.wasSuccessful():
    sys.exit(1)
