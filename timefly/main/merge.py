"""
Merges newly ingested events with an existing store
and writes the union back.
"""

import os

import pandas as pd
from absl import app, flags

from .. import log

flags.DEFINE_string(
    "new_events", "./data/new.pkl", "path pointing to the new rows to add"
)
flags.DEFINE_string(
    "running_events",
    "./data/running.pkl",
    "path pointing to the existing store of data, " "this need not exist",
)


def _main(_argv):
    log.init()

    new = pd.read_pickle(flags.FLAGS.new_events)
    if os.path.exists(flags.FLAGS.running_events):
        running = pd.read_pickle(flags.FLAGS.running_events)
    else:
        running = new

    print("ingested {:5d} events in running store".format(len(running)))
    print("ingested {:5d} events in new store".format(len(new)))

    newnew = new.index.difference(running.index)
    new_running = pd.concat([running, new.loc[newnew]])

    print("unioned  {:5d} events in updated store".format(len(new_running)))

    new_running.to_pickle(flags.FLAGS.running_events)


if __name__ == "__main__":
    app.run(_main)
