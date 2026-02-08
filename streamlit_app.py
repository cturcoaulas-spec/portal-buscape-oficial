import streamlit as st
import pandas as pd
import requests
import re
from urllib.parse import quote
from datetime import datetime
from fpdf import FPDF
import io

# CONFIGURAÇÃO
st.set_page_config(page_title="Portal Família Buscapé", page_icon="🌳", layout="wide")

WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzWJ_nDGDe4a81O5BDx3meMbVJjlcMpJoxoO05lilysWJaj_udqeXqvfYFgzvWPlC-Omw/exec"
CSV_URL = "https://docs.google.com/spreadsheets/d/1jrtIP1lN644dPqY0HPGGwPWQGyYwb8nWsUigVK3QZio/export?format=csv"

# --- FUNÇÕES ---
def limpar_numero(v): return re.sub(r'\D', '', str(v))

def aplicar_mascara_tel(v):
    n = limpar_numero(v)
    return f"({n[:2]}) {n[2:7]}-{n[7:]}" if len(n) == 11 else v

def aplicar_mascara_data(v):
    n = limpar_numero(v)
    return f"{n[:2]}/{n[2:4]}/{n[4:]}" if len(n) == 8 else v

def gerar_pdf(dados_selecionados):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, "Relatório Família Buscapé", ln=True, align="C")
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    for _, r in dados_selecionados.iterrows():
        pdf.set_font("Arial", "B", 12)
        pdf.cell(200, 10, f"Membro: {r['nome']}", ln=True)
        pdf.set_font("Arial", size=10)
        pdf.cell(200, 8, f"Nascimento: {r['nascimento']} | Tel: {r['telefone']}", ln=True)
        pdf.cell(200, 8, f"Endereço: {r['rua']}, {r['num']} - {r['bairro']}", ln=True)
        pdf.cell(200, 8, f"E-mail: {r['email']}", ln=True)
        pdf.ln(5)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)
    return pdf.output(dest='S').encode('latin-1')

# --- LOGIN ---
if 'logado' not in st.session_state: st.session_state.logado = False
if not st.session_state.logado:
    st.title("🌳 Portal Família Buscapé")
    senha = st.text_input("Senha", type="password")
    if st.button("ENTRAR"):
        if senha == "buscape2026":
            st.session_state.logado = True
            st.rerun()
        else: st.error("Senha incorreta.")
else:
    @st.cache_data(ttl=2)
    def carregar():
        try:
            df = pd.read_csv(CSV_URL, dtype=str).fillna("")
            df.columns = [c.strip().lower() for c in df.columns]
            return df
        except: return pd.DataFrame()

    df = carregar()
    lista_nomes = sorted(df['nome'].tolist()) if not df.empty else []

    st.title("🌳 Portal Família Buscapé")
    t1, t2, t3, t4 = st.tabs(["🔍 Membros", "🎂 Aniversários", "➕ Cadastrar", "✏️ Editar"])

    # --- TAB 1: MEMBROS ---
    with t1:
        st.subheader("Visualizar e Exportar")
        selecionados = []
        if not df.empty:
            c_pdf, _ = st.columns([1, 3])
            
            for i, r in df.iterrows():
                col_sel, col_exp = st.columns([0.1, 3.9])
                with col_sel:
                    if st.checkbox("", key=f"sel_{i}"):
                        selecionados.append(r)
                
                with col_exp:
                    label = f"👤 {r['nome']} | 📅 {r['nascimento']} | 📞 {r['telefone']}"
                    with st.expander(label):
                        c1, c2, c3 = st.columns([2, 2, 1])
                        with c1:
                            st.write(f"**Ascendente:** {r['ascendente']}")
                            st.write(f"**E-mail:** {r['email']}")
                        with c2:
                            if r['rua']:
                                st.write(f"🏠 {r['rua']}, {r['num']} - {r['bairro']}")
                                link_maps = f"https://www.google.com/maps/search/?api=1&query={quote(f'{r['rua']}, {r['num']}, Brazil')}"
                                st.link_button("📍 Maps", link_maps)
                        with c3:
                            tel_puro = limpar_numero(r['telefone'])
                            if len(tel_puro) >= 10:
                                st.link_button("💬 Zap", f"https://wa.me/55{tel_puro}")

            if selecionados:
                df_sel = pd.DataFrame(selecionados)
                pdf_data = gerar_pdf(df_sel)
                st.sidebar.download_button("📄 Baixar PDF Selecionados", pdf_data, "familia_buscape.pdf", "application/pdf")
        else: st.info("Nada cadastrado.")

    # --- TAB 2: ANIVERSÁRIOS ---
    with t2:
        st.subheader("🎂 Próximas Velinhas")
        mes_hoje = datetime.now().strftime("%m")
        niver_list = []
        if not df.empty:
            for i, r in df.iterrows():
                d = r['nascimento']
                puro = limpar_numero(d)
                mes = d.split("/")[1] if "/" in d else puro[2:4]
                if mes == mes_hoje:
                    niver_list.append({"dia": d.split("/")[0] if "/" in d else puro[:2], "nome": r['nome']})
            if niver_list:
                for n in sorted(niver_list, key=lambda x: x['dia']):
                    st.write(f"🎂 **Dia {n['dia']}** - {n['nome']}")
            else: st.write("Ninguém assopra velinhas este mês.")

    # --- TAB 3: CADASTRO ---
    with t3:
        st.subheader("Novo Membro")
        with st.form("form_novo", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                f_nome = st.text_input("Nome")
                f_nasc = st.text_input("Data (DDMMAAAA)")
                f_asc = st.selectbox("Ascendente", ["Raiz"] + lista_nomes)
            with col2:
                f_tel = st.text_input("Telefone (DDD + Numero)")
                f_mail = st.text_input("E-mail")
                f_rua = st.text_input("Rua")
                f_num = st.text_input("Nº")
                f_bair = st.text_input("Bairro")
                f_cep = st.text_input("CEP")
            
            if st.form_submit_button("SALVAR"):
                if f_nome:
                    dados = [f_nome, aplicar_mascara_data(f_nasc), f_asc, aplicar_mascara_tel(f_tel), f_mail, f_rua, f_num, "", f_bair, f_cep]
                    requests.post(WEBAPP_URL, json={"action": "append", "data": dados})
                    st.success("Salvo!")
                    st.rerun()

    # --- TAB 4: EDITAR ---
    with t4:
        if lista_nomes:
            sel = st.selectbox("Escolha", lista_nomes)
            p = df[df['nome'] == sel].iloc[0]
            idx = df.index[df['nome'] == sel].tolist()[0] + 2
            with st.form("form_edit"):
                c1, c2 = st.columns(2)
                with c1:
                    e_nasc = st.text_input("Nascimento", value=p['nascimento'])
                    e_tel = st.text_input("Telefone", value=p['telefone'])
                with c2:
                    e_rua = st.text_input("Rua", value=p['rua'])
                    e_num = st.text_input("Nº", value=p['num'])
                if st.form_submit_button("ATUALIZAR"):
                    up = [sel, e_nasc, p['ascendente'], e_tel, p['email'], e_rua, e_num, "", p['bairro'], p['cep']]
                    requests.post(WEBAPP_URL, json={"action": "edit", "row": idx, "data": up})
                    st.success("Ok!")
                    st.rerun()

    st.sidebar.button("Sair", on_click=lambda: st.session_state.update({"logado": False}))
