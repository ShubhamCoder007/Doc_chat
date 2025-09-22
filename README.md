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
