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
