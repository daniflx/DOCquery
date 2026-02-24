import streamlit as st
from app.engine import process_pdf, ask_question, extrair_dados_idp
import os
from PyPDF2 import PdfReader

# Configuração da Página
st.set_page_config(page_title="DocQuery AI", page_icon="📄", layout="centered")

st.title("📄 DocQuery AI")
st.markdown("### Analise seus documentos com Inteligência Artificial")

# Sidebar para Upload
with st.sidebar:
    st.header("Configurações")
    uploaded_files = st.file_uploader("Escolha os PDFs", type="pdf", accept_multiple_files=True)
    
    if st.button("Processar Documentos"):
        if uploaded_files:
            with st.spinner("Lendo e indexando arquivos..."):
                # LIMPA O HISTÓRICO APENAS UMA VEZ NO INÍCIO
                st.session_state.chat_history = [] 
                st.session_state.messages = []
                
                texto_completo = "" # Variável para acumular o texto de todos os arquivos

                for uploaded_file in uploaded_files:
                    path = os.path.join("uploads", uploaded_file.name)
                    with open(path, "wb") as f:
                        f.write(uploaded_file.read())
                    
                    # 1. Processa para o RAG (Vetores)
                    process_pdf(path)

                    # 2. Extrai o texto bruto para a Ficha Técnica (IDP)
                    reader = PdfReader(path)
                    for page in reader.pages:
                        texto_completo += page.extract_text() + "\n"
                
                # Guardamos o texto na "gaveta" da sessão
                st.session_state.texto_bruto = texto_completo
                st.success("Documentos prontos!")
        else:
            st.warning("Selecione ao menos um arquivo.")

# Inicialização de estados
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- ÁREA DA FICHA TÉCNICA ---
# --- ÁREA DA FICHA TÉCNICA (MELHORADA) ---
if st.button("🔍 Gerar Ficha Técnica do Documento"):
    if "texto_bruto" in st.session_state and st.session_state.texto_bruto:
        with st.spinner("Analisando estrutura do documento..."):
            ficha = extrair_dados_idp(st.session_state.texto_bruto)
            
            if ficha:
                st.success("Extração Concluída com Sucesso!")
                
                # Criamos Abas para organizar a visualização
                tab_visual, tab_json = st.tabs(["📊 Visão Estruturada", "💻 JSON Bruto"])
                
                with tab_visual:
                    # Usamos um container com borda para dar destaque
                    with st.container(border=True):
                        st.markdown(f"### {ficha.tipo.value.upper()}")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric(label="Entidade Principal", value=ficha.entidade_principal)
                            st.write(f"📅 **Data:** {ficha.data_documento if ficha.data_documento else 'Não identificada'}")
                        
                        with col2:
                            # Barra de progresso para a confiança
                            st.write(f"🎯 **Confiança da IA:** {ficha.analise_confianca * 100:.0f}%")
                            st.progress(ficha.analise_confianca)
                            st.write(f"💰 **Valor/Objetivo:** {ficha.valor_ou_objetivo}")

                        st.divider()
                        # resumo do Pydantic no engine.py:
                        if hasattr(ficha, 'resumo_critico'):
                            st.markdown(f"**Análise Executiva:**\n\n_{ficha.resumo_critico}_")

                with tab_json:
                    st.markdown("#### Saída Pydantic (Backend)")
                    st.info("Este é o objeto JSON que pode ser enviado diretamente para um Banco de Dados ou API.")
                    # Mostra o JSON formatado
                    st.json(ficha.model_dump()) 

    else:
        st.error("Primeiro, faça o upload e processe um documento!")

# --- ÁREA DO CHAT ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("O que deseja saber sobre o documento?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response = ask_question(prompt, chat_history=st.session_state.chat_history)
        st.markdown(response)

    st.session_state.chat_history.append(("human", prompt))
    st.session_state.chat_history.append(("ai", response))    
    st.session_state.messages.append({"role": "assistant", "content": response})