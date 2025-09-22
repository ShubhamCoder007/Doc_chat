from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3
from state import AgentState
import time
import datetime
from datetime import datetime, timezone
import uuid

sqlite_conn = sqlite3.connect("checkpoint.sqlite", check_same_thread=False)
checkpointer = SqliteSaver(sqlite_conn)


def save_user_state(state: AgentState):
    print("Saving user state...")
    user_id = state.get("user_id")
    if not user_id:
        return

    checkpoint = {
        "v": 4,
        "ts": datetime.now(timezone.utc).astimezone().isoformat() + "Z",
        "id": str(uuid.uuid4()),
        "channel_values": {"__start__": dict(state)}, 
        "channel_versions": {"__start__": str(time.time())}, 
        "versions_seen": {"__input__": {}},
        "updated_channels": ["__start__"],
    }

    write_config = {"configurable": {"thread_id": user_id, "checkpoint_ns": "chat_graph_ns"}}
    checkpointer.put(write_config, checkpoint, {}, {})