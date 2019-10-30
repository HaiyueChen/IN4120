import unittest
from test import data_path

class TestSuffixArray(unittest.TestCase):
    def setUp(self):
        from normalization import BrainDeadNormalizer
        from tokenization import BrainDeadTokenizer
        self._normalizer = BrainDeadNormalizer()
        self._tokenizer = BrainDeadTokenizer()

    def _process_query_and_verify_winner(self, engine, query, winners, score):
        matches = []
        options = {"debug": False, "hit_count": 5}
        engine.evaluate(query, options, lambda m: matches.append(m))
        if winners:
            self.assertGreaterEqual(len(matches), 1)
            self.assertLessEqual(len(matches), 5)
            self.assertIn(matches[0]["document"].document_id, winners)
            if score:
                self.assertEqual(matches[0]["score"], score)
        else:
            self.assertEqual(len(matches), 0)

    def test_cran_corpus(self):
        import os.path
        from corpus import InMemoryCorpus
        from suffixarray import SuffixArray
        corpus = InMemoryCorpus(os.path.join(data_path,'cran.xml'))
        engine = SuffixArray(corpus, ["body"], self._normalizer, self._tokenizer)
        self._process_query_and_verify_winner(engine, "visc", [328], 11)
        self._process_query_and_verify_winner(engine, "Of  A", [946], 10)
        self._process_query_and_verify_winner(engine, "", [], None)
        self._process_query_and_verify_winner(engine, "approximate solution", [159, 1374], 3)

    def test_memory_usage(self):
        import tracemalloc
        import inspect
        from corpus import InMemoryDocument, InMemoryCorpus
        from suffixarray import SuffixArray
        corpus = InMemoryCorpus()
        corpus.add_document(InMemoryDocument(0, {"a": "o  o\n\n\no\n\no", "b": "o o\no   \no"}))
        corpus.add_document(InMemoryDocument(1, {"a": "ba", "b": "b bab"}))
        corpus.add_document(InMemoryDocument(2, {"a": "o  o O o", "b": "o o"}))
        corpus.add_document(InMemoryDocument(3, {"a": "oO" * 10000, "b": "o"}))
        corpus.add_document(InMemoryDocument(4, {"a": "cbab o obab O ", "b": "o o " * 10000}))
        tracemalloc.start()
        snapshot1 = tracemalloc.take_snapshot()
        engine = SuffixArray(corpus, ["a", "b"], self._normalizer, self._tokenizer)
        snapshot2 = tracemalloc.take_snapshot()
        tracemalloc.stop()
        for statistic in snapshot2.compare_to(snapshot1, "filename"):
            if statistic.traceback[0].filename == inspect.getfile(SuffixArray):
                self.assertLessEqual(statistic.size_diff, 2000000, "Memory usage seems excessive.")

    def test_multiple_fields(self):
        from corpus import InMemoryDocument, InMemoryCorpus
        from suffixarray import SuffixArray
        corpus = InMemoryCorpus()
        corpus.add_document(InMemoryDocument(0, {"field1": "a b c", "field2": "b c d"}))
        corpus.add_document(InMemoryDocument(1, {"field1": "x", "field2": "y"}))
        corpus.add_document(InMemoryDocument(2, {"field1": "y", "field2": "z"}))
        engine0 = SuffixArray(corpus, ["field1", "field2"], self._normalizer, self._tokenizer)
        engine1 = SuffixArray(corpus, ["field1"], self._normalizer, self._tokenizer)
        engine2 = SuffixArray(corpus, ["field2"], self._normalizer, self._tokenizer)
        self._process_query_and_verify_winner(engine0, "b c", [0], 2)
        self._process_query_and_verify_winner(engine0, "y", [1, 2], 1)
        self._process_query_and_verify_winner(engine1, "x", [1], 1)
        self._process_query_and_verify_winner(engine1, "y", [2], 1)
        self._process_query_and_verify_winner(engine1, "z", [], None)
        self._process_query_and_verify_winner(engine2, "z", [2], 1)


if __name__ == '__main__':
    unittest.main()
