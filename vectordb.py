import chromadb
from chromadb.utils import embedding_functions

from embedding_creator import HFEmbeddings

# embedding_function = HFEmbeddings()
embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

client = chromadb.PersistentClient(path="./chroma_db")

collection = client.get_or_create_collection(
    name="pdf_docs",
    embedding_function=embedding_function
)

def store_in_chroma(chunks, embeddings, doc_id):
    for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
        collection.add(
            ids=[f"{doc_id}_{i}"],
            documents=[chunk],
            embeddings=[emb],
            metadatas=[{"doc_id": doc_id, "chunk": i}]
        )


