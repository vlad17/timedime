"""
Logs in to Google.

Extracts calendar events between a specified range of
dates (ranges are expanded to include overlapping events).

Saves extracted features as a pandas dataframe in the specified
destination. Prints diagnostic information about the quality
of the data.
"""

import heapq
import itertools
from functools import partial
import logging
import os
import re
import warnings
from collections import defaultdict
from datetime import timezone
from types import SimpleNamespace

import dateutil.parser as parser
import numpy as np
import pandas as pd
from absl import app, flags
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import client, file, tools

from .. import log
from ..tags import explode
from ..interval import find_intervals, hrs_bw
from ..format_utils import indented_list
from ..utils import splat, compose, parse_date, pretty_date


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
flags.DEFINE_string(
    "dst", "./data/new.pkl", "path in which to save ingested input"
)
flags.DEFINE_string(
    "credentials", "~/credentials.json", "gcal API credentials"
)


# Modifying this scope would require regenerating the gcal creds
# in /tmp/token.json
READONLY_GCAL = "https://www.googleapis.com/auth/calendar.readonly"

GCAL_SERVICE = None


def init_gcal_service():
    global GCAL_SERVICE
    if GCAL_SERVICE:
        return

    logging.getLogger("googleapiclient").setLevel(logging.WARNING)

    tokenfile = "/tmp/token.json"

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        store = file.Storage(tokenfile)
        creds = store.get()
    if not creds or creds.invalid:
        log.debug(
            "token in {} invalid or not found -- authenticating", tokenfile
        )
        credfile = os.path.expanduser(flags.FLAGS.credentials)
        if not os.path.exists(credfile):
            raise ValueError(
                "Expected Google calendar API credentials to reside "
                "in the file specified by the --credentials flag "
                f"(currently {flags.FLAGS.credentials}), "
                "but the file is not present. See the following page: "
                "https://developers.google.com/calendar/quickstart/python"
            )
        flow = client.flow_from_clientsecrets(credfile, READONLY_GCAL)
        ports = np.arange(0, 1000, 100) + 8080
        flow_flags = SimpleNamespace(
            auth_local_webserver=True,
            noauth_local_webserver=False,
            auth_host_port=ports.tolist(),
            logging_level="ERROR",
            auth_host_name="localhost",
        )
        creds = tools.run_flow(flow, store, flags=flow_flags)
    GCAL_SERVICE = build(
        "calendar", "v3", http=creds.authorize(Http()), cache_discovery=False
    )


def _add_event(event, events):
    """Save event in the events lists"""
    start = event["start"].get("dateTime")
    end = event["end"].get("dateTime")
    start = start and parser.parse(start)
    end = end and parser.parse(end)
    if start and end:
        hrs = hrs_bw(start, end)
    else:
        hrs = np.nan

    raw_summary = event["summary"]
    tags = extract_tags(raw_summary)
    summary = remove_tags(raw_summary)

    events["raw_json"].append(event)
    events["start"].append(start.astimezone(timezone.utc))
    events["end"].append(end.astimezone(timezone.utc))
    events["duration_hours"].append(hrs)
    events["raw_summary"].append(raw_summary)
    events["event_id"].append(event["id"])
    events["summary"].append(summary)
    events["tags"].append(tags)


def extract_tags(summary):
    # https://stackoverflow.com/questions/2852484
    return frozenset(re.findall(r"\[([^]]*)\]", summary))


def remove_tags(summary):
    summary = re.sub(r"\s+\[([^]]*)\]\s+", " ", summary)
    summary = re.sub(r"\[([^]]*)\]\s+", " ", summary)
    summary = re.sub(r"\s+\[([^]]*)\]", " ", summary)
    return summary.strip()


