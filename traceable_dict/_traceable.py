from _meta import TraceableMeta

__all__ = []

_trace_key = '__trace__'


class TraceableDict(dict):
    """
    A Traceable dictionary, that stores change history in an efficient way inside the object.
    
    Example:

        >>> from traceable_dict import TraceableDict
        >>>
        >>> d1 = {'old_key': 'old_value'}
        >>>
        >>> D1 = TraceableDict(d1)
        >>> D1
        {'old_key': 'old_value', '__trace__': {}}
        >>>
        >>> D1['new_key'] = 'new_val'
        [(('_root_', 'new_key'), None, __added__)]


        >>> from traceable_dict import TraceableDict
        >>>
        >>> d1 = {'old_key': 'old_value'}
        >>> d2 = d1.copy()
        >>> d2['new_key'] = 'new_val
        >>>
        >>> D1 = TraceableDict(d1)
        >>> D3 = D1 | d2
        >>> D3
        {'old_key': 'old_value', 'new_key': 'new_val', '__trace__': {('root', 'new_key'): [(None, __added__)]}}
        >>>
        >>> D1 | d2 | D1
        {'old_key': 'old_value', '__trace__': {('root', 'new_key'): [(None, __added__), ('new_val', __removed__)]}}

    """

    __metaclass__ = TraceableMeta

    def __init__(self, *args, **kwargs):
        print 'child.__init__()'
        super(TraceableDict, self).__init__(*args, **kwargs)
        self.setdefault(_trace_key, {})
        
    @staticmethod
    def _update(orig, other):
        trace = orig.trace
        super(TraceableDict, orig).clear()
        super(TraceableDict, orig).__init__(other)
        orig.timestamp = other.timestamp
        orig[_trace_key] = trace
        
    def __or__(self, other):
        res = TraceableDict(self)
        TraceableDict._update(res, other)
        return res
    
    def update_trace(self, trace):
        trace_dict = self._copy_trace()
        for path, v, type_ in trace:
            trace_dict.setdefault(path, [])
            trace_dict[path].append((v, type_, self.timestamp))
        self[_trace_key] = trace_dict
        
    def _copy_trace(self):
        return dict((k, v[:]) for k, v in self[_trace_key].iteritems())

    @property
    def freeze(self):
        frozen = dict(self)
        return dict((k, frozen[k]) for k in frozen if k != _trace_key)

    @property
    def trace(self):
        return dict(self[_trace_key])

    @property
    def timestamp(self):
        return self._timestamp

    @timestamp.setter
    def timestamp(self, updated_time):
        self._timestamp = updated_time
        

__all__ += ['TraceableDict']
