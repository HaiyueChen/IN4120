from test import simple_repl, data_path


def main():
    import os.path
    from normalization import BrainDeadNormalizer
    from tokenization import BrainDeadTokenizer
    from corpus import InMemoryCorpus
    from naivebayesclassifier import NaiveBayesClassifier
    print("Initializing naive Bayes classifier from news corpora...")
    normalizer = BrainDeadNormalizer()
    tokenizer = BrainDeadTokenizer()
    languages = ["en", "no", "da", "de"]
    training_set = {language: InMemoryCorpus(os.path.join(data_path,f"{language}.txt")) for language in languages}
    classifier = NaiveBayesClassifier(training_set, ["body"], normalizer, tokenizer)
    print(f"Enter some text and classify it into {languages}.")
    print(f"Returned scores are log-probabilities.")

    def evaluator(text):
        results = []
        classifier.classify(text, lambda m: results.append(m))
        return results
    simple_repl("text", evaluator)

if __name__ == '__main__':
    main()
