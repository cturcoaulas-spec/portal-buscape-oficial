import streamlit as st
import pandas as pd
import requests

# CONFIGURAÇÃO DE INTERFACE
st.set_page_config(page_title="Família Buscapé", page_icon="🌳", layout="centered")

# URL DO SEU APP SCRIPT (Mantenha a sua última versão aqui)
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzDd11VRMTQSvd3MDNZgok8qV4o_y4s0KhBaAJQFC0HZtg36mpydMTVmPQXg34lZp_RCQ/exec"
CSV_URL = "https://docs.google.com/spreadsheets/d/1jrtIP1lN644dPqY0HPGGwPWQGyYwb8nWsUigVK3QZio/export?format=csv"

# --- SEGURANÇA ---
if 'logado' not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.title("🌳 Portal Buscapé")
    senha = st.text_input("Senha de Acesso", type="password")
    if st.button("ACESSAR"):
        if senha == "buscape2026":
            st.session_state.logado = True
            st.rerun()
        else:
            st.error("Senha incorreta.")
else:
    def carregar_dados():
        try:
            df = pd.read_csv(CSV_URL, dtype=str).fillna("")
            # Padroniza os nomes das colunas para evitar o erro de KeyError
            df.columns = [c.strip().lower() for c in df.columns]
            return df
        except:
            return pd.DataFrame()

    df = carregar_dados()

    st.title("🌳 Portal Buscapé")
    aba1, aba2, aba3 = st.tabs(["🔍 Consultar", "➕ Cadastrar", "✏️ Editar"])

    with aba1:
        st.subheader("Lista da Família")
        st.dataframe(df, use_container_width=True)

    with aba2:
        st.subheader("Novo Cadastro")
        with st.form("form_novo"):
            nome = st.text_input("Nome Completo")
            nasc = st.text_input("Nascimento")
            tel = st.text_input("Telefone")
            # BOTÃO QUE ESTAVA FALTANDO:
            enviar_novo = st.form_submit_button("SALVAR NOVO")
            if enviar_novo:
                dados = [nome, nasc, "", tel, "", "", "", "", "", ""]
                requests.post(WEBAPP_URL, json={"action": "append", "data": dados})
                st.success("Adicionado!")
                st.rerun()

    with aba3:
        st.subheader("Editar Cadastro")
        if not df.empty:
            nome_sel = st.selectbox("Escolha quem editar", df['nome'].tolist())
            pessoa = df[df['nome'] == nome_sel].iloc[0]
            # Pegamos a linha (index + 2 para o Google Sheets)
            idx = df.index[df['nome'] == nome_sel].tolist()[0] + 2

            with st.form("form_editar"):
                # Usamos .get() ou o nome minúsculo para evitar o erro de KeyError
                edit_nasc = st.text_input("Nascimento", value=pessoa.get('nascimento', ''))
                edit_tel = st.text_input("Telefone", value=pessoa.get('telefone', ''))
                
                # BOTÃO QUE ESTAVA FALTANDO:
                enviar_edit = st.form_submit_button("ATUALIZAR DADOS")
                
                if enviar_edit:
                    dados_up = [nome_sel, edit_nasc, pessoa.get('ascendente',''), edit_tel, "", "", "", "", "", ""]
                    requests.post(WEBAPP_URL, json={"action": "edit", "row": idx, "data": dados_up})
                    st.success("Dados atualizados na nuvem!")
                    st.rerun()
