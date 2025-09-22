# chat_api.py
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse
from state import init_state
from chat_graph import graph_app  # import your compiled graph
import json
import asyncio

app = FastAPI(title="Document Chat API")

@app.post("/chat/")
async def chat_endpoint(request: Request):
    """
    Expects JSON payload:
    {
        "user_id": "user123",
        "doc_id": "61aa142c-a63e-4597-a654-d5405adc85e7",
        "question": "Explain attention"
    }
    """
    data = await request.json()
    user_id = data.get("user_id")
    doc_id = data.get("doc_id")
    question = data.get("question")

    if not all([user_id, doc_id, question]):
        return JSONResponse({"error": "user_id, doc_id, and question are required"}, status_code=400)

    # Initialize state for this user
    ob = init_state(doc_id=doc_id, user_id=user_id)
    ob['question'] = question

    # Use user_id as thread_id to maintain per-user history
    config = {"configurable": {"thread_id": user_id}}

    # Stream generator
    async def event_generator():
        try:
            # graph_app.stream returns a generator of state events
            for event in graph_app.stream(input=ob, config=config):
                # Yield each node update as JSON line
                for node, value in event.items():
                    output = json.dumps({"node": node, "answer": value.get('answer')})
                    yield f"data: {output}\n\n"
                    await asyncio.sleep(0.01)  # tiny sleep to allow streaming
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
