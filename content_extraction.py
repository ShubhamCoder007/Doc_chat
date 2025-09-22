import fitz  # PyMuPDF

def extract_text_from_pdf(pdf_path: str) -> str:
    text = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text += page.get_text("text") + "\n"
    return text



# print(extract_text_from_pdf(r"C:\Users\shubh\Desktop\Workspace\doc_interact\data\1706.03762v7.pdf"))