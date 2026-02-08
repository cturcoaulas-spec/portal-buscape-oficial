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
    # ORDEM ALFABÉTICA
    df_m = df_todo[df_todo['nome'].str.strip() != ""].sort_values(by='nome').copy()
    nomes_lista = df_m['nome'].tolist()

    st.title("🌳 Família Buscapé")
    tabs = st.tabs(["🔍 Membros", "🎂 Aniversários", "📢 Mural", "➕ Cadastrar", "✏️ Gerenciar"])

    # --- TAB 1: MEMBROS ---
    with tabs[0]:
        st.subheader("Lista de Membros")
        sel_ids = []
        
        # BOTÃO DE PDF NO TOPO (Facilita no celular)
        if not df_m.empty:
            container_pdf = st.container()
            
            for i, r in df_m.iterrows():
                c1, c2 = st.columns([0.2, 3.8])
                if c1.checkbox("", key=f"check_{i}"): sel_ids.append(i)
                with c2.expander(f"👤 {r.get('nome','-')}"):
                    col_i1, col_i2 = st.columns(2)
                    with col_i1:
                        st.write(f"💍 **Cônjuge:** {r.get('conjuge','-')}")
                        st.write(f"🌳 **Vínculo:** {r.get('ascendente','-')}")
                        st.write(f"📅 **Nasc:** {r.get('nascimento','-')}")
                        st.write(f"📞 **Tel:** {r.get('telefone','-')}")
                    with col_i2:
                        rua, n_rua, bai = r.get('rua',''), r.get('num',''), r.get('bairro','')
                        st.write(f"🏠 {rua}, {n_rua} - {bai}")
                        st.write(f"📍 CEP: {r.get('cep','')}")
                        st.write(f"✉️ {r.get('email','')}")
                        
                        st.divider()
                        # BOTÕES DE WHATSAPP E MAPS
                        c_zap, c_map = st.columns(2)
                        t_limpo = limpar(r.get('telefone',''))
                        if len(t_limpo) >= 10:
                            c_zap.link_button("💬 WhatsApp", f"https://wa.me/55{t_limpo}")
                        if rua:
                            q_map = quote(f"{rua}, {n_rua}, {bai}")
                            c_map.link_button("📍 Google Maps", f"https://www.google.com/maps/search/?api=1&query={q_map}")

            if sel_ids:
                pdf_data = gerar_pdf(df_m.loc[sel_ids])
                container_pdf.download_button("📥 BAIXAR PDF DOS SELECIONADOS", pdf_data, "familia.pdf", "application/pdf")
                st.sidebar.download_button("📥 BAIXAR PDF (Menu)", pdf_data, "familia.pdf", "application/pdf")

    # --- TAB 3: MURAL (3 AVISOS) ---
    with tabs[2]:
        st.subheader("📢 Mural de Avisos")
        av1 = df_todo.iloc[0].get('email', 'Vazio')
        av2 = df_todo.iloc[0].get('rua', 'Vazio')
        av3 = df_todo.iloc[0].get('num', 'Vazio')
        
        c_av1, c_av2, c_av3 = st.columns(3)
        c_av1.warning(f"**Aviso 1**\n\n{av1}")
        c_av2.warning(f"**Aviso 2**\n\n{av2}")
        c_av3.warning(f"**Aviso 3**\n\n{av3}")

        st.divider()
        st.write("✏️ **Gerenciar Avisos**")
        with st.form("mural_edit"):
            nv1 = st.text_input("Aviso 1", value=av1)
            nv2 = st.text_input("Aviso 2", value=av2)
            nv3 = st.text_input("Aviso 3", value=nv3 if 'nv3' in locals() else av3)
            if st.form_submit_button("💾 Salvar Mural"):
                requests.post(WEBAPP_URL, json={"action": "edit", "row": 2, "data": ["AVISO","", "", "", nv1, nv2, nv3, "", "", ""]})
                st.success("Mural atualizado!"); st.rerun()

    # --- TAB 4: CADASTRAR ---
    with tabs[3]:
        with st.form("form_novo", clear_on_submit=True):
            f1, f2 = st.columns(2)
            with f1:
                new_n = st.text_input("Nome completo")
                new_d = st.text_input("Nascimento (DDMMAAAA)")
                new_t = st.text_input("Telefone (DDD + Número)")
                new_v = st.radio("Vínculo", ["Filho(a) de", "Cônjuge de"], horizontal=True)
                new_ref = st.selectbox("Referência na família", ["Raiz"] + nomes_lista)
            with f2:
                new_e, new_ru, new_nu, new_ba, new_ce = st.text_input("E-mail"), st.text_input("Rua"), st.text_input("Nº"), st.text_input("Bairro"), st.text_input("CEP")
            if st.form_submit_button("💾 SALVAR"):
                vinc_final = f"{new_v} {new_ref}" if new_ref != "Raiz" else "Raiz"
                conj_final = new_ref if "Cônjuge" in new_v else ""
                payload = [new_n, mask_data(new_d), vinc_final, mask_tel(new_t), new_e, new_ru, new_nu, conj_final, new_ba, new_ce]
                requests.post(WEBAPP_URL, json={"action": "append", "data": payload})
                st.success("Cadastrado!"); st.rerun()

    # --- TAB 5: GERENCIAR (EDIÇÃO) ---
    with tabs[4]:
        escolha = st.selectbox("Selecione para alterar", ["--"]
