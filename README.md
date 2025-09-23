# Doc_chat
Agentic doc chat application. 

Install all the dependencies from requirements.txt
pip install -r requirements.txt

Index_app has the FastAPI implementation for exposing the indexing service index_api/ end point.
Run: 
uvicorn index_app:app --host 0.0.0.0 --port 8118 --reload

chat_app has the FastAPI implementation for exposing the chat function service end point.
Run:
uvicorn chat_app:app --host 0.0.0.0 --port 8008 --reload

Finally Run the streamlit_app ui, or use the above service contained inside other service and so on.
Run:
streamlit run Streamlit_app.py

*******************************************************************************************************

Techniques and frameworks
================================================
Vector data base & Retriever: chromadb / Chroma
Embeddings: MiniLM L6, embedding dim 384
LLM: gemini 2 flash
Architecture: Multi turn Agentic RAG
Persistence checkpointer: Sqlite saver
Endpoint: FastAPI
UI: streamlit
Framework: langchain, langgraph
================================================


Upload and Index
=================
We first upload a document, perform content extraction using pymupdf.
Following this we perform chunking, we did simple Reccurssive text splitter with chunk size 1000, and overlap of 200.
Then we embed the chunks and index it in the vector db, we use chroma db here.
I have used simple embedding MiniLM L6 - which has around 384 dimensional embeddings.
Higher dimensional like the HFEmbedding can be used from embedding creator if the system configuration is higher.
Index file has all the above implementation which performs the file indexation.

Chat Function
=================
We define all the chat function flow in the chat function.
It follows a complete Agentic flow. When the query is first triggered, we set the entry point in the graph
to query_rewriter_node which leverages the chat history which we custom build by first filtering out using the doc_id 
for only the matching doc_id in hand and then considering only the last 3 state, and building the chat history out of this.
Using chat history, we rewrite the query to make it contextually whole query, or a rephrased version if the chat history is not available.

Then we classify the query to check whether it references the same document or not, if not it routes to off topic node and then ends.

Post this we move to the retrieval node, where we first filter by the doc_id and then make vector search retrieval with search type as
Maximal marginal relevance and chunk numbers as 4. We do the retrieval by leveraging contextually whole query.

After the retrieval operation we then proceed to the chunk filter where it filters the chunk for the relevancy to answer the
user query. If it completely filters out or discards the chunks then refine query node gets triggered for max retry of 3,
else if there is atleast one candidate chunk, it proceeds to answer generation.
Refine query again tries to rephrase the query better so that better retrieval can happen.
Finally post answer generation we save the state using sqlite saver.


All of the functional node implementation in chat function is encapsulated in the graph structure in chat graph file,
with sqlite saver being the checkpointer persistence state saving option.

Exposing Endpoint
===================
We expose the endpoint for chat function using FastAPI in the chat_app file and,
the endpoint for indexation in the index_app file.

UI
======
We have a very simple UI implementation leveraging streamlit which interacts with the endpoints.


Scopes for improvement and Future scopes
===========================================
Robust chunking pipeline like semantic chunking with added table data preserving capability.
Richer metadata field population while indexing.
Advanced vector retrieval strategies like hybrid retrieval / multivector retrieval.
Query decomposition and augmentation pipeline.
Chunk continuation implementation.

