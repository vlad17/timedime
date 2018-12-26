"""
Logs in to Google.

Extracts calendar events between a specified range of
dates (ranges are expanded to include overlapping events).

Saves extracted features as a pandas dataframe in the specified
destination. Prints diagnostic information about the quality
of the data.
"""

import os
import operator
import heapq
import itertools
import re
from collections import defaultdict
from types import SimpleNamespace
import warnings
import pickle
import string
import sys
import logging
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
import dateutil.parser as parser
from absl import app, flags
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import client, file, tools

from .. import log

flags.DEFINE_string('begin', None, 'YYYY-MM-DD specification for begin of '
                    + 'fetch range (start of day)')
flags.mark_flag_as_required('begin')
flags.DEFINE_string('end', 'now', 'YYYY-MM-DD specification for begin of '
                    + 'fetch range (end of day)')
flags.DEFINE_boolean('verbose', True, 'whether to activate logging')
flags.DEFINE_string('dst', './data/new.pkl',
                    'path in which to save ingested input')
flags.DEFINE_string('credentials', '~/credentials.json',
                    'gcal API credentials')

def hrs_bw(begin, end):
    """
    Returns the floating point number of hours between
    the beginning and the end events.
    """
    return (end - begin).total_seconds() / 3600

def splat(f):
    return lambda x: f(*x)

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
    if datestr == 'now':
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

# Modifying this scope would require regenerating the gcal creds
# in /tmp/token.json
READONLY_GCAL = 'https://www.googleapis.com/auth/calendar.readonly'

GCAL_SERVICE = None

def init_gcal_service():
    global GCAL_SERVICE
    if GCAL_SERVICE:
        return

    logging.getLogger('googleapiclient').setLevel(logging.WARNING)

    tokenfile = '/tmp/token.json'

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        store = file.Storage(tokenfile)
        creds = store.get()
    if not creds or creds.invalid:
        log.debug('token in {} invalid or not found -- authenticating',
                  tokenfile)
        credfile = os.path.expanduser(flags.FLAGS.credentials)
        if not os.path.exists(credfile):
            raise ValueError(
                "Expected Google calendar API credentials to reside "
                   "in the file specified by the --credentials flag "
                   f"(currently {flags.FLAGS.credentials}), "
                   "but the file is not present. See the following page: "
                   "https://developers.google.com/calendar/quickstart/python")
        flow = client.flow_from_clientsecrets(credfile, READONLY_GCAL)
        ports = np.arange(0, 1000, 100) + 8080
        flow_flags = SimpleNamespace(
            auth_local_webserver=True,
            noauth_local_webserver=False,
            auth_host_port=ports.tolist(),
            logging_level='ERROR',
            auth_host_name="localhost")
        creds = tools.run_flow(flow, store, flags=flow_flags)
    GCAL_SERVICE = build('calendar', 'v3', http=creds.authorize(Http()), cache_discovery=False)

def _add_event(event, events):
    """Save event in the events lists"""
    start = event['start'].get('dateTime')
    end = event['end'].get('dateTime')
    start = start and parser.parse(start)
    end = end and parser.parse(end)
    if start and end:
        hrs = hrs_bw(start, end)
    else:
        hrs = np.nan

    raw_summary = event['summary']
    tags = extract_tags(raw_summary)
    summary = remove_tags(raw_summary)

    events["raw_json"].append(event)
    events["start"].append(start)
    events["end"].append(end)
    events["duration_hours"].append(hrs)
    events["raw_summary"].append(raw_summary)
    events["event_id"].append(event["id"])
    events["summary"].append(summary)
    events["tags"].append(tags)

def extract_tags(summary):
    # https://stackoverflow.com/questions/2852484
    return frozenset(re.findall(r'\[([^]]*)\]', summary))

def remove_tags(summary):
    summary = re.sub(r'\s+\[([^]]*)\]\s+', ' ', summary)
    summary = re.sub(r'\[([^]]*)\]\s+', ' ', summary)
    summary = re.sub(r'\s+\[([^]]*)\]', ' ', summary)
    return summary.strip()

