import warnings
import time
import unittest
import warnings


from traceable_dict import TraceableDict

from traceable_dict._utils import key_removed, key_added, key_updated, root, uncommitted


class _WarningTestMixin(object):
    """A test which checks if the specified warning was raised"""

    def assertWarns(self, warning, callable, msg, *args, **kwds):
        with warnings.catch_warnings(record=True) as warning_list:
            warnings.simplefilter('always')

            result = callable(*args, **kwds)

            self.assertTrue(any(item.category == warning for item in warning_list))
            self.assertTrue(msg == str(warning_list[-1].message))


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
        D1.commit(revision=r2)

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

    def test_new_value_is_traceable(self):
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


class CommitTest(unittest.TestCase, _WarningTestMixin):

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

        td_with_previous_revisions = TraceableDict(td1)
        self.assertFalse(td_with_previous_revisions.has_uncommitted_changes)

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

        self.assertWarns(
            UserWarning,
            td1.commit,
            msg='nothing to commit',
            revision=18
        )

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
        self.assertTrue(td1.has_uncommitted_changes)
        self.assertEquals(
            td1.trace,
            {uncommitted: [((root, 'a'), 'aa', key_updated)]})

        self.assertEquals(td1.as_dict(), {"a": 1, "b": "bb"})
        td1.revert()
        self.assertEquals(td1.as_dict(), {"a": "aa", "b": "bb"})
        self.assertEquals(td1.trace, {})

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


