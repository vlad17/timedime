"""
Linear-time interval analysis -- find all the existing
intersections and empty spaces in time intervals.
"""

import operator
import itertools
from types import SimpleNamespace

from .utils import splat

def find_intervals(df, from_time, to_time):
    """
    Given a dataframe with unique interval indices,
    where each row has a start and end column
    containing pandas timestamps, compute
    the parsimonious lists of all the intervals
    between a given range that are the

    uncovered, overlaps

    where uncovered is a list of time pairs
    that are uncovered by the given time intervals
    and overlaps is a list of the time pairs
    that are covered by the given time intervals.

    from_time and to_time are the desired begin and ranges
    for consideration. They should be python datetimes.

    It's OK for events to intersect with the from/to values.
    """

    # TODO: could pre-filter for events overlapping with
    # [from, to)

    # a more efficient alternative could be to use flatMap
    # https://stackoverflow.com/questions/31080258
    endpoints = list(
        itertools.chain.from_iterable(
            (
                [
                    SimpleNamespace(
                        event_id=idx,
                        time=row.start.to_pydatetime(),
                        start=True,
                    ),
                    SimpleNamespace(
                        event_id=idx, time=row.end.to_pydatetime(), start=False
                    ),
                ]
                for idx, row in df.iterrows()
            )
        )
    )
    # crucially, starts first!
    endpoints.sort(key=lambda e: (e.time, not e.start))

    # O(n) algorithm to find maximal contiguous uncovered/doubled
    # intervals.

    uncovered = []
    overlaps = []
    stack_height = 0
    latest_active = from_time
    earliest_overlap = None
    for endpoint in endpoints:
        if endpoint.start:
            if stack_height == 0 and latest_active < endpoint.time:
                uncovered.append((latest_active, endpoint.time))
            elif stack_height == 1:
                earliest_overlap = endpoint.time
            stack_height += 1
        else:
            if stack_height == 1:
                latest_active = endpoint.time
            elif stack_height == 2:
                overlaps.append((earliest_overlap, endpoint.time))
            stack_height -= 1
    if (
        stack_height == 0
        and endpoints
        and not endpoint.start
        and endpoint.time < to_time
    ):
        uncovered.append((endpoint.time, to_time))

    overlaps = list(itertools.filterfalse(splat(operator.eq), overlaps))
    # uncovered should have no empty intervals due to the sort

    # post-process to remove out-of range stuff:
    def _outside_range(start, end):
        return end <= from_time or start >= to_time

    overlaps = list(itertools.filterfalse(splat(_outside_range), overlaps))
    uncovered = list(itertools.filterfalse(splat(_outside_range), uncovered))

    def _trim(tup):
        start, end = tup
        return max(start, from_time), min(end, to_time)

    overlaps = list(map(_trim, overlaps))
    uncovered = list(map(_trim, uncovered))

    return uncovered, overlaps

def filter_range(df, from_time, to_time):
    """
    Filter a dataframe of intervals with start and end members
    that are not intersecting with the given interval
    between the from and to times, inclusive.

    The pandas dataframe should contain pandas timestamps
    and the from/to times should be python datetime objects.
    """
    ix = (df.end <= from_time) | (df.start >= to_time)
    return df.loc[~ix]

def hrs_bw(begin, end):
    """
    Returns the floating point number of hours between
    the beginning and the end events.
    """
    return (end - begin).total_seconds() / 3600
