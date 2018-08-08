from _meta import TraceableMeta

__all__ = []


class TraceableDict(dict):

    __metaclass__ = TraceableMeta

    def __init__(self, *args):
        print 'child.__init__()'
        super(TraceableDict, self).__init__(*args)
        self.setdefault('__trace__', {})
        
    @staticmethod
    def _update(orig, other):
        super(TraceableDict, orig).__init__(other)

    def __or__(self, other):
        res = TraceableDict(self)
        TraceableDict._update(res, other)
        return res
    
    def update_trace(self, trace):
        trace_dict = self._copy_trace()
        for path, v, type_ in trace:
            trace_dict.setdefault(path, [])
            trace_dict[path].append((v, type_))
        self['__trace__'] = trace_dict
        
    def _copy_trace(self):
        return dict((k, v[:]) for k, v in self['__trace__'].iteritems())

    @property
    def freeze(self):
        frozen = dict(self)
        return dict((k, frozen[k]) for k in frozen if k != '__trace__')


__all__ += ['TraceableDict']
