__all__ = []


class AddedKey(object):
    """
    Indicates the key was added
    """
    def __repr__(self):
        return "__added__"
    
    def __str__(self):
        return self.__repr__()

    
class RemovedKey(object):
    """
    Indicates the key was removed
    """
    def __repr__(self):
        return "__removed__"
    
    def __str__(self):
        return self.__repr__()

    
class UpdatedKey(object):
    """
    Indicates the key-value pair was updated
    """
    def __repr__(self):
        return "__updated__"

    def __str__(self):
        return self.__repr__()

    
key_removed = RemovedKey()
__all__ += ['key_removed']

key_added = AddedKey()
__all__ += ['key_added']

key_updated = UpdatedKey()
__all__ += ['key_updated']
