#! /usr/bin/env bash

# Lints code:
#
#   # Lint timedime by default.
#   ./scripts/lint.sh
#   # Lint specific files.
#   ./scripts/lint.sh asn4sql/somefile/*.py

set -euo pipefail

lint() {
    pylint "$@"
}

main() {
    if [[ "$#" -eq 0 ]]; then
        lint timedime
    else
        lint "$@"
    fi
}

main "$@"
