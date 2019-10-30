from test import simple_repl, data_path

def main():
    import os.path
    from normalization import BrainDeadNormalizer
    from tokenization import BrainDeadTokenizer
    from corpus import InMemoryCorpus
    from invertedindex import InMemoryInvertedIndex

    print("Building inverted index from Cranfield corpus...")
    normalizer = BrainDeadNormalizer()
    tokenizer = BrainDeadTokenizer()
    corpus = InMemoryCorpus(os.path.join(data_path, 'cran.xml'))
    index = InMemoryInvertedIndex(corpus, ["body"], normalizer, tokenizer)
    print("Enter one or more index terms and inspect their posting lists.")

    def evaluator(terms):
        terms = index.get_terms(terms)
        return {term: list(index.get_postings_iterator(term)) for term in terms}
    simple_repl("terms", evaluator)


if __name__ == '__main__':
    main()
