#!/usr/bin/python
# -*- coding: utf-8 -*-

from typing import Iterator
from invertedindex import Posting
import copy

class PostingsMerger:
    """
    Utility class for merging posting lists.
    """

    @staticmethod
    def intersection(p1: Iterator[Posting], p2: Iterator[Posting]) -> Iterator[Posting]:
        """
        A generator that yields a simple AND of two posting lists, given
        iterators over these.

        The posting lists are assumed sorted in increasing order according
        to the document identifiers.
        """
        intersect = []
        p1_list = [*p1]
        p2_list = [*p2]
        
        if not p1_list or not p2_list:
            return iter(intersect)

        p1_index = 0
        p2_index =0
        while p1_index < len(p1_list) and p2_index < len(p2_list):
            p1_item = p1_list[p1_index]
            p2_item = p2_list[p2_index]
            if p1_item.document_id == p2_item.document_id:
                intersect.append(copy.deepcopy(p1_item))
                p1_index += 1
                p2_index += 1
            else:
                if p1_item.document_id < p2_item.document_id:
                    p1_index += 1
                else:
                    p2_index += 1

        return iter(intersect)
        

    @staticmethod
    def union(p1: Iterator[Posting], p2: Iterator[Posting]) -> Iterator[Posting]:
        """
        A generator that yields a simple OR of two posting lists, given
        iterators over these.

        The posting lists are assumed sorted in increasing order according
        to the document identifiers.
        """         

        return iter(sorted(list(p1) + list(p2), key=lambda x: x.document_id))
