#!/bin/bash
# Runs every server test. Each test is its own small program that loads main.py with stand-ins for FastAPI,
# pydantic and the settings (tests/stubs), and a pretend AI, so nothing real is called and no keys are needed.
# Any failure fails the whole run, and GitHub marks the commit red; Render then does not deploy it
# (Render: Settings, Auto-Deploy, "After CI Checks Pass").
cd "$(dirname "$0")/.." || exit 1
fail=0
for t in tests/test_*.py; do
  out=$(PYTHONPATH=tests/stubs:. timeout 180 python3 "$t" 2>&1)
  if [ $? -eq 0 ]; then echo "PASS $(basename "$t"): $(echo "$out" | grep -v '^INFO\|^WARNING' | tail -1)"
  else echo "FAIL $(basename "$t")"; echo "$out" | tail -25; fail=1; fi
done
exit $fail
