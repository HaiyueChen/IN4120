import unittest


class TestBrainDeadNormalizer(unittest.TestCase):
    def setUp(self):
        from normalization import BrainDeadNormalizer
        self._normalizer = BrainDeadNormalizer()

    def test_canonicalize(self):
        self.assertEqual(self._normalizer.canonicalize("Dette ER en\nprØve!"), "Dette ER en\nprØve!")

    def test_normalize(self):
        self.assertEqual(self._normalizer.normalize("grÅFustaSJEOpphengsForKOBling"), "gråfustasjeopphengsforkobling")
