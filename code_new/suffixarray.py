#!/usr/bin/python
# -*- coding: utf-8 -*-

import itertools
from collections import Counter
from utilities import Sieve, apply
from corpus import Corpus
from normalization import Normalizer
from tokenization import Tokenizer
from typing import Callable, Any, Iterable, Tuple


class SuffixArray:
    """
    A simple suffix array implementation. Allows us to conduct efficient substring searches.
    The prefix of a suffix is an infix!

    In a serious application we'd make use of least common prefixes (LCPs), pay more attention
    to memory usage, and add more lookup/evaluation features.
    """

    def __init__(self, corpus: Corpus, fields: Iterable[str], normalizer: Normalizer, tokenizer: Tokenizer):
        self._corpus = corpus
        self._haystack = []
        self._suffixes = []
        self._normalizer = normalizer
        self._tokenizer = tokenizer
        self._build_suffix_array(fields)

    def _build_suffix_array(self, fields: Iterable[str]) -> None:
        """
        Builds a simple suffix array from the set of named fields in the document collection.
        The suffix array allows us to search across all named fields in one go.
        """

        # We allow searching across multiple document fields simultaneously, so join the named fields
        # to produce the haystack that we'll search for needles in. Avoid cross-field matches.
        self._haystack = [(d.document_id, " \0 ".join([self._normalize(d.get_field(f, "")) for f in fields]))
                          for d in self._corpus]

        # We don't actually store all suffixes, instead we store (index, offset) pairs which allows us
        # to generate the suffixes if/when we need them: The index identifies the document, and the
        # offset identifies where in the document the substring starts.
        self._suffixes = [(i, r[0])
                          for i in range(len(self._haystack))
                          for r in self._tokenizer.ranges(self._haystack[i][1])]
        self._suffixes.sort(key=lambda t: self._get_suffix2(t))

    def _normalize(self, buffer: str) -> str:
        """
        Produces a normalized version of the given string. Both queries and documents need to be
        identically processed for lookups to succeed.
        """

        # Tokenize and join to be robust to nuances in whitespace and punctuation.
        return self._normalizer.normalize(" ".join(self._tokenizer.strings(self._normalizer.canonicalize(buffer))))

    def _get_suffix1(self, i: int) -> str:
        """
        Produces the suffix/substring from the normalized document buffer for the entry i in the suffix array.
        """
        return self._get_suffix2(self._suffixes[i])

    def _get_suffix2(self, pair: Tuple[int, int]) -> str:
        """
        Produces the suffix/substring from the normalized document buffer for the given (index, offset) pair.
        """

        # TODO: Slicing implies copying. This should be possible to avoid.
        return self._haystack[pair[0]][1][pair[1]:]

    def _binary_search(self, needle: str) -> int:
        """
        Does a binary search for a given normalized query (the needle) in the suffix array (the haystack).
        Returns the position in the suffix array where the normalized query is either found, or, if not found,
        should have been inserted.

        Kind of silly to roll our own binary search instead of using the bisect module, but seems needed
        due to how we represent the suffixes via (index, offset) tuples.
        """
        left = 0
        right = len(self._suffixes)
        while left < right:
            middle = (left + right) // 2
            suffix = self._get_suffix1(middle)
            if suffix < needle:
                left = middle + 1
            else:
                right = middle
        return left

    def _emit_match(self, index: int, score: float, callback: Callable[[dict], Any]) -> None:
        """
        Given an index that identifies a matching document in the haystack, emits the complete and original
        document (and its associated relevancy score) back to the client via the supplied callback.
        """
        callback({"score": score, "document": self._corpus[self._haystack[index][0]]})

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

        # Search for the needle in the haystack, using binary search. Define that the empty query matches
        # nothing, not everything.
        needle = self._normalize(query)
        if not needle:
            return
        where_start = self._binary_search(needle)

        # Helper predicate. Checks if the identified suffix starts with the needle. Since slicing implies copying,
        # cap the length of the slice to the length of the needle. The starts-with relation then becomes the same
        # as equality, which is quick to check.
        def _is_match(i: int) -> bool:
            (index, offset) = self._suffixes[i]
            return self._haystack[index][1][offset:(offset + len(needle))] == needle

        # Suffixes sharing a prefix are consecutive in the suffix array. Scan ahead from the located index until
        # we no longer get a match. We expect a low number of matches for typical queries, and we process all the
        # matches below anyway. If we just wanted to count the number of matches without processing them, we
        # could instead of a linear scan do another binary search to locate where the range ends.
        matches = itertools.takewhile(_is_match, range(where_start, len(self._suffixes)))

        # Deduplicate. A document in the haystack might contain multiple occurrences of the needle.
        # Rank according to occurrence count, and emit in ranked order.
        if matches:
            debug = options.get("debug", False)
            pairs = [self._suffixes[i] for i in matches]
            if debug:
                apply(lambda p: print("*** MATCH", p, self._get_suffix2(p)), pairs)
            counter = Counter([i for (i, _) in pairs])
            sieve = Sieve(max(1, min(100, options.get("hit_count", 10))))
            apply(lambda t: sieve.sift(t[1], t[0]), counter.items())
            apply(lambda w: self._emit_match(w[1], w[0], callback), sieve.winners())
