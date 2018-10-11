import time
import unittest
import pytest

from traceable_dict import DictDiff
from traceable_dict import TraceableDict

from traceable_dict._utils import key_removed, key_added, key_updated, root, uncommitted


class KeyEventTypeTests(unittest.TestCase):

    def test_equality(self):
        from traceable_dict._utils import KeyAdded, KeyRemoved, KeyUpdated
        
        d_orig = {
            'old_key': 'old_value',
        }
        d = d_orig.copy()
        d['new_key'] = 'new_val'
        res = DictDiff.find_diff(d_orig, d)
        self.assertEqual(len(res), 1)

        self.assertEquals(
            [((root, 'new_key'), None, key_added)],
            res)

        self.assertEquals(
            [((root, 'new_key'), None, repr(KeyAdded()))],
            res)

        self.assertEquals(KeyAdded(), KeyAdded())
        self.assertEquals(('foo', key_added), ('foo', repr(KeyAdded())))
        self.assertEquals((None, key_added), (None, repr(KeyAdded())))

        self.assertEquals(KeyRemoved(), KeyRemoved())
        self.assertEquals(KeyUpdated(), KeyUpdated())


class DiffTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls._d1 = {1: {2: "A", 3: {4: "B", 5: [1, 2, 3]}}}
        cls._d2 = {1: {2: "A_UPDATED", 3: {4: "B_UPDATED"}}}

    def test_traversal(self):
        expected_leaf_vals = [[1, 2, 3], 'B', 'A']
        expected_leaf_paths = [[1, 2], [1, 3, 4], [1, 3, 5]]
            
        res = DictDiff._traversal(self._d1)
        for path, val in res:
            self.assertIn(val, expected_leaf_vals)
            self.assertIn(path, expected_leaf_paths)

    def test_diff_basic(self):
        d_orig = {
            'old_key_1': 'old_value_1',
            'old_key_2': 'old_value_2'
        }

        d = d_orig.copy()
        
        d['new_key'] = 'new_val'
        res = DictDiff.find_diff(d_orig, d)
        self.assertEqual(len(res), 1)
        self.assertEquals(
            [((root, 'new_key'), None, key_added)],
            res)

        d.pop('new_key')
        res = DictDiff.find_diff(d_orig, d)
        self.assertEquals([], res)

        d.pop('old_key_1')
        res = DictDiff.find_diff(d_orig, d)
        self.assertEqual(len(res), 1)
        self.assertEquals(
            [((root, 'old_key_1'), 'old_value_1', key_removed)],
            res)

        d.update({'old_key_2': 'new_val'})
        res = DictDiff.find_diff(d_orig, d)
        self.assertEqual(len(res), 2)
        self.assertIn(
            ((root, 'old_key_2'), 'old_value_2', key_updated),
            res)

    def test_diff_nested(self):
        res = DictDiff.find_diff(self._d1, self._d2)
        self.assertEqual(len(res), 3)
        self.assertIn(
            ((root, 1, 2), 'A', key_updated),
            res)
        self.assertIn(
            ((root, 1, 3, 4), 'B', key_updated),
            res)
        self.assertIn(
            ((root, 1, 3, 5), self._d1[1][3][5], key_removed),
            res)

        res = DictDiff.find_diff(self._d2, self._d1)
        self.assertEqual(len(res), 3)
        self.assertIn(
            ((root, 1, 3, 5), None, key_added),
            res)
        
    def test_diff_symmetry(self):
        def _symmetric_event_type(type_):
            if type_ == key_removed:
                return key_added
            if type_ == key_added:
                return key_removed
            return key_updated

        res_side_1 = DictDiff.find_diff(self._d1, self._d2)
        res_side_2 = DictDiff.find_diff(self._d2, self._d1)

        self.assertEqual(len(res_side_1), len(res_side_2))

        diffs_side_1 = [(path, type_) for path, prev_val, type_ in res_side_1]
        diffs_side_2 = [(path, type_) for path, prev_val, type_ in res_side_2]

        for diff in diffs_side_1:
            path, type_ = diff
            symmetric_diff = (path, _symmetric_event_type(type_))
            self.assertIn(symmetric_diff, diffs_side_2)
        
    def test_diff_same_dict(self):
        res = DictDiff.find_diff(self._d1, self._d1)
        self.assertFalse(res)

    def test_diff_empry_dict(self):
        res = DictDiff.find_diff(self._d1, {})
        self.assertEqual(len(res), len(DictDiff._traversal(self._d1)))
                         
        res = DictDiff.find_diff(self._d1, {})
        self.assertEqual(len(res), len(DictDiff._traversal(self._d1)))

    def test_diff_key_updated(self):
        d_orig = {
            'old_key_1': 'old_value_1',
            'old_key_2': 'old_value_2'
        }

        d = d_orig.copy()

        d['old_key_2'] = [1,2,3]
        res = DictDiff.find_diff(d_orig, d)
        self.assertEqual(len(res), 1)
        self.assertEquals(
            [((root, 'old_key_2'), 'old_value_2', key_updated)],
            res)

        # value changes from non-dict to dict - this is not supported
        d['old_key_2'] = {1: "A", 2: "B"}
        with self.assertRaises(AttributeError) as e:
            DictDiff.find_diff(d_orig, d)
        self.assertEquals(
            "'str' object has no attribute 'keys'",
            str(e.exception))

    def test_diff_key_added(self):
        d_orig = {
            'old_key_1': 'old_value_1',
            'old_key_2': 'old_value_2'
        }

        d = d_orig.copy()

        d['new_key'] = {1: "a", 2:"b"}
        res = DictDiff.find_diff(d_orig, d)
        self.assertEqual(len(res), 2)
        self.assertIn(
            ((root, 'new_key', 1), None, key_added),
            res)
        self.assertIn(
            ((root, 'new_key', 2), None, key_added),
            res)
        
        
class TraceableTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls._d1 = {1: {2: "A", 3: {4: "B", 5: [1, 2, 3]}}}
        cls._d2 = {1: {2: "A_UPDATED", 3: {4: "B_UPDATED"}}}

    def test_basic(self):
        r1, r2, r3 = 1, 2, 3

        d1 = self._d1.copy()
        D1 = TraceableDict(d1)

        self.assertEquals(d1, D1.as_dict())
        self.assertEquals(D1.trace, {})
        self.assertEquals(D1.revisions, [])
        self.assertTrue(D1.has_uncommitted_changes)

        D1.commit(revision=r1)

        self.assertEquals(d1, D1.as_dict())
        self.assertEquals(D1.trace, {})
        self.assertEquals(D1.revisions, [r1])
        self.assertFalse(D1.has_uncommitted_changes)

        D1['new_key'] = 'new_val'
        self.assertTrue(D1.has_uncommitted_changes)
        print D1
        print D1.trace
        D1.commit(revision=r2)
        print D1
        print D1.trace
        d1['new_key'] = 'new_val'
        self.assertEquals(d1, D1.as_dict())
        self.assertEquals([r1, r2], D1.revisions)
        self.assertFalse(D1.has_uncommitted_changes)

        self.assertEquals(
            D1.trace,
            {str(r2): [((root, 'new_key'), None, key_added)]})

        D1.pop('new_key')
        D1.commit(revision=r3)
        self.assertNotEquals(d1, D1.as_dict())
        d1.pop('new_key')
        self.assertEquals(d1, D1.as_dict())
        self.assertEquals([r1, r2, r3], D1.revisions)

        self.assertEquals(
            D1.trace,
            {'2': [((root, 'new_key'), None, key_added)],
             '3': [((root, 'new_key'), 'new_val', key_removed)]})

    def test_new_traceable(self):
        r1, r2 = 1, 2

        d1 = self._d1.copy()
        D1 = TraceableDict(d1)

        self.assertEquals(d1, D1.as_dict())
        self.assertEquals(D1.trace, {})
        self.assertEquals(D1.revisions, [])
        self.assertTrue(D1.has_uncommitted_changes)

        D1['new_key'] = 'new_val'

        self.assertEquals(D1.as_dict(), {1: {2: 'A', 3: {4: 'B', 5: [1, 2, 3]}}, 'new_key': 'new_val'})
        self.assertEquals(D1.trace, {})
        self.assertEquals(D1.revisions, [])
        self.assertTrue(D1.has_uncommitted_changes)

        D1['new_key'] = 'updated_val'

        self.assertEquals(D1.as_dict(), {1: {2: 'A', 3: {4: 'B', 5: [1, 2, 3]}}, 'new_key': 'updated_val'})
        self.assertEquals(D1.trace, {})
        self.assertEquals(D1.revisions, [])
        self.assertTrue(D1.has_uncommitted_changes)

        D1.commit(revision=r1)

        self.assertFalse(D1.has_uncommitted_changes)
        self.assertEquals(D1.as_dict(), {1: {2: 'A', 3: {4: 'B', 5: [1, 2, 3]}}, 'new_key': 'updated_val'})
        self.assertEquals(D1.trace, {})
        self.assertEquals(D1.revisions, [r1])

    def test_full(self):
        r1 = int(time.time() * 1000)

        d1 = self._d1.copy()
        d2 = d1.copy()
        d2['new_key'] = 'new_val'

        D1 = TraceableDict(d1)
        D2 = TraceableDict(d2)
        D3 = TraceableDict(self._d2)

        D1 = D1 | D2
        D1_Base = TraceableDict(D1)
        D1.commit(revision=r1)

        self.assertEquals(D1.as_dict(), d2)
        self.assertEquals(D1.trace, {})
        self.assertEquals(D1.revisions, [r1])

        D1 = D1 | D3
        self.assertTrue(D1.has_uncommitted_changes)
        self.assertEquals(D1.as_dict(), self._d2)
        self.assertEquals(D1.revisions, [r1])

        r2 = int((time.time() - 5000) * 1000)
        with self.assertRaises(ValueError) as err:
            D1.commit(revision=r2)
        self.assertTrue('cannot commit to earlier revision' in err.exception)

        r2 = int((time.time() + 5000) * 1000)
        D1.commit(revision=r2)

        self.assertFalse(D1.has_uncommitted_changes)
        self.assertEquals(D1.as_dict(), self._d2)
        self.assertEquals(D1.revisions, [r1, r2])

        result_base = D1.checkout(revision=r1)
        self.assertEquals(result_base.as_dict(), D1_Base.as_dict())
        self.assertEquals(result_base.revisions, [r1])

    def test_pipe_immutable(self):
        d1 = self._d1.copy()
        d2 = d1.copy()
        d2['new_key'] = 'new_val'

        D1 = TraceableDict(d1)
        self.assertEquals(d1, D1.as_dict())

        D2 = TraceableDict(d2)

        D1_before = D1.copy()
        D1_tag = D1 | D2
        D1_tag.commit(revision=1)
        self.assertEquals(d2, D1_tag.as_dict())

        self.assertEquals(d1, D1.as_dict())
        self.assertFalse(D1.trace)
        self.assertEquals(D1, D1_before)

    def test_pipe_operator(self):
        r1, r2, r3 = 1, 2, 3

        d1 = self._d1.copy()
        d2 = d1.copy()
        d2['new_key'] = 'new_val'

        D1 = TraceableDict(d1)
        self.assertEquals(d1, D1.as_dict())

        D2 = TraceableDict(d2)
        D2.commit(revision=r2)
        self.assertEquals(d2, D2.as_dict())

        D1 = D1 | D2
        D1.commit(revision=r1)
        self.assertEquals(d2, D1.as_dict())

        self.assertEquals(D1.trace, {})

        D1['new_key'] = 'updated_value'
        D1.commit(revision=r2)
        self.assertEquals(
            D1.trace,
            {str(r2): [((root, 'new_key'), 'new_val', key_updated)]})

        D3 = TraceableDict(d1)

        D2 = D2 | D3
        D2.commit(revision=r3)
        self.assertEquals(d1, D2.as_dict())

        self.assertEquals(
            D2.trace,
            {str(r3): [((root, 'new_key'), 'new_val', key_removed)]})

    def test_pipe_operator_multiple(self):
        r1, r2 = 1, 2
        d1 = self._d1.copy()
        d2 = d1.copy()
        d2['new_key'] = 'new_val'

        D1 = TraceableDict(d2)
        D1.commit(revision=r1)
        D2 = TraceableDict(d1)
        D2.commit(revision=r1)
        D3 = TraceableDict(d2)
        D3.commit(revision=r1)

        D4 = D1 | D2 | D3
        D4.commit(revision=r2)
        self.assertEquals(d2, D4.as_dict())

        trace = D4.trace[str(r2)]
        self.assertIn(
            ((root, 'new_key'), 'new_val', key_removed),
            trace)
        self.assertIn(
            ((root, 'new_key'), None, key_added),
            trace)

    def test_init_traceable_dict(self):
        r1, r2 = int((time.time()*1) * 1000), int((time.time()*2) * 1000)

        td1 = TraceableDict({'a': 1, 'b':2})
        td1.commit(revision=r1)

        td1['a'] = 8
        td1.commit(revision=r2)

        self.assertEquals(td1.as_dict(), {'a': 8, 'b': 2})
        self.assertEquals(td1.trace, {str(r2): [(('_root_', 'a'), 1, key_updated)]})
        self.assertEquals(td1.revisions, [r1, r2])

        td2 = TraceableDict(td1)
        self.assertEquals(td2.as_dict(), td1.as_dict())
        self.assertEquals(td2.trace, td1.trace)
        self.assertEquals(td2.revisions, td1.revisions)


