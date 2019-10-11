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

        print(f"Min matches: {min_matches}")

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
        
        to_delete = []
        current_postings = {}
        for term in posting_iters:
            itt = posting_iters[term]
            posting = next(itt, None)
            if not posting:
                to_delete.append(term)
            else:
                current_postings[term] = posting
    
        for term in to_delete:
            del posting_iters[term]

        # last_sifted = []
        last_match_doc_id = -1
        while len(posting_iters) >= min_matches:
            min_doc_id = float("inf")
            itter_to_advance = []
            match_grouping = {}
            # print(f"current_postings: {current_postings}")
            # input()
            for term in current_postings:
                posting = current_postings[term]
                doc_id = posting.document_id
                if doc_id < min_doc_id:
                    itter_to_advance.clear()
                    min_doc_id = doc_id
                    itter_to_advance.append(term)
                elif doc_id == min_doc_id:
                    itter_to_advance.append(term)

                # Group terms and itters by doc_id
                if doc_id in match_grouping:
                    match_grouping[doc_id].append((term, posting))
                else:
                    match_grouping[doc_id] = [(term, posting)]
            # print(f"match_grouping: {match_grouping}")
            # print(f"itter_to_advance: {itter_to_advance}")
            # print(f"last match id: {last_match_doc_id}")

            ## Check for match
            # for doc_id in match_grouping:
            #     print(doc_id)
            #     if doc_id in last_sifted or len(match_grouping[doc_id]) < min_matches:
            #         print("skip")
            #         print(f"match num: {len(match_grouping[doc_id])}")
            #         continue

            #     if len(match_grouping[doc_id]) >= min_matches:
            #         last_matching_doc_id = doc_id
            #         ranker.reset(doc_id)
            #         match_tuples = match_grouping[doc_id]
            #         for match_tuple in match_tuples:
            #             multiplicity = query_terms[match_tuple[0]]
            #             posting = match_tuple[1]
            #             ranker.update(term, multiplicity, posting)
                    
                    # score = ranker.evaluate()
                    # sieve.sift(score, doc_id)
                    # print(f"sifted: {doc_id}  score: {score}")
            min_grouping = match_grouping[min_doc_id]
            if min_doc_id != last_match_doc_id and len(min_grouping) >= min_matches:
                last_match_doc_id = min_doc_id
                ranker.reset(min_doc_id)
                match_tuples = match_grouping[min_doc_id]
                for match_tuple in match_tuples:
                    term = match_tuple[0]
                    multiplicity = query_terms[term]
                    posting = match_tuple[1]
                    ranker.update(term, multiplicity, posting)
                score = ranker.evaluate()
                sieve.sift(score, min_doc_id)
                # print(f"sifted: {min_doc_id}  score: {score}")

            ## Advance iters
            to_delete = []
            for term in itter_to_advance:
                itt = posting_iters[term]
                posting = next(itt, None)
                if not posting:
                    to_delete.append(term)
                    # del posting_iters[term]
                    # del current_postings[term]
                else:
                    current_postings[term] = posting

            for term in to_delete:
                del posting_iters[term]
                del current_postings[term]

            # input("next loop")
        ## callbacks
        for winner in sieve.winners():
            to_return = {
                "score": winner[0],
                "document": self._corpus.get_document(winner[1])
            }
            # print(to_return)
            callback(to_return)
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