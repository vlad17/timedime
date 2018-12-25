# timedime

## Setup

See `setup.py` for necessary python packages. Requires a linux x64 box.

```
conda create -y -n timedime-env python=3.6
source activate timedime-env
```

## Scripts

All scripts are available in `scripts/`, and should be run from the repo root in the `timedime-env`.

| script | purpose |
| ------ | ------- |
| `lint.sh` | invokes `pylint` with the appropriate flags for this repo |
| `format.sh` | auto-format the entire `timedime` directory |

## Example

All mainfiles are documented. Run `python timedime/main/*.py --help` for any `*` for details.

