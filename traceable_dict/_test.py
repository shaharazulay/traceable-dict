import unittest

from traceable_dict._utils import key_removed, key_added, key_updated
from traceable_dict._diff import DictDiff, root

from traceable_dict import TraceableDict


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
        
        
class TraceableTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls._d1 = {1: {2: "A", 3: {4: "B", 5: [1, 2, 3]}}}
        cls._d2 = {1: {2: "A_UPDATED", 3: {4: "B_UPDATED"}}}
 
    def test_basic(self):
        d1 = self._d1.copy()
        D1 = TraceableDict(d1)
        self.assertEquals(d1, D1.freeze)

        self.assertEquals(D1.trace, {})
        
        D1['new_key'] = 'new_val'
        d1['new_key'] = 'new_val'
        self.assertEquals(d1, D1.freeze)

        self.assertEquals(
            D1.trace,
            {(root, 'new_key'): [(None, key_added)]})

        D1.pop('new_key')
        self.assertNotEquals(d1, D1.freeze)
        d1.pop('new_key')
        self.assertEquals(d1, D1.freeze)

        self.assertEquals(
            D1.trace,
            {(root, 'new_key'): [(None, key_added), ('new_val', key_removed)]})

    def test_pipe_immutable(self):
        d1 = self._d1.copy()
        d2 = d1.copy()
        d2['new_key'] = 'new_val'
        
        D1 = TraceableDict(d1)
        self.assertEquals(d1, D1.freeze)

        D1_before = D1.copy()
        D1_tag = D1 | d2
        self.assertEquals(d2, D1_tag.freeze)

        self.assertEquals(d1, D1.freeze)
        self.assertFalse(D1.trace)
        self.assertEquals(D1, D1_before)
        
    def test_pipe_operator(self):
        d1 = self._d1.copy()
        d2 = d1.copy()
        d2['new_key'] = 'new_val'
        
        D1 = TraceableDict(d1)
        self.assertEquals(d1, D1.freeze)
        
        D1 = D1 | d2
        self.assertEquals(d2, D1.freeze)
        
        self.assertEquals(
            D1.trace,
            {(root, 'new_key'): [(None, key_added)]})

        D2 = TraceableDict(d2)
        self.assertEquals(d2, D2.freeze)
        D2 = D2 | d1
        self.assertEquals(d1, D2.freeze)
        
        self.assertEquals(
            D2.trace,
            {(root, 'new_key'): [('new_val', key_removed)]})

        D1 = TraceableDict(d1)
        D2 = TraceableDict(d2)
        D3 = D2 | D1 | D2
        self.assertEquals(d2, D3.freeze)

        trace = D3.trace[(root, 'new_key')]
        self.assertIn(
            ('new_val', key_removed),
            trace)
        self.assertIn(
            (None, key_added),
            trace)
        

if __name__ == '__main__':
    unittest.main()
