"""
Merges newly ingested events with an existing store
and writes the union back.
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

flags.DEFINE_string('new_events', './data/new.pkl',
                    'path pointing to the new rows to add')
flags.DEFINE_string('running_events', './data/running.pkl',
                    'path pointing to the existing store of data, '
                    'this need not exist')
def _main(_argv):
    log.init()

    new = pd.read_pickle(flags.FLAGS.new_events)
    if os.path.exists(flags.FLAGS.running_events):
        running = pd.read_pickle(flags.FLAGS.running_events)
    else:
        running = new

    print('ingested {:5d} events in running store'.format(
        len(running)))
    print('ingested {:5d} events in new store'.format(
        len(new)))

    newnew = new.index.difference(running.index)
    new_running = pd.concat([running, new.loc[newnew]])

    print('unioned  {:5d} events in updated store'.format(
        len(new_running)))

    new_running.to_pickle(flags.FLAGS.running_events)

if __name__ == '__main__':
    app.run(_main)
