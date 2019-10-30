from test import simple_repl, data_path


def main():
    import os.path
    from normalization import BrainDeadNormalizer
    from tokenization import BrainDeadTokenizer
    from corpus import InMemoryCorpus
    from invertedindex import InMemoryInvertedIndex
    from ranking import BetterRanker
    from searchengine import SimpleSearchEngine
    print("Indexing English news corpus...")
    normalizer = BrainDeadNormalizer()
    tokenizer = BrainDeadTokenizer()
    corpus = InMemoryCorpus(os.path.join(data_path, 'en.txt'))
    index = InMemoryInvertedIndex(corpus, ["body"], normalizer, tokenizer)
    ranker = BetterRanker(corpus, index)
    engine = SimpleSearchEngine(corpus, index)
    options = {"debug": False, "hit_count": 5, "match_threshold": 0.5}
    print("Enter a query and find matching documents.")
    print(f"Lookup options are {options}.")
    print(f"Tokenizer is {tokenizer.__class__.__name__}.")
    print(f"Ranker is {ranker.__class__.__name__}.")

    def evaluator(query):
        matches = []
        engine.evaluate(query, options, ranker, lambda m: matches.append(m))
        return matches
    simple_repl("query", evaluator)


if __name__ == '__main__':
    main()
