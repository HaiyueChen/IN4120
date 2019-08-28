#!/usr/bin/python
# -*- coding: utf-8 -*-

from normalization import Normalizer, BrainDeadNormalizer
from tokenization import BrainDeadTokenizer
from corpus import Document, InMemoryDocument, Corpus, InMemoryCorpus
from invertedindex import Posting, InvertedIndex, InMemoryInvertedIndex
from traversal import PostingsMerger
import re
import sys


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
        print(re.sub("\W+", " " + operator + " ", query))
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
    posting = Posting(0, 0)
    assert list(merger.intersection(iter([]), iter([]))) == []
    assert list(merger.intersection(iter([]), iter([posting]))) == []
    assert list(merger.intersection(iter([posting]), iter([]))) == []
    assert list(merger.union(iter([]), iter([]))) == []
    assert list(merger.union(iter([]), iter([posting]))) == [posting]
    assert list(merger.union(iter([posting]), iter([]))) == [posting]


def assignment_a():
    assignment_a_inverted_index_1()
    assignment_a_inverted_index_2()
    assignment_a_postingsmerger_1()
    assignment_a_postingsmerger_2()


def assignment_b():
    pass


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
    assignments = sys.argv[1:] or tests.keys()
    for assignment in assignments:
        print("*** ASSIGNMENT", assignment.upper(), "***")
        tests[assignment.lower()]()
    print("*************************")
    print("*** ALL TESTS PASSED! ***")
    print("*************************")


if __name__ == "__main__":
    main()
