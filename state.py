from typing import TypedDict, List, Annotated, Dict
import operator

class AgentState(TypedDict):
    chat_history: List[Dict[str, str]]
    question: str
    contextually_whole_query: str
    answer: str
    retrieved_docs: List[str]
    relevant_docs: List[str]
    retry_count: int
    doc_id: str
    user_id: str
    on_topic: bool



def init_state(doc_id: str, user_id) -> AgentState:
    return {
        "chat_history": [],              
        "question": "",                 
        "contextually_whole_query": "",  
        "answer": "",             
        "retrieved_docs": [],  
        "relevant_docs": [],
        "retry_count": 0, 
        "on_topic": True,
        "doc_id": doc_id,
        "user_id": user_id
    }
