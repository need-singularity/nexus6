#!/bin/bash
# Run all n6-replication tests
# Usage: ./run-tests.sh           (local, tier1 only — no install needed)
#        docker build -t n6 . && docker run n6  (Docker, all tests)
set -e
cd "$(dirname "$0")"
python -m pytest tests/tier1/ -v --tb=short
echo "All tests passed!"
