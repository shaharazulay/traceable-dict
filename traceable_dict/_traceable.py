from _meta import TraceableMeta
from _time import get_time

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
        >>> with set_time(timestamp=1):
        >>>     D1['new_key'] = 'new_val'
        [(('_root_', 'new_key'), None, __added__, 1)]


        >>> from traceable_dict import TraceableDict
        >>>
        >>> d1 = {'old_key': 'old_value'}
        >>> d2 = d1.copy()
        >>> d2['new_key'] = 'new_val
        >>>
        >>> D1 = TraceableDict(d1)
        >>> D2 = TraceableDict(d2)
        >>> with set_time(timestamp=1)
        >>>     D3 = D1 | d2
        >>> D3
        {'old_key': 'old_value', 'new_key': 'new_val', '__trace__': {('root', 'new_key'): [(None, __added__, 1)]}}
        >>>
        >>> D3 = TraceableDict(d1)
        >>> with set_time(timestamp=2)
        >>>     D1 | D2 | D3
        {'old_key': 'old_value', '__trace__': {('root', 'new_key'): [(None, __added__, 1), ('new_val', __removed__, 2)]}}

    """

    __metaclass__ = TraceableMeta

    def __init__(self, *args, **kwargs):
        print 'child.__init__()'
        super(TraceableDict, self).__init__(*args, **kwargs)
        self.setdefault(_trace_key, {})

    def _update(self, other):
        trace = self.trace
        super(TraceableDict, self).clear()
        super(TraceableDict, self).__init__(other)
        self[_trace_key] = trace
        
    def __or__(self, other):
        res = TraceableDict(self)
        res._update(other)
        return res
    
    def update_trace(self, trace):
        trace_dict = self._copy_trace()
        for path, v, type_ in trace:
            trace_dict.setdefault(path, [])
            trace_dict[path].append((v, type_, get_time()))
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
        

__all__ += ['TraceableDict']
