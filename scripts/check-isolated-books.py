#!/usr/bin/env python3
"""Run book regressions while denying every access to operational book data."""
import builtins
import io
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'tests')]
real_open, real_io_open = builtins.open, io.open
protected = [(ROOT / name).resolve() for name in ('books', 'book-radar')]


def guarded(opener):
    def open_file(file, *args, **kwargs):
        if isinstance(file, (str, bytes, Path)):
            path = Path(file).resolve()
            if any(path == base or base in path.parents for base in protected):
                raise AssertionError(f'Operational data access in isolated suite: {path.relative_to(ROOT)}')
        return opener(file, *args, **kwargs)
    return open_file


if __name__ == '__main__':
    with patch('builtins.open', guarded(real_open)), patch('io.open', guarded(real_io_open)):
        suite = unittest.TestSuite()
        for name in ('test_book_core', 'test_book_radar_prior', 'test_book_radar_reachability',
                     'test_book_three_orchestrator', 'test_gate_a'):
            suite.addTests(unittest.defaultTestLoader.loadTestsFromName(name))
        result = unittest.TextTestRunner(verbosity=1).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)
