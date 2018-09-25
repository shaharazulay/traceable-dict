import time
import unittest

from traceable_dict import DictDiff
from traceable_dict import TraceableDict
from traceable_dict import BaseRevision

from traceable_dict._utils import key_removed, key_added, key_updated, root


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
            [((root, 'new_key'), None, KeyAdded())],
            res)

        self.assertEquals(KeyAdded(), KeyAdded())
        self.assertEquals(('foo', key_added), ('foo', KeyAdded()))
        self.assertEquals((None, key_added), (None, KeyAdded()))

        self.assertEquals(KeyRemoved(), KeyRemoved())
        self.assertEquals(key_updated, KeyUpdated())


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
        r1, r2 = 1, 2

        d1 = self._d1.copy()
        D1 = TraceableDict(d1)

        self.assertEquals(d1, D1.freeze)
        self.assertEquals(D1.trace, {})
        self.assertEquals([BaseRevision], D1.revisions)
        self.assertFalse(D1.has_uncommitted_changes)

        D1['new_key'] = 'new_val'
        self.assertTrue(D1.has_uncommitted_changes)
        D1.commit(revision=r1)
        d1['new_key'] = 'new_val'
        self.assertEquals(d1, D1.freeze)
        self.assertEquals([BaseRevision, r1], D1.revisions)
        self.assertFalse(D1.has_uncommitted_changes)

        self.assertEquals(
            D1.trace,
            {(root, 'new_key'): [(None, key_added, r1)]})

        D1.pop('new_key')
        D1.commit(revision=r2)
        self.assertNotEquals(d1, D1.freeze)
        d1.pop('new_key')
        self.assertEquals(d1, D1.freeze)
        self.assertEquals([BaseRevision, r1, r2], D1.revisions)

        self.assertEquals(
            D1.trace,
            {(root, 'new_key'): [(None, key_added, r1), ('new_val', key_removed, r2)]})

    def test_full(self):
        r1 = int(time.time() * 1000)

        d1 = self._d1.copy()
        d2 = d1.copy()
        d2['new_key'] = 'new_val'

        D1 = TraceableDict(d1)
        D1_base = TraceableDict(d1)
        D2 = TraceableDict(d2)
        D3 = TraceableDict(self._d2)

        D1 = D1 | D2
        D1.commit(revision=r1)

        self.assertEquals(D1.freeze, d2)
        self.assertEquals(D1.trace, {(root, 'new_key'): [(None, key_added, r1)]})
        self.assertEquals(D1.revisions, [BaseRevision, r1])

        D1 = D1 | D3
        self.assertTrue(D1.has_uncommitted_changes)
        self.assertEquals(D1.freeze, self._d2)
        self.assertEquals(D1.revisions, [BaseRevision, r1])

        r2 = int((time.time() - 5000) * 1000)
        with self.assertRaises(ValueError) as err:
            D1.commit(revision=r2)
        self.assertTrue('cannot commit to earlier revision' in err.exception)

        r2 = int((time.time() + 5000) * 1000)
        D1.commit(revision=r2)

        self.assertFalse(D1.has_uncommitted_changes)
        self.assertEquals(D1.freeze, self._d2)
        self.assertEquals(D1.revisions, [BaseRevision, r1, r2])

        result_base = D1.checkout(revision=BaseRevision)
        self.assertEquals(result_base.freeze, D1_base.freeze)
        self.assertEquals(result_base.revisions, [BaseRevision])

    def test_pipe_immutable(self):
        d1 = self._d1.copy()
        d2 = d1.copy()
        d2['new_key'] = 'new_val'

        D1 = TraceableDict(d1)
        self.assertEquals(d1, D1.freeze)

        D2 = TraceableDict(d2)

        D1_before = D1.copy()
        D1_tag = D1 | D2
        D1_tag.commit(revision=1)
        self.assertEquals(d2, D1_tag.freeze)

        self.assertEquals(d1, D1.freeze)
        self.assertFalse(D1.trace)
        self.assertEquals(D1, D1_before)

    def test_pipe_operator(self):
        r1, r2, r3 = 1, 2, 3

        d1 = self._d1.copy()
        d2 = d1.copy()
        d2['new_key'] = 'new_val'

        D1 = TraceableDict(d1)
        self.assertEquals(d1, D1.freeze)

        D2 = TraceableDict(d2)
        self.assertEquals(d2, D2.freeze)

        D1 = D1 | D2
        D1.commit(revision=r2)
        self.assertEquals(d2, D1.freeze)

        self.assertEquals(
            D1.trace,
            {(root, 'new_key'): [(None, key_added, r2)]})

        D1['new_key'] = 'updated_value'
        D1.commit(revision=r2)
        self.assertEquals(
            D1.trace,
            {(root, 'new_key'): [(None, key_added, r2), ('new_val', key_updated, r2)]})

        D3 = TraceableDict(d1)

        D2 = D2 | D3
        D2.commit(revision=r3)
        self.assertEquals(d1, D2.freeze)

        self.assertEquals(
            D2.trace,
            {(root, 'new_key'): [('new_val', key_removed, r3)]})

    def test_pipe_operator_multiple(self):

        d1 = self._d1.copy()
        d2 = d1.copy()
        d2['new_key'] = 'new_val'

        D1 = TraceableDict(d2)
        D2 = TraceableDict(d1)
        D3 = TraceableDict(d2)

        D4 = D1 | D2 | D3
        D4.commit(revision=1)
        self.assertEquals(d2, D4.freeze)

        trace = D4.trace[(root, 'new_key')]
        self.assertIn(
            ('new_val', key_removed, 1),
            trace)
        self.assertIn(
            (None, key_added, 1),
            trace)


