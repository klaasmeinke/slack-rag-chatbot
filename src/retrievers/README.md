This package defines retrievers that scrape sources and return documents.
Each retriever maps to a document type in the docs packages, except for the combined retriever (CombinedRetriever).
The combined retriever combines the other retrievers to get all documents.
The abstract class that retrievers inherit from is defined in type.py.