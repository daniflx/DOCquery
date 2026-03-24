# test_ragas.py

import os
import pandas as pd
from dotenv import load_dotenv
from datasets import Dataset

# Importando o RAGAS e as duas métricas que você pediu
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy

# Importando os modelos que o RAGAS vai usar como "Juiz"
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.embeddings import HuggingFaceEmbeddings

# Importando o SEU motor para gerar as respostas
from app.engine import ask_question

# Carrega as variáveis de ambiente (sua GOOGLE_API_KEY)
load_dotenv()
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY", "")
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-2.5-flash-lite")

def executar_avaliacao():
    print("🤖 Iniciando Avaliação RAGAS...")

    # 1. Configurando o Juiz (A IA que vai dar a nota)
    # O RAGAS precisa de um LLM e de um modelo de embeddings para avaliar. 
    # Vamos usar os mesmos que você já tem no projeto.
    juiz_llm = ChatGoogleGenerativeAI(model=MODEL_NAME, temperature=0)
    juiz_embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    # 2. Criando nossas perguntas de teste
    # Escolha perguntas que você sabe que o documento que você subiu pode responder
    perguntas_teste = [
        "Qual é o nome da pessoa ou empresa mencionada no documento?",
        "Quais são os valores ou objetivos destacados no documento?",
    ]

    # O RAGAS exige que os dados estejam neste formato exato de dicionário:
    dados_para_ragas = {
        "question": [], # As perguntas
        "answer": [],   # A resposta que SUA IA gerou
        "contexts": []  # Os pedaços do PDF que o FAISS achou
    }

    print(f"🔍 Gerando respostas para {len(perguntas_teste)} perguntas usando seu sistema...")

    # 3. Rodando o SEU sistema para cada pergunta e guardando os resultados
    for pergunta in perguntas_teste:
        print(f"  - Perguntando: '{pergunta}'")
        
        # Chama a sua função (agora ela devolve um dicionário)
        resultado = ask_question(pergunta)
        
        # Guardamos os dados nas listas
        dados_para_ragas["question"].append(pergunta)
        dados_para_ragas["answer"].append(resultado["answer"])
        dados_para_ragas["contexts"].append(resultado["contexts"])

    # 4. Convertendo o dicionário para um "Dataset" do HuggingFace (exigência do RAGAS)
    dataset = Dataset.from_dict(dados_para_ragas)

    print("⚖️  Enviando para o RAGAS avaliar (Isso pode demorar alguns segundos...)")

    # 5. A Mágica Acontece Aqui: Avaliando!
    resultado_avaliacao = evaluate(
        dataset=dataset,
        metrics=[faithfulness, answer_relevancy], # As métricas que você pediu
        llm=juiz_llm,
        embeddings=juiz_embeddings
    )

    # 6. Exibindo os resultados de forma bonita (via Pandas)
    print("\n✅ Avaliação Concluída! Veja as notas (de 0.0 a 1.0):")
    
    # Converte o resultado para um DataFrame do Pandas para visualização fácil
    df = resultado_avaliacao.to_pandas()
    
    # Opcional: Salvar em Excel/CSV para analisar depois
    df.to_csv("resultado_ragas.csv", sep=";", index=False)
    
# 1. Imprime os nomes exatos das colunas que o RAGAS gerou
    
    # Configura o Pandas para não esconder o texto com '...'
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_colwidth', None)
    pd.set_option('display.width', 1000)

    # Imprime apenas as colunas que nos interessam
    print("\n🚀 RESULTADO FINAL DA AVALIAÇÃO:")
    print(df[['user_input', 'faithfulness', 'answer_relevancy', 'response']])

if __name__ == "__main__":
    executar_avaliacao()