import unittest


class TestBrainDeadRanker(unittest.TestCase):
    def setUp(self):
        from ranking import BrainDeadRanker
        self._ranker = BrainDeadRanker()

    def test_term_frequency(self):
        from invertedindex import Posting
        self._ranker.reset(21)
        self._ranker.update("foo", 2, Posting(21, 4))
        self._ranker.update("bar", 1, Posting(21, 3))
        self.assertEqual(self._ranker.evaluate(), 11)
        self._ranker.reset(42)
        self._ranker.update("foo", 1, Posting(42, 1))
        self._ranker.update("baz", 2, Posting(42, 2))
        self.assertEqual(self._ranker.evaluate(), 5)
