TraceableDict
============

**Traceable Python dictionary, that stores change history in an efficient way inside the object.**


.. image:: _static/logo.jpg

Shahar Azulay, Rinat Ishak

|Travis|_ |Codecov|_ |Python27|_ |Python35|_ |License|_

.. |License| image:: https://img.shields.io/badge/license-BSD--3--Clause-brightgreen.svg
.. _License: https://github.com/shaharazulay/traceable-dict/blob/master/LICENSE
   
.. |Travis| image:: https://travis-ci.org/shaharazulay/traceable-dict.svg?branch=master
.. _Travis: https://travis-ci.org/shaharazulay/traceable-dict

.. |Codecov| image:: https://codecov.io/gh/shaharazulay/traceable-dict/branch/master/graph/badge.svg
.. _Codecov: https://codecov.io/gh/shaharazulay/traceable-dict
    
.. |Python27| image:: https://img.shields.io/badge/python-2.7-blue.svg
.. _Python27:

.. |Python35| image:: https://img.shields.io/badge/python-3.5-blue.svg
.. _Python35:
    
.. |Documentation| image:: _static/readthedocs_logo.jpg
.. _Documentation: https://traceable-dict.readthedocs.io/en/latest/

|Documentation|_

**Usage Examples:**

   Change a single key inside an exisiting dictionary: 
   
        >>> from traceable_dict import TraceableDict
        >>> from traceable_dict._utils import key_removed, key_added, key_updated, root
        >>>
        >>> d1 = {'old_key': 'old_value'}
        >>>
        >>> D1 = TraceableDict(d1)
        >>> D1
        {'old_key': 'old_value', '__trace__': {}, '__revisions__': []}
        >>> D1.revisions
        []
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
        {"('_root_', 'new_key')": [(None, '_A_', None)]}
        >>> D1.has_uncommitted_changes
        True
        >>> D1.commit(revision=2)
        >>> D1.trace
        {"('_root_', 'new_key')": [(None, '_A_', 2)]}
        >>> D1.has_uncommitted_changes
        False
        >>> D1.revisions
        [1, 2]

   Update an entire dictionary and track the changes:
   
        >>> from traceable_dict import TraceableDict
        >>>
        >>> d1 = {'old_key': 'old_value'}
        >>> d2 = d1.copy()
        >>> d2['new_key'] = 'new_val'
        >>>
        >>> D1 = TraceableDict(d1)
        >>> D1.commit(revision=1)
        >>> D2 = TraceableDict(d2)
        >>> D2.commit(revision=1)
        >>> D1 = D1 | d2
        >>> D1
        {'old_key': 'old_value', 'new_key': 'new_val', '__trace__': {"('_root_', 'new_key')": [(None, '_A_', None)]}, '__revisions__': [1]}
        >>> D1.has_uncommitted_changes
        True
        >>> D1.commit(revision=2)
        >>> D1
        {'old_key': 'old_value', 'new_key': 'new_val', '__trace__': {"('_root_', 'new_key')": [(None, '_A_', 2)]}, '__revisions__': [1, 2]}
        >>> D1.has_uncommitted_changes
        False
        >>>
        >>> D3 = TraceableDict(d1)
        >>> D3.has_uncommitted_changes
        True
        >>> D3.revisions
        []
        >>> D4 = D1 | D3
        >>> D4.commit(revision=3)
        >>> D4
        {'old_key': 'old_value', '__trace__': {"('_root_', 'new_key')": [(None, '_A_', 2), ('new_val', '_R_', 3)]}, '__revisions__': [1, 2, 3]}

   Revert uncommitted changes
       >>> from traceable_dict import TraceableDict
       >>>
       >>> d1 = {'old_key': 'old_value'}
       >>>
       >>> D1 = TraceableDict(d1)
       >>> D1.commit(revision=1)
       >>> D1.has_uncommitted_changes
       False
       >>> D1
       {'old_key': 'old_value', '__trace__': {}, '__revisions__': [1]}
       >>>
       >>> D1['new_key'] = 'new_val'
       >>> D1
       {'old_key': 'old_value', 'new_key': 'new_val', '__trace__': {"('_root_', 'new_key')": [(None, '_A_', None)]}, '__revisions__': [1]}
       >>> D1.has_uncommitted_changes
       True
       >>> D1.revert()
       >>> D1
       {'old_key': 'old_value', '__trace__': {}, '__revisions__': [1]}

   Checkout previous revisions
        >>> import copy
        >>> from traceable_dict import TraceableDict
        >>>
        >>> d1 = {'key1': 'value1'}
        >>> d2 = {'key2': 'value2'}
        >>>
        >>> D1 = TraceableDict(d1)
        >>> D1.commit(revision=1)
        >>> _r1 = copy.deepcopy(D1)
        >>>
        >>> D1 = D1 | d2
        >>> D1.commit(revision=2)
        >>> _r2 = copy.deepcopy(D1)
        >>>
        >>> r1 = D1.checkout(revision=1)
        >>> r1.freeze == _r1.freeze
        True
        >>> r1.trace == _r1.trace
        True
        >>> r1.revisions == _r1.revisions
        True
        >>>
        >>> r2 = D1.checkout(revision=2)
        >>> r2.freeze == _r2.freeze
        True
        >>> r2.trace == _r2.trace
        True
        >>> r2.revisions == _r2.revisions
        True

   Display the commit logs
        >>> from traceable_dict import TraceableDict
        >>>
        >>> d1 = {'key1': 'value1'}
        >>>
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