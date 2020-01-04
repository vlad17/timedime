"""
Compare two periods of time for changes in what you've done.
"""
import sys

from datetime import timedelta
import numpy as np
import pandas as pd
from absl import app, flags

from .. import log
from ..format_utils import indented_list
from ..interval import filter_range, find_intervals, hrs_bw
from ..tags import explode, df_filter
from ..utils import parse_date, pretty_date, splat


flags.DEFINE_string(
    "filter",
    None,
    "Filter down to events matching this string",
)
flags.DEFINE_string(
    "running_events",
    "./data/running.pkl",
    "path pointing to the existing store of data, " "this need not exist",
)
flags.DEFINE_string(
    "start1",
    None,
    "YYYY-MM-DD specification for begin of first range"
)
flags.DEFINE_string(
    "end1",
    None,
    "YYYY-MM-DD specification for end of first range"
)
flags.DEFINE_string(
    "start2",
    None,
    "YYYY-MM-DD specification for begin of second range"
)
flags.DEFINE_string(
    "end2",
    None,
    "YYYY-MM-DD specification for end of second range"
)
flags.DEFINE_float(
    "min_support",
    0.025,
    "Minimum support, inclusive, necessary for a category to be included"
    " in the view",
    lower_bound=0,
    upper_bound=1,
)
flags.mark_flag_as_required("start1")
flags.mark_flag_as_required("end1")
flags.mark_flag_as_required("start2")
flags.mark_flag_as_required("end2")

def format_percent(x):
    return '{:3.1%}'.format(x)

HOURS_WIDTH = 5

def format_hours(x):
    return ('{:' + str(HOURS_WIDTH) + '.1f}').format(x)


def _main(_argv):
    df = pd.read_pickle(flags.FLAGS.running_events)
    start1, end1, start2, end2 = (
        parse_date(x, start_of_day=False) for x in
        (flags.FLAGS.start1, flags.FLAGS.end1, flags.FLAGS.start2, flags.FLAGS.end2))
    df = filter_range(df, start1, end2)

    ef = explode(df)

    df, ef = df_filter(df, ef, flags.FLAGS.filter, keep=False)

    prev_df = filter_range(df, start1, end1)
    next_df = filter_range(df, start2, end2)

    print(
        "{} events in range {} - {}".format(
            len(prev_df),
        pretty_date(start1),
        pretty_date(end1),
    ))
    print(
        "{} events in range {} - {}".format(
            len(next_df),
        pretty_date(start2),
        pretty_date(end2),
    ))
    uncovered, _ = find_intervals(df, start1, end1)
    uncovered += find_intervals(df, start2, end2)[0]
    uncovered_hrs = sum(map(splat(hrs_bw), uncovered))
    range_hrs = hrs_bw(start1, end1) + hrs_bw(start2, end2)

    ndigits = len(str(int(range_hrs)))
    global HOURS_WIDTH
    HOURS_WIDTH = ndigits + 2 # decimal

    print(format_hours(uncovered_hrs),
          "hours of",
          format_hours(range_hrs),
          "uncovered (",
          format_percent(uncovered_hrs / range_hrs),
          "total)")

    nef = explode(next_df)
    pef = explode(prev_df)

    for c in nef.columns:
        if c not in pef.columns:
            pef[c] = np.zeros(len(pef), dtype=bool)


    for c in pef.columns:
        if c not in nef.columns:
            nef[c] = np.zeros(len(nef), dtype=bool)

    print('from prev to next, units are hours')

    ptot = prev_df.duration_hours.sum()
    ntot = next_df.duration_hours.sum()

    print('range 1 event hrs {:.0f} range 2 event hrs {:.0f}'.format(
        ptot, ntot))

    # Yes, this can be made much more efficient by caching 'x'
    # and then incrementally updating it instead of removing rows
    # associated with tags and restarting
    #
    # but completion > speed

    tot = 0 # here all incremental changes are mutex
    # (note how we're excerpting rows and keeping ptot, ntot the same)

    while True:

        jdf = pd.concat([prev_df, next_df])

        s = jdf.apply(lambda x: pd.Series(list(x["tags"]) + [x["summary"]]),axis=1).stack().reset_index(level=1, drop=True)
        s.name='tag'
        singles = jdf.drop('tags', axis=1).join(s)

        sprev = singles[singles.index.isin(prev_df.index)]
        snext = singles[singles.index.isin(next_df.index)]

        gbp = sprev[["tag", "duration_hours"]].groupby('tag').sum() / ptot
        gbn = snext[["tag", "duration_hours"]].groupby('tag').sum() / ntot

        x = gbn.combine(-gbp, lambda x, y: x + y, fill_value=0)
        x = x[x.index != '']

        x = x.reset_index()
        x["abs"] = np.abs(x["duration_hours"])

        if not len(x):
            break

        tag, hrs = x.sort_values('abs', ascending=False).iloc[0][["tag", "duration_hours"]]
        tot += hrs
        ptag = pef[tag]
        ntag = nef[tag]

        tag_prev_tot = prev_df[ptag].duration_hours.sum()
        tag_next_tot = next_df[ntag].duration_hours.sum()

        if abs(hrs) < flags.FLAGS.min_support:
            break

        print('{:+6.1%}'.format(hrs), tag, 'from', '{:4.1f} to {:4.1f}'.format(
            tag_prev_tot, tag_next_tot))

        prev_df = prev_df[~ptag]
        next_df = next_df[~ntag]
        pef = pef[~ptag]
        nef = nef[~ntag]

    print('{:+6.1%}'.format(hrs), 'other changes')

if __name__ == "__main__":
    app.run(_main)
