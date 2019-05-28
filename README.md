# timefly

This module, `timefly`, helps you keep track of where you're spending your time.
It's pretty specific to how I've set up my calendar. You'll likely not get much use
out of this unless you use your calendar the same way.

For *literally* every hour of your day, record what you're doing and tag it appropriately.

These scripts only look at the `summary` field, which is specified by the "Event Title" field
in the calendar application. If you tag your events with square bracket tags, then this package
can do a little bit of analysis for you.

For instance, you might create an event called `[health] sleep` from 11PM to 7AM, followed by
`[transportation] go to work` from 7AM to 8AM, and then another one called
`[work] [do some coding] new feature push` from 8AM to 5PM. This can handle multiple tags
and tags with spaces in them. Just don't do dumb shit like `[ [] i ] do Q][A`.

## Setup

Only tested on linux. To install the enviornment:

```
conda env create -f environment.yaml
```

To activate the environment:

```
conda activate timefly-env
```

To update deps:

```
conda env export > environment.yaml
```



## Scripts

All scripts are available in `scripts/`, and should be run from the repo root in the `timefly-env`.

| script | purpose |
| ------ | ------- |
| `format.sh` | auto-format the entire `timefly` directory |

## Example

All mainfiles are documented. Run `python -m timefly.main.* --help` for any `*` for details.

```{bash}
python -m timefly.main.ingest --begin 2018-12-01
# outputs the following
# 
# [2018-12-25 18:13:26 PST timefly/main/ingest.py:169] fetching events overlapping with time range 2018-12-01 12:00AM PST - 2018-12-25 06:13PM PST
# [2018-12-25 18:13:27 PST timefly/main/ingest.py:186] fetched   416 events
# [2018-12-25 18:13:27 PST timefly/main/ingest.py:191] loaded    416 events in the time range 2018-12-01 12:00AM PST - 2018-12-25 06:13PM PST
# [2018-12-25 18:13:27 PST timefly/main/ingest.py:197] missing start time 0.0%
# [2018-12-25 18:13:27 PST timefly/main/ingest.py:198] missing end time   0.0%
# DIAGNOSTICS
# 
# expanded range for overlapping events
#     begin  : 2018-11-30 06:00PM PST
#     end    : 2018-12-25 06:30PM PST
#     tot hrs: 600.5
# 
# interval coverage analysis
#     overlap hrs  : 6.0 (1.0%)
#     uncovered hrs: 0.0 (0.0%)
#     top overlapping intervals
#         2018-12-03 01:00PM PST - 2018-12-03 02:00PM PST
#         2018-12-10 01:00PM PST - 2018-12-10 02:00PM PST
#         2018-12-14 03:00PM PST - 2018-12-14 04:00PM PST
#     top uncovered intervals
# 
# tag quantity analysis
#     num unique tags: 31
#     most popular tags by event count
#         sisu           : 34.6%
#         health         : 22.4%
#         fun            : 12.3%
#     most popular tags by event duration
#         health         :  247.0
#         sisu           :  175.2
#         fun            :   81.5
# [2018-12-25 18:13:27 PST timefly/main/ingest.py:290] writing loaded data to ./data/new.pkl (WARNING: file will be overwritten)

python -m timefly.main.merge

python -m timefly.main.digest --begin 2019-05-18

# python -m timefly.main.drill --begin 2019-05-01
```

# TODO

* move `rank_by_popular_tag` from `versus.py` into `tags.py`, reuse in `drill` and `digest`.
