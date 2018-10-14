  
Reverting un-committed changes to a dictionary
-----

    >>> from traceable_dict import TraceableDict
    >>>
    >>> d1 = {'old_key': 'old_value'}
    >>> D1 = TraceableDict(d1)
    >>> D1.commit(revision=1)
    >>>
    >>> D1['new_key'] = 'new_val'
    >>> D1.as_dict() 
    {'new_key': 'new_val', 'old_key': 'old_value'}
    >>> D1.trace
    {'_uncommitted_': [(('_root_', 'new_key'), None, '__a__')]}
    >>>
    >>> D1.revert()
    >>>
    >>> D1.has_uncommitted_changes
    False
    >>> D1.as_dict()
    {'old_key': 'old_value'}
    
    
Checkout previous revisions of the dictionary
-----

    >>> from traceable_dict import TraceableDict
    >>>
    >>> d1 = {'old_key': 'old_value'}
    >>> D1 = TraceableDict(d1)
    >>> D1.commit(revision=1)
    >>>
    >>> d2 = {'old_key': 'updated_value', 'new_key': 'new_value'}
    >>>
    >>> D1 = D1 | d2
    >>> D1.as_dict()
    {'new_key': 'new_value', 'old_key': 'updated_value'}
    >>>
    >>> D1.commit(revision=2)
    >>> D1.revisions
    [1, 2]
    >>>
    >>> D_original = D1.checkout(revision=1)
    >>> D_original.as_dict()
    {'old_key': 'old_value'}
    
    
Displaying the commit logs over the different revisions
-----

    >>> from traceable_dict import TraceableDict
    >>>
    >>> d1 = {'key1': 'value1'}
    >>> D1 = TraceableDict(d1)
    >>> D1.commit(revision=1)
    >>>
    >>> D1['key1'] = 'new_val'
    >>> D1.commit(revision=2)
    >>>
    >>> log = D1.log(path=('key1',))
    changeset:   1
    value:       {'key1': 'value1'}
    <BLANKLINE>
    <BLANKLINE>
    changeset:   2
    value:       {'key1': 'new_val'}
    <BLANKLINE>
    <BLANKLINE>
    >>> log
    {1: {'key1': 'value1'}, 2: {'key1': 'new_val'}}
    
    
Show changes between revisions, or latest revision and working tree
-----

    >>> from traceable_dict import TraceableDict


Dropping the oldest revision of the traceable dict
-----
This option allows the user to contol the amount of revisions stored in the traceable-dict object,
by trimming the tail of the trace stored in the traceable-dict.
The oldest revision is cleared out and cannot be returned to again.
 
