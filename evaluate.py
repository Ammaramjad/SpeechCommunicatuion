#!/usr/bin/env python3
"""Evaluate a trained MR-AVT checkpoint, optionally with robustness sweeps."""

import sys

from mr_avt.engine import main

if __name__ == "__main__":
    if "--eval-only" not in sys.argv:
        sys.argv.append("--eval-only")
    main()
