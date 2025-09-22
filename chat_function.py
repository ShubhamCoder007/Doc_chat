from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticToolsParser
from langchain_google_genai import ChatGoogleGenerativeAI

from state import AgentState
from retriever import get_retriever
from utils import get_filtered_history
from schemas import QueryRefined, BoolResult
from checkpointer import checkpointer, save_user_state
from dotenv import load_dotenv
load_dotenv()


llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key="")


def build_chat_history(state: AgentState, limit: int = 10):
    """
    Reconstruct the chat history for a user from persisted checkpoints.
    """
    print("Building chat history from persistence...")
    history = []

    user_id = state.get("user_id")
    if not user_id:
        print("No user_id provided")
        return history

    try:
        # Fetch all checkpoints for this user
        checkpoints = list(checkpointer.list({"configurable": {"thread_id": user_id}}))
    except Exception as e:
        print(f"Failed to load checkpoints: {e}")
        return history

    for cp_tuple in checkpoints:
        try:
            # cp_tuple is a CheckpointTuple
            checkpoint_data = cp_tuple.checkpoint
            # user state is usually under channel_values -> __start__
            user_state = checkpoint_data.get("channel_values", {}).get("__start__", {})
            q = user_state.get("question")
            a = user_state.get("answer")
            doc_id = user_state.get("doc_id")
            if q and a:
                history.append({"question": q, "answer": a, "doc_id": doc_id})
        except Exception as e:
            print(f"Failed to read checkpoint: {e}")

    # Keep only last N entries
    if limit:
        history = history[-limit:]

    print(f"Total chat history: {len(history)}")
    return history




def query_rewriter_node(state: AgentState) -> AgentState:
    user_query = state["question"]
    chat_history = build_chat_history(state)
    state["chat_history"] = (
        get_filtered_history(state["doc_id"], chat_history) if chat_history else []
    )

    last_3_qa = state.get("chat_history", [])
    
    # Build context from history
    context = ""
    if last_3_qa:
        context = "Here is the recent conversation:\n"
        for qa in last_3_qa:
            context += f"Q: {qa['question']}\nA: {qa['answer']}\n"
    
    # Rewriting instructions
    prompt = f"""
You are a query rewriting assistant.

chat history: {context}

The user just asked: "{user_query}"

Your task:
1. If chat history exists, rewrite the query so it becomes a clear, contextually whole question.
2. If there is no history but the query is vague, try to make it more precise and meaningful.
3. If the query is already clear, keep it unchanged.

Return only the rewritten query, nothing else.
"""
    
    rephrased_query = llm.invoke(prompt)
    state["contextually_whole_query"] = rephrased_query.content
    
    return state




def question_classifier(state: AgentState):
    question = state["question"]
    retriever = get_retriever(state['doc_id'], k=8)
    chunks = retriever.get_relevant_documents("What is the document about?")

    context = ""
    for c in chunks:
        context += c.page_content + "\n\n"


    prompt = ChatPromptTemplate.from_messages([
    ("system", "Identify whether the question that is being asked is related to the document or not."),
    ("human", """
    this is an excerpt from the document: {context}

    question: {question}

    If the question is relevant output boolean True else False.
    """)
    ])

    parser = PydanticToolsParser(tools=[BoolResult])
    chain = prompt | llm.bind_tools(tools=[BoolResult], tool_choice=['BoolResult']) | parser
    result = chain.invoke({"question":question, "context":context})[0].bool_result
    state['on_topic'] = True#result

    return state


def on_topic_router(state: AgentState):
    if state['on_topic']:
        return "retriever_node"
    else:
        return "off_topic_node"
    

def off_topic_node(state: AgentState):
    state['answer'] = "Is there anything related to the document that I can help you with?"
    return state
    

def retriever_node(state: AgentState):
    print(f"[Retriever] performing retrieval on {state['doc_id']}")
    retriever = get_retriever(doc_id=state['doc_id'])
    print("state['contextually_whole_query'] -> ",state['contextually_whole_query'])
    question = state.get("contextually_whole_query") or state["question"]
    chunks = retriever.get_relevant_documents(question)
    chunk_list = []
    for chunk in chunks:
        chunk_list.append(chunk.page_content)
    state['retrieved_docs'] = chunk_list
    return state


