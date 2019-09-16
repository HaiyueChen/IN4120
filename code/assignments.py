#!/usr/bin/python
# -*- coding: utf-8 -*-

from normalization import Normalizer, BrainDeadNormalizer
from tokenization import BrainDeadTokenizer
from corpus import Document, InMemoryDocument, Corpus, InMemoryCorpus
from invertedindex import Posting, InMemoryInvertedIndex
from traversal import PostingsMerger
from suffixarray import SuffixArray
from ahocorasick import Trie, StringFinder
import re
import sys
import tracemalloc
import inspect


def assignment_a_inverted_index_1():

    # Use these throughout below.
    normalizer = BrainDeadNormalizer()
    tokenizer = BrainDeadTokenizer()

    # Dump postings for a dummy two-document corpus.
    print("INDEXING...")
    corpus = InMemoryCorpus()
    corpus.add_document(InMemoryDocument(0, {"body": "this is a Test"}))
    corpus.add_document(InMemoryDocument(1, {"body": "test TEST prØve"}))
    index = InMemoryInvertedIndex(corpus, ["body"], normalizer, tokenizer)
    for (term, expected) in zip(index.get_terms("PRøvE wtf tesT"), [[(1, 1)], [], [(0, 1), (1, 2)]]):
        print(term)
        assert term in ["prøve", "wtf", "test"]
        postings = list(index[term])
        for posting in postings:
            print(posting)
        assert len(postings) == len(expected)
        assert [(p.document_id, p.term_frequency) for p in postings] == expected
    print(index)

    # Document counts should be correct.
    assert index.get_document_frequency("wtf") == 0
    assert index.get_document_frequency("test") == 2
    assert index.get_document_frequency("prøve") == 1


def assignment_a_inverted_index_2():

    # Use these throughout below.
    normalizer = BrainDeadNormalizer()
    tokenizer = BrainDeadTokenizer()

    # Dump postings for a slightly bigger corpus.
    print("LOADING...")
    corpus = InMemoryCorpus("../data/mesh.txt")
    print("INDEXING...")
    index = InMemoryInvertedIndex(corpus, ["body"], normalizer, tokenizer)
    for (term, expected_length) in [("hydrogen", 8),
                                    ("hydrocephalus", 2)]:
        print(term)
        for posting in index[term]:
            print(posting)
        assert len(list(index[term])) == expected_length


def assignment_a_postingsmerger_1():

    # A small but real corpus.
    normalizer = BrainDeadNormalizer()
    tokenizer = BrainDeadTokenizer()
    corpus = InMemoryCorpus("../data/mesh.txt")
    index = InMemoryInvertedIndex(corpus, ["body"], normalizer, tokenizer)

    # Test that we merge posting lists correctly. Note implicit test for case- and whitespace robustness.
    print("MERGING...")
    merger = PostingsMerger()
    and_query = ("HIV  pROtein", "AND", [11316, 11319, 11320, 11321])
    or_query = ("water Toxic", "OR", [3078, 8138, 8635, 9379, 14472, 18572, 23234, 23985] +
                                     [i for i in range(25265, 25282)])
    for (query, operator, expected_document_ids) in [and_query, or_query]:
        print(re.sub(r"\W+", f" {operator} ", query))
        terms = list(index.get_terms(query))
        assert len(terms) == 2
        postings = [index[terms[i]] for i in range(len(terms))]
        merged = {"AND": merger.intersection, "OR": merger.union}[operator](postings[0], postings[1])
        documents = [corpus[posting.document_id] for posting in merged]
        print(*documents, sep="\n")
        assert len(documents) == len(expected_document_ids)
        assert [d.document_id for d in documents] == expected_document_ids


def assignment_a_postingsmerger_2():
    # Test some corner cases with empty lists.
    merger = PostingsMerger()
    posting = Posting(123, 4)
    assert list(merger.intersection(iter([]), iter([]))) == []
    assert list(merger.intersection(iter([]), iter([posting]))) == []
    assert list(merger.intersection(iter([posting]), iter([]))) == []
    assert list(merger.union(iter([]), iter([]))) == []
    assert [p.document_id for p in merger.union(iter([]), iter([posting]))] == [posting.document_id]
    assert [p.document_id for p in merger.union(iter([posting]), iter([]))] == [posting.document_id]


