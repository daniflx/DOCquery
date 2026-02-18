import streamlit as st
from app.engine import process_pdf, ask_question
import os

# Configuração da Página
st.set_page_config(page_title="DocQuery AI", page_icon="📄", layout="centered")

st.title("📄 DocQuery AI")
st.markdown("### Analise seus documentos com Inteligência Artificial")
st.info("Faça o upload de currículos ou documentos e tire suas dúvidas.")

# Sidebar para Upload
with st.sidebar:
    st.header("Configurações")
    uploaded_files = st.file_uploader("Escolha os PDFs", type="pdf", accept_multiple_files=True)
    
    if st.button("Processar Documentos"):
        if uploaded_files:
            with st.spinner("Lendo e indexando arquivos..."):
                for uploaded_file in uploaded_files:
                   # Salva temporariamente para processar
                    path = os.path.join("uploads", uploaded_file.name)
                    with open(path, "wb") as f:
                        f.write(uploaded_file.read()) # <-- Mudamos de get_buffer() para read()
                    
                    process_pdf(path)
                    
                st.success("Documentos prontos!")
        else:
            st.warning("Selecione ao menos um arquivo.")

# Inicializa o histórico do chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Exibe as mensagens do chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Campo de entrada de pergunta
if prompt := st.chat_input("O que deseja saber sobre os documentos?"):
    # Adiciona pergunta do usuário ao histórico
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Gera a resposta da IA
    with st.chat_message("assistant"):
        with st.spinner("Consultando cérebro digital..."):
            response = ask_question(prompt)
            st.markdown(response)
    
    # Adiciona resposta da IA ao histórico
    st.session_state.messages.append({"role": "assistant", "content": response})