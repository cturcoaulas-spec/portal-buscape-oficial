import streamlit as st
import pandas as pd
import requests
import re
from urllib.parse import quote
from datetime import datetime
from fpdf import FPDF

# CONFIGURAÇÃO
st.set_page_config(page_title="Família Buscapé", page_icon="🌳", layout="wide")

WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzWJ_nDGDe4a81O5BDx3meMbVJjlcMpJoxoO05lilysWJaj_udqeXqvfYFgzvWPlC-Omw/exec"
CSV_URL = "https://docs.google.com/spreadsheets/d/1jrtIP1lN644dPqY0HPGGwPWQGyYwb8nWsUigVK3QZio/export?format=csv"

# --- FUNÇÕES ---
def limpar(v): return re.sub(r'\D', '', str(v))
def mask_tel(v):
    n = limpar(v)
    if len(n) >= 11: return f"({n[:2]}) {n[2:7]}-{n[7:11]}"
    return v
def mask_data(v):
    n = limpar(v)
    if len(n) >= 8: return f"{n[:2]}/{n[2:4]}/{n[4:8]}"
    return v

def gerar_pdf(dados):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(200, 10, "Relatorio Familia Buscape", ln=True, align="C")
    for _, r in dados.iterrows():
        pdf.set_font("Arial", "B", 11)
        pdf.cell(0, 10, f"Membro: {r.get('nome','-')}", ln=True)
        pdf.set_font("Arial", size=10)
        pdf.cell(0, 7, f"Nasc: {r.get('nascimento','-')} | Tel: {r.get('telefone','-')}", ln=True)
        pdf.ln(5); pdf.line(10, pdf.get_y(), 200, pdf.get_y()); pdf.ln(5)
    return pdf.output(dest='S').encode('latin-1')

# --- ACESSO ---
if 'logado' not in st.session_state: st.session_state.logado = False
if not st.session_state.logado:
    st.title("🌳 Portal Família Buscapé")
    if st.text_input("Senha", type="password") == "buscape2026":
        if st.button("ENTRAR"): st.session_state.logado = True; st.rerun()
else:
    @st.cache_data(ttl=2)
    def carregar():
        try:
            df = pd.read_csv(CSV_URL, dtype=str).fillna("")
            df.columns = [c.strip().lower() for c in df.columns]
            return df
        except: return pd.DataFrame()

    df_bruto = carregar()
    df_m = df_bruto[df_bruto['nome'].str.strip() != ""]
    nomes = sorted(df_m['nome'].tolist())

    # --- SINO DE NOTIFICAÇÕES ---
    st.sidebar.title("🔔 Notificações")
    hoje = datetime.now().strftime("%d/%m")
    niver_hoje = [r['nome'] for _, r in df_m.iterrows() if r.get('nascimento','').startswith(hoje)]
    if niver_hoje:
        for n in niver_hoje: st.sidebar.success(f"🎂 Hoje: {n}")
    else: st.sidebar.info("Nenhum aniversário hoje.")

    st.title("🌳 Família Buscapé")
    t1, t2, t3, t4, t5 = st.tabs(["🔍 Membros", "🎂 Aniversários", "📢 Mural", "➕ Cadastrar", "✏️ Gerenciar"])

    # --- TAB 1: MEMBROS ---
    with t1:
        sel_idx = []
        c_top1, c_top2 = st.columns([3, 1])
        with c_top2:
            if st.button("📥 Modo Baixar (PDF)"): st.info("Selecione os membros abaixo.")
        
        for i, r in df_m.iterrows():
            c1, c2 = st.columns([0.2, 3.8])
            if c1.checkbox("", key=f"p_{i}"): sel_idx.append(i)
            with c2.expander(f"👤 {r.get('nome','-')}"):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.write(f"💍 Cônjuge: {r.get('conjuge','-')}")
                    st.write(f"📞 {r.get('telefone','-')}")
                with col_b:
                    tel_l = limpar(r.get('telefone',''))
                    if len(tel_l) >= 10: st.link_button("💬 WhatsApp", f"https://wa.me/55{tel_l}")

        if sel_idx:
            pdf_b = gerar_pdf(df_m.loc[sel_idx])
            st.sidebar.download_button("📥 BAIXAR PDF SELECIONADOS", pdf_b, "familia.pdf", "application/pdf")

    # --- TAB 3: MURAL DE AVISOS (3 AVISOS) ---
    with t3:
        st.subheader("📢 Mural de Avisos")
        # Lendo 3 campos de aviso (usando colunas email, rua e num da linha 2 como exemplo de estoque)
        av1 = df_bruto.iloc[0].get('email', 'Vazio')
        av2 = df_bruto.iloc[0].get('rua', 'Vazio')
        av3 = df_bruto.iloc[0].get('num', 'Vazio')
        
        col_av1, col_av2, col_av3 = st.columns(3)
        with col_av1: st.warning(f"**Aviso 1**\n\n{av1}")
        with col_av2: st.warning(f"**Aviso 2**\n\n{av2}")
        with col_av3: st.warning(f"**Aviso 3**\n\n{av3}")

        st.divider()
        st.subheader("📝 Editar Mural")
        v1 = st.text_input("Aviso 1", value=av1)
        v2 = st.text_input("Aviso 2", value=av2)
        v3 = st.text_input("Aviso 3", value=av3)
        
        if st.button("💾 Salvar Todos os Avisos"):
            # Salvando na linha 2 da planilha
            requests.post(WEBAPP_URL, json={"action": "edit", "row": 2, "data": ["AVISO","", "", "", v1, v2, v3, "", "", ""]})
            st.success("Mural atualizado!"); st.rerun()

    # --- TAB 5: GERENCIAR (LIMPO - SEM AVISOS AQUI) ---
    with t5:
        st.subheader("✏️ Edição de Membros")
        s = st.selectbox("Selecione para editar", ["--"] + nomes)
        if s != "--":
            m = df_m[df_m['nome'] == s].iloc[0]
            idx = df_m.index[df_m['nome'] == s].tolist()[0] + 2
            with st.form("f_edit"):
                ed = st.text_input("Nascimento", m.get('nascimento',''))
                et = st.text_input("Telefone", m.get('telefone',''))
                if st.form_submit_button("Atualizar"):
                    up = [s, mask_data(ed), m.get('ascendente',''), mask_tel(et), m.get('email',''), m.get('rua',''), m.get('num',''), m.get('conjuge',''), m.get('bairro',''), m.get('cep','')]
                    requests.post(WEBAPP_URL, json={"action": "edit", "row": idx, "data": up}); st.rerun()

    st.sidebar.button("🚪 Sair", on_click=lambda: st.session_state.update({"logado": False}))
