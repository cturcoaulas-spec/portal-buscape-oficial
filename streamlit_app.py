import streamlit as st
import pandas as pd
import requests
import re
import unicodedata
import time
from urllib.parse import quote
from datetime import datetime
from fpdf import FPDF

# 1. CONFIGURAÇÃO MOBILE E ESTILO
st.set_page_config(page_title="Família Buscapé", page_icon="🌳", layout="wide")

st.markdown("""
    <style>
    [data-baseweb="tab-list"] { gap: 8px; overflow-x: auto; }
    [data-baseweb="tab"] { padding: 10px; border-radius: 10px; background: #f0f2f6; min-width: 110px; }
    button { height: 3.5em !important; font-weight: bold !important; border-radius: 12px !important; width: 100% !important; }
    .stExpander { border-radius: 12px !important; border: 1px solid #ddd !important; }
    </style>
    """, unsafe_allow_html=True)

# VERIFIQUE SE ESSE LINK É O DA SUA ÚLTIMA IMPLANTAÇÃO (VERSÃO 2 OU SUPERIOR)
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzWJ_nDGDe4a81O5BDx3meMbVJjlcMpJoxoO05lilysWJaj_udqeXqvfYFgzvWPlC-Omw/exec"
CSV_URL = "https://docs.google.com/spreadsheets/d/1jrtIP1lN644dPqY0HPGGwPWQGyYwb8nWsUigVK3QZio/export?format=csv"
MESES_BR = ["", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

# --- FUNÇÕES DE SUPORTE ---
def normalizar(t):
    return "".join(ch for ch in unicodedata.normalize('NFKD', str(t).lower()) if not unicodedata.combining(ch)).strip()

def limpar(v): return re.sub(r'\D', '', str(v))

def mask_tel(v):
    n = limpar(str(v))[:11]
    if len(n) == 11: return f"({n[:2]}) {n[2:7]}-{n[7:11]}"
    if len(n) == 10: return f"({n[:2]}) {n[2:6]}-{n[6:10]}"
    return n if n else "-"

@st.cache_data(ttl=2)
def carregar_dados():
    try:
        df = pd.read_csv(CSV_URL, dtype=str).fillna("")
        cols_originais = df.columns
        mapa_novo = {}
        for c in cols_originais:
            cn = normalizar(c)
            if 'nome' in cn: mapa_novo[c] = 'nome'
            elif 'nasc' in cn: mapa_novo[c] = 'nascimento'
            elif 'vinc' in cn: mapa_novo[c] = 'vinculo'
            elif 'tel' in cn or 'zap' in cn: mapa_novo[c] = 'telefone'
            elif 'rua' in cn: mapa_novo[c] = 'rua'
            elif 'num' in cn: mapa_novo[c] = 'num'
        df = df.rename(columns=mapa_novo)
        if 'nome' in df.columns: df['nome'] = df['nome'].str.strip(); return df
        return pd.DataFrame()
    except: return pd.DataFrame()

# --- INTERFACE ---
if 'logado' not in st.session_state: st.session_state.logado = False
if not st.session_state.logado:
    st.title("🌳 Portal Família Buscapé")
    psw = st.text_input("Senha", type="password")
    if st.button("ENTRAR"):
        if psw == "buscape2026": st.session_state.logado = True; st.rerun()
        else: st.error("Senha incorreta!")
else:
    df_todo = carregar_dados()
    if df_todo.empty: st.error("⚠️ Planilha não carregada.")
    else:
        df_m = df_todo[df_todo['nome'] != ""].sort_values(by='nome').copy()
        nomes_lista = sorted(df_m['nome'].unique().tolist())
        with st.sidebar:
            st.title("⚙️ Painel")
            if st.button("🔄 Sincronizar"): st.cache_data.clear(); st.rerun()
            st.divider(); st.button("🚪 Sair", on_click=lambda: st.session_state.update({"logado": False}))

        st.title("🌳 Família Buscapé")
        tabs = st.tabs(["🔍 Membros", "🎂 Niver", "📢 Mural", "➕ Novo", "✏️ Gerenciar", "🌳 Árvore", "📖 Manual"])

        # ... (abas de Membros e Mural continuam iguais)

        with tabs[3]: # 4. Cadastrar (COM TESTE DE ENVIO)
            with st.form("c_f", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1: nc = st.text_input("Nome *"); dc = st.text_input("Nasc *"); tc = st.text_input("Tel")
                with c2: vc = st.radio("Vínculo", ["Filho(a) de", "Cônjuge de"]); rc = st.selectbox("Referência", ["Raiz"] + nomes_lista)
                if st.form_submit_button("💾 CADASTRAR"):
                    try:
                        res = requests.post(WEBAPP_URL, json={"action":"append", "data":[nc, dc, f"{vc} {rc}" if rc!="Raiz" else "Raiz", tc, "", "", "", "", "", ""]}, timeout=10)
                        if res.status_code == 200:
                            st.success(f"✅ Cadastrado na Planilha! Resposta: {res.text}")
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error(f"❌ Erro no Google Sheets: {res.status_code}. Verifique a Implantação.")
                    except Exception as e:
                        st.error(f"❌ Falha na conexão: {e}")

        # ... (resto das abas continua igual)
