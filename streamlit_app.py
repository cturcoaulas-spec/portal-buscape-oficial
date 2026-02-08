import streamlit as st
import pandas as pd
import requests
import re
from urllib.parse import quote
from datetime import datetime

# CONFIGURAÇÃO
st.set_page_config(page_title="Portal Família Buscapé", page_icon="🌳", layout="wide")

WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzWJ_nDGDe4a81O5BDx3meMbVJjlcMpJoxoO05lilysWJaj_udqeXqvfYFgzvWPlC-Omw/exec"
CSV_URL = "https://docs.google.com/spreadsheets/d/1jrtIP1lN644dPqY0HPGGwPWQGyYwb8nWsUigVK3QZio/export?format=csv"

# --- FUNÇÕES DE FAXINA ---
def faxina_tel(v):
    # Deixa apenas números
    n = re.sub(r'\D', '', str(v))
    # Se for celular (11 dígitos)
    if len(n) >= 11:
        n = n[:11] # Corta se for maior
        return f"({n[:2]}) {n[2:7]}-{n[7:]}"
    # Se for fixo (10 dígitos)
    elif len(n) == 10:
        return f"({n[:2]}) {n[2:6]}-{n[6:]}"
    return v

def faxina_data(v):
    n = re.sub(r'\D', '', str(v))
    if len(n) >= 8:
        n = n[:8]
        return f"{n[:2]}/{n[2:4]}/{n[4:]}"
    return v

# --- LOGIN ---
if 'logado' not in st.session_state: st.session_state.logado = False
if not st.session_state.logado:
    st.title("🌳 Portal Família Buscapé")
    senha = st.text_input("Senha", type="password")
    if st.button("ENTRAR"):
        if senha == "buscape2026": st.session_state.logado = True; st.rerun()
        else: st.error("Senha incorreta.")
else:
    @st.cache_data(ttl=2)
    def carregar():
        try:
            df = pd.read_csv(CSV_URL, dtype=str).fillna("")
            df.columns = [c.strip().lower() for c in df.columns]
            return df[df['nome'].str.strip() != ""]
        except: return pd.DataFrame()

    df = carregar()
    lista_nomes = sorted(df['nome'].tolist()) if not df.empty else []

    st.title("🌳 Portal Família Buscapé")
    t1, t2, t3, t4 = st.tabs(["🔍 Membros", "🎂 Aniversários", "➕ Cadastrar", "✏️ Editar"])

    # --- TAB 1: MEMBROS ---
    with t1:
        st.subheader("Lista da Família")
        if not df.empty:
            for i, r in df.iterrows():
                with st.expander(f"👤 {r.get('nome','-')} | 📅 {r.get('nascimento','-')}"):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.write(f"📞 **Tel:** {r.get('telefone','-')}")
                        st.write(f"✉️ **E-mail:** {r.get('email','-')}")
                    with c2:
                        st.write(f"🏠 {r.get('rua','-')}, {r.get('num','-')} {r.get('complemento','')}")
                        st.write(f"📍 {r.get('bairro','-')} | {r.get('cep','-')}")
        else: st.info("Nada cadastrado.")

    # --- TAB 2: ANIVERSÁRIOS ---
    with t2:
        st.subheader("Aniversariantes")
        mes_h = datetime.now().strftime("%m")
        n_list = []
        if not df.empty:
            for _, r in df.iterrows():
                d = r.get('nascimento',''); p = re.sub(r'\D', '', d)
                m = d.split("/")[1] if "/" in d else (p[2:4] if len(p)>=4 else "")
                if m == mes_h: n_list.append({"dia": d.split("/")[0] if "/" in d else p[:2], "nome": r.get('nome','')})
            for n in sorted(n_list, key=lambda x: x['dia']):
                st.write(f"🎂 **Dia {n['dia']}** - {n['nome']}")

    # --- TAB 3: CADASTRO ---
    with t3:
        st.subheader("Novo Membro")
        with st.form("f_novo", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                f_n = st.text_input("Nome")
                f_d = st.text_input("Nascimento (DDMMAAAA)")
                f_a = st.selectbox("Ascendente", ["Raiz"] + lista_nomes)
                f_t = st.text_input("Telefone (Só números)")
            with col2:
                f_e = st.text_input("E-mail")
                f_r = st.text_input("Rua")
                f_u = st.text_input("Nº")
                f_c = st.text_input("Complemento")
                f_b = st.text_input("Bairro")
                f_ce = st.text_input("CEP")
            
            if st.form_submit_button("SALVAR"):
                if f_n:
                    dados = [f_n, faxina_data(f_d), f_a, faxina_tel(f_t), f_e, f_r, f_u, f_c, f_b, f_ce]
                    requests.post(WEBAPP_URL, json={"action": "append", "data": dados})
                    st.success("✅ Salvo e formatado!"); st.rerun()

    # --- TAB 4: EDITAR ---
    with t4:
        st.subheader("Gerenciar")
        op = ["-- Escolha --"] + lista_nomes
        sel = st.selectbox("Quem?", op)
        if sel != "-- Escolha --":
            p = df[df['nome'] == sel].iloc[0]
            idx = df.index[df['nome'] == sel].tolist()[0] + 2
            with st.form("f_edit"):
                c1, c2 = st.columns(2)
                with c1:
                    e_d = st.text_input("Nascimento", value=p.get('nascimento',''))
                    e_t = st.text_input("Telefone", value=p.get('telefone',''))
                with c2:
                    e_r = st.text_input("Rua", value=p.get('rua',''))
                    e_u = st.text_input("Nº", value=p.get('num',''))
                    e_c = st.text_input("Complemento", value=p.get('complemento',''))
                    e_b = st.text_input("Bairro", value=p.get('bairro',''))
                    e_ce = st.text_input("CEP", value=p.get('cep',''))
                
                if st.form_submit_button("ATUALIZAR"):
                    up = [sel, faxina_data(e_d), p.get('ascendente',''), faxina_tel(e_t), p.get('email',''), e_r, e_u, e_c, e_b, e_ce]
                    requests.post(WEBAPP_URL, json={"action": "edit", "row": idx, "data": up}); st.rerun()
                if st.form_submit_button("EXCLUIR"):
                    requests.post(WEBAPP_URL, json={"action": "edit", "row": idx, "data": [""] * 10}); st.rerun()

    st.sidebar.button("Sair", on_click=lambda: st.session_state.update({"logado": False}))
