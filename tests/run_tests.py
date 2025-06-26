#!/usr/bin/env python3
"""
Test runner for PolyhedronEmu utility modules.
Discovers and runs all tests in the tests directory.
"""

import unittest
import sys
import os

from server.logger import cleanup_old_logs


# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def run_tests():
    """Discover and run all tests."""
    cleanup_old_logs("logs")
    cleanup_old_logs("tests/logs")

    test_dir = os.path.dirname(__file__)

    loader = unittest.TestLoader()
    start_dir = test_dir
    pattern = "test_*.py"

    suite = loader.discover(start_dir, pattern)

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)
