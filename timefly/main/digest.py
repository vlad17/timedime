"""
Create a textual digest of a single time period.
"""
import sys

import numpy as np
import pandas as pd
from absl import app, flags

from .. import log
from ..format_utils import indented_list
from ..interval import filter_range, find_intervals, hrs_bw
from ..tags import expand_explode, explode
from ..utils import parse_date, pretty_date, splat

flags.DEFINE_string(
    "running_events",
    "./data/running.pkl",
    "path pointing to the existing store of data, " "this need not exist",
)
flags.DEFINE_string(
    "begin",
    None,
    "YYYY-MM-DD specification for begin of " + "fetch range (start of day)",
)
flags.DEFINE_string(
    "end",
    "now",
    "YYYY-MM-DD specification for begin of " + "fetch range (end of day)",
)
flags.DEFINE_float(
    "min_support",
    0.05,
    "Minimum support, inclusive, necessary for a category to be included"
    " in the drill-down view",
    lower_bound=0,
    upper_bound=1,
)

HOURS_WIDTH = 5

def format_percent(x):
    return '{:3.1%}'.format(x)

def format_hours(x):
    return ('{:' + str(HOURS_WIDTH) + '.1f}').format(x)

def _main(_argv):
    log.init()
    df = pd.read_pickle(flags.FLAGS.running_events)

    from_time = parse_date(flags.FLAGS.begin, start_of_day=True)
    to_time = parse_date(flags.FLAGS.end, start_of_day=False)

    df = filter_range(df, from_time, to_time)

    print(
        "events in range {} - {}".format(
        pretty_date(from_time),
        pretty_date(to_time),
    ))
    uncovered, _ = find_intervals(df, from_time, to_time)
    uncovered_hrs = sum(map(splat(hrs_bw), uncovered))
    range_hrs = hrs_bw(from_time, to_time)

    ndigits = len(str(int(range_hrs)))
    global HOURS_WIDTH
    HOURS_WIDTH = ndigits + 2 # decimal

    print(format_hours(uncovered_hrs),
          "hours of",
          format_hours(range_hrs),
          "uncovered (",
          format_percent(uncovered_hrs / range_hrs),
          "total)")

    ef = explode(df)
    print(
        "found {} tags in range".format(len(ef.columns))
    )

    print_context(df, ef, [], 1.0)

def print_context(df, ef, context, frac):

    cdf, cef = get_context_df(df, ef, context)
    if cdf is None and cef is None:
        # base case
        return

    cef = expand_explode(cdf, cef)

    min_support = flags.FLAGS.min_support / frac
    max_values = int(np.ceil(1 / min_support))
    ranked_tags, percentages = rank_by_popular_tag(
        cdf, cef, min_support, max_values
    )

    ranked_tags_print = list(ranked_tags)
    percentages_print = list(percentages)

    if ranked_tags_print == ["<unk>"]:
        return


    if len(percentages):
        ranked_tags_print.append("other")
        percentages_print.append(1 - percentages.sum())

    percentages_print = [
        '{:.1%}'.format(p)
        for p in percentages_print]

    lines = indented_list(
        pairs=zip(percentages_print, ranked_tags_print),
        join=False,
        sep=' ',
        indentation_level=len(context))

    for line, percent, tag in zip(lines, percentages, ranked_tags):
        print(line)
        if percent >= flags.FLAGS.min_support:
            print_context(df, ef, context + [tag], frac * percent)

    if len(percentages):
        print(lines[-1])

def get_context_df(df, ef, context):
    if any(c not in ef.columns for c in context):
        # one of the tags was a description; short circuit
        return None, None
    is_in_context = ef[context].prod(axis=1).astype(bool)
    df = df.loc[is_in_context]
    ef = ef.loc[is_in_context]
    ef = ef.drop(columns=context)
    sef = ef.sum(axis=0)
    ef.drop(columns=sef[sef == 0].index, inplace=True)
    return df, ef

def rank_by_popular_tag(df, ef, min_support, max_values):
    # this could be done all-sparse, but pandas flips to dense
    # frequently and this needs a delicate second pass for that first
    supports = ef.mean(axis=0)
    cols = list(ef.columns)
    cols.sort(key=lambda x: supports.at[x], reverse=True)
    ef = ef.loc[:, cols]
    ef = ef.to_dense().replace(False, np.nan)
    ef = ef * np.arange(1, len(cols) + 1, dtype=int)
    ef = ef.min(axis=1)
    ef = ef.fillna(0).astype(int)
    ef = ef.replace(list(range(len(cols) + 1)), ["<unk>"] + cols)

    # count hrs
    hrs_by_tag = df.duration_hours.groupby(ef).sum()

    percent_by_tag = hrs_by_tag / hrs_by_tag.sum()
    percent_by_tag = percent_by_tag[percent_by_tag >= min_support]
    percent_by_tag.sort_values(ascending=False, inplace=True)
    percent_by_tag = percent_by_tag.iloc[:max_values]

    return percent_by_tag.index, percent_by_tag.values


if __name__ == "__main__":
    flags.mark_flag_as_required("begin")
    app.run(_main)
