import unittest
from test import data_path

class TestNaiveBayesClassifier(unittest.TestCase):
    def setUp(self):
        from normalization import BrainDeadNormalizer
        from tokenization import BrainDeadTokenizer
        self._normalizer = BrainDeadNormalizer()
        self._tokenizer = BrainDeadTokenizer()

    def test_china_example_from_textbook(self):
        import math
        from corpus import InMemoryDocument, InMemoryCorpus
        from naivebayesclassifier import NaiveBayesClassifier
        china = InMemoryCorpus()
        china.add_document(InMemoryDocument(0, {"body": "Chinese Beijing Chinese"}))
        china.add_document(InMemoryDocument(1, {"body": "Chinese Chinese Shanghai"}))
        china.add_document(InMemoryDocument(2, {"body": "Chinese Macao"}))
        not_china = InMemoryCorpus()
        not_china.add_document(InMemoryDocument(0, {"body": "Tokyo Japan Chinese"}))
        training_set = {"china": china, "not china": not_china}
        classifier = NaiveBayesClassifier(training_set, ["body"], self._normalizer, self._tokenizer)
        results = []
        classifier.classify("Chinese Chinese Chinese Tokyo Japan", lambda m: results.append(m))
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["category"], "china")
        self.assertAlmostEqual(math.exp(results[0]["score"]), 0.0003, 4)
        self.assertEqual(results[1]["category"], "not china")
        self.assertAlmostEqual(math.exp(results[1]["score"]), 0.0001, 4)

    def _classify_buffer_and_verify_top_categories(self, buffer, classifier, categories):
        results = []
        classifier.classify(buffer, lambda m: results.append(m))
        self.assertListEqual([results[i]["category"] for i in range(0, len(categories))], categories)

    def test_language_detection_trained_on_some_news_corpora(self):
        import os.path
        from corpus import InMemoryCorpus
        from naivebayesclassifier import NaiveBayesClassifier
        training_set = {language: InMemoryCorpus(os.path.join(data_path, f"{language}.txt")) for language in ["en", "no", "da", "de"]}
        classifier = NaiveBayesClassifier(training_set, ["body"], self._normalizer, self._tokenizer)
        self._classify_buffer_and_verify_top_categories("Vil det riktige språket identifiseres? Dette er bokmål.",
                                                        classifier, ["no"])
        self._classify_buffer_and_verify_top_categories("I don't believe that the number of tokens exceeds a billion.",
                                                        classifier, ["en"])
        self._classify_buffer_and_verify_top_categories("De danske drenge drikker snaps!",
                                                        classifier, ["da"])
        self._classify_buffer_and_verify_top_categories("Der Kriminalpolizei! Haben sie angst?",
                                                        classifier, ["de"])


if __name__ == '__main__':
    unittest.main()
