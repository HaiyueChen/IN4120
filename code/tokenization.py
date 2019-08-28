#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
from abc import ABC, abstractmethod
from typing import List, Tuple


class Tokenizer(ABC):
    """
    Simple abstract base class for tokenizers, with some default implementations.
    """

    @abstractmethod
    def ranges(self, buffer: str) -> List[Tuple[int, int]]:
        """
        Returns the positional range pairs that indicate where in the buffer the
        tokens begin and end.
        """
        pass

    def strings(self, buffer: str) -> List[str]:
        """
        Returns the strings that make up the tokens in the given buffer.
        """
        return [buffer[r[0]:r[1]] for r in self.ranges(buffer)]

    def tokens(self, buffer: str) -> List[Tuple[str, Tuple[int, int]]]:
        """
        Returns the (string, range) pairs that make up the tokens in the given buffer.
        """
        return [(buffer[r[0]:r[1]], r) for r in self.ranges(buffer)]


class BrainDeadTokenizer(Tokenizer):
    """
    A dead simple tokenizer for testing purposes. A real tokenizer
    wouldn't be implemented this way. Kids, don't do this at home.
    """

    _pattern = re.compile("(\w+)", re.UNICODE | re.MULTILINE | re.DOTALL)

    def __init__(self):
        pass

    def ranges(self, buffer: str) -> List[Tuple[int, int]]:
        return [(m.start(), m.end()) for m in self._pattern.finditer(buffer)]


def main():
    """
    Example usage. A tiny unit test, in a sense.
    """
    tokenizer = BrainDeadTokenizer()
    assert tokenizer.strings("Dette  er en\nprøve!") == ["Dette", "er", "en", "prøve"]
    assert tokenizer.tokens("Dette  er en\nprøve!") == [("Dette", (0, 5)), ("er", (7, 9)),
                                                        ("en", (10, 12)), ("prøve", (13, 18))]
    assert tokenizer.ranges("Dette  er en\nprøve!") == [(0, 5), (7, 9), (10, 12), (13, 18)]


if __name__ == "__main__":
    main()
