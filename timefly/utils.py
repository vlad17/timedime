"""
Generic utilities file.
"""

from datetime import datetime, timedelta, timezone
from functools import reduce

# https://stackoverflow.com/questions/16739290


def splat(f):
    """pre-splat an argument into a function and return the new lambda"""
    return lambda x: f(*x)


def compose2(f, g):
    return lambda *a, **kw: f(g(*a, **kw))


def compose(*fs):
    return reduce(compose2, fs)


def parse_date(datestr, start_of_day):
    """
    Converts a date YYYY-MM-DD into the datetime associated
    with the start of the day if start_of_day (else the last second of
    that day).

    The special value "now" is also allowed, in which case the current
    timestamp is returned.

    All times UTC, but start of day / end of day are relative to the
    current timezone.
    """
    if datestr == "now":
        return datetime.now(timezone.utc)
    parsed = datetime.strptime(datestr, "%Y-%m-%d")
    parsed = parsed.astimezone()
    if start_of_day:
        return parsed.astimezone(timezone.utc)
    parsed += timedelta(hours=23, minutes=59, seconds=99)
    return parsed.astimezone(timezone.utc)


def pretty_date(dt):
    """
    Formats a datetime instance, which can be none, in the local TZ
    """
    if not dt:
        return "<unk date>"
    return dt.astimezone().strftime("%Y-%m-%d %I:%M%p %Z")
