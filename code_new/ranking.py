#!/usr/bin/python
# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
from corpus import Corpus
from invertedindex import Posting, InvertedIndex
import math


class Ranker(ABC):
    """
    Abstract base class for rankers used together with document-at-a-time traversal.
    """

    @abstractmethod
    def reset(self, document_id: int) -> None:
        """
        Resets the ranker, i.e., prepares it for evaluating another document.
        """
        pass

    @abstractmethod
    def update(self, term: str, multiplicity: int, posting: Posting) -> None:
        """
        Tells the ranker to update its internals based on information from one
        query term and the associated posting. This method might be invoked multiple
        times if the query contains multiple unique terms. Since a query term might
        occur multiple times in a query, the query term's multiplicity or occurrence
        count in the query is also provided.
        """
        pass

    @abstractmethod
    def evaluate(self) -> float:
        """
        Returns the current document's relevancy score. I.e., evaluates how relevant
        the current document is, given all the previous update invocations.
        """
        pass


class BrainDeadRanker(Ranker):
    """
    A dead simple ranker.
    """

    def __init__(self):
        self._score = 0.0

    def reset(self, document_id: int) -> None:
        self._score = 0.0

    def update(self, term: str, multiplicity: int, posting: Posting) -> None:
        self._score += multiplicity * posting.term_frequency

    def evaluate(self) -> float:
        return self._score


class BetterRanker(Ranker):
    """
    A ranker that does traditional TF-IDF ranking, possibly combining it with
    a static document score (if present).

    The static document score is assumed accessible in a document field named
    "static_quality_score". If the field is missing or doesn't have a value, a
    default value of 0.0 is assumed for the static document score.
    """

    def __init__(self, corpus: Corpus, inverted_index: InvertedIndex):
        self._score = 0.0
        self._document_id = None
        self._corpus = corpus
        self._inverted_index = inverted_index
        self._dynamic_score_weight = 1.0  # TODO: Make this configurable.
        self._static_score_weight = 1.0  # TODO: Make this configurable.
        self._static_score_field_name = "static_quality_score"  # TODO: Make this configurable.

    def reset(self, document_id: int) -> None:
        self._score = 0.0
        self._document_id = document_id

    def update(self, term: str, multiplicity: int, posting: Posting) -> None:
        tf_score = math.log10(multiplicity * (1 + posting.term_frequency))
        idf_score = math.log10(self._corpus.size() / float(self._inverted_index.get_document_frequency(term)))
        self._score += tf_score * idf_score

    def evaluate(self) -> float:
        document = self._corpus[self._document_id]
        static_quality_score = float(document[self._static_score_field_name] or 0.0)
        return (self._dynamic_score_weight * self._score) + (self._static_score_weight * static_quality_score)
