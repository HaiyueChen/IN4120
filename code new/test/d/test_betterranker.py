import unittest

class TestBetterRanker(unittest.TestCase):
    def setUp(self):
        from normalization import BrainDeadNormalizer
        from tokenization import BrainDeadTokenizer
        from corpus import InMemoryDocument, InMemoryCorpus
        from invertedindex import InMemoryInvertedIndex
        from ranking import BetterRanker
        normalizer = BrainDeadNormalizer()
        tokenizer = BrainDeadTokenizer()
        corpus = InMemoryCorpus()
        corpus.add_document(InMemoryDocument(0, {"title":"the foo", "static_quality_score": 0.9}))
        corpus.add_document(InMemoryDocument(1, {"title":"the foo", "static_quality_score": 0.2}))
        corpus.add_document(InMemoryDocument(2, {"title":"the foo foo", "static_quality_score": 0.2}))
        corpus.add_document(InMemoryDocument(3, {"title":"the bar"}))
        corpus.add_document(InMemoryDocument(4, {"title":"the bar bar"}))
        corpus.add_document(InMemoryDocument(5, {"title":"the baz"}))
        corpus.add_document(InMemoryDocument(6, {"title":"the baz"}))
        corpus.add_document(InMemoryDocument(7, {"title":"the baz baz"}))
        index = InMemoryInvertedIndex(corpus, ["title"], normalizer, tokenizer)
        self._ranker = BetterRanker(corpus, index)

    def test_term_frequency(self):
        from invertedindex import Posting
        self._ranker.reset(1)
        self._ranker.update("foo", 1, Posting(1, 1))
        score1 = self._ranker.evaluate()
        self._ranker.reset(2)
        self._ranker.update("foo", 1, Posting(1, 2))
        score2 = self._ranker.evaluate()
        self.assertGreater(score1, 0.0)
        self.assertGreater(score2, 0.0)
        self.assertGreater(score2, score1)

    def test_inverse_document_frequency(self):
        from invertedindex import Posting
        self._ranker.reset(3)
        self._ranker.update("the", 1, Posting(3, 1))
        self.assertAlmostEqual(self._ranker.evaluate(), 0.0, 8)
        self._ranker.reset(3)
        self._ranker.update("bar", 1, Posting(3, 1))
        score1 = self._ranker.evaluate()
        self._ranker.reset(5)
        self._ranker.update("baz", 1, Posting(5, 1))
        score2 = self._ranker.evaluate()
        self.assertGreater(score1, 0.0)
        self.assertGreater(score2, 0.0)
        self.assertGreater(score1, score2)

    def test_static_quality_score(self):
        from invertedindex import Posting
        self._ranker.reset(0)
        self._ranker.update("foo", 1, Posting(0, 1))
        score1 = self._ranker.evaluate()
        self._ranker.reset(1)
        self._ranker.update("foo", 1, Posting(1, 1))
        score2 = self._ranker.evaluate()
        self.assertGreater(score1, 0.0)
        self.assertGreater(score2, 0.0)
        self.assertGreater(score1, score2)

if __name__ == '__main__':
    unittest.main()
