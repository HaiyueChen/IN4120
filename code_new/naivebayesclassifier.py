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
from functools import reduce


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
        
        
        """
        Definition of a category object (an entry in the self._categories dictionary)
        
        category: {
            "doc_count": int,
            "word_count": int,
            "probability": float
        }
        """
        # I have chosen to store some of the intermediate values of the calculation as instance variables
        # such that it would be easy to retrain the model if more documents/corpora were to be added
        self._categories = {}
        self._sum_documents = sum(len(training_set[category]) for category in training_set)
        for category in training_set:
            corpus = training_set[category]
            self._categories[category] = {}
            self._categories[category]["doc_count"] = len(corpus)
            self._categories[category]["word_count"] = 0
            self._categories[category]["probability"] = len(corpus) / self._sum_documents



        """
        Definition of a term category frequency object (an element in the self._term_category_frequency list)
        The index of an term category frequency object in the list is the term_id, which is assigned by the self._vocabulary dict
        [
            {
                "category": int,
                "category": int,
                "category": int,
                ...
            },
            ...
        ]
        """
        
        self._term_category_frequency = []
        base_term_category_frequency_object = {}
        for category in training_set:
            base_term_category_frequency_object[category] = 0

        for category in training_set:                
            corpus = training_set[category]
            for document in corpus:
                document_content = " ".join(document.get_field(field, "") for field in fields)
                terms = self._get_terms(document_content)
                self._categories[category]["word_count"] += len(terms)
                for term in terms:
                    term_id = self._vocabulary.add_if_absent(term)
                    if term_id == len(self._term_category_frequency):
                        self._term_category_frequency.append(base_term_category_frequency_object.copy())
                    self._term_category_frequency[term_id][category] += 1
        
        

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
        vocabulary_size = len(self._vocabulary)
        probabilities = []
        terms = self._get_terms(buffer)

        for category in self._categories:
            category_obj = self._categories[category]
            probability_of_category = math.log(category_obj["probability"])
            # probability_of_category = 1
            terms_in_category = category_obj["word_count"]
            print("\n",category)
            for term in terms:
                term_id = self._vocabulary.get_term_id(term)
                if term_id == None:
                    print("wtf")
                    continue
                term_obj = self._term_category_frequency[term_id]
                term_category_occurance = term_obj[category]
                probability_term_given_category = (term_category_occurance + 1) / (terms_in_category + vocabulary_size)
                print(term, math.log(probability_term_given_category))
                probability_of_category += math.log(probability_term_given_category)
            
            # log_probability = math.log(probability_of_category)
            # category_score_obj = {
            #     "category": category,
            #     "score": log_probability
            # }
            category_score_obj = {
                "category": category,
                "score": probability_of_category
            }
            probabilities.append(category_score_obj)


        probabilities.sort(key=lambda x: x["score"], reverse=True)
        for category_score_obj in probabilities:
            print(category_score_obj)
            callback(category_score_obj)
        
        return

