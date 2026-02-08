import streamlit as st
import pandas as pd
import requests
import re
import time
import unicodedata
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

WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzWJ_nDGDe4a81O5BDx3meMbVJjlcMpJoxoO05lilysWJaj_udqeXqvfYFgzvWPlC-Omw/exec"
CSV_URL = "https://docs.google.com/spreadsheets/d/1jrtIP1lN644dPqY0HPGGwPWQGyYwb8nWsUigVK3QZio/export?format=csv"
MESES_BR = ["", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

# --- FUNÇÕES DE SUPORTE ---
def limpar(v): return re.sub(r'\D', '', str(v))

def mask_tel(v):
    n = limpar(str(v))[:11]
    if len(n) == 11: return f"({n[:2]}) {n[2:7]}-{n[7:11]}"
    if len(n) == 10: return f"({n[:2]}) {n[2:6]}-{n[6:10]}"
    return n if n else "-"

def mask_data(v):
    n = limpar(str(v))
    if len(n) == 8: return f"{n[:2]}/{n[2:4]}/{n[4:8]}"
    return v

# --- LOGIN ---
if 'logado' not in st.session_state: st.session_state.logado = False
if not st.session_state.logado:
    st.title("🌳 Portal Família Buscapé")
    st.info("Senha de Acesso: buscape2026")
    psw = st.text_input("Digite a senha para entrar:", type="password")
    if st.button("ENTRAR NO PORTAL"):
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
        st.title("🔔 Notificações")
        hoje_dm = datetime.now().strftime("%d/%m")
        niver_hoje = [r['nome'] for _, r in df_m.iterrows() if str(r.get('nascimento','')).startswith(hoje_dm)]
        if niver_hoje:
            for n in niver_hoje: st.success(f"🎂 Hoje: {n}")
        else: st.info("Sem aniversários hoje")
        
        st.divider()
        if st.button("📄 Gerar Manual Completo (PDF)"):
            pdf_m = FPDF(); pdf_m.add_page()
            pdf_m.set_font("Arial", "B", 16)
            pdf_m.cell(200, 10, "Guia do Portal Familia Buscape", ln=True, align="C")
            pdf_m.ln(10)
            pdf_m.set_font("Arial", "B", 12); pdf_m.cell(0, 10, "Sejam Bem-Vindos!", ln=True)
            pdf_m.set_font("Arial", "", 11)
            pdf_m.multi_cell(0, 7, "Este portal foi criado pela Valeria para unir ainda mais a nossa familia. Aqui podemos compartilhar informacoes e manter nossa historia viva.")
            pdf_m.ln(5); pdf_m.set_font("Arial", "B", 12); pdf_m.cell(0, 10, "Responsabilidade e Dados", ln=True)
            pdf_m.set_font("Arial", "", 11)
            pdf_m.multi_cell(0, 7, "IMPORTANTE: Este sistema e compartilhado. O que voce edita ou apaga, muda para TODOS. Use com carinho. Mantenha seu Telefone e Endereco atualizados.")
            pdf_m.ln(5); pdf_m.set_font("Arial", "B", 12); pdf_m.cell(0, 10, "Funcionalidades", ln=True)
            pdf_m.set_font("Arial", "", 11)
            pdf_m.multi_cell(0, 7, "- Membros: Contatos, WhatsApp e Google Maps.\n- Niver: Aniversariantes do mes.\n- Mural: Avisos da familia.\n- Arvore: Fluxograma visual.")
            pdf_m.ln(5); pdf_m.set_font("Arial", "B", 12); pdf_m.cell(0, 10, "Instalar no Celular", ln=True)
            pdf_m.set_font("Arial", "", 11)
            pdf_m.multi_cell(0, 7, "Android: No Chrome, use 'Instalar aplicativo'.\niPhone: No Safari, use 'Adicionar a Tela de Inicio'.")
            pdf_m.ln(10); pdf_m.set_font("Arial", "B", 12); pdf_m.cell(0, 10, "SENHA: buscape2026", ln=True, align="C")
            manual_out = pdf_m.output(dest='S').encode('latin-1')
            st.download_button("📥 BAIXAR MANUAL", manual_out, "Manual_Buscape.pdf")
            
        st.divider(); st.button("🚪 Sair", on_click=lambda: st.session_state.update({"logado": False}))

    st.title("🌳 Família Buscapé")
    tabs = st.tabs(["🔍 Membros", "🎂 Niver", "📢 Mural", "➕ Novo", "✏️ Gerenciar", "🌳 Árvore"])

    with tabs[0]: # Membros
        for i, r in df_m.iterrows():
            nome_at = r.get('nome','').strip()
            with st.expander(f"👤 {nome_at} | 🎂 {r.get('nascimento','-')}"):
                ci, cl = st.columns([3, 1])
                with ci:
                    conj_b = str(r.get('conjuge','')).strip(); vinc_b = str(r.get('vinculo','')).strip(); parc = ""
                    if conj_b.lower() not in ["", "nan", "false", "0", "none", "sim"]: parc = conj_b
                    elif "Cônjuge de" in vinc_b: parc = vinc_b.replace("Cônjuge de", "").strip()
                    else:
                        recip = df_m[df_m['conjuge'].str.strip() == nome_at]['nome'].tolist()
                        if recip: parc = recip[0]
                    if parc and parc != nome_at: st.write(f"💍 **Cônjuge:** {parc}")
                    else: st.write("**Cônjuge:** Nenhum")
                    vinc_f = vinc_b
                    if vinc_b and vinc_b != "Raiz" and "Cônjuge" not in