class CommitTest(unittest.TestCase):

    def test_basic(self):
        r1, r2 = 1, 2
        d1 = {"a": "aa", "b":"bb"}

        td1 = TraceableDict(d1)
        self.assertEquals([], td1.revisions)
        self.assertEquals({}, td1.trace)
        self.assertTrue(td1.has_uncommitted_changes)

        td1.commit(r1)
        self.assertEquals([r1], td1.revisions)
        self.assertEquals({}, td1.trace)
        self.assertFalse(td1.has_uncommitted_changes)

        td1["a"] = 1
        self.assertEquals([r1], td1.revisions)
        self.assertTrue(td1.has_uncommitted_changes)
        self.assertEquals(td1.as_dict(), {'a': 1, 'b': 'bb'})
        self.assertEquals(td1.trace, {uncommitted: [((root, 'a'), 'aa', key_updated)]})

        td1.commit(revision=r2)

        self.assertFalse(td1.has_uncommitted_changes)
        self.assertEquals(td1.as_dict(), {'a': 1, 'b': 'bb'})
        self.assertEquals(td1.trace, {str(r2): [((root, 'a'), 'aa', key_updated)]})
        self.assertEquals([r1, r2], td1.revisions)

    def test_first_commit(self):
        d1 = {"a": "aa", "b":"bb"}
        d2 = {"a": "aa", "b":"bb", "c": "cc"}

        td1 = TraceableDict(d1)
        self.assertEquals(d1, td1.as_dict())
        self.assertEquals([], td1.revisions)
        self.assertEquals({}, td1.trace)
        self.assertTrue(td1.has_uncommitted_changes)

        td2 = TraceableDict(d2)

        td1 = td1 | td2

        self.assertEquals(td2.as_dict(), td1.as_dict())
        self.assertEquals([], td1.revisions)
        self.assertEquals({}, td1.trace)
        self.assertTrue(td1.has_uncommitted_changes)

        r1 = 1
        td1.commit(revision=r1)

        self.assertEquals(td2.as_dict(), td1.as_dict())
        self.assertEquals([r1], td1.revisions)
        self.assertEquals({}, td1.trace)
        self.assertFalse(td1.has_uncommitted_changes)

    def test_commit_invalid_revision(self):
        d1 = {"a": "aa", "b":"bb"}
        td1 = TraceableDict(d1)
        self.assertEquals([], td1.revisions)
        self.assertTrue(td1.has_uncommitted_changes)

        with self.assertRaises(ValueError) as err:
            td1.commit(revision=None)

        self.assertTrue('revision cannot be None' in err.exception)
        self.assertTrue(td1.has_uncommitted_changes)
        self.assertEquals(td1.trace, {})
        self.assertEquals(td1.revisions, [])

        with self.assertRaises(ValueError) as err:
            td1.commit(revision='invalid')

        self.assertTrue('revision must be an integer' in err.exception)
        self.assertTrue(td1.has_uncommitted_changes)
        self.assertEquals(td1.trace, {})
        self.assertEquals(td1.revisions, [])

    def test_commit_current_revision(self):
        r1 = 1

        d1 = {"a": "aa", "b":"bb"}
        td1 = TraceableDict(d1)
        td1.commit(revision=r1)
        self.assertEquals([r1], td1.revisions)
        self.assertFalse(td1.has_uncommitted_changes)

        td1["a"] = 1
        self.assertTrue(td1.has_uncommitted_changes)

        with self.assertRaises(ValueError) as err:
            td1.commit(revision=r1)

        self.assertTrue('cannot commit to earlier revision' in err.exception)
        self.assertTrue(td1.has_uncommitted_changes)
        self.assertEquals(td1.trace, {uncommitted: [((root, 'a'), 'aa', key_updated)]})
        self.assertEquals([r1], td1.revisions)

    def test_commit_earlier_revision(self):
        r1 = 1
        td1 = TraceableDict({"a": "aa", "b":"bb"})
        td1.commit(revision=1)
        self.assertEquals([1], td1.revisions)
        self.assertFalse(td1.has_uncommitted_changes)

        td1["a"] = 1
        self.assertTrue(td1.has_uncommitted_changes)

        revision = 3
        td1.commit(revision=revision)
        self.assertEquals([r1, revision], td1.revisions)
        self.assertFalse(td1.has_uncommitted_changes)

        td1["a"] = 2
        self.assertTrue(td1.has_uncommitted_changes)

        earlier_revision = 2
        with self.assertRaises(ValueError) as err:
            td1.commit(revision=earlier_revision)

        self.assertTrue('cannot commit to earlier revision' in err.exception)
        self.assertTrue(td1.has_uncommitted_changes)
        self.assertEquals(td1.trace, {'3': [((root, 'a'), 'aa', key_updated)], uncommitted: [((root, 'a'), 1, key_updated)]})
        self.assertEquals([r1, revision], td1.revisions)

    def test_commit_no_diff(self):
        base_revision = 1
        d1 = {"a": "aa", "b":"bb"}

        td1 = TraceableDict(d1)
        td1.commit(revision=base_revision)
        self.assertEquals({}, td1.trace)
        self.assertEquals(d1, td1.as_dict())
        self.assertFalse(td1.has_uncommitted_changes)
        self.assertEquals([base_revision], td1.revisions)

        with pytest.warns(UserWarning, match='nothing to commit'):
            td1.commit(revision=18)

        self.assertEquals({}, td1.trace)
        self.assertEquals(d1, td1.as_dict())
        self.assertFalse(td1.has_uncommitted_changes)
        self.assertEquals([base_revision], td1.revisions)


