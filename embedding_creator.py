from sentence_transformers import SentenceTransformer

from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from transformers import AutoModel, AutoTokenizer
from langchain.embeddings.base import Embeddings
from typing import List
from dotenv import load_dotenv
import torch

# load_dotenv()


def embed_chunks(chunks):
    embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    return embedding_model.encode(chunks, show_progress_bar=True).tolist()
 

 

class HFEmbeddings(Embeddings):
    def __init__(self, model_name='jinaai/jina-embeddings-v2-base-en'):
        self.model = AutoModel.from_pretrained(model_name, trust_remote_code=True)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)


    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        embeddings = self.model.encode(texts)
        if torch.is_tensor(embeddings):
            embeddings = embeddings.cpu().numpy()
        return embeddings.tolist()

   
    def embed_query(self, text: str) -> List[float]:
        embedding = self.model.encode([text])
        if torch.is_tensor(embedding):
            embedding = embedding.cpu().numpy()
        return embedding[0].tolist()

