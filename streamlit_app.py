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
        pdf.cell(0, 7, f"Tel: {r.get('telefone','-')} | Conjuge: {r.get('conjuge','-')}", ln=True)
        pdf.cell(0, 7, f"End: {r.get('rua','-')}, {r.get('num','-')} - {r.get('bairro','-')}", ln=True)
        pdf.ln(5); pdf.line(10, pdf.get_y(), 200, pdf.get_y()); pdf.ln(5)
    return pdf.output(dest='S').encode('latin-1')

# --- ACESSO ---
if 'logado' not in st.session_state: st.session_state.logado = False
if not st.session_state.logado:
    st.title("🌳 Portal Família Buscapé")
    psw = st.text_input("Senha", type="password")
    if st.button("ENTRAR"):
        if psw == "buscape2026": st.session_state.logado = True; st.rerun()
        else: st.error("Senha incorreta")
else:
    @st.cache_data(ttl=2)
    def carregar():
        try:
            df = pd.read_csv(CSV_URL, dtype=str).fillna("")
            df.columns = [c.strip().lower() for c in df.columns]
            return df
        except: return pd.DataFrame()

    df_todo = carregar()
    # GARANTE ORDEM ALFABÉTICA
    df_m = df_todo[df_todo['nome'].str.strip() != ""].sort_values(by='nome').copy()
    nomes_lista = df_m['nome'].tolist()

    st.title("🌳 Família Buscapé")
    tabs = st.tabs(["🔍 Membros", "🎂 Aniversários", "📢 Mural", "➕ Cadastrar", "✏️ Gerenciar"])

    # --- TAB 1: MEMBROS ---
    with tabs[0]:
        st.subheader("Lista de Membros (Ordem Alfabética)")
        sel_ids = []
        
        # Espaço para o botão de baixar no topo
        container_pdf = st.container()
        
        if not df_m.empty:
            for i, r in df_m.iterrows():
                col_check, col_exp = st.columns([0.2, 3.8])
                if col_check.checkbox("", key=f"check_{i}"): sel_ids.append(i)
                with col_exp.expander(f"👤 {r.get('nome','-')}"):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.write(f"💍 **Cônjuge:** {r.get('conjuge','-')}")
                        st.write(f"🌳 **Vínculo:** {r.get('ascendente','-')}")
                        st.write(f"📞 **Tel:** {r.get('telefone','-')}")
                    with c2:
                        rua, n_rua, bai = r.get('rua',''), r.get('num',''), r.get('bairro','')
                        st.write(f"🏠 {rua}, {n_rua} - {bai}")
                        st.write(f"📍 CEP: {r.get('cep','')}")
                        
                        st.divider()
                        # WHATSAPP E MAPS POR EXTENSO
                        czap, cmap = st.columns(2)
                        t_l = limpar(r.get('telefone',''))
                        if len(t_l) >= 10:
                            czap.link_button("💬 WhatsApp", f"https://wa.me/55{t_l}")
                        if rua:
                            q_map = quote(f"{rua}, {n_rua}, {bai}")
                            cmap.link_button("📍 Google Maps", f"https://www.google.com/maps/search/?api=1&query={q_map}")

            if sel_ids:
                pdf_data = gerar_pdf(df_m.loc[sel_ids])
                container_pdf.download_button("📥 BAIXAR PDF SELECIONADOS", pdf_data, "familia.pdf", "application/pdf")

    # --- TAB 3: MURAL (3 AVISOS) ---
    with tabs[2]:
        st.subheader("📢 Mural de Avisos")
        av1 = df_todo.iloc[0].get('email', 'Vazio')
        av2 = df_todo.iloc[0].get('rua', 'Vazio')
        av3 = df_todo.iloc[0].get('num', 'Vazio')
        
        c_av1, c_av2, c_av3 = st.columns(3)
        c_av1.warning(f"**Aviso 1**\n\n{av1}")
        c_av2.warning(f"**Aviso 2**\n\n{av2}")
        c_
