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
import gc


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
        self._document_tokens = {}
        self._document_suffix_ids = {}
        self._fields = fields
        self._build_suffix_array(fields)

    def _build_suffix_array(self, fields: Iterable[str]) -> None:
        """
        Builds a simple suffix array from the set of named fields in the document collection.
        The suffix array allows us to search across all named fields in one go.
        """
        for document in self._corpus:
            document_id = document.get_document_id()
            normalized_content = self._build_normailized_document_content(document_id)
            self._normalized_document_contents[document.get_document_id()] = normalized_content
            tokens = self._tokenizer.ranges(normalized_content)
            # print(self._tokenizer.strings(normalized_content))
            self._document_tokens[document_id] = tokens
            # if document_id < 4:
            #     print(normalized_content)
            #     print(tokens)

            suffix_ids = []
            for i in range(len(tokens)):
                suffix_ids.append(i)
            suffix_ids.sort(key=functools.cmp_to_key(lambda x, y: self._compare_suffixes(x, y, document_id)))
            self._document_suffix_ids[document_id] = suffix_ids


    def _build_normailized_document_content(self, document_id: int) -> str:
        document = self._corpus.get_document(document_id)
        contents = [document.get_field(field, "") for field in self._fields]
        normalized_contents = [self._normalize(content) for content in contents]
        proccesed_content = "\0".join(normalized_contents)
        return proccesed_content



    def _compare_suffixes(self, token_id_1, token_id_2, document_id):
        if token_id_1 == token_id_2:
            return 0

        token_list = self._document_tokens[document_id]
        normalized_document_content = self._normalized_document_contents[document_id]

        suffix_1_tuples = token_list[token_id_1:len(token_list)]
        suffix_2_tuples = token_list[token_id_2:len(token_list)]

        suffix_1_string = " ".join([normalized_document_content[token[0]:token[1]] for token in suffix_1_tuples])
        suffix_2_string = " ".join([normalized_document_content[token[0]:token[1]] for token in suffix_2_tuples])

        if suffix_1_string > suffix_2_string:
            return 1
        else:
            return -1

    def _compare_suffixes_using_token_indices(self, token_id_1, token_id_2, document_id):
        if token_id_1 == token_id_2:
            return 0

        token_list = self._document_tokens[document_id]
        normalized_document_content = self._normalized_document_contents[document_id]

        suffix_1_tokens = token_list[token_id_1:len(token_list)]
        suffix_2_tokens = token_list[token_id_2:len(token_list)]

        suffix_1_index = 0
        suffix_2_index = 0
        suffix_1_token_string = self._get_token_string(suffix_1_index, suffix_1_tokens, normalized_document_content)
        suffix_2_token_string = self._get_token_string(suffix_2_index, suffix_2_tokens, normalized_document_content)

        token_index_1 = 0
        token_index_2 = 0
        while suffix_1_token_string != None and suffix_2_token_string != None:
            while token_index_1 < len(suffix_1_token_string) and token_index_2 < len(suffix_2_token_string):
                if suffix_1_token_string[token_index_1] > suffix_2_token_string[token_index_2]:
                    return 1
                if suffix_1_token_string[token_index_1] < suffix_2_token_string[token_index_2]:
                    return -1
                token_index_1 += 1
                token_index_2 += 1

            if token_index_1 == len(suffix_1_token_string):
                token_index_1 = 0
                suffix_1_index += 1
                suffix_1_token_string = self._get_token_string(suffix_1_index, suffix_1_tokens, normalized_document_content)
                if suffix_1_token_string != None and len(suffix_1_token_string) < 50:
                    suffix_1_index += 1
                    next_token = self._get_token_string(suffix_1_index, suffix_1_tokens, normalized_document_content)
                    while next_token != None and len(suffix_1_token_string) < 50:
                        suffix_1_token_string += next_token
                        suffix_1_index += 1
                        next_token = self._get_token_string(suffix_1_index, suffix_1_tokens, normalized_document_content)

            if token_index_2 == len(suffix_2_token_string):
                token_index_2 = 0
                suffix_2_index += 1
                suffix_2_token_string = self._get_token_string(suffix_2_index, suffix_2_tokens, normalized_document_content)
                if suffix_2_token_string != None and len(suffix_2_token_string) < 50:
                    suffix_2_index += 1
                    next_token = self._get_token_string(suffix_2_index, suffix_2_tokens, normalized_document_content)
                    while next_token != None and len(suffix_2_token_string) < 50:
                        suffix_2_token_string += next_token
                        suffix_2_index += 1
                        next_token = self._get_token_string(suffix_2_index, suffix_2_tokens, normalized_document_content)


        if suffix_1_token_string == None:
            return -1

        if suffix_2_token_string == None:
            return 1


    def _get_token_string(self, index, suffix_tuple_list, content):
        if index >= len(suffix_tuple_list):
            return None
        suffix_tuple = suffix_tuple_list[index]
        token_string = content[suffix_tuple[0]:suffix_tuple[1]]
        return token_string


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
        if query == "":
            return

        hit_count = options["hit_count"]
        normalized_query = self._normalize(query)
        query_tokens = self._tokenizer.strings(normalized_query)
        proccesed_query = " ".join(query_tokens)
        print(f"searching for: {query} normailized: {proccesed_query}")
        # input()
        temp_matches = []
        for doc_id in self._document_suffix_ids:
            doc_tokens = self._document_tokens[doc_id]
            sorted_suffix_ids = self._document_suffix_ids[doc_id]
            # print(self._document_suffix_ids)

            normalized_doc_content = self._normalized_document_contents[doc_id]
            null_char_present = '\0' in normalized_doc_content
            print(f"doc: {doc_id} null char: {null_char_present}]")
            # print(f"Searching in doc: {doc_id} content: {normalized_doc_content}")
            # match_range = self._suffix_binary_search(normalized_query, doc_suffixes, normalized_doc_content)
            # match_score = match_range[1] - match_range[0]
            match_score = self._suffix_linear_search(proccesed_query, sorted_suffix_ids, doc_tokens, normalized_doc_content)
            if len(sorted_suffix_ids) < 1:

                print(f"Doc: {doc_id} No suffixes: {normalized_doc_content} query: {proccesed_query}")
                # print(match_score)
                # match_score = 1 if proccesed_query in normalized_doc_content else 0
            # print("Found range")
            # if doc_id == 328:
            #     print(normalized_doc_content)
            #     print(doc_id, match_score)
            #     input()
            if match_score > 0:
                new_match_dict = {"score": match_score, "document": self._corpus.get_document(doc_id)}
                self._insert_into_temp_results(new_match_dict, temp_matches, hit_count)
            print(f"Doc: {doc_id} match score: {match_score}")
        # print("adding winners with callback")
        for match in temp_matches:
            callback(match)

        return


    def _insert_into_temp_results(self, new_match: dict, temp_results: List[dict], hit_count: int) -> None:
        temp_results.append(new_match)
        temp_results.sort(key=lambda x: x["score"], reverse=True)
        if len(temp_results) > hit_count:
            temp_results.pop(hit_count)




    def _suffix_linear_search(self, query: str, sorted_suffix_ids: List[int], doc_tokens: List[Tuple[int]], content: str) -> int:
        lower = 0
        found_lower = False
        for i in range(len(sorted_suffix_ids)):
            suffix_tuples = doc_tokens[sorted_suffix_ids[i]:len(doc_tokens)]
            if self._prefix_match(query, suffix_tuples, content) == 0:
                found_lower = True
                lower = i
                break

        if not found_lower:
            return 0

        num_matches = 1
        for i in range(lower + 1, len(sorted_suffix_ids)):
            suffix_tuples = doc_tokens[sorted_suffix_ids[i]:len(doc_tokens)]
            match_result = self._prefix_match(query, suffix_tuples, content)
            if match_result == 0:
                num_matches += 1
            # elif match_result == -1:
            #     break

        return num_matches

    def _prefix_match(self, prefix: str, suffix_tuples: List[Tuple[int]], content: str):
        suffix_tokens = []
        delim_index = -1
        try:
            delim_index = content.index("\0")
        except Exception:
            pass
        # for token in suffix_tuples:
        #     # suffix_tokens.append(content[token[0]:token[1]])
        #     suffix_string = (content[token[0]:token[1]])
        #     if token[1] == delim_index or token == delim_index + 1:
        #         # print("null char added")
        #         # suffix_tokens.append(content[token[0]:token[1]+1])
        #         # print(content[token[0]:token[1]+1])
        #         # suffix_string = (content[token[0]:token[1]]) + "\0"
        #         suffix_string += "\0"
        #         # suffix_string += "\0"
        #         # suffix_tokens.append(suffix_string)
        #     # else:
        #     #     suffix_string += content[token[0]:token[1]]
        #     #     suffix_string += " "
        #     suffix_tokens.append(suffix_string)
        # suffix_string = " ".join(suffix_tokens)
        # null_char_found = '\0' in suffix_string
        # # print(f"null char in suffix: {null_char_found}")
        # if len(suffix_string) < len(prefix):
        #     for i in range(len(suffix_string)):
        #         if prefix[i] < suffix_string[i]:
        #             return -1
        #         if prefix[i] > suffix_string[i]:
        #             return 1
        # else:
        #     for i in range(len(prefix)):
        #         if prefix[i] < suffix_string[i]:
        #             return -1
        #         if prefix[i] > suffix_string[i]:
        #             return 1
        #     return 0

        suffix_length = 0
        prefix_length = len(prefix)
        suffix_index = 0
        suffix_tokens = []
        while suffix_length < prefix_length and suffix_index < len(suffix_tuples):
            token_tuple = suffix_tuples[suffix_index]
            suffix_token = content[token_tuple[0]: token_tuple[1]]
            if token_tuple[1] < len(content) and token_tuple[1] == delim_index:
                suffix_token += "\0"
            suffix_tokens.append(suffix_token)
            suffix_length += len(suffix_token)
            suffix_index += 1

        suffix_string = " ".join(suffix_tokens)

        if len(suffix_string) < prefix_length:
            for i in range(len(suffix_string)):
                if prefix[i] > suffix_string[i]:
                    return 1
                if prefix[i] < suffix_string[i]:
                    return -1
            return -1
        else:
            for i in range(prefix_length):
                for i in range(prefix_length):
                    if prefix[i] > suffix_string[i]:
                        return 1
                    if prefix[i] < suffix_string[i]:
                        return -1
                return 0