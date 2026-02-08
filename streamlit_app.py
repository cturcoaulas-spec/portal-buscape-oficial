import streamlit as st
import pandas as pd
import requests
import re
from datetime import datetime
from fpdf import FPDF

# CONFIGURAÇÃO
st.set_page_config(page_title="Portal Família Buscapé", page_icon="🌳", layout="wide")

WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzWJ_nDGDe4a81O5BDx3meMbVJjlcMpJoxoO05lilysWJaj_udqeXqvfYFgzvWPlC-Omw/exec"
CSV_URL = "https://docs.google.com/spreadsheets/d/1jrtIP1lN644dPqY0HPGGwPWQGyYwb8nWsUigVK3QZio/export?format=csv"

# --- FUNÇÕES ---
def faxina_tel(v):
    n = re.sub(r'\D', '', str(v))
    if len(n) >= 11: return f"({n[:2]}) {n[2:7]}-{n[7:11]}"
    if len(n) == 10: return f"({n[:2]}) {n[2:6]}-{n[6:10]}"
    return v

def faxina_data(v):
    n = re.sub(r'\D', '', str(v))
    if len(n) >= 8: return f"{n[:2]}/{n[2:4]}/{n[4:8]}"
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
        pdf.cell(0, 8, f"Nascimento: {r.get('nascimento','-')} | Vinculo: {r.get('ascendente','-')}", ln=True)
        pdf.cell(0, 8, f"Tel: {r.get('telefone','-')} | Conjuge: {r.get('conjuge','-')}", ln=True)
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
    # BARRA LATERAL
    st.sidebar.title("🌳 Menu")
    
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
    t1, t2, t3, t4 = st.tabs(["🔍 Membros", "🎂 Aniversários", "➕ Cadastrar", "✏️ Editar"])

    # --- TAB 1: MEMBROS (COM SELEÇÃO PDF) ---
    with t1:
        st.subheader("Membros da Família")
        selecionados = []
        if not df.empty:
            for i, r in df.iterrows():
                col_c, col_e = st.columns([0.15, 3.85])
                with col_c:
                    if st.checkbox("", key=f"sel_{i}"): selecionados.append(r)
                with col_e:
                    with st.expander(f"👤 {r.get('nome','')} | 📅 {r.get('nascimento','')}"):
                        c1, c2 = st.columns(2)
                        with c1:
                            st.write(f"💍 **Cônjuge:** {r.get('conjuge','-')}")
                            st.write(f"🌳 **Vínculo:** {r.get('ascendente','-')}")
                        with c2:
                            st.write(f"📞 **Telefone:** {r.get('telefone','-')}")
                            st.write(f"🏠 **Bairro:** {r.get('bairro','-')}")
            
            # Botão PDF na Barra Lateral se houver seleção
            if selecionados:
                pdf_bytes = gerar_pdf(pd.DataFrame(selecionados))
                st.sidebar.markdown("---")
                st.sidebar.subheader("📄 Relatório")
                st.sidebar.download_button(f"Baixar PDF ({len(selecionados)})", pdf_bytes, "familia.pdf", "application/pdf")
        else: st.info("Nada cadastrado.")

    # --- TAB 2: ANIVERSÁRIOS ---
    with t2:
        st.subheader("🎂 Aniversariantes do Mês")
        mes_h = datetime.now().strftime("%m")
        n_list = []
        if not df.empty:
            for _, r in df.iterrows():
                d = r.get('nascimento',''); p = re.sub(r'\D', '', d)
                m = d.split("/")[1] if "/" in d else (p[2:4] if len(p)>=4 else "")
                if m == mes_h: n_list.append({"dia": d.split("/")[0] if "/" in d else p[:2], "nome": r.get('nome','')})
            for n in sorted(n_list, key=lambda x: x['dia']):
                st.write(f"🎈 **Dia {n['dia']}** - {n['nome']}")

    # --- TAB 3: CADASTRO ---
    with t3:
        st.subheader("Novo Cadastro")
        with st.form("f_novo", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                f_n = st.text_input("Nome Completo")
                f_d = st.text_input("Nascimento (DDMMAAAA)")
                f_t = st.text_input("Telefone (Só números)")
                f_tipo = st.radio("Vínculo:", ["Filho(a) de", "Cônjuge de"], horizontal=True)
            with col2:
                f_ref = st.selectbox("Pessoa de Referência", ["Raiz"] + lista_nomes)
                f_r = st.text_input("Rua")
                f_u = st.text_input("Número")
                f_b = st.text_input("Bairro")
            
            if st.form_submit_button("💾 SALVAR"):
                if f_n:
                    vinc = f"{f_tipo} {f_ref}" if f_ref != "Raiz" else "Raiz"
                    conj = f_ref if "Cônjuge" in f_tipo else ""
                    # Ordem: Nome, Nascimento, Ascendente, Tel, Email, Rua, Num, Conjuge, Bairro, CEP
                    dados = [f_n, faxina_data(f_d), vinc, faxina_tel(f_t), "", f_r, f_u, conj, f_b, ""]
                    requests.post(WEBAPP_URL, json={"action": "append", "data": dados})
                    st.success("✅ Salvo!"); st.rerun()

    # --- TAB 4: EDITAR ---
    with t4:
        st.subheader("Gerenciar")
        sel = st.selectbox("Escolha um membro", ["--"] + lista_nomes)
        if sel != "--":
            p_d = df[df['nome'] == sel].iloc[0]
            idx = df.index[df['nome'] == sel].tolist()[0] + 2
            with st.form("f_edit"):
                e_d = st.text_input("Nascimento", value=p_d.get('nascimento',''))
                e_t = st.text_input("Telefone", value=p_d.get('telefone',''))
                e_c = st.text_input("Cônjuge", value=p_d.get('conjuge',''))
                if st.form_submit_button("ATUALIZAR"):
                    up = [sel, faxina_data(e_d), p_d.get('ascendente',''), faxina_tel(e_t), "", p_d.get('rua',''), p_d.get('num',''), e_c, p_d.get('bairro',''), ""]
                    requests.post(WEBAPP_URL, json={"action": "edit", "row": idx, "data": up}); st.rerun()
                if st.form_submit_button("EXCLUIR"):
                    requests.post(WEBAPP_URL, json={"action": "edit", "row": idx, "data": [""] * 10}); st.rerun()

    if st.sidebar.button("🚪 Sair"):
        st.session_state.logado = False
        st.rerun()
