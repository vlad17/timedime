#! /usr/bin/env bash

# Lints code:
#
#   # Lint timedime by default.
#   ./scripts/lint.sh
#   # Lint specific files.
#   ./scripts/lint.sh timedime/somefile/*.py

set -euo pipefail

lint() {
    flake8 "$@"
}

main() {
    if [[ "$#" -eq 0 ]]; then
        lint timedime
    else
        lint "$@"
    fi
}

main "$@"
