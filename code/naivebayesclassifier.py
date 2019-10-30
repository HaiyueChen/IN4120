#!/usr/bin/python
# -*- coding: utf-8 -*-

import math
import operator
from collections import Counter
from dictionary import InMemoryDictionary
from normalization import Normalizer
from tokenization import Tokenizer
from corpus import Corpus
from typing import Callable, Any, Dict, Iterable


class NaiveBayesClassifier:
    """
    Defines a multinomial naive Bayes text classifier.
    """

    def __init__(self, training_set: Dict[str, Corpus], fields: Iterable[str],
                 normalizer: Normalizer, tokenizer: Tokenizer):
        """
        Constructor. Trains the classifier from the named fields in the documents in
        the given training set.
        """

        # Used for breaking the text up into discrete classification features.
        self._normalizer = normalizer
        self._tokenizer = tokenizer

        # The vocabulary we've seen during training.
        self._vocabulary = InMemoryDictionary()

        raise NotImplementedError()

    def _get_terms(self, buffer):
        """
        Processes the given text buffer and returns the sequence of normalized
        terms as they appear. Both the documents in the training set and the buffers
        we classify need to be identically processed.
        """
        return [self._normalizer.normalize(s) for s in self._tokenizer.strings(self._normalizer.canonicalize(buffer))]

    def classify(self, buffer: str, callback: Callable[[dict], Any]) -> None:
        """
        Classifies the given buffer according to the multinomial naive Bayes rule. The computed (score, category) pairs
        are emitted back to the client via the supplied callback sorted according to the scores. The reported scores
        are log-probabilities, to minimize numerical underflow issues. Logarithms are base e.

        The callback function supplied by the client will receive a dictionary having the keys "score" (float) and
        "category" (str).
        """

        raise NotImplementedError()
