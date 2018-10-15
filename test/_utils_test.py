import unittest

from traceable_dict import DictDiff
from traceable_dict._utils import key_removed, key_added, key_updated, root
from traceable_dict._utils import nested_getitem, nested_setitem, nested_pop


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

        self.assertEquals(KeyRemoved(), '__r__')
        self.assertEquals('__u__', KeyUpdated())


class NestedUtilsTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls._d_nested = {
            1: {
                2: "A",
                3: {
                    4: "B", 5: [1, 2, 3]
                }
            }
        }

    def test_nested_getitem(self):

        k_nested = (1, 2)
        self.assertEquals(
            nested_getitem(self._d_nested, k_nested),
            self._d_nested[1][2])

        k_nested = (1, 3)
        self.assertEquals(
            nested_getitem(self._d_nested, k_nested),
            self._d_nested[1][3])

        k_nested = (root, 1, 3)
        self.assertEquals(
            nested_getitem(self._d_nested, k_nested),
            self._d_nested[1][3])

        bad_k_nested = (1, 999)
        self.assertEquals(
            nested_getitem(self._d_nested, bad_k_nested),
            {})


    def test_nested_setitem(self):
        from copy import deepcopy

        d = deepcopy(self._d_nested)
        k_nested = (1, 2)
        nested_setitem(d, k_nested, 'updated_value')
        self.assertEquals(
            d[1][2],
            'updated_value')

        d = deepcopy(self._d_nested)
        k_nested = (1, 3)
        nested_setitem(d, k_nested, 'updated_value')
        self.assertEquals(
            d[1][3],
            'updated_value')

        d = deepcopy(self._d_nested)
        k_nested = (root, 1, 3)
        nested_setitem(d, k_nested, 'updated_value')
        self.assertEquals(
            d[1][3],
            'updated_value')

        d = deepcopy(self._d_nested)
        new_k_nested = (1, 3, 'new_key')
        nested_setitem(d, new_k_nested, 'new_value')
        self.assertEquals(
            d[1][3]['new_key'],
            'new_value')


    def test_nested_pop(self):
        from copy import deepcopy

        d = deepcopy(self._d_nested)
        k_nested = (1, 2)
        nested_pop(d, k_nested)

        with self.assertRaises(Exception):
            d[1][2]

        value = nested_getitem(self._d_nested, k_nested)
        nested_setitem(d, k_nested, value)
        self.assertDictEqual(d, self._d_nested)

        d = deepcopy(self._d_nested)
        k_nested = (1, 3)
        nested_pop(d, k_nested)

        with self.assertRaises(Exception):
            d[1][3]

        value = nested_getitem(self._d_nested, k_nested)
        nested_setitem(d, k_nested, value)
        self.assertDictEqual(d, self._d_nested)

        d = deepcopy(self._d_nested)
        k_nested = (root, 1, 3)
        nested_pop(d, k_nested)

        with self.assertRaises(Exception):
            d[1][3]

        value = nested_getitem(self._d_nested, k_nested)
        nested_setitem(d, k_nested, value)
        self.assertDictEqual(d, self._d_nested)

        bad_k_nested = (1, 999)
        with self.assertRaises(Exception):
            nested_pop(d, bad_k_nested)

if __name__ == '__main__':
    unittest.main()
