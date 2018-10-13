Creating the traceable dict for the first time
-----
    >>> from traceable_dict import TraceableDict
    >>>
    >>> d1 = {'first_key': 'first_value'}
    >>>
    >>> D1 = TraceableDict(d1)
    >>> D1
    {'first_key': 'first_value', '__trace__': {}, '__revisions__': []}
    >>> D1.revisions
    []
    >>> D1.has_uncommitted_changes
    True
    >>>
    >>> D1.commit(revision=1)
    >>>
    >>> D1.has_uncommitted_changes
    False
    >>> D1.revisions
    >>> 
    [1]
    
Updating a single key inside the dictionary
-----

    >>> from traceable_dict import TraceableDict
    >>> from traceable_dict._utils import key_removed, key_added, key_updated, root
    >>>
    >>> d1 = {'old_key': 'old_value'}
    >>> D1 = TraceableDict(d1)
    >>> D1
    {'old_key': 'old_value', '__trace__': {}, '__revisions__': []}
    >>>
    >>> D1.has_uncommitted_changes
    True
    >>>
    >>> D1.commit(revision=1)
    >>> D1
    {'old_key': 'old_value', '__trace__': {}, '__revisions__': [1]}
    >>> D1.revisions
    [1]
    >>> D1.has_uncommitted_changes
    False
    >>> D1['new_key'] = 'new_val'
    >>> D1.trace
    {'_uncommitted_': [(('_root_', 'new_key'), None, '__a__')]}
    >>> D1.has_uncommitted_changes
    True
    >>> D1.commit(revision=2)
    >>> D1.trace
    {'2': [(('_root_', 'new_key'), None, '__a__')]}
    >>> D1.has_uncommitted_changes
    False
    >>> D1.revisions
    [1, 2]


Updating the entire dictionary while tracing the changes
-----

    >>> from traceable_dict import TraceableDict
    >>> from traceable_dict._utils import key_removed, key_added, key_updated, root
    >>>
    >>> d1 = {'old_key': 'old_value'}
    >>> D1 = TraceableDict(d1)
    >>> D1
    {'old_key': 'old_value', '__trace__': {}, '__revisions__': []}
    >>>
    >>> D1.commit(revision=1)
    >>> D1.trace
    {}
    >>> d2 = {'old_key': 'updated_value', 'new_key': 'new_value'}
    >>>
    >>> D1 = D1 | d2
    >>> D1.freeze
    {'new_key': 'new_value', 'old_key': 'updated_value'}
    >>> D1.trace
    {'_uncommitted_': [(('_root_', 'old_key'), 'old_value', '__u__'), (('_root_', 'new_key'), None, '__a__')]}
    >>>
    >>> D1.commit(revision=2)
    >>> D1.trace
    {'2': [(('_root_', 'old_key'), 'old_value', '__u__'), (('_root_', 'new_key'), None, '__a__')]}
    >>> D1.has_uncommitted_changes
    False
    >>> D1.revisions
    [1, 2]
    
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
 
