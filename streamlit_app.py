import streamlit as st
import pandas as pd
import requests
import re

# CONFIGURAÇÃO DE INTERFACE
st.set_page_config(page_title="Portal Família Buscapé", page_icon="🌳", layout="wide")

# --- CONEXÃO ---
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzDd11VRMTQSvd3MDNZgok8qV4o_y4s0KhBaAJQFC0HZtg36mpydMTVmPQXg34lZp_RCQ/exec"
CSV_URL = "https://docs.google.com/spreadsheets/d/1jrtIP1lN644dPqY0HPGGwPWQGyYwb8nWsUigVK3QZio/export?format=csv"

# Máscaras de Formatação
def masc_tel(v):
    n = re.sub(r'\D', '', str(v))
    if len(n) == 11: return f"({n[:2]}) {n[2:7]}-{n[7:]}"
    return v

def masc_data(v):
    n = re.sub(r'\D', '', str(v))
    if len(n) == 8: return f"{n[:2]}/{n[2:4]}/{n[4:]}"
    return v

# SISTEMA DE LOGIN
if 'logado' not in st.session_state: st.session_state.logado = False
if not st.session_state.logado:
    st.title("🌳 Portal Família Buscapé")
    senha = st.text_input("Senha", type="password")
    if st.button("ENTRAR"):
        if senha == "buscape2026":
            st.session_state.logado = True
            st.rerun()
        else: st.error("Senha incorreta.")
else:
    # CARREGAR DADOS DA PLANILHA
    def carregar():
        try:
            df = pd.read_csv(CSV_URL, dtype=str).fillna("")
            df.columns = [c.strip().lower() for c in df.columns]
            return df
        except: return pd.DataFrame()

    df = carregar()
    nomes_lista = sorted(df['nome'].tolist()) if not df.empty and 'nome' in df.columns else []

    st.title("🌳 Portal Família Buscapé")
    tab1, tab2, tab3 = st.tabs(["🔍 Ver Família", "➕ Cadastrar", "✏️ Editar"])

    # --- ABA 1: VISUALIZAÇÃO EXPANSÍVEL (LIMPA) ---
    with tab1:
        st.subheader("Membros Cadastrados")
        if not df.empty:
            for i, row in df.iterrows():
                titulo = f"👤 {row.get('nome','-')} | 📅 {row.get('nascimento','-')} | 📞 {row.get('telefone','-')}"
                with st.expander(titulo):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.write(f"**Ascendente:** {row.get('ascendente','')}")
                        st.write(f"**E-mail:** {row.get('email','')}")
                    with c2:
                        st.write(f"**Endereço:** {row.get('rua','')}, {row.get('num','')} {row.get('comp','')}")
                        st.write(f"**Bairro:** {row.get('bairro','')} | **CEP:** {row.get('cep','')}")
        else: st.info("Nenhum dado encontrado na planilha.")

    # --- ABA 2: CADASTRO ---
    with tab2:
        st.subheader("Novo Integrante")
        with st.form("form_novo", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                f_nome = st.text_input("Nome Completo")
                f_nasc = st.text_input("Nascimento (DDMMAAAA)")
                f_asc  = st.selectbox("Ascendente", ["Raiz"] + nomes_lista)
                f_tel  = st.text_input("Telefone")
                f_mail = st.text_input("E-mail")
            with col2:
                f_rua  = st.text_input("Rua")
                f_num  = st.text_input("Número")
                f_comp = st.text_input("Complemento")
                f_bair = st.text_input("Bairro")
                f_cep  = st.text_input("CEP")
            
            if st.form_submit_button("SALVAR NA NUVEM"):
                if f_nome:
                    lista_dados = [f_nome, masc_data(f_nasc), f_asc, masc_tel(f_tel), f_mail, f_rua, f_num, f_comp, f_bair, f_cep]
                    try:
                        requests.post(WEBAPP_URL, json={"action": "append", "data": lista_dados})
                        st.success("✅ Enviado com sucesso!")
                        st.rerun()
                    except: st.error("Erro na conexão com o banco de dados.")

    # --- ABA 3: EDIÇÃO ---
    with tab3:
        st.subheader("Atualizar Dados")
        if nomes_lista:
            sel = st.selectbox("Escolha quem editar", nomes_lista)
            p = df[df['nome'] == sel].iloc[0]
            idx_linha = df.index[df['nome'] == sel].tolist()[0] + 2
            
            with st.form("form_edit"):
                e_nasc = st.text_input("Nascimento", value=p.get('nascimento',''))
                e_tel  = st.text_input("Telefone", value=p.get('telefone',''))
                e_mail = st.text_input("E-mail", value=p.get('email',''))
                e_bair = st.text_input("Bairro", value=p.get('bairro',''))
                
                if st.form_submit_button("ATUALIZAR"):
                    dados_up = [sel, masc_data(e_nasc), p.get('ascendente',''), masc_tel(e_tel), e_mail, 
                                p.get('rua',''), p.get('num',''), p.get('comp',''), e_bair, p.get('cep','')]
                    requests.post(WEBAPP_URL, json={"action": "edit", "row": idx_linha, "data": dados_up})
                    st.success("✅ Atualizado!")
                    st.rerun()

    st.sidebar.button("Sair", on_click=lambda: st.session_state.update({"logado": False}))