class AsDictTest(unittest.TestCase):

    def test_basic(self):
        base_revision = 0
        d1 = {"a": 1, "b":2, "c": 3}

        td1 = TraceableDict(d1)
        td1.commit(revision=base_revision)
        self.assertEquals([base_revision], td1.revisions)
        self.assertEqual(d1, td1.as_dict())

        r1 = 1
        td1["a"] = "updated"
        td1.commit(revision=r1)
        self.assertEqual(td1.as_dict(), {"a": "updated", "b":2, "c": 3})

        td1["b"] = "also_updated"
        self.assertTrue(td1.has_uncommitted_changes)
        self.assertEqual(td1.as_dict(), {"a": "updated", "b": "also_updated", "c": 3})


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

        unknown_revision = 55
        with self.assertRaises(ValueError) as err:
            td1.checkout(revision=unknown_revision)
        self.assertTrue('unknown revision %s' % unknown_revision in err.exception)

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

        td1 = td1 | d2
        td1.commit(revision=r2)

        td1 = td1 | d3
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

        log = td1.log(path=("A", "B", "E"))
        self.assertEquals(log.keys(), [r2, r3])
        self.assertEquals(log[r2], {'E': 4})
        self.assertEquals(log[r3], {'E': {}})

        log = td1.log(path=("A", "B", "F"))
        self.assertEquals(log.keys(), [r2, r3])
        self.assertEquals(log[r2], {'F': 5})
        self.assertEquals(log[r3], {'F': {}})

        log = td1.log(path=('a',))
        self.assertEquals(log.keys(), [r3])
        self.assertEquals(log[r3], {'a': 1})

    def test_key_not_in_base_revision(self):
        r1, r2, r3 = 1, 2, 3

        d1 = {"A": {"B": {"C": 1, "D": [2, 3]}}}
        d2 = {"A": {"B": {"C": 1, "D": [2, 3], "E": 4, "F": 5}}}
        d3 = {"A": {"B": {"C": 1, "D": [2, 3, 4]}}}

        td1 = TraceableDict(d1)
        td1.commit(revision=r1)

        td1 = td1 | d2
        td1.commit(revision=r2)

        td1 = td1 | d3
        td1.commit(revision=r3)

        log = td1.log(path=("A", "B", "E"))
        self.assertEquals(log.keys(), [r2, r3])
        self.assertEquals(log[r2], {'E': 4})
        self.assertEquals(log[r3], {'E': {}})

        log = td1.log(path=("A", "B", "F"))
        self.assertEquals(log.keys(), [r2, r3])
        self.assertEquals(log[r2], {'F': 5})
        self.assertEquals(log[r3], {'F': {}})

    def test_key_removed_and_returns(self):
        r1, r2, r3 = 1, 2, 3

        d1 = {"A": {"B": {"C": 1, "D": [2, 3]}}}
        d2 = {"A": {"B": {"D": [2, 3], "E": 4, "F": 5}}}
        d3 = {"A": {"B": {"C": 1, "D": [2, 3, 4]}}}

        td1 = TraceableDict(d1)
        td1.commit(revision=r1)

        td1 = td1 | d2
        td1.commit(revision=r2)

        td1 = td1 | d3
        td1.commit(revision=r3)

        log = td1.log(path=("A", "B", "C"))
        self.assertEquals(log.keys(), [r1, r2, r3])
        self.assertEquals(log[r1], {'C': 1})
        self.assertEquals(log[r2], {'C': {}})
        self.assertEquals(log[r3], {'C': 1})

    def test_key_not_changing_in_revision(self):
        r1, r2, r3, r4 = 1, 2, 3, 4

        d1 = {"A": {"B": {"C": 1}}}
        d2 = {"A": {"B": {"C": 2}}}
        d3 = {"A": {"B": {"C": 2, "D": 1}}}
        d4 = {"A": {"B": {"C": 3, "D": 1}}}

        td1 = TraceableDict(d1)
        td1.commit(revision=r1)

        td1 = td1 | d2
        td1.commit(revision=r2)

        td1 = td1 | d3
        td1.commit(revision=r3)

        td1 = td1 | d4
        td1.commit(revision=r4)

        log = td1.log(path=("A", "B", "C"))
        self.assertEquals(log.keys(), [r1, r2, r4])
        self.assertEquals(log[r1], {'C': 1})
        self.assertEquals(log[r2], {'C': 2})
        self.assertEquals(log[r4], {'C': 3})

        d1 = {"A": {"B": {"D": 1}}}
        d2 = {"A": {"B": {"C": 2}}}
        d3 = {"A": {"B": {"C": 2, "D": 1}}}
        d4 = {"A": {"B": {"C": 3, "D": 1}}}

        td1 = TraceableDict(d1)
        td1.commit(revision=r1)

        td1 = td1 | d2
        td1.commit(revision=r2)

        td1 = td1 | d3
        td1.commit(revision=r3)

        td1 = td1 | d4
        td1.commit(revision=r4)

        log = td1.log(path=("A", "B", "C"))
        self.assertEquals(log.keys(), [r2, r4])
        self.assertEquals(log[r2], {'C': 2})
        self.assertEquals(log[r4], {'C': 3})

    def test_log_no_revisions(self):
        d1 = {"A": {"B": {"C": 1, "D": [2, 3]}}}
        td1 = TraceableDict(d1)

        log = td1.log(path=("A",))
        self.assertEquals(log, {})

    def test_log_uncommitted_changes(self):
        r1, r2 = 1, 2
        d1 = {"A": {"B": {"C": 1, "D": [2, 3], "E": 4}}}
        d2 = {"A": {"B": {"C": 1, "D": [2], "F": 5}}}

        td1 = TraceableDict(d1)
        td1.commit(revision=r1)

        td1 = td1 | d2
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
        self.assertEquals(log.keys(), [])
        self.assertEquals(log, {})