class RevertTest(unittest.TestCase):

    def test_basic(self):
        base_revision = 0
        d1 = {"a": "aa", "b":"bb"}

        td1 = TraceableDict(d1)
        td1.commit(revision=base_revision)
        self.assertEquals([base_revision], td1.revisions)

        r1 = 1
        td1["a"] = 1
        td1.commit(revision=r1)

        r2 = 2
        td1["b"] = 2
        td1.commit(revision=r2)

        self.assertFalse(td1.has_uncommitted_changes)
        self.assertEquals(td1.as_dict(), {'a': 1, 'b': 2})
        self.assertEquals(td1.trace, {
            str(r1): [((root, 'a'), 'aa', key_updated)],
            str(r2): [((root, 'b'), 'bb', key_updated)]})
        self.assertEquals([base_revision, r1, r2], td1.revisions)

        td1["b"] = 3

        self.assertTrue(td1.has_uncommitted_changes)
        self.assertEquals(td1.as_dict(), {'a': 1, 'b': 3})
        self.assertEquals(td1.trace, {
            str(r1): [((root, 'a'), 'aa', key_updated)],
            str(r2): [((root, 'b'), 'bb', key_updated)],
            uncommitted:[((root, 'b'), 2, key_updated)]})
        self.assertEquals([base_revision, r1, r2], td1.revisions)

        td1.revert()

        self.assertFalse(td1.has_uncommitted_changes)
        self.assertEquals(td1.as_dict(), {"a": 1, "b": 2})
        self.assertEquals(td1.trace, {
            str(r1): [((root, 'a'), 'aa', key_updated)],
            str(r2): [((root, 'b'), 'bb', key_updated)]})
        self.assertEquals([base_revision, r1, r2], td1.revisions)

    def test_revert_no_revisions(self):
        d1 = {"a": "aa", "b":"bb"}

        td1 = TraceableDict(d1)
        self.assertTrue(td1.has_uncommitted_changes)
        self.assertEquals(td1.as_dict(), d1)
        self.assertEquals(td1.trace, {})
        self.assertEquals(td1.revisions, [])

        td1.revert()

        self.assertTrue(td1.has_uncommitted_changes)
        self.assertEquals(td1.as_dict(), d1)
        self.assertEquals(td1.trace, {})
        self.assertEquals(td1.revisions, [])

    def test_revert_to_first_revision(self):
        base_revision = 0
        d1 = {"a": "aa", "b":"bb"}

        td1 = TraceableDict(d1)
        td1.commit(revision=base_revision)
        self.assertFalse(td1.has_uncommitted_changes)
        self.assertEquals(td1.as_dict(), d1)
        self.assertEquals(td1.trace, {})
        self.assertEquals([base_revision], td1.revisions)

        td1["b"] = 1
        self.assertTrue(td1.has_uncommitted_changes)
        self.assertNotEquals(td1.as_dict(), d1)
        self.assertNotEquals(td1.trace, {})
        self.assertEquals([base_revision], td1.revisions)

        td1.revert()

        self.assertFalse(td1.has_uncommitted_changes)
        self.assertEquals(td1.as_dict(), d1)
        self.assertEquals(td1.trace, {})
        self.assertEquals([base_revision], td1.revisions)

    def test_revert_without_uncommitted_changes(self):
        r1, r2 = 1, 2
        d1 = {"a": "aa", "b":"bb"}

        td1 = TraceableDict(d1)
        td1.commit(revision=r1)
        self.assertEquals([r1], td1.revisions)
        self.assertEquals(td1.as_dict(), d1)
        self.assertEquals(td1.trace, {})
        self.assertFalse(td1.has_uncommitted_changes)

        td1.revert()

        self.assertEquals([r1], td1.revisions)
        self.assertEquals(td1.as_dict(), d1)
        self.assertEquals(td1.trace, {})
        self.assertFalse(td1.has_uncommitted_changes)

        td1["a"] = 1
        td1.commit(revision=r2)

        _trace = {str(r2): [((root, 'a'), 'aa', key_updated)]}

        self.assertEquals([r1, r2], td1.revisions)
        self.assertEquals(td1.as_dict(), {"a": 1, "b": "bb"})
        self.assertEquals(td1.trace, _trace)
        self.assertFalse(td1.has_uncommitted_changes)

        td1.revert()

        self.assertEquals([r1, r2], td1.revisions)
        self.assertEquals(td1.as_dict(), {"a": 1, "b": "bb"})
        self.assertEquals(td1.trace, _trace)
        self.assertFalse(td1.has_uncommitted_changes)


