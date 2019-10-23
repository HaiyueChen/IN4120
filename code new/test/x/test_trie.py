import unittest
import importlib.util

@unittest.skipIf(importlib.util.find_spec('ahocorasick') is None, 'No Trie class available')
class TestTrie(unittest.TestCase):
    def test_access_nodes(self):
        from tokenization import BrainDeadTokenizer
        from ahocorasick import Trie
        tokenizer = BrainDeadTokenizer()
        strings = ["abba", "ørret", "abb", "abbab", "abbor"]
        root = Trie()
        for s in strings:
            root.add(s, tokenizer)
        self.assertFalse(root.is_final())
        self.assertIsNone(root.consume("snegle"))
        node = root.consume("ab")
        self.assertFalse(node.is_final())
        node = node.consume("b")
        self.assertTrue(node.is_final())
        self.assertEqual(node, root.consume("abb"))
