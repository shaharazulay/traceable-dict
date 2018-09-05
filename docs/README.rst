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
        >>>
        >>> d1 = {'old_key': 'old_value'}
        >>>
        >>> D1 = TraceableDict(d1)
        >>> D1.timestamp = 0
        >>> D1
        {'old_key': 'old_value', '__trace__': {}}
        >>>
        >>> D1.timestamp = 1
        >>> D1['new_key'] = 'new_val'
        [(('_root_', 'new_key'), None, __added__, 1)]

   Update an entire dictionary and track the changes:
   
        >>> from traceable_dict import TraceableDict
        >>>
        >>> d1 = {'old_key': 'old_value'}
        >>> d2 = d1.copy()
        >>> d2['new_key'] = 'new_val
        >>>
        >>> D1 = TraceableDict(d1)
        >>> D1.timestamp = 0
        >>> D2 = TraceableDict(d2)
        >>> D2.timestamp = 1
        >>> D3 = D1 | d2
        >>> D3
        {'old_key': 'old_value', 'new_key': 'new_val', '__trace__': {('root', 'new_key'): [(None, __added__, 1)]}}
        >>>
        >>> D3 = TraceableDict(d1)
        >>> D3.timestamp = 2
        >>> D1 | D2 | D3
        {'old_key': 'old_value', '__trace__': {('root', 'new_key'): [(None, __added__, 1), ('new_val', __removed__, 2)]}}

