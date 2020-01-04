"""
Inspect events database and create a "drill-down" view for
a specified date range.
"""
import sys

import numpy as np
import pandas as pd
from absl import app, flags

from .. import log
from ..format_utils import indented_list
from ..interval import filter_range, find_intervals, hrs_bw
from ..tags import explode
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
flags.mark_flag_as_required("begin")
flags.DEFINE_string(
    "end",
    "now",
    "YYYY-MM-DD specification for begin of " + "fetch range (end of day)",
)
flags.DEFINE_float(
    "min_support",
    0.025,
    "Minimum support, inclusive, necessary for a category to be included"
    " in the drill-down view",
    lower_bound=0,
    upper_bound=1,
)


def _main(_argv):
    log.init()
    df = pd.read_pickle(flags.FLAGS.running_events)

    from_time = parse_date(flags.FLAGS.begin, start_of_day=True)
    to_time = parse_date(flags.FLAGS.end, start_of_day=False)

    df = filter_range(df, from_time, to_time)

    log.debug(
        "analyzing events in range {} - {}",
        pretty_date(from_time),
        pretty_date(to_time),
    )
    uncovered, _ = find_intervals(df, from_time, to_time)
    uncovered_hrs = sum(map(splat(hrs_bw), uncovered))
    range_hrs = hrs_bw(from_time, to_time)
    log.debug(
        "{:.1f} hours in range {:.1f} uncovered ({:.1%} total)",
        uncovered_hrs,
        range_hrs,
        uncovered_hrs / range_hrs,
    )

    ef = explode(df)
    log.debug(
        "found {} tags under current support count = {}", len(ef.columns), None
    )

    context_loop(df, ef, flags.FLAGS.min_support, max_values=9)


def get_context_df(df, ef, context):
    is_in_context = ef[context].prod(axis=1).astype(bool)
    df = df.loc[is_in_context]
    ef = ef.loc[is_in_context]
    ef = ef.drop(columns=context)
    sef = ef.sum(axis=0)
    ef.drop(columns=sef[sef == 0].index, inplace=True)
    return df, ef


def get_context_info(df, ef, cdf, cef):
    tot_hrs = df.duration_hours.sum()
    ctx_hrs = cdf.duration_hours.sum()
    ctx_hrs = (
        "ctx hrs",
        "{:.1f} ({:.1%} of total)".format(ctx_hrs, ctx_hrs / tot_hrs),
    )

    tot_events = len(df)
    ctx_events = len(cdf)
    ctx_events = (
        "ctx event count",
        "{:d} ({:.1%} of total)".format(ctx_events, ctx_events / tot_events),
    )

    tot_tags = len(ef.columns)
    ctx_tags = len(cef.columns)
    ctx_tags = (
        "ctx tag count",
        "{:d} ({:.1%} of total)".format(ctx_tags, ctx_tags / tot_tags),
    )

    return [ctx_hrs, ctx_events, ctx_tags]


def rank_by_popular_tag(df, ef, min_support, max_values):
    # this could be done all-sparse, but pandas flips to dense
    # frequently and this needs a delicate second pass for that first
    supports = ef.mean(axis=0)
    cols = list(ef.columns)
    cols.sort(key=lambda x: supports.at[x], reverse=True)
    ef = ef.loc[:, cols]
    ef = ef.replace(False, np.nan)
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


def context_loop(df, ef, min_support_show, max_values):
    """
    Given an event dataframe (as in ingest.py)
    along with its sparse binary tag dataframe ef (columns are tag indicators),
    run a "drill loop", which prints out the tag context
    and some stats, but then enables the user to drill down into the data.
    """
    context = []
    while True:
        print()
        cdf, cef = get_context_df(df, ef, context)
        pairs = get_context_info(df, ef, cdf, cef)
        print(indented_list(title="context {}".format(context), pairs=pairs))
        ranked_tags = []
        if not cdf.empty:
            ranked_tags, percentages = rank_by_popular_tag(
                cdf, cef, min_support_show, max_values
            )
            tagnames = map(splat("{} - {}".format), enumerate(ranked_tags, 1))

            # a popular-tag breakdown does the following:
            # for each item in the context, associate it with a single tag,
            # the most popular tag in its own set of tags.
            #
            # then just break down the overall distribution of most-popular-tags
            #
            # all categories are mutually exclusive in the sense of it being
            # their most popular tag, even if items from other tags might contain
            # selected tags that are simply not those items' most popular.
            print(
                indented_list(
                    title="popular-tag breakdown of context",
                    pairs=zip(tagnames, map("{:.1%}".format, percentages)),
                    indentation_level=1,
                )
            )

        result = drill_get_next(1, len(ranked_tags))
        if result == "q":
            return
        if result == "top":
            context = []
            continue
        if result == "up":
            context.pop()
            continue
        assert isinstance(result, int), result
        if ranked_tags[result - 1] not in ef.columns:
            print("---> cannot break this down further")
            continue
        context.append(ranked_tags[result - 1])


def drill_get_next(lo, hi):
    while True:
        print("drill [{}..{}/up/top/q]? ".format(lo, hi), end="")
        sys.stdout.flush()
        try:
            selection = input()
        except EOFError:
            selection = "q"
        if selection in ["up", "top", "q"]:
            return selection
        try:
            selection = int(selection)
            if selection >= lo and selection <= hi:
                return selection
        except:
            pass


if __name__ == "__main__":
    app.run(_main)