class CheckoutTests(unittest.TestCase):

    def test_basic(self):
        r1, r2, r3 = 1, 2, 3

        d1 = {"a": "aa", "b":"bb"}
        td1 = TraceableDict(d1)
        td1.commit(revision=r1)

        td1["a"] = 2
        td1.commit(revision=r2)

        td1["b"] = 3
        td1.commit(revision=r3)

        self.assertEquals(td1.as_dict(), {'a': 2, 'b': 3})
        self.assertEquals(td1.trace, {
            str(r2): [((root, 'a'), 'aa', key_updated)],
            str(r3): [((root, 'b'), 'bb', key_updated)]})
        self.assertEquals([r1, r2, r3], td1.revisions)

        result_r2 = td1.checkout(revision=r2)
        self.assertFalse(result_r2.has_uncommitted_changes)
        self.assertEquals(result_r2.as_dict(), {'a': 2, 'b': 'bb'})
        self.assertEquals(result_r2.trace, {str(r2): [((root, 'a'), 'aa', key_updated)]})
        self.assertEquals([r1, r2], result_r2.revisions)

        result_r1_1 = td1.checkout(revision=r1)
        self.assertFalse(result_r1_1.has_uncommitted_changes)
        self.assertEquals(result_r1_1.as_dict(), {'a': 'aa', 'b': 'bb'})
        self.assertEquals(result_r1_1.trace, {})
        self.assertEquals([r1], result_r1_1.revisions)

        result_r1_2 = result_r2.checkout(revision=r1)
        self.assertEquals(result_r1_1.has_uncommitted_changes, result_r1_2.has_uncommitted_changes)
        self.assertEquals(result_r1_1.as_dict(), result_r1_2.as_dict())
        self.assertEquals(result_r1_1.trace, result_r1_2.trace)
        self.assertEquals(result_r1_1.revisions, result_r1_2.revisions)

    def test_checkout_key_removed(self):
        r1, r2 = 1, 2

        d1 = {}
        d2 = {"a": "aa", "b":"bb"}

        td1 = TraceableDict(d1)
        td1.commit(revision=r1)
        td2 = TraceableDict(d2)
        td2.commit(revision=r1)

        td1 = td1 | td2
        td1.commit(revision=r2)

        result_r1 = td1.checkout(revision=r1)
        self.assertFalse(result_r1.has_uncommitted_changes)
        self.assertEquals(result_r1.as_dict(), d1)
        self.assertEquals(result_r1.trace, {})
        self.assertEquals([r1], result_r1.revisions)

    def test_checkout_no_revisions(self):
        d1 = {"a": "aa", "b":"bb"}
        td1 = TraceableDict(d1)

        with self.assertRaises(Exception) as err:
            td1.checkout(revision=1)
        self.assertTrue('no revisions available. you must commit an initial revision first.' in err.exception)

    def test_checkout_invalid_revision(self):
        d1 = {"a": "aa", "b":"bb"}
        td1 = TraceableDict(d1)
        td1.commit(revision=1)

        with self.assertRaises(ValueError) as err:
            td1.checkout(revision=None)
        self.assertTrue("revision must be an integer" in err.exception)

        with self.assertRaises(ValueError) as err:
            td1.checkout(revision="invalid")
        self.assertTrue("revision must be an integer" in err.exception)

    def test_checkout_unknown_revision(self):
        r1, r2, r3 = 1, 2, 3

        d1 = {"a": "aa", "b":"bb"}
        td1 = TraceableDict(d1)
        td1.commit(revision=r1)

        td1["a"] = 1
        td1.commit(revision=r2)

        td1["b"] = 2
        td1.commit(revision=r3)

        revision = 55
        with self.assertRaises(ValueError) as err:
            td1.checkout(revision=revision)
        self.assertTrue('unknown revision %s' % revision in err.exception)

    def test_checkout_current_revision(self):
        r1, r2 = 1, 2

        d1 = {"a": "aa", "b":"bb"}
        td1 = TraceableDict(d1)

        td1["a"] = 1
        td1.commit(revision=r1)

        td1["b"] = 2
        td1.commit(revision=r2)

        result_r2 = td1.checkout(revision=r2)
        self.assertEquals(result_r2.has_uncommitted_changes, td1.has_uncommitted_changes)
        self.assertEquals(result_r2.as_dict(), td1.as_dict())
        self.assertEquals(result_r2.trace, td1.trace)
        self.assertEquals(result_r2.revisions, td1.revisions)

    def test_checkout_uncommitted_changes(self):
        r1 = 1

        d1 = {"a": "aa", "b":"bb"}
        td1 = TraceableDict(d1)

        td1["a"] = 1
        td1.commit(revision=r1)

        td1["b"] = 2
        self.assertTrue(td1.has_uncommitted_changes)

        with self.assertRaises(Exception) as err:
            td1.checkout(revision=r1)
        self.assertTrue('dictionary has uncommitted changes. you must commit or revert first.' in err.exception)


