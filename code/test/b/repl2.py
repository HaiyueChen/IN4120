from test import simple_repl, data_path


def main():
    import os.path
    from normalization import BrainDeadNormalizer
    from tokenization import BrainDeadTokenizer
    from corpus import InMemoryCorpus
    from ahocorasick import Trie, StringFinder
    print("Building trie from MeSH corpus...")
    normalizer = BrainDeadNormalizer()
    tokenizer = BrainDeadTokenizer()
    corpus = InMemoryCorpus(os.path.join(data_path,'mesh.txt'))
    dictionary = Trie()
    for document in corpus:
        dictionary.add(normalizer.normalize(normalizer.canonicalize(document["body"])), tokenizer)
    engine = StringFinder(dictionary, tokenizer)
    print("Enter some text and locate words and phrases that are MeSH terms.")

    def evaluator(text):
        matches = []
        engine.scan(normalizer.normalize(normalizer.canonicalize(text)), lambda m: matches.append(m))
        return matches
    simple_repl("text", evaluator)


if __name__ == '__main__':
    main()
