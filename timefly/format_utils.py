"""
This module contains various utilities for pretty-printing
structured data.
"""

def indented_list(title=None, indentation_level=0, pairs=[], singles=[]):
    """
    returns the string

    title
      left1: right1
      left2: right2
      s1
      s2

    all nicely indented where pairs contains [(left1, right1),
    (left2, right2)] and singles contains [s1, s2]

    If title is not present, returns the unindented original list.
    Everything is pre-indented by 2 spaces indentation_level number
    of times.
    """
    indent = indentation_level * '  '
    if title:
        return indent + title + "\n" + indented_list(
            title=None,
            indentation_level=(indentation_level + 1),
            pairs=pairs)
    pairs = list(pairs)
    maxlen = max(len(left) for left, right in pairs) if pairs else 0
    fmt = indent + '{:<' + str(maxlen) + 's}: {}'
    items = [fmt.format(*pair) for pair in pairs]
    items.extend([indent + s for s in singles])
    return '\n'.join(items)
