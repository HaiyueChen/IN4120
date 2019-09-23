#!/usr/bin/python
# -*- coding: utf-8 -*-

from tokenization import Tokenizer, BrainDeadTokenizer
# from utilities import apply
from typing import Optional, TypeVar, Callable, Any

TrieType = TypeVar('Trie', bound='Trie')


class Trie:
    """
    A very simple and straightforward implementation of a trie for demonstration purposes
    and tiny dictionaries.

    A serious real-world implementation of a trie or an automaton would not be implemented
    this way. The trie/automaton would then instead be encoded into a single contiguous buffer
    and there'd be significant attention on memory consumption and scalability with respect to
    dictionary size.

    A node in the trie is also a trie itself in this implementation.
    """

    def __init__(self):
        self._children = {}

    def __repr__(self):
        return repr(self._children)

    def _add(self, string: str) -> None:
        assert 0 < len(string)
        trie = self
        for c in string:
            if c not in trie._children:
                trie._children[c] = Trie()
            trie = trie._children[c]
        trie._children[""] = Trie()

    def add(self, string: str, tokenizer: Tokenizer) -> None:
        """
        Adds the given string to the trie. The tokenizer is used so that we're robust
        to nuances in whitespace and punctuation. Use the same tokenizer throughout.
        """

        # TODO: Make the tokenizer a class variable.
        self._add(" ".join(tokenizer.strings(string)))

    def consume(self, prefix: str) -> Optional[TrieType]:
        """
        Consumes the given prefix, verbatim. If strings that have this prefix have been added to
        the trie, then the trie node corresponding to the prefix is returned. Otherwise, None is returned.
        """
        trie = self
        for c in prefix:
            if c in trie._children:
                trie = trie._children[c]
            else:
                return None
        return trie

    def is_final(self) -> bool:
        """
        Returns True iff the current node is a final/terminal state in the trie/automaton, i.e.,
        if a string has been added to the trie where the end of the string ends up in this node.
        """
        return "" in self._children


class StringFinder:
    """
    Given a trie encoding a dictionary of strings, efficiently finds the subset of strings in the dictionary
    that are also present in a given text buffer. I.e., in a sense computes the "intersection" or "overlap"
    between the dictionary and the text buffer.

    Uses a trie-walk algorithm similar to the Aho-Corasick algorithm with some minor NLP extensions. The
    running time of this algorithm is virtually independent of the size of the dictionary, and linear in
    the length of the buffer we are searching in.

    The tokenizer we use when scanning the input buffer is assumed to be the same as the one that was used
    when adding strings to the trie.
    """

    def __init__(self, trie: Trie, tokenizer: Tokenizer):
        self._trie = trie
        self._tokenizer = tokenizer

    def scan(self, buffer: str, callback: Callable[[dict], Any]) -> None:
        """
        Scans the given buffer and finds all dictionary entries in the trie that are also present in the
        buffer. We only consider matches that begin and end on token boundaries.

        The matching dictionary entries, if any, are reported back to the client via the supplied callback
        function.

        The callback function supplied by the client will receive a dictionary having the keys "match" (str) and
        "range" (Tuple[int, int]).

        In a serious application we'd add more lookup/evaluation features, e.g., support for prefix matching,
        support for leftmost-longest matching (instead of reporting all matches), and support for lemmatization
        or similar linguistic variations.
        """
        # print(self._trie)
        # input()
        normalized = " ".join(self._tokenizer.strings(buffer))
        exploring_queue = []
        matches = []
        is_token_start = False
        is_token_end = False
        for i in range(len(normalized)):
            character = normalized[i]
            if i > 0 and normalized[i - 1] == " ":
                is_token_start = True
            else:
                is_token_start = False
            
            if i == len(normalized) - 1:
                is_token_end = True
            elif normalized[i+1] == " ":
                is_token_end = True
            else:
                is_token_end = False

            # print(f"matching {character}")
            # input()
            new_queue = []
            for node_dict in exploring_queue:
                de_queued_string = normalized[node_dict['start']:node_dict['end']]
                # print(f"dequeueing: {de_queued_string}")
                de_queued = node_dict["node"]
                next_node = de_queued.consume(character)
                if next_node:
                    if next_node.is_final() and len(next_node._children) > 1:
                        if is_token_end:
                            match_result = {"match": normalized[node_dict["start"]:node_dict["end"] + 1], "range": (node_dict["start"], node_dict["end"] + 1)}
                            matches.append(match_result)
                        new_queue.append({"node": next_node, "start": node_dict["start"], "end": node_dict["end"] + 1})
                    elif next_node.is_final() and len(next_node._children) == 1 and is_token_end:
                        match_result = {"match": normalized[node_dict["start"]:node_dict["end"] + 1], "range": (node_dict["start"], node_dict["end"] + 1)}
                        matches.append(match_result)
                    else:
                        new_queue.append({"node": next_node, "start": node_dict["start"], "end": node_dict["end"] + 1})
                        # print(f"Added back to exploration: {normalized[node_dict['start']:node_dict['end']]}")

            exploring_queue = new_queue
            if is_token_start:
                new_node = self._trie.consume(character)
                if new_node:
                # print("appending to exploring queue")
                    exploring_queue.append({"node": new_node, "start": i, "end": i + 1})
        
        for match in matches:
            callback(match)
            



def main():
    """
    Example usage. A tiny unit test, in a sense.
    """
    tokenizer = BrainDeadTokenizer()
    strings = ["abba", "ørret", "abb", "abbab", "abbor"]
    trie = Trie()
    for s in strings:
        trie.add(s, tokenizer)
    assert trie.is_final() is False
    assert trie.consume("snegle") is None
    node = trie.consume("ab")
    assert node.is_final() is False
    node = node.consume("b")
    assert node.is_final() is True
    assert node == trie.consume("abb")


if __name__ == "__main__":
    main()
