from _meta import TraceableMeta

__all__ = []

_trace_key = '__trace__'


class TraceableDict(dict):

    __metaclass__ = TraceableMeta

    def __init__(self, *args):
        print 'child.__init__()'
        super(TraceableDict, self).__init__(*args)
        self.setdefault(_trace_key, {})
        
    @staticmethod
    def _update(orig, other):
        trace = orig.trace
        super(TraceableDict, orig).clear()
        super(TraceableDict, orig).__init__(other)
        orig[_trace_key] = trace
        
    def __or__(self, other):
        res = TraceableDict(self)
        TraceableDict._update(res, other)
        return res
    
    def update_trace(self, trace):
        trace_dict = self._copy_trace()
        for path, v, type_ in trace:
            trace_dict.setdefault(path, [])
            trace_dict[path].append((v, type_))
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
