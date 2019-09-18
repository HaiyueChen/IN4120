#!/usr/bin/python
# -*- coding: utf-8 -*-

# import itertools
# from collections import Counter
# from utilities import Sieve, apply
from corpus import Corpus
from normalization import Normalizer
from tokenization import Tokenizer
from typing import Callable, Any, Iterable, List, Tuple
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
                    contents += f"\0{field_content}"
            normalized_content = self._normalize(contents)
            self._normalized_document_contents[document.get_document_id()] = normalized_content

            suffix_id_tuple = {}
            suffix_id_string = {}
            tokens = self._tokenizer.ranges(normalized_content)
            for i in range(1, len(tokens)):
                suffix = tokens[i:len(tokens)]
                suffix_id_tuple[i] = suffix
                suffix_id_string[i] = "".join([normalized_content[token_tuple[0]:token_tuple[1]] for token_tuple in suffix])

            suffix_ids = list(suffix_id_tuple.keys())
            suffix_ids.sort(key=functools.cmp_to_key(lambda x, y: self._compare_suffixes(x, y, suffix_id_string)))
            
            sorted_document_suffix = []
            for suffix_id in suffix_ids:
                sorted_document_suffix.append(suffix_id_tuple[suffix_id])

            self._document_suffixes[document_id] = sorted_document_suffix

    def _compare_suffixes(self, suffix_id_1: int, suffix_id_2: int, suffix_dict: dict):
        if suffix_id_2 == suffix_id_2:
            return 0        
        return 1 if suffix_dict[suffix_id_1] > suffix_dict[suffix_id_2] else -1


    def print_suffix(self, suffix_tuples, content):
        token_string = " ".join([content[token_tuple[0]:token_tuple[1]] for token_tuple in suffix_tuples])
        print(token_string)


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
        normalized_query = self._normalize(query)
        matched_docs_and_score = {}
        for doc_id in self._document_suffixes:
            doc_suffixes = self._document_suffixes[doc_id]
            normalized_doc_content = self._normalized_document_contents[doc_id]


    def _prefix_match(self, prefix: str, suffix: List[Tuple[int]], content: str):
        pass 


    def _suffix_binary_search(self, query: str, suffix_array: List[List[Tuple[int]]], content: str) -> Tuple[int]:
        lower = 0
        upper = len(suffix_array)
        found = False
        match_index = -1
        while lower < upper:
            index = lower + (upper - lower) // 2
            suffix = suffix_array[index]
            match_result = self._prefix_match(query, suffix, content)
            if match_result == 0:
                found = True
                match_index = index
                break
            elif match_result == -1:
                upper = index
            else:
                if lower == index:
                    break
                lower = index
        
        if not found:
            return (-1, -1)
        