class CommitTest(unittest.TestCase):

    def test_basic(self):
        d1 = {"a": "aa", "b":"bb"}

        td1 = TraceableDict(d1)
        self.assertEquals([BaseRevision], td1.revisions)
        self.assertFalse(td1.has_uncommitted_changes)

        td1["a"] = 1
        self.assertEquals([BaseRevision], td1.revisions)
        self.assertTrue(td1.has_uncommitted_changes)
        self.assertEquals(td1.freeze, {'a': 1, 'b': 'bb'})
        self.assertEquals(td1.trace, {(root, 'a'): [('aa', key_updated, None)]})

        r1 = 1
        td1.commit(revision=r1)

        self.assertFalse(td1.has_uncommitted_changes)
        self.assertEquals(td1.freeze, {'a': 1, 'b': 'bb'})
        self.assertEquals(td1.trace, {(root, 'a'): [('aa', key_updated, 1)]})
        self.assertEquals([BaseRevision, r1], td1.revisions)

    def test_commit_none_revision(self):
        d1 = {"a": "aa", "b":"bb"}
        td1 = TraceableDict(d1)
        self.assertEquals([BaseRevision], td1.revisions)
        self.assertFalse(td1.has_uncommitted_changes)

        td1["a"] = 1
        self.assertTrue(td1.has_uncommitted_changes)

        with self.assertRaises(ValueError) as err:
            td1.commit(revision=None)

        self.assertTrue('revision cannot be None' in err.exception)
        self.assertTrue(td1.has_uncommitted_changes)
        self.assertEquals(td1.trace, {(root, 'a'): [('aa', key_updated, None)]})
        self.assertEquals([BaseRevision], td1.revisions)

    def test_commit_base_revision(self):
        d1 = {"a": "aa", "b":"bb"}
        td1 = TraceableDict(d1)
        self.assertEquals([BaseRevision], td1.revisions)
        self.assertFalse(td1.has_uncommitted_changes)

        td1["a"] = 1
        self.assertTrue(td1.has_uncommitted_changes)

        with self.assertRaises(ValueError) as err:
            td1.commit(revision=BaseRevision)

        self.assertTrue('cannot commit to base revision' in err.exception)
        self.assertTrue(td1.has_uncommitted_changes)
        self.assertEquals(td1.trace, {(root, 'a'): [('aa', key_updated, None)]})
        self.assertEquals([BaseRevision], td1.revisions)

    def test_commit_earlier_revision(self):
        td1 = TraceableDict({"a": "aa", "b":"bb"})
        self.assertEquals([BaseRevision], td1.revisions)
        self.assertFalse(td1.has_uncommitted_changes)

        td1["a"] = 1
        self.assertTrue(td1.has_uncommitted_changes)

        revision = 3
        td1.commit(revision=revision)
        self.assertEquals([BaseRevision, revision], td1.revisions)
        self.assertFalse(td1.has_uncommitted_changes)

        td1["a"] = 2
        self.assertTrue(td1.has_uncommitted_changes)

        earlier_revision = 2
        with self.assertRaises(ValueError) as err:
            td1.commit(revision=earlier_revision)

        self.assertTrue('cannot commit to earlier revision' in err.exception)
        self.assertTrue(td1.has_uncommitted_changes)
        self.assertEquals(td1.trace, {(root, 'a'): [('aa', key_updated, revision), (1, key_updated, None)]})
        self.assertEquals([BaseRevision, revision], td1.revisions)

    def test_commit_same_revision(self):
        td1 = TraceableDict({"a": "aa", "b":"bb"})
        self.assertEquals([BaseRevision], td1.revisions)
        self.assertFalse(td1.has_uncommitted_changes)

        td1["a"] = 1
        self.assertTrue(td1.has_uncommitted_changes)

        revision = 3
        td1.commit(revision=revision)
        self.assertEquals([BaseRevision, revision], td1.revisions)
        self.assertFalse(td1.has_uncommitted_changes)

        td1["a"] = 2
        self.assertTrue(td1.has_uncommitted_changes)
        self.assertEquals(td1.trace, {(root, 'a'): [('aa', key_updated, revision), (1, key_updated, None)]})

        td1.commit(revision=revision)
        self.assertEquals(td1.trace, {(root, 'a'): [('aa', key_updated, revision), (1, key_updated, revision)]})
        self.assertEquals([BaseRevision, revision], td1.revisions)
        self.assertFalse(td1.has_uncommitted_changes)

    def test_commit_no_diff(self):
        d1 = {"a": "aa", "b":"bb"}

        td1 = TraceableDict(d1)
        self.assertEquals({}, td1.trace)
        self.assertEquals(d1, td1.freeze)
        self.assertFalse(td1.has_uncommitted_changes)
        self.assertEquals([BaseRevision], td1.revisions)

        revision = 1
        td1.commit(revision=revision)
        self.assertEquals({}, td1.trace)
        self.assertEquals(d1, td1.freeze)
        self.assertFalse(td1.has_uncommitted_changes)
        self.assertEquals([BaseRevision, revision], td1.revisions)


