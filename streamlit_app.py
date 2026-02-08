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

# --- FUNÇÕES DE MÁSCARA ---
def limpar(v): return re.sub(r'\D', '', str(v))

def mask_tel(v):
    n = limpar(v)
    if len(n) >= 11: return f"({n[:2]}) {n[2:7]}-{n[7:11]}"
    if len(n) == 10: return f"({n[:2]}) {n[2:6]}-{n[6:10]}"
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
        pdf.cell(0, 7, f"Conjuge: {r.get('conjuge','-')} | Vinculo: {r.get('ascendente','-')}", ln=True)
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

    st.title("🌳 Família Buscapé")
    t1, t2, t3, t4, t5 = st.tabs(["🔍 Membros", "🎂 Aniversários", "📢 Mural", "➕ Cadastrar", "✏️ Gerenciar"])

    # --- TAB 1: MEMBROS ---
    with t1:
        sel_idx = []
        for i, r in df_m.iterrows():
            c1, c2 = st.columns([0.1, 3.9])
            if c1.checkbox("", key=f"p_{i}"): sel_idx.append(i)
            with c2.expander(f"👤 {r.get('nome','-')} | 📅 {r.get('nascimento','-')}"):
                col_a, col_b, col_c = st.columns([2, 2, 1])
                with col_a:
                    st.write(f"💍 **Cônjuge:** {r.get('conjuge','-')}")
                    st.write(f"🌳 **Vínculo:** {r.get('ascendente','-')}")
                    st.write(f"✉️ **E-mail:** {r.get('email','-')}")
                with col_b:
                    rua, num, bairro = r.get('rua',''), r.get('num',''), r.get('bairro','')
                    st.write(f"🏠 {rua}, {num}")
                    st.write(f"📍 {bairro} | CEP: {r.get('cep','')}")
                with col_c:
                    tel_limpo = limpar(r.get('telefone',''))
                    if len(tel_limpo) >= 10:
                        st.link_button("💬 Zap", f"https://wa.me/55{tel_limpo}")
                    if rua:
                        mapa_url = f"https://www.google.com/maps/search/?api=1&query={quote(f'{rua}, {num}, {bairro}')}"
                        st.link_button("📍 Maps", mapa_url)

        if sel_idx:
            pdf_b = gerar_pdf(df_m.loc[sel_idx])
            st.sidebar.download_button("📄 Baixar PDF Selecionados", pdf_b, "familia.pdf", "application/pdf")

    # --- TAB 2: ANIVERSÁRIOS ---
    with t2:
        mes_atual = datetime.now().strftime("%m")
        st.subheader(f"🎂 Aniversariantes de {datetime.now().strftime('%B')}")
        for _, r in df_m.iterrows():
            d = r.get('nascimento','-')
            if f"/{mes_atual}/" in d or (len(limpar(d)) >= 4 and limpar(d)[2:4] == mes_atual):
                st.info(f"🎈 Dia {d[:2]} - {r['nome']}")

    # --- TAB 3: MURAL DE AVISOS ---
    with t3:
        st.subheader("📢 Quadro de Avisos da Família")
        aviso_atual = df_bruto.iloc[0].get('email', 'Nenhum aviso no momento.')
        st.warning(f"**AVISO ATUAL:**\n\n{aviso_atual}")
        
        st.divider()
        st.subheader("📝 Gerenciar Avisos")
        novo_aviso = st.text_area("Escreva o novo aviso aqui:", value=aviso_atual if aviso_atual != "Nenhum aviso no momento." else "")
        col_av1, col_av2 = st.columns(2)
        if col_av1.button("💾 Publicar/Salvar Aviso"):
            requests.post(WEBAPP_URL, json={"action": "edit", "row": 2, "data": ["AVISO","","","",novo_aviso,"","","","",""]})
            st.success("Aviso publicado!"); st.rerun()
        if col_av2.button("🗑️ Excluir Aviso"):
            requests.post(WEBAPP_URL, json={"action": "edit", "row": 2, "data": ["AVISO","","","","Nenhum aviso no momento.","","","","",""]})
            st.rerun()

    # --- TAB 4: CADASTRO ---
    with t4:
        with st.form("f_cad", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                n, d, t = st.text_input("Nome"), st.text_input("Nasc (Ex: 08021990)"), st.text_input("Telefone")
                v = st.radio("Vínculo", ["Filho(a) de", "Cônjuge de"], horizontal=True)
                ref = st.selectbox("Pessoa de Referência", ["Raiz"] + nomes)
            with col2:
                mail, ru, num, ba, ce = st.text_input("E-mail"), st.text_input("Rua"), st.text_input("Nº"), st.text_input("Bairro"), st.text_input("CEP")
            if st.form_submit_button("💾 SALVAR CADASTRO"):
                vinc = f"{v} {ref}" if ref != "Raiz" else "Raiz"
                conj = ref if "Cônjuge" in v else ""
                dados = [n, mask_data(d), vinc, mask_tel(t), mail, ru, num, conj, ba, ce]
                requests.post(WEBAPP_URL, json={"action": "append", "data": dados})
                st.success("✅ Cadastrado!"); st.rerun()

    # --- TAB 5: GERENCIAR MEMBROS ---
    with t5:
        s = st.selectbox("Escolha um membro para editar/excluir", ["--"] + nomes)
        if s != "--":
            m = df_m[df_m['nome'] == s].iloc[0]
            idx = df_m.index[df_m['nome'] == s].tolist()[0] + 2
            with st.form("f_edit"):
                c1, c2 = st.columns(2)
                with c1:
                    ed, et, ec = st.text_input("Nasc", m.get('nascimento','')), st.text_input("Tel", m.get('telefone','')), st.text_input("Cônjuge", m.get('conjuge',''))
                with col2: # Reutilizando a lógica de colunas
                    er, en, eb, ece = st.text_input("Rua", m.get('rua','')), st.text_input("Nº", m.get('num','')), st.text_input("Bairro", m.get('bairro','')), st.text_input("CEP", m.get('cep',''))
                
                b_edit, b_excluir = st.columns(2)
                if b_edit.form_submit_button("💾 ATUALIZAR"):
                    up = [s, mask_data(ed), m.get('ascendente',''), mask_tel(et), m.get('email',''), er, en, ec, eb, ece]
                    requests.post(WEBAPP_URL, json={"action": "edit", "row": idx, "data": up}); st.rerun()
                if b_excluir.form_submit_button("🗑️ EXCLUIR"):
                    requests.post(WEBAPP_URL, json={"action": "edit", "row": idx, "data": [""]*10}); st.rerun()

    st.sidebar.button("🚪 Sair", on_click=lambda: st.session_state.update({"logado": False}))