def chunk_filter(state: AgentState):
    chunks = state["retrieved_docs"]
    # question = state['contextually_whole_query']
    question = state.get("contextually_whole_query") or state["question"]
    prompt = ChatPromptTemplate.from_messages([
    ("system", "Identify whether the chunk is relevant to answering the question."),
    ("human", """
    chunk: {chunk}

    question: {question}

    If the chunk is relevant output True else False.
    """)
    ])
    parser = PydanticToolsParser(tools=[BoolResult])
    chain = prompt | llm.bind_tools(tools=[BoolResult], tool_choice=['BoolResult']) | parser

    filtered_chunks = []
    for chunk in chunks:
        result = chain.invoke({"question":question, "chunk":chunk})[0].bool_result
        if result:
            filtered_chunks.append(chunk)

    state['relevant_docs'] = filtered_chunks
    return state



def proceed_to_generate(state: AgentState):
    print(f"[Route] Relevant docs: {len(state['relevant_docs'])}, Retries: {state['retry_count']}")
    if len(state['relevant_docs'])>0:
        print("Routing to answer generation")
        return "answer_node"
    elif state['retry_count']<2:
        print("Routing to query_refine")
        return "refine_query"
    else:
        print("Routing to default fallback")
        return "fallback"


def refine_query(state: AgentState):
    print(f"[Refine] Retry {state['retry_count']} → {state['contextually_whole_query']}")
    rephrase_count = state.get('retry_count', 0)
    if rephrase_count >= 2:
        print("Maximum rephrase attempts reached")
        return state
    question = state['contextually_whole_query']
    chat_history = state.get("chat_history", [])
    history_context = ""
    for qa in chat_history:
        history_context = f"Question: {qa['question']}\n Answer: {qa['answer']}\n\n"
    if len(chat_history)==0:
        history_context = "No chat history available."

    prompt = ChatPromptTemplate.from_messages([
    ("system", "Rephrase the query and keep it semantically same for retrieval purpose."),
    ("human", """
    question: {question}

    chat history: {history_context}

    Refer chat history if it exists to understand the context better and rephrase the question.
    Generate only one rephrased query.
    """)
    ])
    parser = PydanticToolsParser(tools=[QueryRefined])
    chain = prompt | llm.bind_tools(tools=[QueryRefined], tool_choice=['QueryRefined']) | parser
    response = chain.invoke({'question':question, 'history_context':history_context})
    state['retry_count'] = state['retry_count'] + 1
    state['contextually_whole_query'] = response[0].query

    return state


def generate_answer(state: AgentState):
    question = state.get("contextually_whole_query") or state["question"]
    chat_history = state.get("chat_history", [])
    print("chat hist len: ",len(chat_history))
    history_context = ""
    for qa in chat_history[-3:]:
        history_context = f"Question: {qa['question']}\n Answer: {qa['answer']}\n\n"
    if len(chat_history)==0:
        history_context = "No chat history available."

    chunks = state.get('relevant_docs', [])
    context = ""
    for chunk in chunks:
        context += chunk + "\n\n"

    prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an helpful agent who tries to answer the user's queries as best as you can strictly referring the context provided."),
    ("human", """
    question: {question}

    chat history: {history_context}
     
    context: {context}

    Refer chat history and the context provided in order to answer the user query.
    """)
    ])
    chain = prompt | llm
    response = chain.invoke({'question':question, 'history_context':history_context, "context":context})
    res = {}
    state['answer']=response.content
    # res['question']=state['question']
    # res['answer']=response.content
    # res['doc_id']=state['doc_id']
    # state["chat_history"].append(res)

    # chat_history = state.get("chat_history", [])
    # chat_history.append(res)
    # truncated_history = chat_history[-3:]
    # state["chat_history"] = truncated_history

    # return {"question":state.get("question", ""), "answer":state.get("answer", ""), "doc_id":state.get("doc_id", "")}

    # save_state(
    #     {k: state[k] for k in ["question", "answer", "doc_id", "user_id"] if k in state},
    #     state['doc_id']
    # )
    save_user_state(state)

    return {k: state[k] for k in ["question", "answer", "doc_id", "user_id"] if k in state}
    

def fallback(state: AgentState):
    state['answer'] = "Sorry but I'm unable to answer this question."
    return state