def assignment_a_postingsmerger_3():

    # Argument order shouldn't matter.
    merger = PostingsMerger()
    postings1 = [Posting(1, 0), Posting(2, 0), Posting(3, 0)]
    postings2 = [Posting(2, 0), Posting(3, 0), Posting(6, 0)]
    result12 = list(map(lambda p: p.document_id, merger.intersection(iter(postings1), iter(postings2))))
    result21 = list(map(lambda p: p.document_id, merger.intersection(iter(postings2), iter(postings1))))
    print(result12)
    print(result21)
    assert len(result12) == 2
    assert result12 == result21
    result12 = list(map(lambda p: p.document_id, merger.union(iter(postings1), iter(postings2))))
    result21 = list(map(lambda p: p.document_id, merger.union(iter(postings2), iter(postings1))))
    print(result12)
    print(result21)
    assert len(result12) == 4
    assert result12 == result21


def assignment_a():
    assignment_a_inverted_index_1()
    assignment_a_inverted_index_2()
    assignment_a_postingsmerger_1()
    assignment_a_postingsmerger_2()
    assignment_a_postingsmerger_3()


def assignment_b_suffixarray_1():

    # Use these throughout below.
    normalizer = BrainDeadNormalizer()
    tokenizer = BrainDeadTokenizer()

    # Prepare for some suffix array lookups.
    print("LOADING...")
    corpus = InMemoryCorpus("../data/cran.xml")
    print("INDEXING...")
    engine = SuffixArray(corpus, ["body"], normalizer, tokenizer)
    results = []
    hit_count = 5

    # Callback for receiving matches.
    def match_collector(match):
        results.append(match)
        print("*** WINNER", match["score"], match["document"])

    # Define the actual test queries.
    test1 = ("visc", 11, [328])                       # Look for {'viscous', 'viscosity', ...}.
    test2 = ("Of  A", 10, [946])                      # Test robustness for case and whitespace.
    test3 = ("", 0, [])                               # Safety feature: Match nothing instead of everything.
    test4 = ("approximate solution", 3, [1374, 159])  # Multiple winners.

    # Test that the simple occurrence ranking works. Be robust towards how ties are resolved.
    for (query, winner_score, winner_document_ids) in [test1, test2, test3, test4]:
        print("SEARCHING for '" + query + "'...")
        results.clear()
        engine.evaluate(query, {"debug": False, "hit_count": hit_count}, match_collector)
        if winner_document_ids:
            assert results[0]["score"] == winner_score
            assert results[0]["document"].document_id in winner_document_ids
            assert len(results) <= hit_count
        else:
            assert len(results) == 0