class LogTests(unittest.TestCase):

    def test_basic(self):
        r1, r2, r3 = 1, 2, 3

        d1 = {"A": {"B": {"C": 1, "D": [2, 3]}}}
        d2 = {"A": {"B": {"C": 1, "D": [2, 3], "E": 4, "F": 5}}}
        d3 = {"A": {"B": {"C": 1, "D": [2, 3, 4]}}}

        td1 = TraceableDict(d1)
        td1.commit(revision=r1)
        td2 = TraceableDict(d2)
        td2.commit(revision=r1)
        td3 = TraceableDict(d3)
        td3.commit(revision=r1)

        td1 = td1 | td2
        td1.commit(revision=r2)

        td1 = td1 | td3
        td1["a"] = 1
        td1.commit(revision=r3)

        log = td1.log(path=("A",))
        self.assertEquals(log.keys(), [r1, r2, r3])
        self.assertEquals(log[r1], d1)
        self.assertEquals(log[r2], d2)
        self.assertEquals(log[r3], d3)

        log = td1.log(path=("A", "B"))
        self.assertEquals(log.keys(), [r1, r2, r3])
        self.assertEquals(log[r1], d1["A"])
        self.assertEquals(log[r2], d2["A"])
        self.assertEquals(log[r3], d3["A"])

        log = td1.log(path=("A", "B", "C"))
        self.assertEquals(log.keys(), [r1])
        self.assertEquals(log[r1], {"C": 1})

        log = td1.log(path=("A", "B", "D"))
        self.assertEquals(log.keys(), [r1, r3])
        self.assertEquals(log[r1], {"D": [2, 3]})
        self.assertEquals(log[r3], {"D": [2, 3, 4]})

        # TODO: Fix this! BaseRevision = {} r2 = {'E': {}}
        log = td1.log(path=("A", "B", "E"))
        self.assertEquals(log.keys(), [r1, r2, r3])
        self.assertEquals(log[r1], {})
        self.assertEquals(log[r2], {'E': 4})
        self.assertEquals(log[r3], {'E': {}})

        log = td1.log(path=("A", "B", "F"))
        self.assertEquals(log.keys(), [r1, r2, r3])
        self.assertEquals(log[r1], {})
        self.assertEquals(log[r2], {'F': 5})
        self.assertEquals(log[r3], {'F': {}})

        log = td1.log(path=('a',))
        self.assertEquals(log.keys(), [r1, r3])
        self.assertEquals(log[r1], {})
        self.assertEquals(log[r3], {'a': 1})

    def test_log_no_revisions(self):
        d1 = {"A": {"B": {"C": 1, "D": [2, 3]}}}
        td1 = TraceableDict(d1)

        log = td1.log(path=("A",))
        self.assertEquals(log.keys(), [])

    def test_log_uncommitted_changes(self):
        r1, r2 = 1, 2
        d1 = {"A": {"B": {"C": 1, "D": [2, 3], "E": 4}}}
        d2 = {"A": {"B": {"C": 1, "D": [2], "F": 5}}}

        td1 = TraceableDict(d1)
        td1.commit(revision=r1)
        td2 = TraceableDict(d2)
        td2.commit(revision=r1)

        td1 = td1 | td2
        self.assertTrue(td1.has_uncommitted_changes)

        log = td1.log(path=('A',))
        self.assertEquals(log.keys(), [r1])
        self.assertEquals(log[r1], d1)

        td1.commit(revision=r2)
        self.assertFalse(td1.has_uncommitted_changes)

        log = td1.log(path=('A',))
        self.assertEquals(log.keys(), [r1, r2])
        self.assertEquals(log[r1], d1)
        self.assertEquals(log[r2], d2)

    def test_log_invalid_path(self):
        r1 = 1

        d1 = {"A": 1, "B": 2}
        d2 = {"B": 1}

        td1 = TraceableDict(d1)
        td2 = TraceableDict(d2)

        td1 = td1 | td2
        td1.commit(revision=r1)

        invalid_path = None
        with self.assertRaises(TypeError) as err:
            td1.log(path=invalid_path)
        self.assertTrue('path must be tuple' in err.exception)

        invalid_path = 'A'
        with self.assertRaises(TypeError) as err:
            td1.log(path=invalid_path)
        self.assertTrue('path must be tuple' in err.exception)

        invalid_path = ()
        with self.assertRaises(ValueError) as err:
            td1.log(path=invalid_path)
        self.assertTrue('path cannot be empty' in err.exception)

        unknown_path = ('A', 'B')
        log = td1.log(path=unknown_path)
        self.assertEquals(log.keys(), [r1])
        self.assertEquals(log[r1], {'B': {}})


