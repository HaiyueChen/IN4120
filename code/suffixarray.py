#!/usr/bin/python
# -*- coding: utf-8 -*-

# import itertools
# from collections import Counter
# from utilities import Sieve, apply
from corpus import Corpus
from normalization import Normalizer
from tokenization import Tokenizer
from typing import Callable, Any, Iterable, List
import functools


class SuffixArray:
    """
    A simple suffix array implementation. Allows us to conduct efficient substring searches.
    The prefix of a suffix is an infix!

    In a serious application we'd make use of least common prefixes (LCPs), pay more attention
    to memory usage, and add more lookup/evaluation features.
    """

    def __init__(self, corpus: Corpus, fields: Iterable[str], normalizer: Normalizer, tokenizer: Tokenizer):
        self._corpus = corpus
        self._normalizer = normalizer
        self._tokenizer = tokenizer
        self._normalized_document_contents = {}
        self._document_suffixes = {}
        self._build_suffix_array(fields)

    def _build_suffix_array(self, fields: Iterable[str]) -> None:
        """
        Builds a simple suffix array from the set of named fields in the document collection.
        The suffix array allows us to search across all named fields in one go.
        """
        for document in self._corpus:
            document_id = document.get_document_id()
            contents = ""
            for field in fields:
                field_content = document.get_field(field, None)
                if field_content:
                    contents += f" {field_content}"
            normalized_content = self._normalize(contents)
            self._normalized_document_contents[document.get_document_id()] = normalized_content
            suffix_indices = []
            for i in range(1, len(normalized_content)):
                suffix_indices.append(i)

            suffix_indices.sort(key=functools.cmp_to_key(lambda x, y: self._compare_suffixes(x, y, normalized_content)))
            self._document_suffixes[document_id] = suffix_indices


    def _compare_suffixes(self, index_1: int, index_2: int, content: str):
        content_length = len(content)
        if index_1 == index_2:
            return 0

        while index_1 < content_length and index_2 < content_length:
            if content[index_1] < content[index_2]:
                return -1
            if content[index_1] > content[index_2]:
                return 1
            index_1 += 1
            index_2 += 1
        if index_1 == content_length and index_2 < content_length:
            return -1
        else:
            return 1

    def _normalize(self, buffer: str) -> str:
        """
        Produces a normalized version of the given string. Both queries and documents need to be
        identically processed for lookups to succeed.
        """

        # Tokenize and join to be robust to nuances in whitespace and punctuation.
        return self._normalizer.normalize(" ".join(self._tokenizer.strings(self._normalizer.canonicalize(buffer))))

    def evaluate(self, query: str, options: dict, callback: Callable[[dict], Any]) -> None:
        """
        Evaluates the given query, doing a "phrase prefix search".  E.g., for a supplied query phrase like
        "to the be", we return documents that contain phrases like "to the bearnaise", "to the best",
        "to the behemoth", and so on. I.e., we require that the query phrase starts on a token boundary in the
        document, but it doesn't necessarily have to end on one.

        The matching documents are ranked according to how many times the query substring occurs in the document,
        and only the "best" matches are returned to the client via the supplied callback function. Ties are
        resolved arbitrarily.

        The client can supply a dictionary of options that controls this query evaluation process: The maximum
        number of documents to return to the client is controlled via the "hit_count" (int) option.

        The callback function supplied by the client will receive a dictionary having the keys "score" (int) and
        "document" (Document).
        """
        normalized_prefix = self._normalize(query)

        for document_id in self._normalized_document_contents:
            normalized_contents = self._normalized_document_contents[document_id]
            suffix_array = self._document_suffixes[document_id]
            for suffix_index in suffix_array:
                

        raise NotImplementedError()


    def _prefix_match(self, normalized_prefix, suffix_index, document_id):
        normalized_content = self._normalized_document_contents[document_id]
        match = False
        if suffix_index + len(normalized_prefix) > len(normalized_content):
            return False

        for i in range(len(normalized_prefix)):
            if normalized_prefix[i] != normalized_content[suffix_index + i]:
                return False
        return True