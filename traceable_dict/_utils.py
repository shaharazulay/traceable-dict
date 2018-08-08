__all__ = []


class KeyEvent(object):
    """
    Describes general key event
    """
    def __eq__(self, other):
        return isinstance(other, self.__class__)
    
    def __str__(self):
        return self.__repr__()
    

class KeyAdded(KeyEvent):
    """
    Indicates the key was added
    """
    def __repr__(self):
        return "__added__"
    
    
class KeyRemoved(KeyEvent):
    """
    Indicates the key was removed
    """
    def __repr__(self):
        return "__removed__"
    
    
class KeyUpdated(KeyEvent):
    """
    Indicates the key-value pair was updated
    """
    def __repr__(self):
        return "__updated__"

    
key_removed = KeyRemoved()
__all__ += ['key_removed']

key_added = KeyAdded()
__all__ += ['key_added']

key_updated = KeyUpdated()
__all__ += ['key_updated']
