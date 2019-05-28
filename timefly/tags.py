"""
Handling for the tags from calendar events.
"""

import pandas as pd


def explode(df, min_support_count=None):
    """
    Given a dataframe with a tags column that contains an iterable of tags,
    creates a new dataframe containing the (sparse) binary
    columns for each tag. The index is the same.

    Also, generates new tags identical to the "summary" column
    for all summaries that appear
    more than min_support_count times if that's not none.

    The index is preserved.
    """
    # TODO: to avoid actually exploding memory, we could
    # do one tag at a time and explicitly construct the sparse vector.
    # probably need to switch from pandas to a dict.

    # just treat the summary as a tag itself too

    df = df.copy()
    df["tags"] = df[["tags", "summary"]].apply(lambda x: x.tags.union(frozenset([x.summary])), axis=1)

    exploded = df.tags.apply(lambda x: pd.Series({tag: True for tag in x}))
    exploded = exploded.fillna(False)
    return exploded
