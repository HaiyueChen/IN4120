import unittest

class TestShingleGenerator(unittest.TestCase):
    def setUp(self):
        from tokenization import ShingleGenerator
        self._tokenizer = ShingleGenerator(3)

    def test_strings(self):
        self.assertListEqual(self._tokenizer.strings(""), [])
        self.assertListEqual(self._tokenizer.strings("b"), ["b"])
        self.assertListEqual(self._tokenizer.strings("ba"), ["ba"])
        self.assertListEqual(self._tokenizer.strings("ban"), ["ban"])
        self.assertListEqual(self._tokenizer.strings("bana"), ["ban", "ana"])
        self.assertListEqual(self._tokenizer.strings("banan"), ["ban", "ana", "nan"])
        self.assertListEqual(self._tokenizer.strings("banana"), ["ban", "ana", "nan", "ana"])

    def test_tokens(self):
        self.assertListEqual(self._tokenizer.tokens("ba"), [("ba", (0, 2))])
        self.assertListEqual(self._tokenizer.tokens("banan"), [("ban", (0, 3)), ("ana", (1, 4)), ("nan", (2, 5))])

    def test_ranges(self):
        self.assertListEqual(self._tokenizer.ranges("ba"), [(0, 2)])
        self.assertListEqual(self._tokenizer.ranges("banan"), [(0, 3), (1, 4), (2, 5)])

if __name__ == '__main__':
    unittest.main()
