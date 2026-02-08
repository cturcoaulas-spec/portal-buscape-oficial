import streamlit as st
import pandas as pd
import requests
import re
from urllib.parse import quote
from datetime import datetime
from fpdf import FPDF

# CONFIGURAÇÃO
st.set_page_config(page_title="Portal Família Buscapé", page_icon="🌳", layout="wide")

WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzWJ_nDGDe4a81O5BDx3meMbVJjlcMpJoxoO05lilysWJaj_udqeXqvfYFgzvWPlC-Omw/exec"
CSV_URL = "https://docs.google.com/spreadsheets/d/1jrtIP1lN644dPqY0HPGGwPWQGyYwb8nWsUigVK3QZio/export?format=csv"

# --- FUNÇÕES DE LIMPEZA ---
def faxina_tel(v):
    n = re.sub(r'\D', '', str(v))
    if len(n) >= 11:
        n = n[:11]
        return f"({n[:2]}) {n[2:7]}-{n[7:]}"
    elif len(n) == 10:
        return f"({n[:2]}) {n[2:6]}-{n[6:]}"
    return v

def faxina_data(v):
    n = re.sub(r'\D', '', str(v))
    if len(n) >= 8:
        n = n[:8]
        return f"{n[:2]}/{n[2:4]}/{n[4:]}"
    return v

def gerar_pdf(dados_selecionados):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, "Relatorio Familia Buscape", ln=True, align="C")
    pdf.ln(10)
    for _, r in dados_selecionados.iterrows():
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, f"Membro: {r.get('nome','-')}", ln=True)
        pdf.set_font("Arial", size=10)
        pdf.cell(0, 8, f"Nascimento: {r.get('nascimento','-')} | Conjuge: {r.get('conjuge','-')}", ln=True)
        pdf.cell(0, 8, f"Tel: {r.get('telefone','-')} | E-mail: {r.get('email','-')}", ln=True)
        end = f"{r.get('rua','-')}, {r.get('num','-')} - {r.get('bairro','-')}"
        pdf.cell(0, 8, f"End: {end}", ln=True)
        pdf.ln(5); pdf.line(10, pdf.get_y(), 200, pdf.get_y()); pdf.ln(5)
    return pdf.output(dest='S').encode('latin-1')

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
    t1, t2, t3, t4 = st.tabs(["🔍 Membros", "📅 Aniversários", "➕ Cadastrar", "✏️ Editar"])

    # --- TAB 1: MEMBROS ---
    with t1:
        st.subheader("Lista da Família")
        selecionados = []
        if not df.empty:
            for i, r in df.iterrows():
                col_sel, col_exp = st.columns([0.15, 3.85])
                with col_sel:
                    if st.checkbox("", key=f"pdf_{i}"): selecionados.append(r)
                with col_exp:
                    with st.expander(f"👤 {r.get('nome','-')} | 📅 {r.get('nascimento','-')}"):
                        c1, c2 = st.columns(2)
                        with c1:
                            st.write(f"💍 **Conjuge:** {r.get('conjuge','-')}")
                            st.write(f"📞 **Tel:** {r.get('telefone','-')}")
                        with c2:
                            st.write(f"🏠 **Endereço:** {r.get('rua','-')}, {r.get('num','-')}")
                            st.write(f"📍 **Bairro:** {r.get('bairro','-')}")
            
            if selecionados:
                pdf_bytes = gerar_pdf(pd.DataFrame(selecionados))
                st.sidebar.markdown("---")
                st.sidebar.download_button(f"📄 Baixar PDF ({len(selecionados)})", pdf_bytes, "familia_buscape.pdf", "application/pdf")

    # --- TAB 3: CADASTRO ---
    with t3:
        st.subheader("Novo Membro")
        with st.form("f_novo", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                f_n = st.text_input("Nome Completo")
                f_d = st.text_input("Nascimento (DDMMAAAA)")
                f_t = st.text_input("Telefone (Só números)")
                f_conj = st.text_input("Cônjuge / Parceiro(a)")
            with c2:
                f_a = st.selectbox("Ascendente", ["Raiz"] + lista_nomes)
                f_e = st.text_input("E-mail")
                f_r = st.text_input("Rua")
                f_b = st.text_input("Bairro")
            
            if st.form_submit_button("SALVAR"):
                if f_n:
                    dados = [f_n, faxina_data(f_d), f_a, faxina_tel(f_t), f_e, f_r, "", f_conj, f_b, ""]
                    requests.post(WEBAPP_URL, json={"action": "append", "data": dados})
                    st.success("✅ Cadastrado!"); st.rerun()

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
                    e_conj = st.text_input("Cônjuge", value=p.get('conjuge',''))
                with c2:
                    e_r = st.text_input("Rua", value=p.get('rua',''))
                    e_b = st.text_input("Bairro", value=p.get('bairro',''))
                    e_e = st.text_input("E-mail", value=p.get('email',''))
                
                if st.form_submit_button("ATUALIZAR"):
                    up = [sel, faxina_data(e_d), p.get('ascendente',''), faxina_tel(e_t), e_e, e_r, p.get('num',''), e_conj, e_b, p.get('cep','')]
                    requests.post(WEBAPP_URL, json={"action": "edit", "row": idx, "data": up}); st.rerun()
                if st.form_submit_button("EXCLUIR"):
                    requests.post(WEBAPP_URL, json={"action": "edit", "row": idx, "data": [""] * 10}); st.rerun()
