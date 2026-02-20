# DocQuery AI 📄

O **DocQuery AI** é uma plataforma de Processamento Inteligente de Documentos (IDP) que utiliza Inteligência Artificial Generativa para permitir conversas contextuais com arquivos PDF. 

O projeto foi desenvolvido com foco em soluções de **RAG (Retrieval-Augmented Generation)**, permitindo que o usuário faça perguntas sobre documentos específicos e receba respostas precisas baseadas apenas no conteúdo fornecido.

## Funcionalidades Atuais

* **Upload de Múltiplos PDFs:** Processamento e indexação de documentos em lote.
* **Conversa Contextual (RAG):** Busca semântica de informações dentro dos arquivos.
* **Memória de Curto Prazo:** O chat recorda o contexto da conversa atual para perguntas de acompanhamento.
* **Interface Interativa:** Desenvolvido com Streamlit para uma experiência de usuário fluida.

## Tech Stack

* **LLM:** Google Gemini 2.5 FlashLite
* **Orquestração:** LangChain (LCEL)
* **Banco de Dados Vetorial:** FAISS
* **Embeddings:** HuggingFace (all-MiniLM-L6-v2)
* **Frontend:** Streamlit

## Arquitetura do Sistema

1. **Ingestão:** O PDF é carregado e dividido em *chunks* (pedaços) menores.
2. **Vetorização:** Cada pedaço é transformado em um vetor numérico via Embeddings.
3. **Armazenamento:** Os vetores são salvos no FAISS para buscas rápidas.
4. **Recuperação:** Ao fazer uma pergunta, o sistema busca os pedaços mais relevantes.
5. **Geração:** O Gemini processa o contexto e gera uma resposta humanizada.


## 🛠️ Próximos Passos (Roadmap)

### 1. Inteligência de Documentos (IDP)
- [ ] Map-Reduce IDP: Implementar processamento em massa para extrair informações de centenas de documentos simultaneamente, superando o limite de janela de contexto.

### 2. Otimização de Recuperação (RAG Profissional)
- [ ] **Re-ranking com FlashRank:** Refinar os 10 resultados mais próximos para entregar apenas os 3 mais relevantes à LLM.
- [ ] **Contextual Compression:** Reduzir o ruído dos documentos recuperados para economizar tokens e aumentar a precisão.

### 3. Governança e Métricas (MLOps)
- [ ] **Framework RAGAS:** Implementar métricas de *Faithfulness* (fidelidade) e *Answer Relevance* para monitorar alucinações.