import streamlit as st
import requests
import uuid

INDEX_API = "http://localhost:8118/index_pdf/"
CHAT_API = "http://localhost:8008/chat/" 

st.set_page_config(page_title="Document Chat", layout="wide")

st.title("📑 Document Chatbot")

# Sidebar for User ID
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())

st.sidebar.write(f"User ID: `{st.session_state.user_id}`")

# ---- Upload & Index PDF ----
st.header("Step 1: Upload and Index a PDF")
uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])

if uploaded_file is not None:
    if st.button("Index Document"):
        files = {"file": uploaded_file.getvalue()}
        resp = requests.post(INDEX_API, files={"file": uploaded_file})
        if resp.status_code == 200:
            result = resp.json()
            st.session_state.doc_id = result["doc_id"]
            st.success(f"Document indexed ✅ | doc_id: {st.session_state.doc_id}")
        else:
            st.error(f"Failed to index: {resp.text}")

# ---- Chat ----
st.header("Step 2: Chat with the Document")
if "doc_id" not in st.session_state:
    st.warning("⚠️ Please upload and index a PDF first.")
else:
    question = st.text_input("Enter your question:")
    if st.button("Ask"):
        with st.spinner("Thinking..."):
            payload = {
                "user_id": st.session_state.user_id,
                "doc_id": st.session_state.doc_id,
                "question": question,
            }
            resp = requests.post(CHAT_API, json=payload, stream=True)

            if resp.status_code == 200:
                answer = ""
                for line in resp.iter_lines():
                    if line:
                        data = line.decode("utf-8").replace("data: ", "")
                        try:
                            obj = eval(data)  # convert JSON string to dict
                            if obj.get("answer"):
                                answer = obj["answer"]
                                st.write(f"🤖 {answer}")
                        except Exception as e:
                            st.error(f"Parse error: {e}")
            else:
                st.error(f"Chat API error: {resp.text}")
