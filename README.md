# DocQuery AI: Intelligent Document Processing & Advanced RAG

DocQuery AI é uma solução empresarial de Processamento Inteligente de Documentos (IDP) baseada em arquitetura **Retrieval-Augmented Generation (RAG)**. O sistema transforma dados não estruturados (PDFs) em conhecimento acionável através de busca semântica e extração de metadados estruturados.



## Diferenciais de Engenharia

Diferente de implementações RAG convencionais, este projeto aplica padrões de design focados em eficiência operacional:

* **Atribuição de Fonte (Metadata Lineage):** Cada chunk de informação é indexado com metadados de origem, garantindo que a LLM cite o arquivo específico ao gerar respostas, mitigando alucinações.
* **Camada de Persistência Híbrida:** Utilização de FAISS para busca vetorial (semântica) e SQLite para armazenamento de fichas técnicas estruturadas e cache de metadados.
* **Otimização de Custos (FinOps):** Lógica de processamento condicional que verifica a existência do documento no banco de dados antes de realizar chamadas à API de extração de dados (IDP), reduzindo drasticamente o consumo de tokens.
* **Observabilidade:** Implementação de logging estruturado (INFO, DEBUG, ERROR) com captura de Stack Trace para monitoramento de saúde do pipeline em tempo real.

## Tech Stack

* **Modelo de Linguagem:** Google Gemini 2.5 FlashLite (escolhido pelo equilíbrio entre baixa latência e alta janela de contexto).
* **Orquestração:** LangChain (uso de LCEL para chains customizadas).
* **Vector Database:** FAISS (Facebook AI Similarity Search).
* **Embeddings:** HuggingFace (`all-MiniLM-L6-v2`) para processamento local eficiente.
* **Banco de Dados Relacional:** SQLite para persistência de fichas técnicas estruturadas via Pydantic.
* **Interface:** Streamlit.

## Arquitetura de Dados

### 1. Ingestão e Processamento
* Leitura via `PyPDFLoader` e segmentação através de `RecursiveCharacterTextSplitter`.
* Enriquecimento de metadados durante a fase de *chunking* para rastreabilidade de arquivos.

### 2. Extração Estruturada (IDP)
* Utilização de Output Parsers para converter texto não estruturado em objetos JSON tipados (Pydantic), facilitando a integração com outros sistemas e exportação para CSV/Excel.

### 3. Recuperação e Resposta
* Busca por similaridade de cosseno no banco vetorial.
* Injeção de contexto dinâmico no prompt system, forçando a LLM a utilizar apenas a base de conhecimento fornecida.



## Estrutura do Projeto

```text
├── app/
│   ├── database.py       # Gerenciamento SQLite e persistência estruturada
│   ├── engine.py         # Lógica central de RAG e integração com LLM
│   ├── logger_config.py  # Configuração de observabilidade e logs
│── app_web.py            # Interface de usuário e gerenciamento de estado
├── uploads/              # Armazenamento temporário de documentos (ignorado no git)
├── faiss_index/          # Banco de dados vetorial local (ignorado no git)
└── app_debug.log         # Logs de auditoria do sistema (ignorado no git)

Roadmap de Evolução
Fase 1: Infraestrutura e Portabilidade
[ ] Dockerization: Containerização da aplicação para garantir paridade entre ambientes de desenvolvimento e produção.

[ ] Docker Compose: Orquestração de containers para facilitar o setup inicial.

Fase 2: Refinamento de Recuperação
[ ] Re-ranking: Implementação de Cross-Encoders para refinar a relevância dos documentos recuperados antes da síntese.

[ ] Multi-Query Retrieval: Geração de variações da pergunta do usuário para capturar trechos de documentos com diferentes termos semânticos.

Fase 3: MLOps e Avaliação
[ ] Framework RAGAS: Automação de testes para medir a precisão (faithfulness) e relevância das respostas.

Como rodar o projeto
Localmente
Clone o repositório.

Crie um ambiente virtual: python -m venv venv.

Instale as dependências: pip install -r requirements.txt.

Configure sua GOOGLE_API_KEY no arquivo .env.

Execute: streamlit run app/app_web.py.