#!/usr/bin/python
# -*- coding: utf-8 -*-

import heapq
from typing import Callable, Iterable, Iterator, Any, Union, Tuple

Number = Union[int, float]


def apply(f: Callable[[Any], Any], xs: Iterable) -> None:
    """
    Applies the given function to each item in the given iterable.

    Similar to the built-in map/2, at least how map/2 used to work in Python 2.7.x. However,
    in Python 3.x map/2 returns an iterator that is evaluated lazily. This poses a problem
    if the return value from map/2 is never traversed and the intent of using of map/2 was
    really to trigger some side-effect from the function application. This utility method
    avoids that, and was written when porting Python 2.7.x code to Python 3.x.
    """
    for x in xs:
        f(x)


class Sieve:
    """
    Implements a "sieve", i.e., a heap-based data structure through which
    we can "sift" N scored items, and be left with the up to K (item, score)
    pairs having the largest scores. Ties are resolved arbitrarily.

    A sieve is an efficient way of selecting the "best" K items from a set of N
    items, where K << N. An internal heap keeps track of "the worst of the best",
    so that we immediately know if a candidate item makes the cut.

    Candidate items can be of any type, as long as that type has an "<" operator
    defined.
    """

    def __init__(self, size: int):
        assert size > 0
        self._size = size
        self._heap = []

    def sift(self, score: Number, item: Any) -> None:
        """
        Sifts a scored item through the sieve.
        """
        if len(self._heap) < self._size:
            heapq.heappush(self._heap, (score, item))
        else:
            root_score = self._heap[0][0]
            if root_score < score:
                heapq.heapreplace(self._heap, (score, item))

    def winners(self) -> Iterator[Tuple[Number, Any]]:
        """
        Returns the highest-scoring items that have been sifted through the sieve, sorted
        in descending order. The returned list iterator yields (score, item) tuples.

        This implementation is currently not idempotent. Invoke only once.
        """

        # Since the internal heap tracks "the worst of the best" and we want the
        # list sorted as "the best of the best", we reverse the internal heap ordering.
        return reversed([heapq.heappop(self._heap) for _ in range(len(self._heap))])
