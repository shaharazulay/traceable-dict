import copy

from _meta import TraceableMeta
from _utils import key_added, key_removed, key_updated, root
from _utils import nested_getitem, nested_setitem, nested_pop

__all__ = []

BaseRevision = 0
__all__ += ['BaseRevision']

_trace_key = '__trace__'
_revisions_key = '__revisions__'

_keys = [_trace_key, _revisions_key]


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
        {'old_key': 'old_value', '__trace__': {}, '__revisions__': [0]}
        >>> D1.revisions
        [0]
        >>>
        >>> D1['new_key'] = 'new_val'
        >>> D1.trace
        {('_root_', 'new_key'): [(None, __added__, None)]}
        >>> D1.has_uncommitted_changes
        True
        >>> D1.commit(revision=1)
        >>> D1.trace
        {('_root_', 'new_key'): [(None, __added__, 1)]}
        >>> D1.has_uncommitted_changes
        False
        >>> D1.revisions
        [0, 1]


        >>> from traceable_dict import TraceableDict
        >>>
        >>> d1 = {'old_key': 'old_value'}
        >>> d2 = d1.copy()
        >>> d2['new_key'] = 'new_val'
        >>>
        >>> D1 = TraceableDict(d1)
        >>> D2 = TraceableDict(d2)
        >>> D3 = D1 | d2
        >>> D3
        {'old_key': 'old_value', 'new_key': 'new_val', '__trace__': {('_root_', 'new_key'): [(None, __added__, None)]}, '__revisions__': [0]}
        >>> D3.has_uncommitted_changes
        True
        >>> D3.commit(revision=1)
        >>> D3
        {'old_key': 'old_value', 'new_key': 'new_val', '__trace__': {('_root_', 'new_key'): [(None, __added__, 1)]}, '__revisions__': [0, 1]}
        >>> D3.has_uncommitted_changes
        False
        >>>
        >>> D3 = TraceableDict(d1)
        >>> D3.has_uncommitted_changes
        False
        >>> D2_tag = D1 | D2
        >>> D2_tag.commit(revision=1)
        >>> D3_tag = D2_tag | D3
        >>> D3_tag.commit(revision=2)
        >>> D3_tag
        {'old_key': 'old_value', '__trace__': {('_root_', 'new_key'): [(None, __added__, 1), ('new_val', __removed__, 2)]}, '__revisions__': [0, 1, 2]}

    """

    __metaclass__ = TraceableMeta

    def __init__(self, *args, **kwargs):
        # print 'child.__init__()'
        super(TraceableDict, self).__init__(*args, **kwargs)
        self.setdefault(_trace_key, {})
        self.setdefault(_revisions_key, [BaseRevision])
        self._has_uncommitted_changes = False

    def __or__(self, other):
        res = TraceableDict(self)
        res._update(other)
        return res

    def commit(self, revision):
        if revision is None:
            raise ValueError("revision cannot be None")

        if revision == BaseRevision:
            raise ValueError("cannot commit to base revision")

        if revision < self.revisions[-1]:
            raise ValueError("cannot commit to earlier revision")

        trace = {}
        for path, events in self.trace.iteritems():
            trace.update({path: []})
            for value, type_, rev in events:
                _revision = rev if rev is not None else revision
                trace[path].append((value, type_, _revision))
        self[_trace_key] = trace
        self._has_uncommitted_changes = False

        if revision not in self.revisions:
            self[_revisions_key].append(revision)

    def revert(self):
        if self.has_uncommitted_changes:
            result = self._checkout(self.revisions[-1])

            super(TraceableDict, self).clear()
            super(TraceableDict, self).__init__(result)

            self[_trace_key] = result.trace
            self[_revisions_key] = result.revisions
            self._has_uncommitted_changes = False

    def checkout(self, revision):
        if self._has_uncommitted_changes:
            raise Exception("dictionary has uncommitted changes. you must commit or revert first.")
        return self._checkout(revision)

    def log(self, path):
        d_augmented = self._augment(path)
        result = {}
        for revision in d_augmented.revisions:
            value = d_augmented._checkout(revision=revision).freeze
            result.update({revision: value})
            print 'changeset:   %s' % revision
            print 'value:       %s\n\n' % value
        return result

    @property
    def freeze(self):
        frozen = dict(self)
        return dict((k, frozen[k]) for k in frozen if k not in _keys)

    @property
    def trace(self):
        return dict(self[_trace_key])

    @property
    def revisions(self):
        return self[_revisions_key]

    @property
    def has_uncommitted_changes(self):
        return self._has_uncommitted_changes

    def update_trace(self, trace):
        trace_dict = self._copy_trace()
        for path, v, type_ in trace:
            trace_dict.setdefault(path, [])
            trace_dict[path].append((v, type_, None))
        self[_trace_key] = trace_dict
        self._has_uncommitted_changes = True

    def _copy_trace(self):
        return dict((k, v[:]) for k, v in self[_trace_key].iteritems())

    def _update(self, other):
        trace = self.trace
        revisions = self.revisions
        super(TraceableDict, self).clear()
        super(TraceableDict, self).__init__(other)
        self[_trace_key] = trace
        self[_revisions_key] = revisions

    def _checkout(self, revision):

        if revision not in self.revisions:
            raise ValueError("unknown revision %s" % revision)

        revisions = list(self.revisions)
        trace = self._copy_trace()
        dict_ = copy.deepcopy(self.freeze)

        _update_dict = {
            key_added: lambda d, k, v: nested_pop(d, k),
            key_removed: lambda d, k, v: nested_setitem(d, k, v),
            key_updated: lambda d, k, v: nested_setitem(d, k, v)
        }

        for path, events in self.trace.iteritems():
            for value, type_, rev in events[::-1]:
                if (rev is not None) and (rev <= revision):
                    break

                _update_dict[type_](dict_, path, value)
                trace[path].pop()
                if rev in revisions:
                    revisions.remove(rev)

            if not trace[path]:
                trace.pop(path)

        result = TraceableDict(dict_)
        result[_trace_key] = trace
        result[_revisions_key] = revisions
        return result

    def _augment(self, path):
        if path is None:
            raise ValueError("path cannot be None")

        if not isinstance(path, tuple):
            raise TypeError("path must be tuple")

        trace_aug = {}
        revisions_aug = set()

        for k in self.trace.keys():
            if path == k[1: len(path) + 1]:
                k_aug = (root, ) + tuple(k[len(path):])
                trace_aug[k_aug] = self.trace[k]
                [revisions_aug.add(event[-1]) for event in self.trace[k] if event[-1] is not None]

        result = TraceableDict({path[-1]: nested_getitem(self, path)})
        result[_trace_key] = trace_aug
        result._has_uncommitted_changes = any([v for v in values if v[-1] is None] for values in trace_aug.values())
        result[_revisions_key].extend(list(revisions_aug))
        return result

__all__ += ['TraceableDict']
