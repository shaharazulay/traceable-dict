import copy
import warnings

from _meta import TraceableMeta
from _utils import key_added, key_removed, key_updated, root, uncommitted
from _utils import nested_getitem, nested_setitem, nested_pop

__all__ = []

_trace_key = '__trace__'
_revisions_key = '__revisions__'

_keys = [_trace_key, _revisions_key]


class TraceableDict(dict):
    """
    A Traceable dictionary, that stores change history in an efficient way inside the object.
    
    Example:
        >>> ## Create a traceable dictionary
        >>> from traceable_dict import TraceableDict
        >>> d1 = {'old_key': 'old_value'}
        >>> D1 = TraceableDict(d1)
        >>> D1
        {'old_key': 'old_value', '__trace__': {}, '__revisions__': []}
        >>> D1.revisions
        []
        >>>
        >>> ## Commit the dictionary for the first time
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
        >>>
        >>> ## Update the dictionary while tracing the changes
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
        >>>
        >>> ## Checkout previous revisions
        >>> D1.as_dict()
        {'old_key': 'old_value', 'new_key': 'new_value'}
        >>>
        >>> D_original = D1.checkout(revision=1)
        >>> D_original.as_dict()
        {'old_key': 'old_value'}
    """

    __metaclass__ = TraceableMeta

    def __init__(self, *args, **kwargs):
        super(TraceableDict, self).__init__(*args, **kwargs)
        self.setdefault(_trace_key, {})
        self.setdefault(_revisions_key, [])
        # TODO: handle init of dict with uncommitted changes
        self._has_uncommitted_changes = False
        if not self.revisions:
            self._has_uncommitted_changes = True

    def __or__(self, other):
        """
        Pipes one dictionary to another, in order to suggest that the first dictionary was updated
        to the value of the second one.
        This change is considered as a traceable change.
        
         Example:
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
            
        Params:
        -------
            other: dict (or TraceableDict),
                   The updated value of the original dict
        Returns:
        -------
            TraceableDict object
        """
        res = TraceableDict(self)
        res._update(other)
        return res

    def commit(self, revision):
        """
        Commit the current changes into a new revision.
            
        Params:
        -------
            revision: int,
                   The revision number to commit.
        """
        if not self.has_uncommitted_changes:
            warnings.warn("nothing to commit")
            return

        if revision is None:
            raise ValueError("revision cannot be None")

        if type(revision) != int:
            raise ValueError("revision must be an integer")

        if self.revisions and (revision <= self.revisions[-1]):
            raise ValueError("cannot commit to earlier revision")

        if self.trace:
            self[_trace_key][str(revision)] = self[_trace_key].pop(uncommitted)

        self._has_uncommitted_changes = False
        if revision not in self.revisions:
            self[_revisions_key].append(revision)

    def revert(self):
        """
        Revert un-commited changes (performed in-place on the current object).
        """
        if self.revisions and self.has_uncommitted_changes:
            result = self._checkout(self.revisions[-1])

            super(TraceableDict, self).clear()
            super(TraceableDict, self).__init__(result)

            self[_trace_key] = result.trace
            self[_revisions_key] = result.revisions
            self._has_uncommitted_changes = False

    def checkout(self, revision):
        """
        Update dict to a specific stored revision.
            
        Params:
        -------
            revision: int,
                   The revision number to update to.
        Returns:
        -------
            TraceableDict object
        """
        if not self.revisions:
            raise Exception("no revisions available. you must commit an initial revision first.")
        if self._has_uncommitted_changes:
            raise Exception("dictionary has uncommitted changes. you must commit or revert first.")
        return self._checkout(revision)

    def log(self, path):
        """
        Display the commit logs over the different revisions.
            
        Params:
        -------
            path: tuple,
               The nested path inside the dictionary to follow.
        Returns:
        -------
            result: dict, 
                The log of dictionary values, per-revision.
        """
        d_augmented = self._augment(path)
        result = {}
        for revision in d_augmented.revisions:
            value = d_augmented._checkout(revision=revision).as_dict()
            result.update({revision: value})
            print 'changeset:   %s' % revision
            print 'value:       %s\n\n' % value
        return result

    def diff(self, revision=None, path=None):
        """
        Show changes between revisions, or latest revision and working tree.
            
        Params:
        -------
            revision: int,
                   The revision number to observe (the difference will be measure between this revision
                   and its previous revision).
            path: tuple,
               The nested path inside the dictionary to follow.
        """
        if not self.revisions:
            return

        d = self
        if path is not None:
            d = self._augment(path)

        if revision == d.revisions[0]:
            return d.as_dict()

        if revision is None:
            if not d.has_uncommitted_changes:
                return
            revision = uncommitted
            events = d.trace[str(revision)]

        else:
            if revision not in d.revisions:
                raise ValueError("unknown revision %s" % revision)
            events = d.trace[str(revision)]
            d = d._checkout(revision=revision)

        d = copy.deepcopy(d.as_dict())

        for event in events:
            _path, value_before, type_ = event
            value = nested_getitem(d, _path)

            if type_ == key_added:
                nested_setitem(d, _path, '+++++++++' + str(value))
            if type_ == key_removed:
                nested_setitem(d, _path, '---------' + str(value_before))
            if type_ == key_updated:
                nested_setitem(d, _path, '---------' + str(value_before) + ' +++++++++' + str(value))

        return d

    def remove_oldest_revision(self):
        """
        Removing the oldest revision of the traceable dict.
        """
        if len(self.revisions) <= 1:
            return

        self[_revisions_key].pop(0)

        base_revision = str(self.revisions[0])
        self[_trace_key].pop(base_revision)

    def as_dict(self):
        """
        Return the current dict represntation of the traceable dict.
        """
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
        if not self.revisions:
            return

        self[_trace_key].setdefault(uncommitted, [])
        self[_trace_key][uncommitted].extend(trace)
        self._has_uncommitted_changes = True

    def _update(self, other):
        trace = self.trace
        revisions = self.revisions
        super(TraceableDict, self).clear()
        super(TraceableDict, self).__init__(other)
        self[_trace_key] = trace
        self[_revisions_key] = revisions

    def _checkout(self, revision):
        if type(revision) != int:
            raise ValueError("revision must be an integer")
        if revision not in self.revisions:
            raise ValueError("unknown revision %s" % revision)

        revisions = list(self.revisions)
        trace = copy.deepcopy(self.trace)
        dict_ = copy.deepcopy(self.as_dict())

        _update_dict = {
            key_added: lambda d, k, v: nested_pop(d, k),
            key_removed: lambda d, k, v: nested_setitem(d, k, v),
            key_updated: lambda d, k, v: nested_setitem(d, k, v)
        }

        if self.has_uncommitted_changes:
            _uncommitted = self.trace[uncommitted]
            [_update_dict[type_](dict_, path, value) for path, value, type_ in _uncommitted]
            trace.pop(uncommitted)

        for revision_ in reversed(self.revisions):
            if revision_ <= revision:
                break

            events = self.trace[str(revision_)]
            [_update_dict[type_](dict_, path, value) for path, value, type_ in events]

            trace.pop(str(revision_))
            revisions.remove(revision_)

        result = TraceableDict(dict_)
        result[_trace_key] = trace
        result[_revisions_key] = revisions
        result._has_uncommitted_changes = False
        return result

    def _augment(self, path):
        if not isinstance(path, tuple):
            raise TypeError("path must be tuple")
        if len(path) == 0:
            raise ValueError("path cannot be empty")

        trace_aug = {}
        revisions_aug = [self.revisions[0]] if self.revisions else []

        for revision in self.trace.keys():
            events_aug = []
            for event in self.trace[str(revision)]:
                _path, value, type_ = event

                if path == _path[1: len(path) + 1]:
                    path_aug = (root, ) + tuple(_path[len(path):])
                    events_aug.append((path_aug, value, type_))

            if events_aug:
                trace_aug[str(revision)] = events_aug
                if revision != uncommitted:
                    revisions_aug.append(int(revision))

        result = TraceableDict({path[-1]: nested_getitem(self, path)})
        result[_trace_key] = trace_aug
        result._has_uncommitted_changes = (uncommitted in trace_aug.keys())
        result[_revisions_key] = sorted(revisions_aug)
        return result

__all__ += ['TraceableDict']
