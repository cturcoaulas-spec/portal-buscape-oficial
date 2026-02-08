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

# --- FUNÇÕES DE MÁSCARA ---
def limpar_numero(v): return re.sub(r'\D', '', str(v))

def aplicar_mascara_tel(v):
    n = limpar_numero(v)
    if len(n) == 11: return f"({n[:2]}) {n[2:7]}-{n[7:]}" # Celular
    if len(n) == 10: return f"({n[:2]}) {n[2:6]}-{n[6:]}" # Fixo
    return v

def aplicar_mascara_data(v):
    n = limpar_numero(v)
    if len(n) == 8: return f"{n[:2]}/{n[2:4]}/{n[4:]}"
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
        pdf.cell(0, 8, f"Nascimento: {r.get('nascimento','-')} | Tel: {r.get('telefone','-')}", ln=True)
        end = f"{r.get('rua','-')}, {r.get('num','-')} {r.get('complemento','')}".strip()
        pdf.cell(0, 8, f"Endereco: {end} | CEP: {r.get('cep','-')}", ln=True)
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
    @st.cache_data(ttl=1)
    def carregar():
        try:
            df = pd.read_csv(CSV_URL, dtype=str).fillna("")
            df.columns = [c.strip().lower() for c in df.columns]
            # Remove linhas vazias ou sem nome (excluídos)
            df = df[df['nome'].str.strip() != ""]
            return df
        except: return pd.DataFrame()

    df = carregar()
    lista_nomes = sorted(df['nome'].tolist()) if not df.empty else []

    st.title("🌳 Portal Família Buscapé")
    t1, t2, t3, t4 = st.tabs(["🔍 Membros", "🎂 Aniversários", "➕ Cadastrar", "✏️ Editar"])

    # --- TAB 1: MEMBROS ---
    with t1:
        st.subheader("Membros da Família")
        selecionados = []
        if not df.empty:
            for i, r in df.iterrows():
                # Criando colunas para checkbox e expander
                c_sel, c_exp = st.columns([0.1, 3.9])
                with c_sel:
                    if st.checkbox("", key=f"sel_{i}"): selecionados.append(r)
                with c_exp:
                    # Título com ícone fixo
                    with st.expander(f"👤 {r.get('nome','-')} | 📅 {r.get('nascimento','-')}"):
                        col1, col2, col3 = st.columns([2, 2, 1])
                        with col1:
                            st.write(f"📞 **Tel:** {r.get('telefone','-')}")
                            st.write(f"✉️ **E-mail:** {r.get('email','-')}")
                        with col2:
                            st.write(f"🏠 {r.get('rua','-')}, {r.get('num','-')} {r.get('complemento','')}")
                            st.write(f"CEP: {r.get('cep','-')}")
                        with col3:
                            tel_p = limpar_numero(r.get('telefone',''))
                            if len(tel_p) >= 10: st.link_button("💬 Zap", f"https://wa.me/55{tel_p}")

            if selecionados:
                pdf_b = gerar_pdf(pd.DataFrame(selecionados))
                st.sidebar.download_button(f"📄 Baixar PDF ({len(selecionados)})", pdf_b, "familia_buscape.pdf", "application/pdf")
        else: st.info("Nenhum membro cadastrado.")

    # --- TAB 2: ANIVERSÁRIOS 🎂 ---
    with t2:
        st.subheader("🎂 Aniversariantes do Mês")
        mes_h = datetime.now().strftime("%m")
        n_list = []
        if not df.empty:
            for _, r in df.iterrows():
                d = r.get('nascimento','')
                p = limpar_numero(d)
                m = d.split("/")[1] if "/" in d else (p[2:4] if len(p)>=4 else "")
                if m == mes_h: n_list.append({"dia": d.split("/")[0] if "/" in d else p[:2], "nome": r.get('nome','')})
            
            if n_list:
                for n in sorted(n_list, key=lambda x: x['dia']):
                    st.write(f"🎂 **Dia {n['dia']}** - {n['nome']}")
            else: st.info("Ninguém assopra velinhas este mês.")

    # --- TAB 3: CADASTRO ---
    with t3:
        st.subheader("Novo Integrante")
        with st.form("f_novo", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                f_n = st.text_input("Nome Completo")
                f_d = st.text_input("Nascimento (DDMMAAAA)")
                f_a = st.selectbox("Ascendente", ["Raiz"] + lista_nomes)
                f_t = st.text_input("Telefone (Com DDD)")
            with col2:
                f_e = st.text_input("E-mail")
                f_r = st.text_input("Rua")
                f_u = st.text_input("Número")
                f_c = st.text_input("Complemento")
                f_ce = st.text_input("CEP")
            
            if st.form_submit_button("💾 SALVAR"):
                tel_l = limpar_numero(f_t)
                if f_n in lista_nomes: st.error("⚠️ Já tem cadastro!")
                elif len(tel_l) < 10: st.warning("⚠️ Telefone inválido (mínimo 10 números)")
                elif f_n:
                    d_f = [f_n, aplicar_mascara_data(f_d), f_a, aplicar_mascara_tel(f_t), f_e, f_r, f_u, f_c, "", f_ce]
                    requests.post(WEBAPP_URL, json={"action": "append", "data": d_f})
                    st.success("✅ Salvo!"); st.rerun()

    # --- TAB 4: EDITAR ---
    with t4:
        st.subheader("Gerenciar Membro")
        if lista_nomes:
            s_m = st.selectbox("Escolha", lista_nomes)
            p_d = df[df['nome'] == s_m].iloc[0]
            idx = df.index[df['nome'] == s_m].tolist()[0] + 2
            
            with st.form("f_edit"):
                e_d = st.text_input("Nascimento", value=p_d.get('nascimento',''))
                e_t = st.text_input("Telefone", value=p_d.get('telefone',''))
                e_r = st.text_input("Rua", value=p_d.get('rua',''))
                e_ce = st.text_input("CEP", value=p_d.get('cep',''))
                
                c_b1, c_b2 = st.columns(2)
                if c_b1.form_submit_button("💾 ATUALIZAR"):
                    up = [s_m, e_d, p_d.get('ascendente',''), aplicar_mascara_tel(e_t), p_d.get('email',''), e_r, p_d.get('num',''), p_d.get('complemento',''), "", e_ce]
                    requests.post(WEBAPP_URL, json={"action": "edit", "row": idx, "data": up}); st.rerun()
                
                if c_b2.form_submit_button("🗑️ EXCLUIR"):
                    st.session_state.conf_del = True

            if st.session_state.get('conf_del'):
                if st.button("🚨 CONFIRMAR EXCLUSÃO PERMANENTE"):
                    requests.post(WEBAPP_URL, json={"action": "edit", "row": idx, "data": [""] * 10})
                    st.session_state.conf_del = False
                    st.rerun()

    st.sidebar.button("Sair", on_click=lambda: st.session_state.update({"logado": False}))
