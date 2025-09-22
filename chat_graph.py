from langgraph.graph import StateGraph, END

from chat_function import query_rewriter_node
from chat_function import question_classifier
from chat_function import on_topic_router
from chat_function import retriever_node
from chat_function import chunk_filter
from chat_function import proceed_to_generate
from chat_function import refine_query
from chat_function import generate_answer
from chat_function import fallback
from chat_function import off_topic_node
from state import AgentState
from checkpointer import checkpointer


graph = StateGraph(AgentState)

graph.add_node("query_rewriter_node", query_rewriter_node)
graph.add_node("refine_query", refine_query)
graph.add_node("query_classifier", question_classifier)
graph.add_node("off_topic_node", off_topic_node)
graph.add_node("retriever_node", retriever_node)
graph.add_node("chunk_filter", chunk_filter)
graph.add_node("answer_node", generate_answer)
graph.add_node("fallback", fallback)

graph.set_entry_point("query_rewriter_node")
graph.add_edge("query_rewriter_node", "query_classifier")
graph.add_conditional_edges("query_classifier", on_topic_router)
graph.add_edge("retriever_node", "chunk_filter")

graph.add_conditional_edges(
    "chunk_filter",
     proceed_to_generate,
     {
        "answer_node": "answer_node",
        "refine_query": "refine_query",
        "fallback": "fallback",
    })

graph.add_edge("refine_query", "retriever_node")
graph.add_edge("fallback", END)
graph.add_edge("answer_node", END)
graph.add_edge("off_topic_node", END)

graph_app = graph.compile(checkpointer=checkpointer)



#Test
# from state import init_state
# config = {"configurable": {"thread_id":"user123"}}
# doc_id = "1ba16a71-b2e8-4359-8fab-fa75a0eef312"
# ob = init_state(doc_id=doc_id, user_id="user123")
# # ob['question']="explain attention"
# ob['question']="whats the number for it?"
# # ob['question']="give me the formula"
# res = graph_app.stream(input=ob, config=config)

# for event in res:
#     print(event, "\n\n")

#     for node, value in event.items():
#         print(f"Processing {node}")
#         if node == 'answer_node':
#             print("Final Answer:", value["answer"])