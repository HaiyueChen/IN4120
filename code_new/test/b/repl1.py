from test import simple_repl, data_path

def main():
    import os.path
    from normalization import BrainDeadNormalizer
    from tokenization import BrainDeadTokenizer
    from corpus import InMemoryCorpus
    from suffixarray import SuffixArray
    print("Building suffix array from Cranfield corpus...")
    normalizer = BrainDeadNormalizer()
    tokenizer = BrainDeadTokenizer()
    corpus = InMemoryCorpus(os.path.join(data_path, 'cran.xml'))
    engine = SuffixArray(corpus, ["body"], normalizer, tokenizer)
    options = {"debug": False, "hit_count": 5}
    print("Enter a prefix phrase query and find matching documents.")
    print(f"Lookup options are {options}.")
    print("Returned scores are occurrence counts.")

    def evaluator(query):
        matches = []
        engine.evaluate(query, options, lambda m: matches.append(m))
        return matches
    simple_repl("query", evaluator)





if __name__ == '__main__':
    main()
