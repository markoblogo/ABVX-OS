#!/usr/bin/env python3
"""Import an authenticated runtime content receipt; public-page review is owner-optional."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from abvx_harness.runtime_publication import main
main(sys.argv[1:],ROOT)
