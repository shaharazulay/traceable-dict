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
    >>> D1.as_dict()
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
    
