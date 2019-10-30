import unittest
from test import data_path

class TestPostingsMerger(unittest.TestCase):
    def setUp(self):
        from traversal import PostingsMerger
        self._merger = PostingsMerger()

    def test_empty_lists(self):
        from invertedindex import Posting
        posting = Posting(123, 4)
        self.assertListEqual(list(self._merger.intersection(iter([]), iter([]))), [])
        self.assertListEqual(list(self._merger.intersection(iter([]), iter([posting]))), [])
        self.assertListEqual(list(self._merger.intersection(iter([posting]), iter([]))), [])
        self.assertListEqual(list(self._merger.union(iter([]), iter([]))), [])
        self.assertListEqual([p.document_id for p in self._merger.union(iter([]), iter([posting]))], [posting.document_id])
        self.assertListEqual([p.document_id for p in self._merger.union(iter([posting]), iter([]))], [posting.document_id])

    def test_order_independence(self):
        from invertedindex import Posting
        postings1 = [Posting(1, 0), Posting(2, 0), Posting(3, 0)]
        postings2 = [Posting(2, 0), Posting(3, 0), Posting(6, 0)]
        result12 = list(map(lambda p: p.document_id, self._merger.intersection(iter(postings1), iter(postings2))))
        result21 = list(map(lambda p: p.document_id, self._merger.intersection(iter(postings2), iter(postings1))))
        self.assertEqual(len(result12), 2)
        self.assertListEqual(result12, result21)
        result12 = list(map(lambda p: p.document_id, self._merger.union(iter(postings1), iter(postings2))))
        result21 = list(map(lambda p: p.document_id, self._merger.union(iter(postings2), iter(postings1))))
        self.assertEqual(len(result12), 4)
        self.assertListEqual(result12, result21)

    def _process_query_with_two_terms(self, corpus, index, query, operator, expected):
        terms = list(index.get_terms(query))
        postings = [index[terms[i]] for i in range(len(terms))]
        self.assertEqual(len(postings), 2)
        merged = operator(postings[0], postings[1])
        documents = [corpus[posting.document_id] for posting in merged]
        self.assertEqual(len(documents), len(expected))
        self.assertListEqual([d.document_id for d in documents], expected)

    def test_mesh_corpus(self):
        import os.path
        from normalization import BrainDeadNormalizer
        from tokenization import BrainDeadTokenizer
        from corpus import InMemoryCorpus
        from invertedindex import InMemoryInvertedIndex

        normalizer = BrainDeadNormalizer()
        tokenizer = BrainDeadTokenizer()
        corpus = InMemoryCorpus(os.path.join(data_path, 'mesh.txt'))
        index = InMemoryInvertedIndex(corpus, ["body"], normalizer, tokenizer)
        self._process_query_with_two_terms(corpus, index, "HIV  pROtein", self._merger.intersection,
                                           [11316, 11319, 11320, 11321])
        self._process_query_with_two_terms(corpus, index, "water Toxic", self._merger.union,
                                           [3078, 8138, 8635, 9379, 14472, 18572, 23234, 23985] +
                                           [i for i in range(25265, 25282)])


if __name__ == '__main__':
    unittest.main()
