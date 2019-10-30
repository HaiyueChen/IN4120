import unittest


class TestBrainDeadTokenizer(unittest.TestCase):
    def setUp(self):
        from tokenization import BrainDeadTokenizer
        self._tokenizer = BrainDeadTokenizer()

    def test_strings(self):
        result = self._tokenizer.strings("Dette  er en\nprøve!")
        self.assertListEqual(result, ["Dette", "er", "en", "prøve"])

    def test_tokens(self):
        result = self._tokenizer.tokens("Dette  er en\nprøve!")
        self.assertListEqual(result, [("Dette", (0, 5)), ("er", (7, 9)), ("en", (10, 12)), ("prøve", (13, 18))])

    def test_ranges(self):
        result = self._tokenizer.ranges("Dette  er en\nprøve!")
        self.assertListEqual(result, [(0, 5), (7, 9), (10, 12), (13, 18)])