class DiffTests(unittest.TestCase):

    def test_basic(self):
        r1, r2, r3, r4 = 1, 2, 3, 4

        d1 = {"A": {"B": {"C": 1, "D": [2, 3]}}}
        d2 = {"A": {"B": {"C": 2, "D": [2, 3]}}}
        d3 = {"A": {"B": {"D": [2, 3, 5]}}}
        d4 = {"A": {"B": {"D": [2, 3, 5], "E": 1}}}

        td1 = TraceableDict(d1)
        td1.commit(revision=r1)

        td1 = td1 | d2
        td1.commit(revision=r2)

        td1 = td1 | d3
        td1.commit(revision=r3)

        td1 = td1 | d4
        td1.commit(revision=r4)

        diff = td1.diff(revision=1)
        self.assertFalse(diff)

        diff = td1.diff(revision=2)
        self.assertEquals(
            diff,
            {"A": {"B": {"C": "---1 +++2", "D": [2, 3]}}}
        )

        diff = td1.diff(revision=3)
        self.assertEquals(
            diff,
            {"A": {"B": {"C": "---2", "D": "---[2, 3] +++[2, 3, 5]"}}}
        )

        diff = td1.diff(revision=4)
        self.assertEquals(
            diff,
            {"A": {"B": {"D": [2, 3, 5], "E": "+++1"}}}
        )

    def test_with_target_path(self):
        r1, r2, r3, r4 = 1, 2, 3, 4

        d1 = {"A": {"B": {"C": 1, "D": [2, 3]}}}
        d2 = {"A": {"B": {"C": 2, "D": [2, 3]}}}
        d3 = {"A": {"B": {"D": [2, 3, 5]}}}
        d4 = {"A": {"B": {"D": [2, 3, 5], "E": 1}}}

        td1 = TraceableDict(d1)
        td1.commit(revision=r1)

        td1 = td1 | d2
        td1.commit(revision=r2)

        td1 = td1 | d3
        td1.commit(revision=r3)

        td1 = td1 | d4
        td1.commit(revision=r4)

        diff = td1.diff(revision=1, path=('A', 'B'))
        self.assertFalse(diff)

        diff = td1.diff(revision=2, path=('A', 'B'))
        self.assertEquals(
            diff,
            {"B": {"C": "---1 +++2", "D": [2, 3]}}
        )

        diff = td1.diff(revision=3, path=('A', 'B', 'C'))
        self.assertEquals(
            diff,
            {"C": "---2"}
        )

        diff = td1.diff(revision=4, path=('A', 'B'))
        self.assertEquals(
            diff,
            {"B": {"D": [2, 3, 5], "E": "+++1"}}
        )


        diff = td1.diff(revision=4, path=('A', 'B', 'E'))
        self.assertFalse(diff)

    def test_log_no_revisions(self):
        d1 = {"A": {"B": {"C": 1, "D": [2, 3]}}}
        td1 = TraceableDict(d1)

        diff = td1.diff()
        self.assertFalse(diff)

        diff = td1.diff(revision=1)
        self.assertFalse(diff)

    def test_diff_base_revision(self):
        d1 = {"A": {"B": {"C": 1, "D": [2, 3]}}}
        td1 = TraceableDict(d1)
        td1.commit(revision=1)

        diff = td1.diff(revision=1)
        self.assertFalse(diff)

    def test_diff_working_tree(self):
        d1 = {"A": {"B": {"C": 1, "D": [2, 3]}}}
        d2 = {"A": {"B": {"C": 2, "D": [2, 3]}}}

        td1 = TraceableDict(d1)
        td1.commit(revision=1)

        diff = td1.diff()
        self.assertFalse(diff)

        td1 = td1 | d2
        diff = td1.diff()
        self.assertEquals(
            diff,
            {"A": {"B": {"C": "---1 +++2", "D": [2, 3]}}}
        )

        diff = td1.diff(path=("A", "B"))
        self.assertEquals(
            diff,
            {"B": {"C": "---1 +++2", "D": [2, 3]}}
        )

    def test_diff_invalid_revision(self):
        d1 = {"A": {"B": {"C": 1, "D": [2, 3]}}}

        td1 = TraceableDict(d1)
        td1.commit(revision=1)

        unknown_revision = 2
        with self.assertRaises(ValueError) as err:
            td1.diff(revision=unknown_revision)
        self.assertTrue('unknown revision %s' % unknown_revision in err.exception)

        with self.assertRaises(ValueError) as err:
            td1.diff(revision=unknown_revision, path=('A', 'B'))
        self.assertTrue('unknown revision %s' % unknown_revision in err.exception)


class RemoveOldestRevisionTests(unittest.TestCase):

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

        td_past_revision = td1.checkout(revision=r2)
        self.assertEquals(td_past_revision.as_dict(), d2)

        td1.remove_oldest_revision()

        self.assertEquals(td1.as_dict(), d5)
        self.assertEquals(td1.revisions, [r3, r4, r5])
        self.assertEquals(set(td1.trace.keys()), set([str(r4), str(r5)]))

        td_past_revision = td1.checkout(revision=r3)
        self.assertEquals(td_past_revision.as_dict(), d3)

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
        r1, r2 = 1, 2

        d1 = {"a": "a", "b":"b"}
        d2 = {"a": "a_updated", "b":"b_updated"}

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

        td1.remove_oldest_revision()

        self.assertEquals(td1.as_dict(), d2)
        self.assertEquals(td1.revisions, [r2])
        self.assertEquals(td1.trace, {})

    def test_remove_uncommitted_changes(self):
        r1, r2 = 1, 2

        d1 = {"a": "a", "b":"b"}
        d2 = {"a": "a_updated", "b":"b"}
        d3 = {"a": "a_updated", "b":"b_updated"}

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