import unittest


class TestSieve(unittest.TestCase):
    def test_sifting(self):
        from utilities import Sieve
        sieve = Sieve(3)
        sieve.sift(1.0, "one")
        sieve.sift(10.0, "ten")
        sieve.sift(9.0, "nine")
        sieve.sift(2.0, "two")
        sieve.sift(5.0, "five")
        sieve.sift(8.0, "eight")
        sieve.sift(7.0, "seven")
        sieve.sift(6.0, "six")
        sieve.sift(3.0, "three")
        sieve.sift(4.0, "four")
        self.assertListEqual(list(sieve.winners()), [(10.0, "ten"), (9.0, "nine"), (8.0, "eight")])
