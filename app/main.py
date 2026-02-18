import os
from fastapi import FastAPI, UploadFile, File
import shutil
from app.engine import process_pdf
from app.engine import process_pdf, ask_question

app = FastAPI(title="DocQuery API")

# Criar a pasta de uploads se ela não existir
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/")
def home():
    return {"message": "DocQuery Engine Online"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # 1. Limpar o nome do arquivo (remover espaços para evitar o erro que deu)
    clean_name = file.filename.replace(" ", "_") 
    file_path = os.path.join(UPLOAD_DIR, clean_name)
    
    # 2. Salvar o arquivo
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # 3. Converter para "Caminho Absoluto" (Dica de ouro para evitar o ValueError)
    # Isso transforma "uploads/file.pdf" em "C:/Users/Felix.../uploads/file.pdf"
    absolute_path = os.path.abspath(file_path)
    
    # 4. Processar
    chunks = process_pdf(absolute_path)
    
    return {
        "filename": clean_name, 
        "chunks_criados": len(chunks), 
        "message": "Arquivo processado com sucesso!"
    }

@app.get("/ask")
async def ask(question: str):
    answer = ask_question(question)
    return {"question": question, "answer": answer}