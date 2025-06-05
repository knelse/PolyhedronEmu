#!/usr/bin/env python3
"""
Test runner for PolyhedronEmu utility modules.
Discovers and runs all tests in the tests directory.
"""

import unittest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def run_tests():
    """Discover and run all tests."""
    # Get the directory containing this script
    test_dir = os.path.dirname(__file__)

    # Discover all test files
    loader = unittest.TestLoader()
    start_dir = test_dir
    pattern = "test_*.py"

    suite = loader.discover(start_dir, pattern)

    # Run the tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Return exit code based on test results
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)
