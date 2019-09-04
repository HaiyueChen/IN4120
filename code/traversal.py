#!/usr/bin/python
# -*- coding: utf-8 -*-

from typing import Iterator
from typing import List
from invertedindex import Posting
from heapq import merge
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
        
        p1_element = next(p1, None)
        p2_element = next(p2, None)

        if not p1_element or not p2_element:
            return 
        
        if p1_element.document_id == p2_element.document_id:
            yield p1_element
            p1_element = next(p1, None)
            p2_element = next(p2, None)
        

        while p1_element and p2_element:
            if p1_element.document_id == p2_element.document_id:
                yield p1_element
                p1_element = next(p1, None)
                p2_element = next(p2, None)
            else:
                if p1_element.document_id < p2_element.document_id:
                    p1_element = next(p1, None)
                else:
                    p2_element = next(p2, None)
        return
        

    @staticmethod
    def union(p1: Iterator[Posting], p2: Iterator[Posting]) -> Iterator[Posting]:
        """
        A generator that yields a simple OR of two posting lists, given
        iterators over these.

        The posting lists are assumed sorted in increasing order according
        to the document identifiers.
        """
        #I could implement another iterator very similar to the one above,
        #but I found a built in lib that does what is needed
        # https://docs.python.org/3/library/heapq.html#heapq.merge
        return merge(p1, p2, key=lambda x: x.document_id)


    #This method is useless
    @staticmethod
    def _merge_sort(posting_list1: List[Posting], posting_list2: List[Posting]) -> List[Posting]:
        sorted_postings = [None] * (len(posting_list1) + len(posting_list2))
        index_sorted = index_p1 = index_p2 = 0
        while index_p1 < len(posting_list1) and index_p2 < len(posting_list2):
            if posting_list1[index_p1].document_id < posting_list2[index_p2].document_id:
                sorted_postings[index_sorted] = posting_list1[index_p1]
                index_p1 += 1
            else:
                sorted_postings[index_sorted] = posting_list2[index_p2]
                index_p2 += 1
            index_sorted += 1

        while index_p1 < len(posting_list1):
            sorted_postings[index_sorted] = posting_list1[index_p1]
            index_p1 += 1
            index_sorted += 1

        while index_p2 < len(posting_list2):
            sorted_postings[index_sorted] = posting_list2[index_p2]
            index_p2 += 1
            index_sorted += 1
        
        return sorted_postings
