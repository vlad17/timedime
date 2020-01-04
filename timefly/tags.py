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
    df["tags"] = df[["tags", "summary"]].apply(
        lambda x: {y for y in x.tags.union(frozenset([x.summary])) if y},
        axis=1)

    exploded = df.tags.apply(lambda x: pd.Series({tag: True for tag in x}))
    exploded = exploded.fillna(False)
    return exploded

def df_filter(df, ef, tag=None, keep=True):
    """
    No-op if the filter tag is set to None.format

    Otherwise, only includes the rows associated with the string tag,
    which must be a column in the exploded dataframe.

    if keep is false, removes the column associated with the tag.

    Returns the modified df, ef.
    """
    if not tag:
        return df, ef

    chosen = ef[tag]
    df = df[chosen].copy()
    def remove_tag(s):
        s = set(s)
        s.remove(tag)
        return frozenset(s)
    df.loc[:, 'tags'] = df.tags.apply(remove_tag)
    ef = ef[chosen].drop(columns=tag)

    print('only keeping {:.2%} of rows matching {}'.format(chosen.mean(), tag))
    return df, ef
