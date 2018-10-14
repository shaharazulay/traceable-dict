  
Reverting un-wanted changes to a dictionary
-----

    >>> from traceable_dict import TraceableDict
    >>> from traceable_dict._utils import key_removed, key_added, key_updated, root
    >>>
    >>> d1 = {'old_key': 'old_value'}
    >>> D1 = TraceableDict(d1)
    >>> D1.commit(revision=1)
    >>>
    >>> D1['new_key'] = 'new_val'
    >>> D1.freeze 
    {'new_key': 'new_val', 'old_key': 'old_value'}
    >>> D1.trace
    {'_uncommitted_': [(('_root_', 'new_key'), None, '__a__')]}
    >>>
    >>> D1.revert()
    >>>
    >>> D1.has_uncommitted_changes
    False
    >>> D1.freeze 
    {'old_key': 'old_value'}
    
    
Rolling back to old revisions of the dictionary
-----

    >>> from traceable_dict import TraceableDict
    
    
Viewing the change-log of the dictionary over the different revisions
-----

    >>> from traceable_dict import TraceableDict
    
    
Show changes between revisions, or latest revision and working tree
-----

    >>> from traceable_dict import TraceableDict


Dropping the oldest revision of the traceable dict
-----
This option allows the user to contol the amount of revisions stored in the traceable-dict object,
by trimming the tail of the trace stored in the traceable-dict.
The oldest revision is cleared out and cannot be returned to again.
 