def _main(_argv):
    log.init()
    init_gcal_service()

    from_time = parse_date(flags.FLAGS.begin, start_of_day=True)
    to_time = parse_date(flags.FLAGS.end, start_of_day=False)

    log.debug(
        "fetching events overlapping with time range {} - {}",
        pretty_date(from_time),
        pretty_date(to_time),
    )

    # See documentation for GAPI call here
    # https://developers.google.com/calendar/v3/reference/events/list

    events = defaultdict(list)
    page_tok = None
    while True:
        events_result = (
            GCAL_SERVICE.events()
            .list(
                calendarId="primary",
                timeMin=from_time.isoformat(),
                timeMax=to_time.isoformat(),
                pageToken=page_tok,
                maxResults=2000,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        more_events = events_result.get("items", [])
        next_page = events_result.get("nextPageToken")
        for event in more_events:
            _add_event(event, events)
        log.debug("fetched {:5d} events", len(events["event_id"]))
        if not next_page:
            break

    log.debug(
        "loaded  {:5d} events in the time range {} - {}",
        len(events["event_id"]),
        pretty_date(from_time),
        pretty_date(to_time),
    )

    df = pd.DataFrame(events)
    df.start = pd.to_datetime(df.start)
    df.end = pd.to_datetime(df.end)
    assert df.event_id.nunique() == len(df)
    df = df.set_index("event_id")

    log.debug("missing start time {:.1%}", df.start.isna().mean())
    log.debug("missing end time   {:.1%}", df.end.isna().mean())

    df = df.dropna(subset=["start", "end"])

    from_time = from_time
    to_time = to_time
    range_hrs = hrs_bw(from_time, to_time)
    tot_hrs = df.duration_hours.sum()

    print("DIAGNOSTICS")
    print()
    print(indented_list(
        title="expanded range for overlapping events",
        pairs=[
            ("begin", pretty_date(from_time)),
            ("end", pretty_date(to_time)),
            ("range hrs", "{:.1f}".format(range_hrs)),
            ("tot hrs", "{:.1f}".format(tot_hrs)
             + " (sum of all event durations)")]))

    uncovered, overlaps = find_intervals(df, from_time, to_time)

    uncovered_hrs = sum(map(splat(hrs_bw), uncovered))
    overlap_hrs = sum(map(splat(hrs_bw), overlaps))

    print()
    print(indented_list(
        title="interval coverage analysis",
        pairs=[
            ("overlap hrs", "{:.1f} ({:.1%})".format(
            overlap_hrs, overlap_hrs / range_hrs
            )),
            ("uncovered hrs", "{:.1f} ({:.1%})".format(
                uncovered_hrs, uncovered_hrs / range_hrs
                ))]))
    print(indented_list(
        title="top overlapping intervals",
        indentation_level=1,
        singles=map(
            compose(
                splat('{} - {}'.format),
                partial(map, pretty_date)),
            heapq.nlargest(3, overlaps, key=splat(hrs_bw)))))
    print(indented_list(
        title="top uncovered intervals",
        indentation_level=1,
        singles=map(
            compose(
                splat('{} - {}'.format),
                partial(map, pretty_date)),
            heapq.nlargest(3, uncovered, key=splat(hrs_bw)))))

    all_tags = set().union(*df.tags)

    print()
    print(indented_list(
        title="tag quantity analysis",
        pairs=[("num unique tags", len(all_tags))],
    ))

    edf = df.join(explode(df))

    tagcounts = {tag: edf[tag].mean() for tag in all_tags}

    print(indented_list(
        title="most popular tags by event count",
        indentation_level=1,
        pairs=[(tag, "{:.1%}".format(tagcounts[tag])) for tag in
               heapq.nlargest(3, all_tags, key=tagcounts.get)]
        ))

    taghrs = {tag: (edf[tag] * edf.duration_hours).sum() for tag in all_tags}
    print(indented_list(
        title="most popular tags by event duration",
        indentation_level=1,
        pairs=[(tag, "{:6.1f}".format(taghrs[tag])) for tag in
               heapq.nlargest(3, all_tags, key=taghrs.get)]))

    log.debug(
        "writing loaded data to {}{}",
        flags.FLAGS.dst,
        " (WARNING: file will be overwritten)"
        if os.path.exists(flags.FLAGS.dst)
        else "",
    )
    df.to_pickle(flags.FLAGS.dst)


if __name__ == "__main__":
    app.run(_main)
