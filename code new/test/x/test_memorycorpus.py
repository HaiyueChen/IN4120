import unittest
from test import data_path

class TestInMemoryCorpus(unittest.TestCase):
    def test_access_documents(self):
        from corpus import InMemoryDocument, InMemoryCorpus
        corpus = InMemoryCorpus()
        corpus.add_document(InMemoryDocument(0, {"body": "this is a Test"}))
        corpus.add_document(InMemoryDocument(1, {"title": "prØve", "body": "en to tre"}))
        self.assertEqual(corpus.size(), 2)
        self.assertListEqual([d.document_id for d in corpus], [0, 1])
        self.assertListEqual([corpus[i].document_id for i in range(0, corpus.size())], [0, 1])
        self.assertListEqual([corpus.get_document(i).document_id for i in range(0, corpus.size())], [0, 1])

    def test_load_from_file(self):
        import os.path
        from corpus import InMemoryCorpus

        for file_name, file_size in (('mesh.txt', 25588), ('cran.xml', 1400), ('docs.json', 13), ('imdb.csv',1000)):
            self.assertEqual(InMemoryCorpus(os.path.join(data_path, file_name)).size(), file_size)
