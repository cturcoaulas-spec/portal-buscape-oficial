import streamlit as st
import pandas as pd
import requests
import re
import unicodedata
from urllib.parse import quote
from datetime import datetime
from fpdf import FPDF

# 1. CONFIGURAÇÃO E LIMPEZA TOTAL DA INTERFACE
st.set_page_config(page_title="Família Buscapé", page_icon="🌳", layout="wide")

st.markdown("""
    <style>
    /* Nuke total no Header, Footer e Decorações do Streamlit */
    [data-testid="stHeader"] {display: none !important;}
    footer {display: none !important;}
    .stDeployButton {display:none !important;}
    [data-testid="stStatusWidget"] {display:none !important;}
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Ajuste de espaçamento para mobile */
    .main .block-container {padding-top: 2rem !important; padding-bottom: 2rem !important;}
    [data-testid="stSidebarNav"] {margin-top: -20px;}
    
    /* Estilo das Abas e Botões */
    [data-baseweb="tab-list"] { gap: 8px; overflow-x: auto; }
    [data-baseweb="tab"] { padding: 10px; border-radius: 12px; background: #fdf2f2; min-width: 110px; font-weight: bold; }
    button { height: 3.5em !important; font-weight: bold !important; border-radius: 15px !important; width: 100% !important; background-color: #f8d7da !important; color: #721c24 !important; }
    .stExpander { border-radius: 15px !important; border: 1px solid #f5c6cb !important; background-color: #fff; }
    </style>
    """, unsafe_allow_html=True)

WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzWJ_nDGDe4a81O5BDx3meMbVJjlcMpJoxoO05lilysWJaj_udqeXqvfYFgzvWPlC-Omw/exec"
CSV_URL = "https://docs.google.com/spreadsheets/d/1jrtIP1lN644dPqY0HPGGwPWQGyYwb8nWsUigVK3QZio/export?format=csv"
MESES_BR = ["", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

def limpar(v): return re.sub(r'\D', '', str(v))
def mask_tel(v):
    n = limpar(str(v))[:11]
    if len(n) == 11: return f"({n[:2]}) {n[2:7]}-{n[7:11]}"
    if len(n) == 10: return f"({n[:2]}) {n[2:6]}-{n[6:10]}"
    return n if n else "-"

if 'logado' not in st.session_state: st.session_state.logado = False
if not st.session_state.logado:
    st.title("🌳 Família Buscapé")
    psw = st.text_input("Senha da Família", type="password")
    if st.button("ENTRAR"):
        if psw == "buscape2026": st.session_state.logado = True; st.rerun()
        else: st.error("Senha incorreta!")
else:
    @st.cache_data(ttl=2)
    def carregar():
        try:
            df = pd.read_csv(CSV_URL, dtype=str).fillna("")
            def norm(t):
                t = t.strip().lower()
                return "".join(ch for ch in unicodedata.normalize('NFKD', t) if not unicodedata.combining(ch))
            df.columns = [norm(c) for c in df.columns]
            mapa = {'nome':'nome','nascimento':'nascimento','vinculo':'vinculo','ascendente':'vinculo','telefone':'telefone','email':'email','rua':'rua','num':'num','numero':'num','conjuge':'conjuge','conjugue':'conjuge','bairro':'bairro','cep':'cep'}
            return df.rename(columns=mapa)
        except: return pd.DataFrame()

    df_todo = carregar(); df_m = df_todo[df_todo['nome'].str.strip() != ""].sort_values(by='nome').copy()
    nomes_lista = sorted([n.strip() for n in df_m['nome'].unique().tolist() if n.strip()])

    with st.sidebar:
        st.title("🎂 Aniversários")
        hoje_dm = datetime.now().strftime("%d/%m")
        niver = [r['nome'] for _, r in df_m.iterrows() if str(r.get('nascimento','')).startswith(hoje_dm)]
        if niver:
            for n in niver: st.success(f"🎈 Hoje: {n}")
        else: st.info("Sem notificações hoje.")
        st.divider()
        if st.button("📜 Guia de Uso (PDF)"):
            pdf = FPDF(); pdf.add_page(); pdf.set_font("Arial", "B", 16)
            pdf.cell(200, 10, "Manual Familia Buscape", ln=True, align="C"); pdf.ln(10)
            pdf.set_font("Arial", "B", 12); pdf.cell(0, 10, "1. Responsabilidade Coletiva", ln=True)
            pdf.set_font("Arial", "", 11); pdf.multi_
