import sqlite3
import json
from datetime import datetime
from app.logger_config import log # Importe o logger

# Nome do arquivo de banco de dados
DB_NAME = "documentos.db"

def init_db():
    """Cria a tabela se ela ainda não existir"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_arquivo TEXT NOT NULL,
            dados_json TEXT NOT NULL,
            data_processamento TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def salvar_documento(nome, ficha_tecnica_pydantic):
    """Salva a ficha técnica no banco de dados"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Convertemos o objeto Pydantic em uma string JSON para salvar no banco
    json_str = json.dumps(ficha_tecnica_pydantic.model_dump())
    data_agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    cursor.execute('''
        INSERT INTO documentos (nome_arquivo, dados_json, data_processamento)
        VALUES (?, ?, ?)
    ''', (nome, json_str, data_agora))
    
    conn.commit()
    conn.close()

def listar_documentos():
    """Retorna todos os documentos salvos no banco"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT nome_arquivo, dados_json, data_processamento FROM documentos ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

def delete_all():
    """Função para deletar todos os registros (útil para testes)"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM documentos")
    conn.commit()
    conn.close()

def ja_existe(nome_arquivo):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM documentos WHERE nome_arquivo = ?", (nome_arquivo,))
        resultado = cursor.fetchone()
        conn.close()
        
        if resultado:
            log.info(f"Cache Hit: O arquivo {nome_arquivo} já existe no banco.")
        else:
            log.debug(f"Cache Miss: O arquivo {nome_arquivo} é novo.")
            
        return resultado is not None
    except Exception as e:
        log.error(f"Erro ao consultar a existência do arquivo no banco de dados: {str(e)}")
        return False