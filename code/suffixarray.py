#!/usr/bin/python
# -*- coding: utf-8 -*-

# import itertools
# from collections import Counter
# from utilities import Sieve, apply
from corpus import Corpus
from normalization import Normalizer
from tokenization import Tokenizer
from typing import Callable, Any, Iterable


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
        self._fields = fields
        self._document_contents = {}
        self._suffix_array = []
        self._build_suffix_array(fields)

    def _build_suffix_array(self, fields: Iterable[str]) -> None:
        """
        Builds a simple suffix array from the set of named fields in the document collection.
        The suffix array allows us to search across all named fields in one go.
        """
        for document in self._corpus:
            document_id = document.get_document_id()
            normalized_contents = self._build_normalized_content(document)
            self._document_contents[document_id] = normalized_contents
        
        for document_id in self._document_contents:
            normalized_contents = self._document_contents[document_id]
            tokens = self._tokenizer.ranges(normalized_contents)
            for token in tokens:
                self._suffix_array.append((document_id, token[0]))
        
        self._suffix_array.sort(key=lambda x: self._document_contents[x[0]][x[1]:])
    
    def _build_normalized_content(self, document) -> str:
        contents = [document.get_field(field, "") for field in self._fields]
        normalized_contents = [self._normalize(content) for content in contents]
        processed_content = " \0 ".join(normalized_contents)
        return processed_content
        


    def _normalize(self, buffer: str) -> str:
        """
        Produces a normalized version of the given string. Both queries and documents need to be
        identically processed for lookups to succeed.
        """

        # Tokenize and join to be robust to nuances in whitespace and punctuation.
        return self._normalizer.normalize(" ".join(self._tokenizer.strings(self._normalizer.canonicalize(buffer))))

    def _prefix_match(self, prefix: str, suffix_string: str) -> int:
        if len(prefix) == len(suffix_string):
            if prefix == suffix_string:
                return 0
            elif prefix > suffix_string:
                return 1
            else:
                return -1
        
        if len(prefix) > len(suffix_string):
            # for i in range(len(suffix_string)):
            #     if prefix[i] < suffix_string[i]:
            #         return -1
            #     if prefix[i] > suffix_string[i]:
            #         return 1
            # return 1
            if prefix > suffix_string:
                return 1
            else:
                return -1

        else:
            suffix_section = suffix_string[0:len(prefix)]
            if prefix == suffix_section:
                return 0
            elif prefix > suffix_section:
                return 1
            else:
                return -1
            # for i in range(len(prefix)):
            #     if prefix[i] < suffix_string[i]:
            #         return -1
            #     if prefix[i] > suffix_string[i]:
            #         return 1
            # return 0

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

        if query == "":
            return
        
        hit_count = -1
        if "hit_count" in options:
            hit_count = options["hit_count"]

        normalized_query = self._normalize(query)
        
        lower = 0
        upper = len(self._suffix_array) - 1
        found = False
        first_match_index = -1

        while lower <= upper:
            mid = lower + (upper - lower) // 2
            suffix_tuple = self._suffix_array[mid]
            suffix_string = self._document_contents[suffix_tuple[0]][suffix_tuple[1]:]
            
            match_result = self._prefix_match(normalized_query, suffix_string)
            if match_result == 0:
                found = True
                first_match_index = mid
                break

            elif match_result == -1:
                upper = mid - 1
            else:
                lower = mid + 1

        if not found:
            return
        else:
            doc_id_match_map = {}
            mid_suffix_doc_id = self._suffix_array[first_match_index][0]
            doc_id_match_map[mid_suffix_doc_id] = 1

            for i in range(first_match_index + 1, len(self._suffix_array)):
                suffix_tuple = self._suffix_array[i]
                suffix_string = self._document_contents[suffix_tuple[0]][suffix_tuple[1]:]
                if self._prefix_match(normalized_query, suffix_string) == 0:
                    doc_id = suffix_tuple[0]
                    if doc_id in doc_id_match_map:
                        doc_id_match_map[doc_id] += 1
                    else:
                        doc_id_match_map[doc_id] = 1
                else:
                    break

            for i in reversed(range(first_match_index)):
                suffix_tuple = self._suffix_array[i]
                suffix_string = self._document_contents[suffix_tuple[0]][suffix_tuple[1]:]
                if self._prefix_match(normalized_query, suffix_string) == 0:
                    doc_id = suffix_tuple[0]
                    if doc_id in doc_id_match_map:
                        doc_id_match_map[doc_id] += 1
                    else:
                        doc_id_match_map[doc_id] = 1
                else:
                    break
            
            match_obj_list = []
            for doc_id in doc_id_match_map:
                match_obj = {}
                match_obj["score"] = doc_id_match_map[doc_id]
                match_obj["document"] = self._corpus.get_document(doc_id)
                match_obj_list.append(match_obj)
            
            match_obj_list.sort(key=lambda x: x["score"], reverse=True)

            if hit_count == -1:
                for match_obj in match_obj_list:
                    callback(match_obj)
            else:
                if hit_count < len(match_obj_list):
                    for i in range(hit_count):
                        callback(match_obj_list[i])
                else:
                    for match_obj in match_obj_list:
                        callback(match_obj)