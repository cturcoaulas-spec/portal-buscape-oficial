import streamlit as st
import pandas as pd
import requests
import re
from urllib.parse import quote

# CONFIGURAÇÃO DE INTERFACE
st.set_page_config(page_title="Portal Família Buscapé", page_icon="🌳", layout="wide")

# --- CONEXÃO ---
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzWJ_nDGDe4a81O5BDx3meMbVJjlcMpJoxoO05lilysWJaj_udqeXqvfYFgzvWPlC-Omw/exec"
CSV_URL = "https://docs.google.com/spreadsheets/d/1jrtIP1lN644dPqY0HPGGwPWQGyYwb8nWsUigVK3QZio/export?format=csv"

# --- FUNÇÕES DE UTILIDADE ---
def aplicar_mascara_tel(v):
    n = re.sub(r'\D', '', str(v))
    return f"({n[:2]}) {n[2:7]}-{n[7:]}" if len(n) == 11 else v

def aplicar_mascara_data(v):
    n = re.sub(r'\D', '', str(v))
    return f"{n[:2]}/{n[2:4]}/{n[4:]}" if len(n) == 8 else v

# --- LOGIN ---
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
    # CARREGAR DADOS
    @st.cache_data(ttl=10)
    def carregar():
        try:
            df = pd.read_csv(CSV_URL, dtype=str).fillna("")
            df.columns = [c.strip().lower() for c in df.columns]
            return df
        except: return pd.DataFrame()

    df = carregar()
    lista_nomes = sorted(df['nome'].tolist()) if not df.empty else []

    st.title("🌳 Portal Família Buscapé")
    t1, t2, t3 = st.tabs(["🔍 Ver Família", "➕ Cadastrar", "✏️ Editar"])

    # --- ABA 1: VISUALIZAÇÃO COM MAPS ---
    with t1:
        st.subheader("Membros Cadastrados")
        if not df.empty:
            for i, r in df.iterrows():
                label = f"👤 {r.get('nome','-')} | 📅 {r.get('nascimento','-')} | 📞 {r.get('telefone','-')}"
                with st.expander(label):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.write(f"**Ascendente:** {r.get('ascendente','-')}")
                        st.write(f"**E-mail:** {r.get('email','-')}")
                    
                    with c2:
                        rua, num, bairro = r.get('rua',''), r.get('num',''), r.get('bairro','')
                        if rua and num:
                            st.write(f"🏠 **Endereço:** {rua}, {num} - {bairro}")
                            # Link oficial do Google Maps
                            endereco_full = f"{rua}, {num}, {bairro}, Brazil"
                            link_maps = f"https://www.google.com/maps/search/?api=1&query={quote(endereco_full)}"
                            st.link_button("📍 Abrir no Google Maps", link_maps)
                        else:
                            st.write("🏠 Endereço incompleto.")
        else: st.info("Nenhum dado encontrado.")

    # --- ABA 2: CADASTRO ---
    with t2:
        st.subheader("Novo Integrante")
        with st.form("form_novo", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                f_nome = st.text_input("Nome Completo")
                f_nasc = st.text_input("Nascimento (DDMMAAAA)")
                f_asc  = st.selectbox("Ascendente", ["Raiz"] + lista_nomes)
                f_tel  = st.text_input("Telefone")
            with col2:
                f_mail = st.text_input("E-mail")
                f_rua  = st.text_input("Rua")
                f_num  = st.text_input("Nº")
                f_bair = st.text_input("Bairro")
                f_cep  = st.text_input("CEP")
            
            if st.form_submit_button("SALVAR NA NUVEM"):
                if f_nome:
                    dados = [f_nome, aplicar_mascara_data(f_nasc), f_asc, aplicar_mascara_tel(f_tel), f_mail, f_rua, f_num, "", f_bair, f_cep]
                    requests.post(WEBAPP_URL, json={"action": "append", "data": dados})
                    st.success("✅ Salvo com sucesso!")
                    st.rerun()

    # --- ABA 3: EDIÇÃO ---
    with t3:
        st.subheader("Atualizar Dados")
        if lista_nomes:
            sel = st.selectbox("Escolha para editar", lista_nomes)
            p = df[df['nome'] == sel].iloc[0]
            idx = df.index[df['nome'] == sel].tolist()[0] + 2
            with st.form("form_edit"):
                c1, c2 = st.columns(2)
                with c1:
                    e_dt = st.text_input("Nascimento", value=p.get('nascimento',''))
                    e_tel = st.text_input("Telefone", value=p.get('telefone',''))
                    e_mail = st.text_input("E-mail", value=p.get('email',''))
                with c2:
                    e_ru = st.text_input("Rua", value=p.get('rua',''))
                    e_nu = st.text_input("Nº", value=p.get('num',''))
                    e_ba = st.text_input("Bairro", value=p.get('bairro',''))
                    e_ce = st.text_input("CEP", value=p.get('cep',''))
                if st.form_submit_button("ATUALIZAR"):
                    up = [sel, e_dt, p.get('ascendente',''), e_tel, e_mail, e_ru, e_nu, "", e_ba, e_ce]
                    requests.post(WEBAPP_URL, json={"action": "edit", "row": idx, "data": up})
                    st.success("✅ Atualizado!")
                    st.rerun()

    st.sidebar.button("Sair", on_click=lambda: st.session_state.update({"logado": False}))