def assignment_b_suffixarray_2():

    # For testing.
    class TestNormalizer(Normalizer):

        _table = str.maketrans({'Ø': 'O'})

        def canonicalize(self, buffer: str) -> str:
            return buffer

        def normalize(self, token: str) -> str:
            return token.upper().translate(self._table)

    # For testing.
    class TestDocument(Document):

        def __init__(self, document_id: int, a: str, b: str):
            self._document_id = document_id
            self._a = a
            self._b = b

        def get_document_id(self) -> int:
            return self._document_id

        def get_field(self, field_name: str, default: str) -> str:
            if field_name == "a":
                return self._a
            if field_name == "b":
                return self._b
            return default

    # For testing.
    class TestCorpus(Corpus):
        def __init__(self):
            self._docs = []
            self._docs.append(TestDocument(len(self._docs), "ø  o\n\n\nø\n\no", "ø o\nø   \no"))
            self._docs.append(TestDocument(len(self._docs), "ba", "b bab"))
            self._docs.append(TestDocument(len(self._docs), "ø  o Ø o", "ø o"))
            self._docs.append(TestDocument(len(self._docs), "øO" * 10000, "o"))
            self._docs.append(TestDocument(len(self._docs), "cbab o øbab Ø ", "ø o " * 10000))

        def __iter__(self):
            return iter(self._docs)

        def size(self) -> int:
            return len(self._docs)

        def get_document(self, document_id: int) -> Document:
            return self._docs[document_id]

    # Run the tests!
    for fields in [("b",), ("a", "b")]:

        # Create the suffix array over the given set of fields. Measure memory usage. If memory usage is
        # excessive, most likely the implementation is copying strings or doing other silly stuff instead
        # of working with buffer indices. The naive reference implementation is not in any way optimized,
        # and uses about 1.5 MB of memory on this corpus.
        tracemalloc.start()
        snapshot1 = tracemalloc.take_snapshot()
        engine = SuffixArray(TestCorpus(), fields, TestNormalizer(), BrainDeadTokenizer())
        snapshot2 = tracemalloc.take_snapshot()
        for statistic in snapshot2.compare_to(snapshot1, "filename"):
            if statistic.traceback[0].filename == inspect.getfile(SuffixArray):
                assert statistic.size_diff < 2000000, f"Memory usage is {statistic.size_diff}"
        tracemalloc.stop()
        results = []

        def process(m):
            results.append((m['document'].document_id, m['score']))

        expected_results = {
            ('b',): (
                ('bab', [(1, 1)]),
                ('ø o', [(4, 19999), (0, 3), (2, 1)]),
                ('o O', [(4, 19999), (0, 3), (2, 1)]),
                ('oooooo', []),
                ('o o o o', [(4, 19997), (0, 1)]),
            ),
            ('a', 'b'): (
                ('bab', [(1, 1)]),
                ('ø o', [(4, 20000), (0, 6), (2, 4)]),
                ('o O', [(4, 20000), (0, 6), (2, 4)]),
                ('oøØOøO', [(3, 1), ]),
                ('o o o o', [(4, 19997), (0, 2), (2, 1)]),
            )
        }

        for query, expected in expected_results[fields]:
            results.clear()
            engine.evaluate(query, {'hit_count': 10}, process)
            assert results == expected


def assignment_b_stringfinder():

    # Use these throughout below.
    tokenizer = BrainDeadTokenizer()
    results = []

    # Simple test of using a trie-encoded dictionary for efficiently locating substrings in a buffer.
    trie = Trie()
    for s in ["romerike", "apple computer", "norsk", "norsk ørret", "sverige", "ørret", "banan"]:
        trie.add(s, tokenizer)
    finder = StringFinder(trie, tokenizer)
    buffer = "det var en gang en norsk  ørret fra romerike som likte abba fra sverige"
    print("SCANNING...")
    results.clear()
    finder.scan(buffer, lambda m: results.append(m))
    print("Buffer \"" + buffer + "\" contains", results)
    assert [m["match"] for m in results] == ["norsk", "norsk ørret", "ørret", "romerike", "sverige"]

    # Find all MeSH terms that occur verbatim in some selected Cranfield documents! Since MeSH
    # documents are medical terms and the Cranfield documents have technical content, the
    # overlap probably isn't that big.
    print("LOADING...")
    mesh = InMemoryCorpus("../data/mesh.txt")
    cranfield = InMemoryCorpus("../data/cran.xml")
    print("BUILDING...")
    trie = Trie()
    for d in mesh:
        trie.add(d["body"] or "", tokenizer)
    finder = StringFinder(trie, tokenizer)
    print("SCANNING...")
    for (document_id, expected_matches) in [(0, ["wing", "wing"]),
                                            (3, ["solutions", "skin", "friction"]),
                                            (1254, ["electrons", "ions"])]:
        document = cranfield.get_document(document_id)
        buffer = document["body"] or ""
        results.clear()
        finder.scan(buffer, lambda m: results.append(m))
        print("Cranfield document", document, "contains MeSH terms", results)
        assert [m["match"] for m in results] == expected_matches


def assignment_b():
    assignment_b_suffixarray_1()
    assignment_b_suffixarray_2()
    assignment_b_stringfinder()


def assignment_c():
    pass


def assignment_d():
    pass


def assignment_e():
    pass


def main():
    tests = {"a": assignment_a,
             "b": assignment_b,
             "c": assignment_c,
             "d": assignment_d,
             "e": assignment_e}
    assignments = sys.argv[1:] or ["b"]
    for assignment in assignments:
        print("*** ASSIGNMENT", assignment.upper(), "***")
        tests[assignment.lower()]()
    print("*************************")
    print("*** ALL TESTS PASSED! ***")
    print("*************************")


if __name__ == "__main__":
    main()
