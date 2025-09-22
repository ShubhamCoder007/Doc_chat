from content_extraction import extract_text_from_pdf
from chunkify import chunk_text
from embedding_creator import embed_chunks
from vectordb import store_in_chroma

def index_pdf(pdf_path: str, doc_id: str):
    content = extract_text_from_pdf(pdf_path)
    chunks = chunk_text(content)
    embeddings = embed_chunks(chunks)
    store_in_chroma(chunks, embeddings, doc_id)
    print(f"Successfully Indexed {len(chunks)} chunks from {pdf_path}")
    return {"chunk_count":len(chunks)}

