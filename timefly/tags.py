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
    exploded = df.tags.apply(lambda x: pd.Series({tag: True for tag in x}))
    exploded = exploded.fillna(False).to_sparse(fill_value=0)
    return exploded

# TODO: support-based exploding for descriptions above
# TODO: note, we probably want to re-explode at every context

def expand_explode(cdf, cef):
    """
    Augment an exploded df, cef, with summaries that appear
    more than once in the dataframe df.
    """

    summary_gb = cdf.summary.groupby(cdf.summary).size()
    summaries = summary_gb[summary_gb > 1].index
    for summary in summaries:
        if not summary:
            cef['<empty>'] = cdf.summary == ''
            continue
        cef[summary] = cdf.summary == summary
    return cef
