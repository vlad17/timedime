#!/bin/bash
# ./scripts/format.sh [--check]
# automatically formats all files in place

set -e

if [ "$1" = "--check" ] ; then
    black --line-length 79 --py36 --verbose --check timedime
    sed -ns '${/./F}' **/*.{py,sh}
else
    black --line-length 79 --py36 --verbose timedime
    sed -i -e '$a\' **/*.{py,sh}
fi
