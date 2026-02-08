import streamlit as st
import pandas as pd
import requests
import re
from datetime import datetime
from fpdf import FPDF

# CONFIGURAÇÃO
st.set_page_config(page_title="Família Buscapé", page_icon="🌳", layout="wide")

WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzWJ_nDGDe4a81O5BDx3meMbVJjlcMpJoxoO05lilysWJaj_udqeXqvfYFgzvWPlC-Omw/exec"
CSV_URL = "https://docs.google.com/spreadsheets/d/1jrtIP1lN644dPqY0HPGGwPWQGyYwb8nWsUigVK3QZio/export?format=csv"

# --- FUNÇÕES ---
def faxina(v, tipo):
    n = re.sub(r'\D', '', str(v))
    if tipo == "tel":
        if len(n) >= 11: return f"({n[:2]}) {n[2:7]}-{n[7:11]}"
        if len(n) == 10: return f"({n[:2]}) {n[2:6]}-{n[6:10]}"
    if tipo == "data" and len(n) >= 8: return f"{n[:2]}/{n[2:4]}/{n[4:8]}"
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
        pdf.cell(0, 7, f"Nasc: {r.get('nascimento','-')} | Tel: {r.get('telefone','-')} | Conj: {r.get('conjuge','-')}", ln=True)
        pdf.cell(0, 7, f"End: {r.get('rua','-')}, {r.get('num','-')} - {r.get('bairro','-')} | CEP: {r.get('cep','-')}", ln=True)
        pdf.ln(3); pdf.line(10, pdf.get_y(), 200, pdf.get_y()); pdf.ln(3)
    return pdf.output(dest='S').encode('latin-1')

# --- LOGIN ---
if 'logado' not in st.session_state: st.session_state.logado = False
if not st.session_state.logado:
    st.title("🌳 Portal Família Buscapé")
    if st.text_input("Senha", type="password") == "buscape2026":
        if st.button("ENTRAR"): st.session_state.logado = True; st.rerun()
else:
    @st.cache_data(ttl=2)
    def carregar():
        df = pd.read_csv(CSV_URL, dtype=str).fillna("")
        df.columns = [c.strip().lower() for c in df.columns]
        return df

    df_todo = carregar()
    df_m = df_todo[df_todo['nome'].str.strip() != ""]
    nomes = sorted(df_m['nome'].tolist())

    st.title("🌳 Família Buscapé")
    t1, t2, t3, t4 = st.tabs(["🔍 Membros", "📢 Avisos", "➕ Cadastrar", "✏️ Gerenciar"])

    with t1:
        sel_idx = []
        for i, r in df_m.iterrows():
            c1, c2 = st.columns([0.1, 3.9])
            if c1.checkbox("", key=f"p_{i}"): sel_idx.append(i)
            c2.expander(f"👤 {r['nome']} | 📞 {r['telefone']}").write(f"💍 Cônjuge: {r['conjuge']} | 🌳 Vínculo: {r['ascendente']}")
        
        if sel_idx:
            pdf_b = gerar_pdf(df_m.loc[sel_idx])
            st.sidebar.download_button("📄 Baixar PDF Selecionados", pdf_b, "familia.pdf", "application/pdf")

    with t2:
        c_n, c_a = st.columns(2)
        mes = datetime.now().strftime("%m")
        with c_n:
            st.subheader("🎂 Aniversários")
            for _, r in df_m.iterrows():
                d = r['nascimento']
                if mes in d: st.info(f"🎈 {d[:2]} - {r['nome']}")
        with c_a:
            st.subheader("📢 Avisos")
            st.warning(df_todo.iloc[0].get('email', 'Sem avisos.'))

    with t3:
        with st.form("f_n", clear_on_submit=True):
            n, d, t = st.text_input("Nome"), st.text_input("Nasc (DDMMAAAA)"), st.text_input("Tel")
            v = st.radio("Vínculo", ["Filho(a) de", "Cônjuge de"], horizontal=True)
            ref = st.selectbox("Referência", ["Raiz"] + nomes)
            r, num, b, cep = st.text_input("Rua"), st.text_input("Nº"), st.text_input("Bairro"), st.text_input("CEP")
            if st.form_submit_button("SALVAR"):
                vinc = f"{v} {ref}" if ref != "Raiz" else "Raiz"
                conj = ref if "Cônjuge" in v else ""
                dados = [n, faxina(d, "data"), vinc, faxina(t, "tel"), "", r, num, conj, b, cep]
                requests.post(WEBAPP_URL, json={"action": "append", "data": dados})
                st.success("Salvo!"); st.rerun()

    with t4:
        st.subheader("Publicar Aviso")
        av = st.text_area("Novo Aviso")
        if st.button("Publicar"):
            requests.post(WEBAPP_URL, json={"action": "edit", "row": 2, "data": ["AVISO","","","",av,"","","","",""]})
            st.rerun()
        st.divider()
        s = st.selectbox("Editar", ["--"] + nomes)
        if s != "--":
            m = df_m[df_m['nome'] == s].iloc[0]
            idx = df_m.index[df_m['nome'] == s].tolist()[0] + 2
            with st.form("f_e"):
                ed, et, ec = st.text_input("Nasc", m['nascimento']), st.text_input("Tel", m['telefone']), st.text_input("Cônjuge", m['conjuge'])
                er, en, eb, ecp = st.text_input("Rua", m['rua']), st.text_input("Nº", m['num']), st.text_input("Bairro", m['bairro']), st.text_input("CEP", m['cep'])
                if st.form_submit_button("ATUALIZAR"):
                    up = [s, faxina(ed,"data"), m['ascendente'], faxina(et,"tel"), "", er, en, ec, eb, ecp]
                    requests.post(WEBAPP_URL, json={"action": "edit", "row": idx, "data": up}); st.rerun()
                if st.form_submit_button("EXCLUIR"):
                    requests.post(WEBAPP_URL, json={"action": "edit", "row": idx, "data": [""]*10}); st.rerun()

    st.sidebar.button("Sair", on_click=lambda: st.session_state.update({"logado": False}))
