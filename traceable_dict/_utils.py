__all__ = []


root = '_root_'

__all__ += [root]


class KeyEvent(object):
    """
    Describes general key event
    """
    def __eq__(self, other):
        return type(other) == type(self)
    

class KeyAdded(KeyEvent):
    """
    Indicates the key was added
    """
    def __repr__(self):
        return "__added__"

key_added = KeyAdded()
__all__ += ['key_added']


class KeyRemoved(KeyEvent):
    """
    Indicates the key was removed
    """
    def __repr__(self):
        return "__removed__"

key_removed = KeyRemoved()
__all__ += ['key_removed']


class KeyUpdated(KeyEvent):
    """
    Indicates the key-value pair was updated
    """
    def __repr__(self):
        return "__updated__"

key_updated = KeyUpdated()
__all__ += ['key_updated']


def nested_setitem(d, nested_k, v):

    for k in nested_k[:-1]:
        if k == root:
            continue
        d = d.setdefault(k, {})

    d[nested_k[-1]] = v

__all__ += ['nested_setitem']


def nested_pop(d, nested_k):

    stack = []
    for k in nested_k[:-1]:
        if k == root:
            continue
        stack.append((d, k))
        d = d[k]

    d.pop(nested_k[-1])
    while not d:
        d, k = stack.pop()
        d.pop(k)

__all__ += ['nested_pop']


def nested_getitem(d, nested_k):

    for k in nested_k:
        if k == root:
            continue
        d = d.get(k, {})

    return d

__all__ += ['nested_getitem']