#!/usr/bin/env python3
"""Reproduce manuscript tables/figures from logs, and optionally run the synthetic pipeline."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def run(cmd):
    print("+", " ".join(cmd))
    subprocess.check_call(cmd, cwd=ROOT)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--from-logs", action="store_true", default=True, help="Regenerate tables and Figs. 3–7 from results/paper")
    p.add_argument("--demo", action="store_true", help="Train on synthetic speaker-independent data and write results/demo")
    p.add_argument("--skip-figures", action="store_true")
    args = p.parse_args()
    if args.from_logs:
        run([sys.executable, str(ROOT / "tables" / "make_tables.py")])
        if not args.skip_figures:
            run([sys.executable, str(ROOT / "figures" / "make_figures.py")])
    if args.demo:
        sys.path.insert(0, str(ROOT))
        from lstm_eholf.run_demo import run_all_demo

        path = run_all_demo(ROOT / "results" / "demo")
        print("demo logs:", path)


if __name__ == "__main__":
    main()
