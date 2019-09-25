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
from functools import reduce


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
        self._document_field_delim_indices = {}
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
            tokens = self._tokenizer.ranges(normalized_content)
            average_token_size = reduce(lambda x, y: x + y, map(lambda x: x[1] - x[0], tokens)) / len(tokens)

            self._normalized_document_contents[document.get_document_id()] = normalized_content
            self._document_tokens[document_id] = tokens

            suffix_ids = []
            for i in range(len(tokens)):
                suffix_ids.append(i)
            
            # Uses the eager comparison function when the average token size if 1 or 2, otherwise uses the lazy version
            # This is mostly a hack to make the second test go faster, I would very much like to know how to handle
            # lager amount of repeating tokens efficiently
            if average_token_size < 3:
                suffix_ids.sort(key=functools.cmp_to_key(lambda x, y: self._compare_suffixes_eager(x, y, document_id)))
            else:
                suffix_ids.sort(key=functools.cmp_to_key(lambda x, y: self._compare_suffixes_lazy(x, y, document_id)))

            self._document_suffix_ids[document_id] = suffix_ids
            

    def _build_normailized_document_content(self, document_id: int) -> str:
        """
        Builds the normalized document content from document id that is given.
        Returns the processed document content as one continues string by joining the
        specified fields together. Uses "\0" as the deliminator between contents from 
        different fields. Also maintains a dictionary over doc_id -> list_of_deliminator_indices 
        for token fetching later.
        """
        document = self._corpus.get_document(document_id)
        contents = [document.get_field(field, "") for field in self._fields]
        normalized_contents = [self._normalize(content) for content in contents]
        proccesed_content = ""
        delim_indices = []
        for content in normalized_contents:
            if content:
                proccesed_content += content
                delim_indices.append(len(proccesed_content))
                proccesed_content += "\0"
        self._document_field_delim_indices[document_id] = delim_indices

        return proccesed_content


    def _compare_suffixes_eager(self, token_id_1: int, token_id_2: int, document_id: int)-> int:
        """        
        Comparator function supplied to the python built in List.sort().
        Compares two suffixes, represented by their id(index of their first token in the token list).
        Returns 0 if the two ids are the same, -1 if suffix_1 < suffix_2 and 1 if suffix_1 > suffix_2.
        
        This comparator function only gets the whole suffix string at once, and compares them using the 
        python comparison operator.
        """
        if token_id_1 == token_id_2:
            return 0
        
        delim_indices = self._document_field_delim_indices[document_id]

        token_list = self._document_tokens[document_id]
        normalized_document_content = self._normalized_document_contents[document_id]

        suffix_1_tuples = token_list[token_id_1:len(token_list)]
        suffix_2_tuples = token_list[token_id_2:len(token_list)]

        suffix_1_tokens = []
        for token_tuple in suffix_1_tuples:
            token_string = normalized_document_content[token_tuple[0]:token_tuple[1]]
            if token_tuple[1] in delim_indices or token_tuple[1] + 1 in delim_indices:
               token_string += "\0"
            suffix_1_tokens.append(token_string)

        suffix_1_string = " ".join(suffix_1_tokens)
        

        suffix_2_tokens = []
        for token_tuple in suffix_2_tuples:
            token_string = normalized_document_content[token_tuple[0]:token_tuple[1]]
            if token_tuple[1] in delim_indices or token_tuple[1] + 1 in delim_indices:
               token_string += "\0"
            suffix_2_tokens.append(token_string)

        suffix_2_string = " ".join(suffix_2_tokens)

        return 1 if suffix_1_string > suffix_2_string else -1

    def _compare_suffixes_lazy(self, token_id_1: int, token_id_2: int, document_id: int)-> int:
        """
        Comparator function supplied to the python built in List.sort().
        Compares two suffixes, represented by their id(index of their first token in the token list).
        Returns 0 if the two ids are the same, -1 if suffix_1 < suffix_2 and 1 if suffix_1 > suffix_2.
        
        This comparator function only gets the ~50 character chunks of the suffixes, and uses them
        for comparasion, rather than getting the whole suffix string at once.
        """
        if token_id_1 == token_id_2:
            return 0

        token_list = self._document_tokens[document_id]
        normalized_document_content = self._normalized_document_contents[document_id]

        suffix_1_tokens = token_list[token_id_1:len(token_list)]
        suffix_2_tokens = token_list[token_id_2:len(token_list)]

        suffix_1_index = 0
        suffix_2_index = 0
        suffix_1_token_string = self._get_token_string(suffix_1_index, suffix_1_tokens, normalized_document_content, document_id)
        suffix_2_token_string = self._get_token_string(suffix_2_index, suffix_2_tokens, normalized_document_content, document_id)

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
                suffix_1_token_string = self._get_token_string(suffix_1_index, suffix_1_tokens, normalized_document_content, document_id)
                if suffix_1_token_string != None and len(suffix_1_token_string) < 50:
                    suffix_1_index += 1
                    next_token = self._get_token_string(suffix_1_index, suffix_1_tokens, normalized_document_content, document_id)
                    while next_token != None and len(suffix_1_token_string) < 50:
                        suffix_1_token_string += next_token
                        suffix_1_index += 1
                        next_token = self._get_token_string(suffix_1_index, suffix_1_tokens, normalized_document_content, document_id)

            if token_index_2 == len(suffix_2_token_string):
                token_index_2 = 0
                suffix_2_index += 1
                suffix_2_token_string = self._get_token_string(suffix_2_index, suffix_2_tokens, normalized_document_content, document_id)
                if suffix_2_token_string != None and len(suffix_2_token_string) < 50:
                    suffix_2_index += 1
                    next_token = self._get_token_string(suffix_2_index, suffix_2_tokens, normalized_document_content, document_id)
                    while next_token != None and len(suffix_2_token_string) < 50:
                        suffix_2_token_string += next_token
                        suffix_2_index += 1
                        next_token = self._get_token_string(suffix_2_index, suffix_2_tokens, normalized_document_content, document_id)


        if suffix_1_token_string == None:
            return -1

        if suffix_2_token_string == None:
            return 1


    def _get_token_string(self, index: int, suffix_tuple_list: List[Tuple[int]], content: str, document_id: int)-> str:
        """
        Given a list of token ranges, gets the string that is represented by the range at the index, 
        in the content string (normalized document content)
        """
        delim_indices = self._document_field_delim_indices[document_id]
        if index >= len(suffix_tuple_list):
            return None
        
        suffix_tuple = suffix_tuple_list[index]
        token_string = content[suffix_tuple[0]:suffix_tuple[1]]
        if suffix_tuple[1] in delim_indices or suffix_tuple[1] + 1 in delim_indices:
            token_string += "\0"

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

        """
        Loops through all the documents, gets the suffix array for each document.
        Uses binary search if document has more than 50 suffixes, other wise linear search is used.
        """
        temp_matches = []
        for doc_id in self._document_suffix_ids:
            doc_tokens = self._document_tokens[doc_id]
            sorted_suffix_ids = self._document_suffix_ids[doc_id]

            normalized_doc_content = self._normalized_document_contents[doc_id]
            match_score = 0
            if len(sorted_suffix_ids) < 50:
                match_score = self._suffix_linear_search(proccesed_query, sorted_suffix_ids, doc_tokens, normalized_doc_content, doc_id)
            else:
                match_score = self._suffix_binary_search(proccesed_query, sorted_suffix_ids, doc_tokens, normalized_doc_content, doc_id)

            if match_score > 0:
                new_match_dict = {"score": match_score, "document": self._corpus.get_document(doc_id)}
                self._insert_into_temp_results(new_match_dict, temp_matches, hit_count)
        for match in temp_matches:
            callback(match)

        return




    def _insert_into_temp_results(self, new_match: dict, temp_results: List[dict], hit_count: int) -> None:
        """
        Insert a new matches document in the temporary results list. if result_count higher
        than povided hit_count, remove the lowest ranked one.
        """
        temp_results.append(new_match)
        temp_results.sort(key=lambda x: x["score"], reverse=True)
        if len(temp_results) > hit_count:
            temp_results.pop(hit_count)




    def _suffix_linear_search(self, query: str, sorted_suffix_ids: List[int], doc_tokens: List[Tuple[int]], content: str, document_id: int) -> int:
        """
        Searches the suffix array linearly and stops at the first suffix that is bigger than the query.
        Returns the number of suffixes that matches the query.
        """
        lower = 0
        found_lower = False
        for i in range(len(sorted_suffix_ids)):
            suffix_tuples = doc_tokens[sorted_suffix_ids[i]:len(doc_tokens)]
            if self._prefix_match(query, suffix_tuples, content, document_id) == 0:
                found_lower = True
                lower = i
                break

        if not found_lower:
            return 0

        num_matches = 1
        for i in range(lower + 1, len(sorted_suffix_ids)):
            suffix_tuples = doc_tokens[sorted_suffix_ids[i]:len(doc_tokens)]
            match_result = self._prefix_match(query, suffix_tuples, content, document_id)
            if match_result == 0:
                num_matches += 1
            else:
                break

        return num_matches

    def _suffix_binary_search(self, query: str, sorted_suffix_ids: List[int], doc_tokens: List[Tuple[int]], content: str, document_id: int) -> int:
        """
        Searches matches in the suffix array, using the _prefix_match() function as the comaprator
        Uses binary search to find the first match, then searches linearly left and right to count
        all the matches.
        Returns the number of mathces
        """
        num_matches = 0
        
        if len(sorted_suffix_ids) == 1:
            suffix_tuples = doc_tokens
            return 1 if self._prefix_match(query, suffix_tuples, content, document_id) == 0 else 0


        lower = 0
        upper = len(sorted_suffix_ids) - 1
        found = False
        first_match_index = -1

        while lower <= upper:
            mid = lower + (upper - lower) // 2
            suffix_tuples = doc_tokens[sorted_suffix_ids[mid]:len(doc_tokens)]

            match_result = self._prefix_match(query, suffix_tuples, content, document_id)
            if match_result == 0:
                found = True
                first_match_index = mid
                break
            elif match_result < 0:
                upper = mid - 1
            else:
                lower = mid + 1
        
        if not found:
            return 0

        else:
            num_matches = 0
            for i in range(first_match_index + 1, len(sorted_suffix_ids)):
                suffix_tuples = doc_tokens[sorted_suffix_ids[i]:len(doc_tokens)]
                match_result = self._prefix_match(query, suffix_tuples, content, document_id)
                if match_result != 0:
                    break
                num_matches += 1

            for i in reversed(range(first_match_index + 1)):
                suffix_tuples = doc_tokens[sorted_suffix_ids[i]:len(doc_tokens)]
                match_result = self._prefix_match(query, suffix_tuples, content, document_id)
                if match_result != 0:
                    break
                num_matches += 1

            return num_matches


    def _prefix_match(self, prefix: str, suffix_tuples: List[Tuple[int]], content: str, document_id: int) -> int:
        """
        Function that matches a prefex with a suffix. Only fetches enough tokens from the suffix
        in order to compare.
        Returns 0 if match, -1 if prefix < suffix, 1 if prefix > suffix

        """
        
        suffix_tokens = []
        delim_indices = self._document_field_delim_indices[document_id]

        suffix_length = 0
        prefix_length = len(prefix)
        suffix_index = 0
        suffix_tokens = []
        while suffix_length < prefix_length and suffix_index < len(suffix_tuples):
            token_tuple = suffix_tuples[suffix_index]
            suffix_token = content[token_tuple[0]: token_tuple[1]]
            if token_tuple[1] < len(content) and token_tuple[1] in delim_indices:
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
            return 1
        else:
            for i in range(prefix_length):
                if prefix[i] > suffix_string[i]:
                    return 1
                if prefix[i] < suffix_string[i]:
                    return -1
            return 0