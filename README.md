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

See the [Example section](#example) below.

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
# load all data from gcal from given date (default --end is now)
# stores to ./data/new.pkl by default
python -m timefly.main.ingest --begin 2018-12-01

# merge new data from ./data/new.pkl into ./data/running.pkl
python -m timefly.main.merge

# overview of my work-related time spend over the last 4 months
# use timefly.main.drill for an interactive version
FOUR_MONTHS_AGO=$(date --date="$(date) -4 month" "+%Y-%m-%d")
python -m timefly.main.digest --begin $FOUR_MONTHS_AGO --filter sisu

ONE_MONTH_AGO=$(date --date="$(date) -1 month" "+%Y-%m-%d")
TODAY=$(date "+%Y-%m-%d")
# over those last 4 months, how did time spend fraction change from
# the previous 3 to the most recent one?
python -m timefly.main.versus --start1 $FOUR_MONTHS_AGO  --end1 $ONE_MONTH_AGO --start2 $ONE_MONTH_AGO --end2 $TODAY --filter sisu
```

Example outputs for digest (here, with `--min_support 0.5`)
```
events in range 2019-09-03 12:00AM PDT - 2020-01-03 07:45PM PST
  30.5 hours of 2948.8 uncovered ( 1.0% total)
only keeping 35.18% of rows matching sisu
found 656 tags in range
100.0% sisu
  21.1% recruiting
  19.3% software engineering
    54.0% coding
      54.8% machine learning
      45.2% other
    46.0% other
  13.8% solutions engineering
    64.6% [redacted]
    35.4% other
  13.7% machine learning
  8.4%  meeting
  23.8% other
0.0%   other
```
Example outputs for versus (here, with `--min_support 0.5`)
```
only keeping 35.01% of rows matching sisu
558 events in range 2019-09-04 12:00AM PDT - 2019-12-04 12:00AM PST
123 events in range 2019-12-04 12:00AM PST - 2020-01-04 12:00AM PST
[redacted]
from prev to next, units are hours
range 1 event hrs 644 range 2 event hrs 135
+30.8% [redacted] from 44.8 to 51.0
-13.8% machine learning from 153.2 to 13.5
-12.3% software engineering from 98.2 to  4.0
 +5.8% [redacted] from  0.5 to  8.0
 -5.5% solutions engineering from 35.5 to  0.0
 +4.8% other changes
```

Here's an excerpt from my calendar, which actually contains this data. You can see me trying to sleep in on Saturday:

![calendar](cal.png)

_Doesn't tracking at this granularity make you insane?_ I suppose it depends on the person. I don't keep accurate records when I'm on `[vacation]`.

# TODO

* move `rank_by_popular_tag` from `versus.py` into `tags.py`, reuse in `drill` and `digest`.
