import streamlit as st
import pandas as pd
import requests
import re
import unicodedata
import time
from urllib.parse import quote
from datetime import datetime
from fpdf import FPDF

# 1. CONFIGURAÇÃO (OBRIGATORIAMENTE O PRIMEIRO COMANDO)
st.set_page_config(page_title="Família Buscapé", page_icon="🌳", layout="wide")

# 2. BLOCO DE SEGURANÇA E ESTILO (TRAVAS DE VISUALIZAÇÃO)
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    [data-testid="stToolbar"] {visibility: hidden !important;}
    
    /* Ajuste para mobile */
    .stApp { margin-top: -50px; }
    [data-baseweb="tab-list"] { gap: 8px; overflow-x: auto; }
    [data-baseweb="tab"] { padding: 10px; border-radius: 10px; background: #f0f2f6; min-width: 110px; }
    button { height: 3.5em !important; font-weight: bold !important; border-radius: 12px !important; width: 100% !important; }
    .stExpander { border-radius: 12px !important; border: 1px solid #ddd !important; }
    </style>
    """, unsafe_allow_html=True)

# LINKS DE INTEGRAÇÃO
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

def gerar_pdf_membros(dados):
    pdf = FPDF()
    pdf.add_page(); pdf.set_font("Arial", "B", 14)
    pdf.cell(200, 10, "Relatorio Familia Buscape", ln=True, align="C"); pdf.ln(5)
    for _, r in dados.iterrows():
        pdf.set_font("Arial", "B", 11); pdf.cell(0, 8, f"Nome: {r.get('nome','-')}", ln=True)
        pdf.set_font("Arial", size=10); pdf.cell(0, 6, f"Nasc: {r.get('nascimento','-')} | Tel: {mask_tel(r.get('telefone','-'))}", ln=True)
        pdf.cell(0, 6, f"End: {r.get('rua','-')}, {r.get('num','-')} - {r.get('bairro','-')}", ln=True)
        pdf.ln(2); pdf.line(10, pdf.get_y(), 200, pdf.get_y()); pdf.ln(4)
    return pdf.output(dest='S').encode('latin-1')

@st.cache_data(ttl=2)
def carregar_dados():
    try:
        df = pd.read_csv(CSV_URL, dtype=str).fillna("")
        cols_originais = df.columns
        mapa_novo = {}
        for c in cols_originais:
            c_norm = normalizar(c)
            if 'nome' in c_norm: mapa_novo[c] = 'nome'
            elif 'nasc' in c_norm: mapa_novo[c] = 'nascimento'
            elif 'vinc' in c_norm: mapa_novo[c] = 'vinculo'
            elif 'tel' in c_norm: mapa_novo[c] = 'telefone'
            elif 'rua' in c_norm: mapa_novo[c] = 'rua'
            elif 'num' in c_norm: mapa_novo[c] = 'num'
            elif 'bair' in c_norm: mapa_novo[c] = 'bairro'
        df = df.rename(columns=mapa_novo)
        if 'nome' in df.columns:
            df['nome'] = df['nome'].str.strip()
            return df
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
    if df_todo.empty:
        st.error("⚠️ Erro ao carregar dados da planilha.")
    else:
        df_m = df_todo[df_todo['nome'] != ""].sort_values(by='nome').copy()
        nomes_lista = sorted(df_m['nome'].unique().tolist())

        with st.sidebar:
            st.title("⚙️ Painel")
            if st.button("🔄 Sincronizar"): st.cache_data.clear(); st.rerun()
            st.divider()
            st.button("🚪 Sair", on_click=lambda: st.session_state.update({"logado": False}))

        st.title("🌳 Família Buscapé")
        tabs = st.tabs(["🔍 Membros", "🎂 Niver", "📢 Mural", "➕ Novo", "✏️ Gerenciar", "🌳 Árvore", "📖 Manual"])

        with tabs[0]: # 1. Membros
            sel_ids = []; c_topo = st.container()
            for i, r in df_m.iterrows():
                col_sel, col_exp = st.columns([0.15, 3.85])
                if col_sel.checkbox("", key=f"sel_{i}"): sel_ids.append(i)
                with col_exp.expander(f"👤 {r['nome']} | 🎂 {r.get('nascimento','-')}"):
                    ci, cl = st.columns([3, 1])
                    with ci:
                        st.write(f"📞 Tel: {mask_tel(r.get('telefone','-'))}")
                        st.write(f"🏠 End: {r.get('rua','-')}, {r.get('num','-')} - {r.get('bairro','-')}")
                    with cl:
                        t = limpar(r.get('telefone',''))
                        if len(t) >= 10: st.link_button("💬 Zap", f"https://wa.me/55{t}")
                        end_rua = str(r.get('rua', '')).strip()
                        if end_rua and end_rua != "-":
                            st.link_button("📍 Mapa", f"https://www.google.com/maps/search/?api=1&query={quote(f'{end_rua},{r.get('num','')}')}")
            if sel_ids:
                c_topo.download_button("📥 PDF SELECIONADOS", gerar_pdf_membros(df_m.loc[sel_ids]), "familia.pdf")

        with tabs[2]: # 3. Mural
            try: avs = [df_todo.iloc[0].get('email','Vazio'), df_todo.iloc[0].get('rua','Vazio'), df_todo.iloc[0].get('num','Vazio')]
            except: avs = ["Vazio", "Vazio", "Vazio"]
            cols = st.columns(3)
            for idx in range(3): cols[idx].warning(f"**Aviso {idx+1}**\n\n{avs[idx]}")
            with st.form("m_f"):
                v1, v2, v3 = st.text_input("A1", avs[0]), st.text_input("A2", avs[1]), st.text_input("A3", avs[2])
                b_s, b_l = st.columns(2)
                if b_s.form_submit_button("💾 SALVAR"): 
                    requests.post(WEBAPP_URL, json={"action":"edit", "row":2, "data":["AVISO","","","",v1, v2, v3, "","",""]}); st.rerun()
                if b_l.form_submit_button("🗑️ LIMPAR"): 
                    requests.post(WEBAPP_URL, json={"action":"edit", "row":2, "data":["AVISO","","","","Vazio","Vazio","Vazio","","",""]}); st.rerun()

        with tabs[3]: # 4. Cadastrar
            with st.form("c_f", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1: nc = st.text_input("Nome *"); dc = st.text_input("Nasc *"); tc = st.text_input("Tel")
                with c2: vc = st.radio("Vínculo", ["Filho(a) de", "Cônjuge de"]); rc = st.selectbox("Ref", ["Raiz"] + nomes_lista)
                if st.form_submit_button("💾 CADASTRAR"):
                    requests.post(WEBAPP_URL, json={"action":"append", "data":[nc, dc, f"{vc} {rc}" if rc!="Raiz" else "Raiz", tc, "", "", "", "", "", ""]}); st.rerun()

        with tabs[4]: # 5. Gerenciar
            esc = st.selectbox("Editar", ["--"] + nomes_lista)
            if esc != "--":
                m = df_m[df_m['nome'] == esc].iloc[0]; idx = df_todo.index[df_todo['nome'] == esc].tolist()[0] + 2
                with st.form("g_f"):
                    ed = st.text_input("Nasc", value=m.get('nascimento','')); et = st.text_input("Tel", value=m.get('telefone',''))
                    b1, b2 = st.columns(2)
                    if b1.form_submit_button("💾 ATUALIZAR"):
                        requests.post(WEBAPP_URL, json={"action":"edit", "row":idx, "data":[esc, ed, m.get('vinculo',''), et, "", "", "", "", "", ""]}); st.rerun()
                    if b2.form_submit_button("🗑️ EXCLUIR"):
                        requests.post(WEBAPP_URL, json={"action":"edit", "row":idx, "data":[""]*10}); st.rerun()

        with tabs