def _main(_argv):
    log.init(flags.FLAGS.verbose)
    init_gcal_service()

    from_time = parse_date(flags.FLAGS.begin, start_of_day=True)
    to_time = parse_date(flags.FLAGS.end, start_of_day=True)

    log.debug("fetching events overlapping with time range {} - {}",
              pretty_date(from_time), pretty_date(to_time))

    # See documentation for GAPI call here
    # https://developers.google.com/calendar/v3/reference/events/list

    events = defaultdict(list)
    page_tok = None
    while True:
        events_result = GCAL_SERVICE.events().list(
            calendarId='primary', timeMin=from_time.isoformat(),
            timeMax=to_time.isoformat(), pageToken=page_tok,
            maxResults=2000, singleEvents=True,
            orderBy='startTime').execute()
        more_events = events_result.get('items', [])
        next_page = events_result.get('nextPageToken')
        for event in more_events:
            _add_event(event, events)
        log.debug('fetched {:5d} events', len(events["event_id"]))
        if not next_page:
            break

    log.debug('loaded  {:5d} events in the time range {} - {}',
              len(events["event_id"]), pretty_date(from_time), pretty_date(to_time))

    df = pd.DataFrame(events)
    assert df.event_id.nunique() == len(df)
    df = df.set_index('event_id')

    log.debug('missing start time {:.1%}', df.start.isna().mean())
    log.debug('missing end time   {:.1%}', df.end.isna().mean())

    df = df.dropna(subset=['start', 'end'])

    from_time = min(df.start.min().to_pydatetime(), from_time)
    to_time = max(df.end.max().to_pydatetime(), to_time)
    tot_hrs = hrs_bw(from_time, to_time)
    print('DIAGNOSTICS')
    print()
    print('expanded range for overlapping events')
    print('    begin  :', pretty_date(from_time))
    print('    end    :', pretty_date(to_time))
    print('    tot hrs: {:.1f}'.format(tot_hrs))

    # a more efficient alternative could be to use flatMap
    # https://stackoverflow.com/questions/31080258
    endpoints = list(
        itertools.chain.from_iterable(
            ([SimpleNamespace(event_id=idx, time=row.start.to_pydatetime(), start=True),
              SimpleNamespace(event_id=idx, time=row.end.to_pydatetime(), start=False)]
             for idx, row in df.iterrows())))
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
    if stack_height == 0 and endpoints \
       and not endpoint.start and endpoint.time < to_time:
        uncovered.append((endpoint.time, to_time))

    overlaps = list(itertools.filterfalse(splat(operator.eq), overlaps))
    # uncovered should have no empty intervals due to the sort

    uncovered_hrs = sum(map(splat(hrs_bw), uncovered))
    overlap_hrs = sum(map(splat(hrs_bw), overlaps))

    print()
    print('interval coverage analysis')
    print('    overlap hrs  : {:.1f} ({:.1%})'.format(overlap_hrs, overlap_hrs / tot_hrs))
    print('    uncovered hrs: {:.1f} ({:.1%})'.format(uncovered_hrs, uncovered_hrs / tot_hrs))
    print('    top overlapping intervals')
    for begin, end in heapq.nlargest(3, overlaps, key=splat(hrs_bw)):
        print('        {} - {}'.format(
            pretty_date(begin), pretty_date(end)))
    print('    top uncovered intervals')
    for begin, end in heapq.nlargest(3, uncovered, key=splat(hrs_bw)):
        print('        {} - {}'.format(
            pretty_date(begin), pretty_date(end)))

    print()
    print('tag quantity analysis')
    all_tags = set().union(*df.tags)
    print('    num unique tags:', len(all_tags))

    exploded = df.tags.apply(lambda x: pd.Series({tag: True for tag in x}))
    exploded = exploded.fillna(False)

    edf = df.join(exploded)

    tagcounts = {tag: edf[tag].mean() for tag in all_tags}
    print('    most popular tags by event count')
    for tag in heapq.nlargest(3, all_tags, key=tagcounts.get):
        print(' ' * 8 + '{:<15s}: {:.1%}'.format(tag, tagcounts[tag]))

    taghrs = {tag: (edf[tag] * edf.duration_hours).sum() for tag in all_tags}
    print('    most popular tags by event duration')
    for tag in heapq.nlargest(3, all_tags, key=taghrs.get):
        print(' ' * 8 + '{:<15s}: {:6.1f}'.format(tag, taghrs[tag]))


    saveloc = os.path.expanduser(flags.FLAGS.dst)
    log.debug('writing loaded data to {}{}',
              saveloc,
              ' (WARNING: file will be overwritten)' if os.path.exists(saveloc) else '')
    df.to_pickle(saveloc)

if __name__ == '__main__':
    app.run(_main)
