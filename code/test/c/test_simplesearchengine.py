import unittest
from test import data_path

class TestSimpleSearchEngine(unittest.TestCase):
    def setUp(self):
        from normalization import BrainDeadNormalizer
        from tokenization import BrainDeadTokenizer
        self._normalizer = BrainDeadNormalizer()
        self._tokenizer = BrainDeadTokenizer()

    def _process_two_term_query_verify_matches(self, query, engine, options, expected):
        from ranking import BrainDeadRanker
        ranker = BrainDeadRanker()
        matches = []
        hits, winners = expected
        engine.evaluate(query, options, ranker, lambda m: matches.append((m["score"], m["document"].document_id)))
        self.assertEqual(len(matches), hits)
        for (score, winner) in matches[:len(winners)]:
            self.assertEqual(score, 2.0)
            self.assertIn(winner, winners)
        for (score, contender) in matches[len(winners):]:
            self.assertEqual(score, 1.0)

    def test_mesh_corpus(self):
        import os.path
        from corpus import InMemoryCorpus
        from invertedindex import InMemoryInvertedIndex
        from searchengine import SimpleSearchEngine
        corpus = InMemoryCorpus(os.path.join(data_path, 'mesh.txt'))
        index = InMemoryInvertedIndex(corpus, ["body"], self._normalizer, self._tokenizer)
        engine = SimpleSearchEngine(corpus, index)
        query = "polluTION Water"
        self._process_two_term_query_verify_matches(query, engine,
                                                    {"match_threshold": 0.1, "hit_count": 10},
                                                    (10, [25274, 25275, 25276]))
        self._process_two_term_query_verify_matches(query, engine,
                                                    {"match_threshold": 1.0, "hit_count": 10},
                                                    (3, [25274, 25275, 25276]))

    def _process_query_verify_matches(self, query, engine, options, expected):
        from itertools import takewhile
        from ranking import BrainDeadRanker
        ranker = BrainDeadRanker()
        matches = []
        hits, score, winners = expected
        engine.evaluate(query, options, ranker, lambda m: matches.append((m["score"], m["document"].document_id)))
        self.assertEqual(len(matches), hits)
        if matches:
            for i in range(1, hits):
                self.assertGreaterEqual(matches[i - 1][0], matches[i][0])
            if score:
                self.assertEqual(matches[0][0], score)
            if winners:
                top = takewhile(lambda m: m[0] == matches[0][0], matches)
                self.assertListEqual(winners, list(sorted([m[1] for m in top])))

    def test_synthetic_corpus(self):
        from itertools import product, combinations_with_replacement
        from corpus import InMemoryDocument, InMemoryCorpus
        from invertedindex import InMemoryInvertedIndex
        from searchengine import SimpleSearchEngine
        corpus = InMemoryCorpus()
        words = ("".join(term) for term in product("bcd", "aei", "jkl"))
        texts = (" ".join(word) for word in combinations_with_replacement(words, 3))
        for text in texts:
            corpus.add_document(InMemoryDocument(corpus.size(), {"a": text}))
        engine = SimpleSearchEngine(corpus, InMemoryInvertedIndex(corpus, ["a"], self._normalizer, self._tokenizer))
        epsilon = 0.0001
        self._process_query_verify_matches("baj BAJ    baj", engine,
                                           {"match_threshold": 1.0, "hit_count": 27},
                                           (27, 9.0, [0]))
        self._process_query_verify_matches("baj caj", engine,
                                           {"match_threshold": 1.0, "hit_count": 100},
                                           (27, None, None))
        self._process_query_verify_matches("baj caj daj", engine,
                                           {"match_threshold": 2/3 + epsilon, "hit_count": 100},
                                           (79, None, None))
        self._process_query_verify_matches("baj caj", engine,
                                           {"match_threshold": 2/3 + epsilon, "hit_count": 100},
                                           (100, 3.0, [0, 9, 207, 2514]))
        self._process_query_verify_matches("baj cek dil", engine,
                                           {"match_threshold": 1.0, "hit_count": 10},
                                           (1, 3.0, [286]))
        self._process_query_verify_matches("baj cek dil", engine,
                                           {"match_threshold": 1.0, "hit_count": 10},
                                           (1, None, None))
        self._process_query_verify_matches("baj cek dil", engine,
                                           {"match_threshold": 2/3 + epsilon, "hit_count": 80},
                                           (79, 3.0, [13, 26, 273, 286, 377, 3107, 3198]))
        self._process_query_verify_matches("baj xxx yyy", engine,
                                           {"match_threshold": 2/3 + epsilon, "hit_count": 100},
                                           (0, None, None))
        self._process_query_verify_matches("baj xxx yyy", engine,
                                           {"match_threshold": 2/3 - epsilon, "hit_count": 100},
                                           (100, None, None))

    def test_document_at_a_time_traversal_mesh_corpus(self):
        from typing import Iterator, List, Tuple
        import os.path
        from invertedindex import Posting, InvertedIndex, InMemoryInvertedIndex
        from corpus import InMemoryCorpus
        from searchengine import SimpleSearchEngine
        from ranking import BrainDeadRanker

        class AccessLoggedIterator(Iterator[Posting]):
            def __init__(self, term: str, history: List[Tuple[str, int]], wrapped: Iterator[Posting]):
                self._term = term
                self._history = history
                self._wrapped = wrapped

            def __next__(self):
                posting = next(self._wrapped)
                self._history.append((self._term, posting.document_id))
                return posting

        class AccessLoggedInvertedIndex(InvertedIndex):
            def __init__(self, wrapped: InvertedIndex):
                self._wrapped = wrapped
                self._history = []

            def get_terms(self, buffer: str) -> Iterator[str]:
                return self._wrapped.get_terms(buffer)

            def get_postings_iterator(self, term: str) -> Iterator[Posting]:
                return AccessLoggedIterator(term, self._history, self._wrapped.get_postings_iterator(term))

            def get_document_frequency(self, term: str) -> int:
                return self._wrapped.get_document_frequency(term)

            def get_history(self) -> List[Tuple[str, int]]:
                return self._history

        corpus = InMemoryCorpus(os.path.join(data_path, 'mesh.txt'))
        index = AccessLoggedInvertedIndex(InMemoryInvertedIndex(corpus, ["body"], self._normalizer, self._tokenizer))
        engine = SimpleSearchEngine(corpus, index)
        ranker = BrainDeadRanker()
        query = "Water  polluTION"
        options = {"match_threshold": 0.5, "hit_count": 1, "debug": False}
        engine.evaluate(query, options, ranker, lambda m: None)
        history = index.get_history()
        ordering1 = [('water', 3078),  # Document-at-a-time ordering if evaluated as "water pollution".
                     ('pollution', 788), ('pollution', 789), ('pollution', 790), ('pollution', 8079),
                     ('water', 8635),
                     ('pollution', 23837),
                     ('water', 9379), ('water', 23234), ('water', 25265),
                     ('pollution', 25274),
                     ('water', 25266), ('water', 25267), ('water', 25268), ('water', 25269), ('water', 25270),
                     ('water', 25271), ('water', 25272), ('water', 25273), ('water', 25274), ('water', 25275),
                     ('pollution', 25275),
                     ('water', 25276),
                     ('pollution', 25276),
                     ('water', 25277), ('water', 25278), ('water', 25279), ('water', 25280), ('water', 25281)]
        ordering2 = [('pollution', 788),  # Document-at-a-time ordering if evaluated as "pollution water".
                     ('water', 3078),
                     ('pollution', 789), ('pollution', 790), ('pollution', 8079),
                     ('water', 8635),
                     ('pollution', 23837),
                     ('water', 9379), ('water', 23234), ('water', 25265),
                     ('pollution', 25274),
                     ('water', 25266), ('water', 25267), ('water', 25268), ('water', 25269), ('water', 25270),
                     ('water', 25271), ('water', 25272), ('water', 25273), ('water', 25274),
                     ('pollution', 25275),
                     ('water', 25275),
                     ('pollution', 25276),
                     ('water', 25276), ('water', 25277), ('water', 25278), ('water', 25279), ('water', 25280),
                     ('water', 25281)]
        self.assertTrue(history == ordering1 or history == ordering2)  # Strict. Advanced implementations might fail.

    def test_shingled_mesh_corpus(self):
        import os.path
        from tokenization import ShingleGenerator
        from corpus import InMemoryCorpus
        from invertedindex import InMemoryInvertedIndex
        from searchengine import SimpleSearchEngine

        tokenizer = ShingleGenerator(3)
        corpus = InMemoryCorpus(os.path.join(data_path, 'mesh.txt'))
        index = InMemoryInvertedIndex(corpus, ["body"], self._normalizer, tokenizer)
        engine = SimpleSearchEngine(corpus, index)
        self._process_query_verify_matches("orGAnik kEMmistry", engine,
                                           {"match_threshold": 0.1, "hit_count": 10},
                                           (10, 8.0, [4408, 4410, 4411, 16980, 16981]))
        self._process_query_verify_matches("synndrome", engine,
                                           {"match_threshold": 0.1, "hit_count": 10},
                                           (10, 7.0, [1275]))

if __name__ == '__main__':
    unittest.main()

