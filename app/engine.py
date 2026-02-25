import os
from dotenv import load_dotenv
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum
from langchain_community.document_loaders import PyPDFLoader # 1. O "Leitor" de PDF
from langchain_text_splitters import RecursiveCharacterTextSplitter # 2. O "Fatiador" de texto
from langchain_community.embeddings import HuggingFaceEmbeddings # Gerador de números
from langchain_community.vectorstores import FAISS # O Banco de Dados
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_community.chat_message_histories import ChatMessageHistory

load_dotenv()
# Isso garante que o Google encontre sua chave
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY", "")

# Variáveis globais baseadas no .env
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-2.5-flash-lite")

embeddings_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")


# 1. Definimos as categorias possíveis (Enum) - Isso evita que a IA invente tipos
class DocumentType(str, Enum):
    CURRICULO = "curriculo"
    NOTA_FISCAL = "nota_fiscal"
    OUTRO = "outro"

# 2. Criamos o Schema (Molde) que a IA deve preencher
class FichaTecnica(BaseModel):
    tipo: DocumentType = Field(description="O tipo de documento identificado")
    entidade_principal: Optional[str] = Field(None, description="Nome da pessoa ou da empresa")
    data_documento: Optional[str] = Field(None, description="Data de emissão ou nascimento se houver")
    valor_ou_objetivo: Optional[str] = Field(None, description="Valor total (nota) ou Objetivo profissional (currículo)")
    analise_confianca: float = Field(description="Nota de 0 a 1 sobre o quão confiável é essa extração")
    resumo_critico: Optional[str] = Field(None, description="Um resumo curto destacando os pontos mais importantes do documento")

# 3. Função de Extração
def extrair_dados_idp(texto_completo: str):
    # Usamos temperatura 0 para máxima precisão técnica
    llm = ChatGoogleGenerativeAI(model=MODEL_NAME, temperature=0)
    
    # O método 'with_structured_output' força o Gemini a retornar um objeto Pydantic
    extrator = llm.with_structured_output(FichaTecnica)
    
    prompt = f"""
    Sua tarefa é ler o texto de um documento e extrair uma ficha técnica estruturada.
    Se o documento não for um currículo ou nota fiscal, classifique como 'outro'.
    
    TEXTO:
    {texto_completo[:5000]} # Limitamos para segurança de tokens
    """
    
    try:
        resultado = extrator.invoke(prompt)
        return resultado
    except Exception as e:
        print(f"Erro na extração estruturada: {e}")
        return None
    
def process_pdf(file_path: str):
    # PASSO A: Carregar o PDF
    loader = PyPDFLoader(file_path) # Função da Biblioteca
    pages = loader.load() # Função da Biblioteca (extrai o texto de todas as páginas)

    # Limpar o metadado para exibir apenas o nome do arquivo e retirar o caminho completo, para evitar problemas de tokenização
    nome_arquivo = os.path.basename(file_path)
    for page in pages:
        page.metadata["source"] = nome_arquivo  # Padroniza a etiqueta da fonte

    # PASSO B: Configurar o Fatiador (Text Splitter)
    # Criamos uma "variável de configuração" do fatiador
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,   # Tamanho de cada "fatia" (1000 caracteres)
        chunk_overlap=100, # "Sobra" de texto para não cortar uma frase no meio
        length_function=len
    )

    # PASSO C: Cortar o texto em pedaços (Chunks)
    chunks = text_splitter.split_documents(pages)

# LÓGICA DE ACÚMULO:
    if os.path.exists("faiss_index"):
        # Se o banco já existe, carrega ele e adiciona os novos chunks
        vector_db = FAISS.load_local("faiss_index", embeddings_model, allow_dangerous_deserialization=True)
        vector_db.add_documents(chunks)
    else:
        # Se não existe, cria o primeiro
        vector_db = FAISS.from_documents(chunks, embeddings_model)
        
    # Salvar localmente
    vector_db.save_local("faiss_index")
   
    return chunks

def ask_question(question: str, chat_history: list = None):
    # Se não passarem histórico, iniciamos uma lista vazia
    if chat_history is None:
        chat_history = []

    vector_db = FAISS.load_local("faiss_index", embeddings_model, allow_dangerous_deserialization=True)
    retriever = vector_db.as_retriever(search_kwargs={"k": 5})

    llm = ChatGoogleGenerativeAI(model=MODEL_NAME, temperature=0)

    # NOVO PROMPT: Agora ele entende o que é Histórico e o que é Contexto
    prompt = ChatPromptTemplate.from_messages([
        ("system", """Você é um especialista em análise de documentos sênior. 
        Use estritamente o contexto fornecido para responder.
        REGRAS:
        1. Sempre identifique de qual arquivo (Source) veio a informação.
        2. Se a informação não estiver no contexto, diga que não sabe.
        3. Seja conciso e profissional."""),
        MessagesPlaceholder(variable_name="chat_history"), # O "buraco" para o histórico
        ("human", "Aqui está o contexto extraído dos documentos:\n{context}\n\nPERGUNTA: {question}")
    ])

    # A CHAIN: Agora ela mapeia o chat_history que vem lá do Streamlit
    chain = (
        {
            "context": retriever, 
            "question": RunnablePassthrough(),
            "chat_history": lambda x: chat_history # Injeta o histórico aqui
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    return chain.invoke(question)