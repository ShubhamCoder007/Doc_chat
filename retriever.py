from langchain.vectorstores import Chroma
from chromadb.utils import embedding_functions

embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

def get_retriever(doc_id:str, search_type="mmr", k=4):
    retriever = Chroma(
    collection_name="pdf_docs",  # your existing collection
    embedding_function=embedding_function,
    persist_directory="./chroma_db"
    ).as_retriever(
        search_type=search_type,
        search_kwargs={"k": k},
        filter={"doc_id": doc_id}
    )

    return retriever