class RevertTest(unittest.TestCase):

    def test_basic(self):
        d1 = {"a": "aa", "b":"bb"}

        td1 = TraceableDict(d1)
        self.assertEquals([BaseRevision], td1.revisions)

        r1 = 1
        td1["a"] = 1
        td1.commit(revision=r1)

        r2 = 2
        td1["b"] = 2
        td1.commit(revision=r2)

        self.assertFalse(td1.has_uncommitted_changes)
        self.assertEquals(td1.freeze, {"a": 1, "b": 2})
        self.assertEquals(td1.trace, {(root, "b"): [("bb", key_updated, 2)], (root, "a"): [("aa", key_updated, 1)]})
        self.assertEquals([BaseRevision, r1, r2], td1.revisions)

        td1["b"] = 3

        self.assertTrue(td1.has_uncommitted_changes)
        self.assertEquals(td1.freeze, {"a": 1, "b": 3})
        self.assertEquals(td1.trace, {(root, "b"): [("bb", key_updated, 2), (2, key_updated, None)], (root, "a"): [("aa", key_updated, 1)]})
        self.assertEquals([BaseRevision, r1, r2], td1.revisions)

        td1.revert()

        self.assertFalse(td1.has_uncommitted_changes)
        self.assertEquals(td1.freeze, {"a": 1, "b": 2})
        self.assertEquals(td1.trace, {(root, "b"): [("bb", key_updated, 2)], (root, "a"): [("aa", key_updated, 1)]})
        self.assertEquals([BaseRevision, r1, r2], td1.revisions)

    def test_revert_to_base_revision(self):
        d1 = {"a": "aa", "b":"bb"}

        td1 = TraceableDict(d1)
        self.assertFalse(td1.has_uncommitted_changes)
        self.assertEquals(td1.freeze, d1)
        self.assertEquals(td1.trace, {})
        self.assertEquals([BaseRevision], td1.revisions)

        td1["b"] = 1
        self.assertTrue(td1.has_uncommitted_changes)
        self.assertNotEquals(td1.freeze, d1)
        self.assertNotEquals(td1.trace, {})
        self.assertEquals([BaseRevision], td1.revisions)

        td1.revert()

        self.assertFalse(td1.has_uncommitted_changes)
        self.assertEquals(td1.freeze, d1)
        self.assertEquals(td1.trace, {})
        self.assertEquals([BaseRevision], td1.revisions)

    def test_revert_without_uncommitted_changes(self):
        d1 = {"a": "aa", "b":"bb"}

        td1 = TraceableDict(d1)
        self.assertEquals([BaseRevision], td1.revisions)
        self.assertEquals(td1.freeze, {"a": "aa", "b": "bb"})
        self.assertEquals(td1.trace, {})
        self.assertFalse(td1.has_uncommitted_changes)

        td1.revert()

        td1 = TraceableDict(d1)
        self.assertEquals([BaseRevision], td1.revisions)
        self.assertEquals(td1.freeze, {"a": "aa", "b": "bb"})
        self.assertEquals(td1.trace, {})
        self.assertFalse(td1.has_uncommitted_changes)

        r1 = 1
        td1["a"] = 1
        td1.commit(revision=r1)

        self.assertEquals([BaseRevision, r1], td1.revisions)
        self.assertEquals(td1.freeze, {"a": 1, "b": "bb"})
        self.assertEquals(td1.trace, {(root, 'a'): [('aa', key_updated, 1)]})
        self.assertFalse(td1.has_uncommitted_changes)

        td1.revert()

        self.assertEquals([BaseRevision, r1], td1.revisions)
        self.assertEquals(td1.freeze, {"a": 1, "b": "bb"})
        self.assertEquals(td1.trace, {(root, 'a'): [('aa', key_updated, 1)]})
        self.assertFalse(td1.has_uncommitted_changes)


