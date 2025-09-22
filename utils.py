from state import AgentState
from checkpointer import checkpointer


def get_filtered_history(doc_id, chat_hist, k=3):
    """
    Filters chat history for the respective doc_id
    """
    filtered_chat_history = []
    for ch in chat_hist[::-1]:
        d={}
        if ch['doc_id']==doc_id:
            d['question']=ch['question']
            d['answer']=ch['answer']
            filtered_chat_history.append(d)
    print(f"Found {len(filtered_chat_history)} previous chat history for {doc_id}")
    return filtered_chat_history[::-1][-3:]



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
