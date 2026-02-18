import os
from dotenv import load_dotenv
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

def process_pdf(file_path: str):
    # PASSO A: Carregar o PDF
    loader = PyPDFLoader(file_path) # Função da Biblioteca
    pages = loader.load() # Função da Biblioteca (extrai o texto de todas as páginas)

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
    retriever = vector_db.as_retriever()

    llm = ChatGoogleGenerativeAI(model=MODEL_NAME, temperature=0)

    # NOVO PROMPT: Agora ele entende o que é Histórico e o que é Contexto
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Você é um especialista em análise de documentos. Use o contexto para responder."),
        MessagesPlaceholder(variable_name="chat_history"), # O "buraco" para o histórico
        ("human", "CONTEXTO:\n{context}\n\nPERGUNTA: {question}")
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