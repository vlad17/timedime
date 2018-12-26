# timedime

## Setup

See `setup.py` for necessary python packages. Requires a linux x64 box.

```
conda create -y -n timedime-env python=3.6
source activate timedime-env
pip install --no-cache-dir --editable .
```

## Scripts

All scripts are available in `scripts/`, and should be run from the repo root in the `timedime-env`.

| script | purpose |
| ------ | ------- |
| `lint.sh` | invokes `pylint` with the appropriate flags for this repo |
| `format.sh` | auto-format the entire `timedime` directory |

## Example

All mainfiles are documented. Run `python -m timedime.main.* --help` for any `*` for details.

```
python -m timedime.main.ingest --help
```
