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
    pdf.cell(200, 10, "Relatorio Familia Buscape", ln=True, align="C")
    pdf.ln(10)
    for _, r in dados_selecionados.iterrows():
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, f"Membro: {r.get('nome','-')}", ln=True)
        pdf.set_font("Arial", size=10)
        pdf.cell(0, 8, f"Nascimento: {r.get('nascimento','-')} | Tel: {r.get('telefone','-')}", ln=True)
        end = f"{r.get('rua','-')}, {r.get('num','-')} {r.get('complemento','')}".strip()
        pdf.cell(0, 8, f"Endereco: {end}", ln=True)
        pdf.cell(0, 8, f"CEP: {r.get('cep','-')}", ln=True)
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
            for i, r in df.iterrows():
                col_sel, col_exp = st.columns([0.15, 3.85])
                with col_sel:
                    # CHECKBOX PARA PDF
                    if st.checkbox("", key=f"check_pdf_{i}"):
                        selecionados.append(r)
                with col_exp:
                    with st.expander(f"👤 {r.get('nome','')} | 📅 {r.get('nascimento','')}"):
                        c1, c2, c3 = st.columns([2, 2, 1])
                        with c1:
                            st.write(f"📞 **Telefone:** {r.get('telefone','-')}")
                            st.write(f"✉️ **E-mail:** {r.get('email','-')}")
                        with c2:
                            st.write(f"🏠 {r.get('rua','-')}, {r.get('num','-')} {r.get('complemento','')}")
                            st.write(f"Bairro: {r.get('bairro','-')} | CEP: {r.get('cep','-')}")
                        with c3:
                            tel_p = limpar_numero(r.get('telefone',''))
                            if len(tel_p) >= 10: st.link_button("💬 Zap", f"https://wa.me/55{tel_p}")

            # BOTÃO DE PDF NA BARRA LATERAL
            if selecionados:
                pdf_b = gerar_pdf(pd.DataFrame(selecionados))
                st.sidebar.markdown("---")
                st.sidebar.subheader("📄 Exportar")
                st.sidebar.download_button(f"Baixar PDF ({len(selecionados)})", pdf_b, "familia_buscape.pdf", "application/pdf")
        else: st.info("Nada cadastrado.")

    # --- TAB 2: ANIVERSÁRIOS 🎂 ---
    with t2:
        st.subheader("🎂 Aniversariantes do Mês")
        # Pega o mês atual do sistema
        mes_atual = datetime.now().strftime("%m")
        niver_list = []
        if not df.empty:
            for _, r in df.iterrows():
                d = r.get('nascimento','')
                p = limpar_numero(d)
                m = d.split("/")[1] if "/" in d else (p[2:4] if len(p)>=4 else "")
                if m == mes_atual:
                    niver_list.append({"dia": d.split("/")[0] if "/" in d else p[:2], "nome": r.get('nome','')})
            
            if niver_list:
                for n in sorted(niver_list, key=lambda x: x['dia']):
                    st.write(f"🎂 **Dia {n['dia']}** - {n['nome']}")
            else: st.info("Ninguém faz aniversário este mês.")

    # --- TAB 3: CADASTRO ---
    with t3:
        st.subheader("Novo Integrante")
        with st.form("f_novo", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                f_n = st.text_input("Nome Completo")
                f_d = st.text_input("Nascimento (DDMMAAAA)")
                f_a = st.selectbox("Ascendente", ["Raiz"] + lista_nomes)
                f_t = st.text_input("Telefone")
            with c2:
                f_e = st.text_input("E-mail")
                f_r = st.text_input("Rua")
                f_u = st.text_input("Número")
                f_c = st.text_input("Complemento")
                f_ba = st.text_input("Bairro")
                f_ce = st.text_input("CEP")
            
            if st.form_submit_button("💾 SALVAR"):
                if f_n in lista_nomes: st.error("⚠️ Já tem cadastro!")
                elif f_n:
                    d_final = [f_n, aplicar_mascara_data(f_d), f_a, aplicar_mascara_tel(f_t), f_e, f_r, f_u, f_c, f_ba, f_ce]
                    requests.post(WEBAPP_URL, json={"action": "append", "data": d_final})
                    st.success("✅ Salvo!")
                    st.rerun()

    # --- TAB 4: EDITAR ---
    with t4:
        st.subheader("Gerenciar")
        if lista_nomes:
            s_m = st.selectbox("Escolha um membro para editar", lista_nomes)
            p_d = df[df['nome'] == s_m].iloc[0]
            idx = df.index[df['nome'] == s_m].tolist()[0] + 2
            with st.form("f_edit"):
                c1, c2 = st.columns(2)
                with c1:
                    e_d = st.text_input("Nascimento", value=p_d.get('nascimento',''))
                    e_t = st.text_input("Telefone", value=p_d.get('telefone',''))
                with c2:
                    e_r = st.text_input("Rua", value=p_d.get('rua',''))
                    e_ce = st.text_input("CEP", value=p_d.get('cep',''))
                
                b1, b2 = st.columns(2)
                if b1.form_submit_button("💾 ATUALIZAR"):
                    up = [s_m, e_d, p_d.get('ascendente',''), e_t, p_d.get('email',''), e_r, p_d.get('num',''), p_d.get('complemento',''), p_d.get('bairro',''), e_ce]
                    requests.post(WEBAPP_URL, json={"action": "edit", "row": idx, "data": up}); st.rerun()
                if b2.form_submit_button("🗑️ EXCLUIR"):
                    requests.post(WEBAPP_URL, json={"action": "edit", "row": idx, "data": [""] * 10}); st.rerun()

    st.sidebar.button("Sair", on_click=lambda: st.session_state.update({"logado": False}))
