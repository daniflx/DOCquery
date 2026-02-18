import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader # 1. O "Leitor" de PDF
from langchain_text_splitters import RecursiveCharacterTextSplitter # 2. O "Fatiador" de texto
from langchain_community.embeddings import HuggingFaceEmbeddings # Gerador de números
from langchain_community.vectorstores import FAISS # O Banco de Dados
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

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

def ask_question(question: str):
    # Carrega o banco
    vector_db = FAISS.load_local("faiss_index", embeddings_model, allow_dangerous_deserialization=True)
    retriever = vector_db.as_retriever()

    # Configura a IA
    llm = ChatGoogleGenerativeAI(
        model=MODEL_NAME,
        google_api_key=os.getenv("GOOGLE_API_KEY"), # Passando a chave diretamente aqui por segurança
        version="v1",
        temperature=0 # Deixa a resposta mais precisa e menos "criativa"
    )
    # Criamos o "Template" da conversa (O que a IA deve fazer)
    template = """Você é um especialista em análise de documentos PDF.

        CONTEXTO:
            {context}

        INSTRUÇÕES:
        1. Analise o contexto acima e responda à pergunta do usuário.
        2. Seja extremamente atento a links (URLs), nomes de redes sociais (LinkedIn) e portfólios (Notion, GitHub , Sites).
        4. Seja atento a datas, cargos, empresas e habilidades técnicas.
        5. Seja atento a Números, Valores em dinheiro, porcentagens e métricas de desempenho.
        6. Se encontrar algo que pareça um link, extraia-o integralmente.
        7. Se a informação não estiver no contexto, diga claramente: "Não encontrei essa informação específica nos documentos."

        PERGUNTA: {question}

        RESPOSTA:"""
    prompt = ChatPromptTemplate.from_template(template)

    # A "Corrente" Moderna (Chain) - Isso substitui o load_qa_chain
    chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    return chain.invoke(question)