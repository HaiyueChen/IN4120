import unittest


class TestInMemoryDictionary(unittest.TestCase):
    def test_access_vocabulary(self):
        from dictionary import InMemoryDictionary
        vocabulary = InMemoryDictionary()
        vocabulary.add_if_absent("foo")
        vocabulary.add_if_absent("bar")
        vocabulary.add_if_absent("foo")
        self.assertEqual(len(vocabulary), 2)
        self.assertEqual(vocabulary.size(), 2)
        self.assertEqual(vocabulary.get_term_id("foo"), 0)
        self.assertEqual(vocabulary.get_term_id("bar"), 1)
        self.assertEqual(vocabulary["bar"], 1)
        self.assertIn("bar", vocabulary)
        self.assertNotIn("wtf", vocabulary)
        self.assertIsNone(vocabulary.get_term_id("wtf"))
        self.assertListEqual(sorted([v for v in vocabulary]), [("bar", 1), ("foo", 0)])
