import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import shutil
from app.engine import process_pdf, ask_question
from app.logger_config import log

app = FastAPI(
    title="DocQuery API",
    description="Backend API para análise de documentos com IA",
    version="1.0.0"
)

# ===== CONFIGURAÇÃO DE CORS =====
# Permite requisições do Streamlit (localhost:8501) para a API (localhost:8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especifique os domínios exatos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Criar a pasta de uploads se ela não existir
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/")
def home():
    """Endpoint de health check"""
    return {
        "message": "DocQuery Engine Online",
        "status": "healthy",
        "version": "1.0.0"
    }

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Faz upload de um arquivo PDF e o processa para embeddings.
    
    Args:
        file: Arquivo PDF enviado pelo cliente
        
    Returns:
        Informações sobre o processamento do arquivo
    """
    try:
        # 1. Validar tipo de arquivo
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Apenas arquivos PDF são permitidos")
        
        # 2. Limpar o nome do arquivo (remover espaços)
        clean_name = file.filename.replace(" ", "_") 
        file_path = os.path.join(UPLOAD_DIR, clean_name)
        
        log.info(f"Iniciando upload do arquivo: {clean_name}")
        
        # 3. Salvar o arquivo
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 4. Converter para caminho absoluto
        absolute_path = os.path.abspath(file_path)
        log.debug(f"Arquivo salvo em: {absolute_path}")
        
        # 5. Processar o PDF
        chunks = process_pdf(absolute_path)
        
        if chunks is None:
            raise HTTPException(status_code=500, detail="Erro ao processar o PDF")
        
        log.info(f"Arquivo {clean_name} processado com sucesso. Total de chunks: {len(chunks)}")
        
        return {
            "status": "success",
            "filename": clean_name, 
            "chunks_criados": len(chunks), 
            "message": "Arquivo processado com sucesso!"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Erro ao fazer upload/processar arquivo: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao processar arquivo: {str(e)}")

@app.post("/ask")
async def ask_endpoint(question: str):
    """
    Faz uma pergunta baseada nos documentos indexados.
    
    Args:
        question: Pergunta do usuário
        
    Returns:
        Resposta baseada nos documentos indexados
    """
    try:
        if not question or question.strip() == "":
            raise HTTPException(status_code=400, detail="Pergunta não pode estar vazia")
        
        log.info(f"Pergunta recebida: {question}")
        
        answer = ask_question(question)
        
        if answer is None:
            raise HTTPException(status_code=500, detail="Erro ao processar a pergunta")
        
        log.info(f"Resposta gerada com sucesso")
        
        return {
            "status": "success",
            "question": question, 
            "answer": answer
        }
    
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Erro ao processar pergunta: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao processar pergunta: {str(e)}")