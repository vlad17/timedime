# timedime

This module, `timedime`, helps you keep track of where your spending your time.
It's pretty specific to how I've set up your calendar. You'll likely not get much use
out of this unless you use your calendar the same way.

For *literally* every hour of your day, record what you're doing and tag it appropriately.

These scripts only look at the `summary` field, which is specified by the "Event Title" field
in the calendar application. If tag your events with square bracket tags, then this package
can do a little bit of analysis for you.

For instance, you might create an event called `[health] sleep` from 11PM to 7AM, followed by
`[transportation] go to work` from 7AM to 8AM, and then another one called
`[work] [do some coding] new feature push` from 8AM to 5PM. This can handle multiple tags
and tags with spaces in them. Just don't do dumb shit like `[ [] i ] do Q][A`.

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
