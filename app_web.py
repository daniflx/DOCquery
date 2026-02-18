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
    
    #ESTÁ SALVANDO HISTÓRICO DE APENAS DE UM DOCUMENTO, LIMPA O HISTÓRICO QUANDO SOBE NOVOS ARQUIVOS!!
    if st.button("Processar Documentos"):
        if uploaded_files:
            with st.spinner("Lendo e indexando arquivos..."):
                for uploaded_file in uploaded_files:
                   # Salva temporariamente para processar
                   # LIMPA O HISTÓRICO QUANDO SOBE NOVOS ARQUIVOS
                    st.session_state.chat_history = [] 
                    st.session_state.messages = []

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

# 1. Inicializa o histórico no estado da sessão se não existir
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [] # Lista vazia para começar

# Campo de entrada de pergunta
if prompt := st.chat_input("O que deseja saber sobre o documento?"):
    # Exibe a pergunta do usuário
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # GERA A RESPOSTA PASSANDO O HISTÓRICO
    with st.chat_message("assistant"):
        # Chamamos a função passando o histórico que guardamos
        response = ask_question(prompt, chat_history=st.session_state.chat_history)
        st.markdown(response)

    # 2. ATUALIZA O HISTÓRICO PARA A PRÓXIMA PERGUNTA
    # O LangChain espera objetos de mensagem ou tuplas ("human", "texto")
    st.session_state.chat_history.append(("human", prompt))
    st.session_state.chat_history.append(("ai", response))    
    st.session_state.messages.append({"role": "assistant", "content": response})