class DiffTests(unittest.TestCase):

    def test_basic(self):
        raise NotImplementedError


class RemoveTests(unittest.TestCase):

    def test_basic(self):
        r1, r2, r3, r4, r5 = 1, 2, 3, 4, 5

        d1 = {"a": "aa", "b":"bb"}
        d2 = {"a": "a", "b":"bb"}
        d3 = {"a": "a", "b":"b"}
        d4 = {"a": "a"}
        d5 = {"aa": "aa", "bb":"bb", "c":"c"}

        td1 = TraceableDict(d1)
        td1.commit(revision=r1)
        self.assertEquals(td1.as_dict(), d1)

        td1 = td1 | d2
        td1.commit(revision=r2)
        self.assertEquals(td1.as_dict(), d2)

        td1 = td1 | d3
        td1.commit(revision=r3)
        self.assertEquals(td1.as_dict(), d3)

        td1 = td1 | d4
        td1.commit(revision=r4)
        self.assertEquals(td1.as_dict(), d4)

        td1 = td1 | d5
        td1.commit(revision=r5)
        self.assertEquals(td1.as_dict(), d5)

        self.assertEquals(td1.revisions, [r1, r2, r3, r4, r5])

        td1.remove_oldest_revision()

        self.assertEquals(td1.as_dict(), d5)
        self.assertEquals(td1.revisions, [r2, r3, r4, r5])
        self.assertEquals(set(td1.trace.keys()), set([str(r3), str(r4), str(r5)]))

        td1.remove_oldest_revision()

        self.assertEquals(td1.as_dict(), d5)
        self.assertEquals(td1.revisions, [r3, r4, r5])
        self.assertEquals(set(td1.trace.keys()), set([str(r4), str(r5)]))

    def test_remove_no_revisions(self):
        d1 = {"a": "aa", "b":"bb"}

        td1 = TraceableDict(d1)
        self.assertEquals(td1.as_dict(), d1)
        self.assertEquals(td1.trace, {})
        self.assertEquals(td1.revisions, [])

        td1.remove_oldest_revision()

        self.assertEquals(td1.as_dict(), d1)
        self.assertEquals(td1.trace, {})
        self.assertEquals(td1.revisions, [])

    def test_remove_base_revision(self):
        r1, r2= 1, 2

        d1 = {"a": "aa", "b":"bb"}
        d2 = {"a": "a", "b":"bb"}

        td1 = TraceableDict(d1)
        td1.commit(revision=r1)
        self.assertEquals(td1.as_dict(), d1)

        td1 = td1 | d2
        td1.commit(revision=r2)
        self.assertEquals(td1.as_dict(), d2)

        self.assertEquals(td1.revisions, [r1, r2])

        td1.remove_oldest_revision()

        self.assertEquals(td1.as_dict(), d2)
        self.assertEquals(td1.revisions, [r2])
        self.assertEquals(td1.trace, {})

    def test_remove_uncommitted_changes(self):
        r1, r2 = 1, 2

        d1 = {"a": "aa", "b":"bb"}
        d2 = {"a": "a", "b":"bb"}
        d3 = {"a": "a", "b":"b"}

        td1 = TraceableDict(d1)
        td1.commit(revision=r1)
        self.assertEquals(td1.as_dict(), d1)

        td1 = td1 | d2
        td1.commit(revision=r2)
        self.assertEquals(td1.as_dict(), d2)

        td1 = td1 | d3
        self.assertEquals(td1.as_dict(), d3)
        self.assertTrue(td1.has_uncommitted_changes)

        self.assertEquals(td1.revisions, [r1, r2])
        self.assertEquals(set(td1.trace.keys()), set([str(r2), uncommitted]))

        td1.remove_oldest_revision()

        self.assertEquals(td1.as_dict(), d3)
        self.assertEquals(td1.revisions, [r2])
        self.assertEquals(set(td1.trace.keys()), set([uncommitted]))

        td1.remove_oldest_revision()

        self.assertEquals(td1.as_dict(), d3)
        self.assertEquals(td1.revisions, [r2])
        self.assertEquals(set(td1.trace.keys()), set([uncommitted]))

        td1.revert()

        self.assertEquals(td1.as_dict(), d2)
        self.assertEquals(td1.revisions, [r2])
        self.assertEquals(td1.trace, {})


if __name__ == '__main__':
    unittest.main()
