#!/usr/bin/env bash
set -euo pipefail
# Simple helper to run the CLI on the sample configuration
export PYTHONPATH=./src:${PYTHONPATH:-}
python3 src/cli.py --configs ./configs/sample --build-topology --validate --analyze-load --simulate --viz
