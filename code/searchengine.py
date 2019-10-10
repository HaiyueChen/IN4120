#!/usr/bin/python
# -*- coding: utf-8 -*-

# from collections import Counter
# from utilities import Sieve
from ranking import Ranker
from corpus import Corpus
from invertedindex import InvertedIndex
from typing import Callable, Any, Dict
from utilities import Sieve


class SimpleSearchEngine:
    """
    A simple implementation of a search engine based on an inverted index, suitable for small corpora.
    """

    def __init__(self, corpus: Corpus, inverted_index: InvertedIndex):
        self._corpus = corpus
        self._inverted_index = inverted_index

    def evaluate(self, query: str, options: dict, ranker: Ranker, callback: Callable[[dict], Any]) -> None:
        """
        Evaluates the given query, doing N-out-of-M ranked retrieval. I.e., for a supplied query having M terms,
        a document is considered to be a match if it contains at least N <= M of those terms.

        The matching documents are ranked by the supplied ranker, and only the "best" matches are returned to the
        client via the supplied callback function.

        The client can supply a dictionary of options that controls this query evaluation process: The value of
        N is inferred from the query via the "match_threshold" (float) option, and the maximum number of documents
        to return to the client is controlled via the "hit_count" (int) option.

        The callback function supplied by the client will receive a dictionary having the keys "score" (float) and
        "document" (Document).
        """

        # Print verbose debug information?
        # debug = options.get("debug", False)
        # print(query)

        query_terms = self._get_query_terms(query)
        threshold = options["match_threshold"] if "match_threshold" in options else 0
        min_matches = max(1, min(len(query_terms), int(threshold * len(query_terms))))
        hit_count = options["hit_count"] if "hit_count" in options else 0
        if hit_count == 0:
            return

        sieve = Sieve(hit_count)

        posting_iters = {}
        for term in query_terms:
            posting_iter = self._inverted_index.get_postings_iterator(term)
            if posting_iter:
                posting_iters[term] = posting_iter
        
        if len(posting_iters) < min_matches:
            return
        
        current_postings = {}
        for term in posting_iters:
            itt = posting_iters[term]
            posting = next(itt, None)
            if not posting:
                del posting_iters[term]
            else:
                current_postings[term] = posting
    
        last_matching_doc_id = -1
        while len(posting_iters) >= min_matches:
            min_doc_id = float("inf")
            itter_to_advance = []
            match_grouping = {}
            for term in current_postings:
                posting = current_postings[term]
                doc_id = posting.document_id
                if doc_id < min_doc_id:
                    itter_to_advance.clear()
                    min_doc_id = doc_id
                    itter_to_advance.append(term)
                elif doc_id == min_doc_id:
                    itter_to_advance.append(term)

                if doc_id in match_grouping:
                    match_grouping[doc_id].append((term, posting))
                else:
                    match_grouping[doc_id] = [(term, posting)]

            ## Check for match
            for doc_id in match_grouping:
                if doc_id == last_matching_doc_id:
                    continue

                if len(match_grouping[doc_id]) >= min_matches:
                    last_matching_doc_id = doc_id
                    ranker.reset(doc_id)
                    match_tuples = match_grouping[doc_id]
                    for match_tuple in match_tuples:
                        multiplicity = query_terms[match_tuple[0]]
                        ranker.update(term, multiplicity, match_tuple[1])
                    score = ranker.evaluate()
                    sieve.sift(score, doc_id)

            ## Advance iters
            for term in itter_to_advance:
                itt = posting_iters[term]
                posting = next(itt, None)
                if not posting:
                    del posting_iters[term]
                    del current_postings[term]
                else:
                    current_postings[term] = posting

        ## callbacks
        for winner in sieve.winners():
            print(winner)
            to_return = {
                "score": winner[0],
                "document": self._corpus.get_document(winner[1])
            }

        return 

    def _get_query_terms(self, query) -> Dict[str, int]:
        query_terms = self._inverted_index.get_terms(query)
        query_terms_dict = {}
        for term in query_terms:
            if term in query_terms_dict:
                query_terms_dict[term] += 1
            else:
                query_terms_dict[term] = 1
        return query_terms_dict