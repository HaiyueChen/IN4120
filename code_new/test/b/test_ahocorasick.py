import unittest
from test import data_path

class TestStringFinder(unittest.TestCase):
    def setUp(self):
        from tokenization import BrainDeadTokenizer
        self._tokenizer = BrainDeadTokenizer()

    def _scan_buffer_verify_matches(self, finder, buffer, expected):
        matches = []
        finder.scan(buffer, lambda m: matches.append(m))
        self.assertListEqual([m["match"] for m in matches], expected)

    def test_scan(self):
        from ahocorasick import Trie, StringFinder
        dictionary = Trie()
        for s in ["romerike", "apple computer", "norsk", "norsk ørret", "sverige", "ørret", "banan", "a", "a b"]:
            dictionary.add(s, self._tokenizer)
        finder = StringFinder(dictionary, self._tokenizer)
        self._scan_buffer_verify_matches(finder,
                                         "en norsk     ørret fra romerike likte abba fra sverige",
                                         ["norsk", "norsk ørret", "ørret", "romerike", "sverige"])
        self._scan_buffer_verify_matches(finder, "the apple is red", [])
        self._scan_buffer_verify_matches(finder, "", [])
        self._scan_buffer_verify_matches(finder,
                                         "apple computer banan foo sverige ben reddik fy fasan",
                                         ["apple computer", "banan", "sverige"])
        self._scan_buffer_verify_matches(finder, "a a b", ["a", "a", "a b"])

    def test_mesh_terms_in_cran_corpus(self):
        import os.path
        from corpus import InMemoryCorpus
        from ahocorasick import Trie, StringFinder

        mesh = InMemoryCorpus(os.path.join(data_path, 'mesh.txt'))
        cran = InMemoryCorpus(os.path.join(data_path, 'cran.xml'))
        trie = Trie()
        for d in mesh:
            trie.add(d["body"] or "", self._tokenizer)
        finder = StringFinder(trie, self._tokenizer)
        self._scan_buffer_verify_matches(finder, cran[0]["body"], ["wing", "wing"])
        self._scan_buffer_verify_matches(finder, cran[3]["body"], ["solutions", "skin", "friction"])
        self._scan_buffer_verify_matches(finder, cran[1254]["body"], ["electrons", "ions"])


if __name__ == '__main__':
    unittest.main()
