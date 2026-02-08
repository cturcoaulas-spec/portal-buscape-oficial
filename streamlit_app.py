import streamlit as st
import pandas as pd
import requests
import re

# CONFIGURAÇÃO DE INTERFACE
st.set_page_config(page_title="Portal Família Buscapé", page_icon="🌳", layout="centered")

# --- CONEXÃO (COLOQUE SEU LINK /EXEC AQUI) ---
WEBAPP_URL = "COLE_AQUI_SEU_LINK_DO_GOOGLE_SCRIPT"
CSV_URL = "https://docs.google.com/spreadsheets/d/1jrtIP1lN644dPqY0HPGGwPWQGyYwb8nWsUigVK3QZio/export?format=csv"

# Funções de Máscara
def masc_tel(v):
    n = re.sub(r'\D', '', str(v))
    if len(n) == 11: return f"({n[:2]}) {n[2:7]}-{n[7:]}"
    return v

def masc_data(v):
    n = re.sub(r'\D', '', str(v))
    if len(n) == 8: return f"{n[:2]}/{n[2:4]}/{n[4:]}"
    return v

# --- LOGIN ---
if 'logado' not in st.session_state: st.session_state.logado = False
if not st.session_state.logado:
    st.title("🌳 Portal Buscapé")
    senha = st.text_input("Senha", type="password")
    if st.button("ENTRAR"):
        if senha == "buscape2026":
            st.session_state.logado = True
            st.rerun()
        else: st.error("Senha incorreta.")
else:
    # --- APP PRINCIPAL ---
    def carregar():
        try:
            # Lendo a planilha em tempo real
            df = pd.read_csv(CSV_URL, dtype=str).fillna("")
            # Padroniza nomes das colunas para minúsculo
            df.columns = [c.strip().lower() for c in df.columns]
            return df
        except: return pd.DataFrame()

    df = carregar()
    nomes = sorted(df['nome'].tolist()) if not df.empty else []

    st.title("🌳 Portal Família Buscapé")
    tab1, tab2, tab3 = st.tabs(["🔍 Ver Família", "➕ Cadastrar", "✏️ Editar"])

    with tab1:
        st.subheader("Membros Cadastrados")
        st.dataframe(df, use_container_width=True, hide_index=True)

    with tab2:
        st.subheader("Novo Cadastro")
        # FORMULÁRIO DE CADASTRO
        with st.form("form_novo", clear_on_submit=True):
            f_nome = st.text_input("Nome Completo")
            f_nasc = st.text_input("Nascimento (DDMMAAAA)")
            f_asc  = st.selectbox("Ascendente", ["Raiz"] + nomes)
            f_tel  = st.text_input("Telefone")
            f_mail = st.text_input("E-mail")
            
            # O BOTÃO DEVE ESTAR AQUI DENTRO:
            bt_cad = st.form_submit_button("SALVAR NA NUVEM")
            
            if bt_cad:
                if f_nome:
                    # Organiza os dados para as colunas da sua planilha
                    dados = [f_nome, masc_data(f_nasc), f_asc, masc_tel(f_tel), f_mail, "", "", "", "", ""]
                    requests.post(WEBAPP_URL, json={"action": "append", "data": dados})
                    st.success("✅ Enviado para a Planilha!")
                    st.rerun()

    with tab3:
        st.subheader("Atualizar Cadastro")
        if nomes:
            sel = st.selectbox("Escolha quem editar", nomes)
            # Busca os dados da pessoa selecionada
            pessoa = df[df['nome'] == sel].iloc[0]
            idx = df.index[df['nome'] == sel].tolist()[0] + 2
            
            # FORMULÁRIO DE EDIÇÃO
            with st.form("form_edit"):
                e_nasc = st.text_input("Nascimento", value=pessoa.get('nascimento', ''))
                e_tel  = st.text_input("Telefone", value=pessoa.get('telefone', ''))
                e_mail = st.text_input("E-mail", value=pessoa.get('email', ''))
                
                # O BOTÃO DEVE ESTAR AQUI DENTRO:
                bt_up = st.form_submit_button("ATUALIZAR DADOS")
                
                if bt_up:
                    # Envia os dados atualizados
                    up = [sel, masc_data(e_nasc), pessoa.get('ascendente',''), masc_tel(e_tel), e_mail, "", "", "", "", ""]
                    requests.post(WEBAPP_URL, json={"action": "edit", "row": idx, "data": up})
                    st.success("✅ Atualizado com sucesso!")
                    st.rerun()

    st.sidebar.button("Sair", on_click=lambda: st.session_state.update({"logado": False}))