class CheckoutTests(unittest.TestCase):

    def test_basic(self):
        r1, r2 = 1, 2

        d1 = {"a": "aa", "b":"bb"}
        td1 = TraceableDict(d1)

        td1["a"] = 1
        td1.commit(revision=r1)

        td1["b"] = 2
        td1.commit(revision=r2)

        self.assertEquals(td1.freeze, {'a': 1, 'b': 2})
        self.assertEquals(td1.trace, {(root, 'a'): [('aa', key_updated, r1)], (root, 'b'): [('bb', key_updated, r2)]})
        self.assertEquals([BaseRevision, r1, r2], td1.revisions)

        result_r1 = td1.checkout(revision=r1)
        self.assertFalse(result_r1.has_uncommitted_changes)
        self.assertEquals(result_r1.freeze, {'a': 1, 'b': 'bb'})
        self.assertEquals(result_r1.trace, {(root, 'a'): [('aa', key_updated, 1)]})
        self.assertEquals([BaseRevision, r1], result_r1.revisions)

        result_base = td1.checkout(revision=BaseRevision)
        self.assertFalse(result_base.has_uncommitted_changes)
        self.assertEquals(result_base.freeze, {'a': 'aa', 'b': 'bb'})
        self.assertEquals(result_base.trace, {})
        self.assertEquals([BaseRevision], result_base.revisions)

        result_base_2 = result_r1.checkout(revision=BaseRevision)
        self.assertEquals(result_base.has_uncommitted_changes, result_base_2.has_uncommitted_changes)
        self.assertEquals(result_base.freeze, result_base_2.freeze)
        self.assertEquals(result_base.trace, result_base_2.trace)
        self.assertEquals(result_base.revisions, result_base_2.revisions)

    def test_checkout_none_revision(self):
        d1 = {"a": "aa", "b":"bb"}
        td1 = TraceableDict(d1)

        with self.assertRaises(ValueError) as err:
            td1.checkout(revision=None)
        self.assertTrue('unknown revision None' in err.exception)

    def test_checkout_unknown_revision(self):
        r1, r2 = 1, 2

        d1 = {"a": "aa", "b":"bb"}
        td1 = TraceableDict(d1)

        td1["a"] = 1
        td1.commit(revision=r1)

        td1["b"] = 2
        td1.commit(revision=r2)

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
        self.assertEquals(result_r2.freeze, td1.freeze)
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


if __name__ == '__main__':
    unittest.main()
