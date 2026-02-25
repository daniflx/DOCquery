import streamlit as st
from app.engine import process_pdf, ask_question, extrair_dados_idp
import os
from PyPDF2 import PdfReader
from app.database import delete_all, init_db, salvar_documento, listar_documentos, ja_existe
import pandas as pd
import json

# Configuração da Página
st.set_page_config(page_title="DocQuery AI", page_icon="📄", layout="centered")

st.title("📄 DocQuery AI")
st.markdown("### Analise seus documentos com Inteligência Artificial")

# Inicializa o banco de dados
init_db()

# Inicialização de estados da sessão
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Sidebar para Upload e Configurações
with st.sidebar:
    st.header("Configurações")
    uploaded_files = st.file_uploader("Escolha os PDFs", type="pdf", accept_multiple_files=True)
    
    if st.button("Processar Documentos"):
        if uploaded_files:
            with st.spinner("Analisando documentos e economizando tokens..."):
                # Limpa o histórico do chat para novos processamentos
                st.session_state.chat_history = [] 
                st.session_state.messages = []
                
                for uploaded_file in uploaded_files:
                    nome_arq = uploaded_file.name
                    path = os.path.join("uploads", nome_arq)
                    
                    # Salva o arquivo fisicamente
                    with open(path, "wb") as f:
                        f.write(uploaded_file.read())
                    
                    # 1. Processamento para o RAG (Chat/FAISS) - Sempre ocorre
                    process_pdf(path)

                    # 2. Extração Inteligente (IDP) - Só gasta tokens se o arquivo for novo
                    if not ja_existe(nome_arq):
                        st.write(f"🔍 Extraindo dados: {nome_arq}")
                        
                        reader = PdfReader(path)
                        # Otimização: Pegamos apenas as primeiras 4 páginas para a ficha técnica
                        texto_ia = ""
                        for page in reader.pages[:4]:
                            texto_ia += page.extract_text() + "\n"
                        
                        ficha = extrair_dados_idp(texto_ia)
                        
                        if ficha:
                            # Salva no SQLite para persistência e economia futura
                            salvar_documento(nome_arq, ficha)
                    else:
                        st.write(f"✅ {nome_arq} já possui ficha técnica. Pulando extração...")
                
                st.success("Processamento concluído!")
                st.rerun() 
        else:
            st.warning("Selecione ao menos um arquivo.")

# --- HISTÓRICO E EXPORTAÇÃO ---
st.header("📚 Gerenciador de Documentos")
historico = listar_documentos()

if historico:
    # 1. Organizamos os dados expandindo o JSON para colunas reais
    lista_para_df = []
    for nome, dados_json, data in historico:
        info = json.loads(dados_json)
        # Criamos um dicionário plano (flat) para o Pandas entender
        linha = {
            "Arquivo": nome,
            "Tipo": info.get("tipo", "N/A"),
            "Entidade Principal": info.get("entidade_principal", "N/A"),
            "Valor/Objetivo": info.get("valor_ou_objetivo", "N/A"),
            "Confiança IA": f"{info.get('analise_confianca', 0)*100:.1f}%",
            "Resumo Executivo": info.get("resumo_critico", "N/A"),
            "Processado em": data
        }
        lista_para_df.append(linha)

    df_apresentavel = pd.DataFrame(lista_para_df)

    # 2. Exibimos a tabela na tela (versão resumida para não poluir)
    st.dataframe(df_apresentavel[["Arquivo", "Tipo", "Entidade Principal", "Processado em"]], 
                 use_container_width=True, hide_index=True)

    # 3. Botão de Download Organizado
    # Usamos sep=';' para que o Excel brasileiro abra direto sem desconfigurar
    csv = df_apresentavel.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
    
    st.download_button(
        label="📥 Baixar Base de Dados Completa (CSV/Excel)",
        data=csv,
        file_name='extracao_documentos_ia.csv',
        mime='text/csv',
    )
    
    # VISUALIZAÇÃO DETALHADA: Permite clicar/selecionar cada PDF individualmente
    st.markdown("### 🔍 Detalhes da Ficha Técnica")
    lista_nomes = [row[0] for row in historico]
    selecionado = st.selectbox("Selecione um documento para visualizar os dados extraídos:", ["-- Selecione um arquivo --"] + lista_nomes)

    if selecionado != "-- Selecione um arquivo --":
        # Localiza os dados do arquivo selecionado no histórico
        registro = next(h for h in historico if h[0] == selecionado)
        ficha_data = json.loads(registro[1])

        tab_visual, tab_json = st.tabs(["📊 Visão Estruturada", "💻 JSON Bruto"])
        
        with tab_visual:
            with st.container(border=True):
                st.markdown(f"### {ficha_data.get('tipo', 'DOCUMENTO').upper()}")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(label="Entidade Principal", value=ficha_data.get("entidade_principal", "N/A"))
                    st.write(f"📅 **Data do Doc:** {ficha_data.get('data_documento', 'Não identificada')}")
                
                with col2:
                    confianca = ficha_data.get("analise_confianca", 0.0)
                    st.write(f"🎯 **Confiança da IA:** {confianca * 100:.0f}%")
                    st.progress(confianca)
                    st.write(f"💰 **Valor/Objetivo:** {ficha_data.get('valor_ou_objetivo', 'N/A')}")

                st.divider()
                if "resumo_critico" in ficha_data:
                    st.markdown(f"**Análise Executiva:**\n\n_{ficha_data['resumo_critico']}_")

        with tab_json:
            st.info("Objeto estruturado recuperado do banco de dados SQLite.")
            st.json(ficha_data)

    if st.button("🗑️ Limpar Histórico Completo"):
        delete_all()
        st.rerun()
else:
    st.info("Ainda não existem documentos guardados no histórico.")

st.divider()

# --- ÁREA DO CHAT ---
st.header("💬 Converse com seus Documentos")
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