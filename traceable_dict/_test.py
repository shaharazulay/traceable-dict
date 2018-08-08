import unittest


class DiffeTest(unittest.TestCase):
    from _diff import DictDiff
    
    def test_diff(self):
        pass

    
class TraceableTest(unittest.TestCase):
    import traceable_dict
    
    def test_basic(self):
        pass


if __name__ == '__main__':
    unittest.main()
