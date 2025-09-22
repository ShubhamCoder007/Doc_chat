import shutil
import os
from fastapi import FastAPI, UploadFile, File
from index import index_pdf as run_index_pdf
import uuid

app = FastAPI(title="PDF Indexing API", version="1.0")

@app.post("/index_pdf/")
async def index_pdf_endpoint(file: UploadFile = File(...)):
    temp_dir = "temp_data"
    os.makedirs(temp_dir, exist_ok=True)

    file_path = os.path.join(temp_dir, file.filename)

    # Use shutil to copy file safely
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Run indexing
    doc_id = str(uuid.uuid4())
    result = run_index_pdf(pdf_path=file_path, doc_id=doc_id)

    # Clean up
    file.file.close() 
    os.remove(file_path)

    return {
        "filename": file.filename,
        "doc_id": doc_id,
        "chunk_count": result["chunk_count"]
    }
