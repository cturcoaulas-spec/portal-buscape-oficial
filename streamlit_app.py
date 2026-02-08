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
        pdf.cell(0, 8, f"Endereco: {r.get('rua','-')}, {r.get('num','-')} - {r.get('bairro','-')}", ln=True)
        pdf.cell(0, 8, f"E-mail: {r.get('email','-')}", ln=True)
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
        if not df.empty:
            selecionados = []
            for i, r in df.iterrows():
                col_sel, col_exp = st.columns([0.1, 3.9])
                with col_sel:
                    if st.checkbox("", key=f"ch_{i}"): selecionados.append(r)
                with col_exp:
                    label = f"👤 {r.get('nome','-')} | 📅 {r.get('nascimento','-')} | 📞 {r.get('telefone','-')}"
                    with st.expander(label):
                        c1, c2, c3 = st.columns([2, 2, 1])
                        with c1:
                            st.write(f"**Ascendente:** {r.get('ascendente','-')}")
                            st.write(f"**E-mail:** {r.get('email','-')}")
                        with c2:
                            rua, num, bairro = r.get('rua',''), r.get('num',''), r.get('bairro','')
                            if rua:
                                st.write(f"🏠 {rua}, {num} - {bairro}")
                                link_maps = f"https://www.google.com/maps/search/?api=1&query={quote(f'{rua}, {num}, {bairro}, Brazil')}"
                                st.link_button("📍 Maps", link_maps)
                        with c3:
                            tel_puro = limpar_numero(r.get('telefone',''))
                            if len(tel_puro) >= 10:
                                st.link_button("💬 Zap", f"https://wa.me/55{tel_puro}")
                                st.link_button("📞 Ligar", f"tel:+55{tel_puro}")

            if selecionados:
                pdf_bytes = gerar_pdf(pd.DataFrame(selecionados))
                st.sidebar.download_button("📄 Baixar PDF Selecionados", pdf_bytes, "familia_buscape.pdf", "application/pdf")
        else: st.info("Nenhum membro cadastrado.")

    # --- TAB 2: ANIVERSÁRIOS 🎂 ---
    with t2:
        st.subheader("🎂 Aniversariantes do Mês")
        mes_hoje = datetime.now().strftime("%m")
        niver_list = []
        if not df.empty:
            for i, r in df.iterrows():
                d = r.get('nascimento','')
                puro = limpar_numero(d)
                mes = d.split("/")[1] if "/" in d else (puro[2:4] if len(puro) >= 4 else "")
                if mes == mes_hoje:
                    niver_list.append({"dia": d.split("/")[0] if "/" in d else puro[:2], "nome": r['nome']})
            if niver_list:
                for n in sorted(niver_list, key=lambda x: x['dia']):
                    st.write(f"🎂 **Dia {n['dia']}** - {n['nome']}")
            else: st.info("Ninguém assopra velinhas este mês.")

    # --- TAB 3: CADASTRO (TODOS OS CAMPOS) ---
    with t3:
        st.subheader("Novo Integrante")
        with st.form("form_novo", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                f_nome = st.text_input("Nome Completo")
                f_nasc = st.text_input("Nascimento (DDMMAAAA)")
                f_asc = st.selectbox("Ascendente", ["Raiz"] + lista_nomes)
                f_tel = st.text_input("Telefone (Com DDD)")
                f_mail = st.text_input("E-mail")
            with col2:
                f_rua = st.text_input("Rua")
                f_num = st.text_input("Número")
                f_bair = st.text_input("Bairro")
                f_cep = st.text_input("CEP")
                f_comp = st.text_input("Complemento")
            
            if st.form_submit_button("💾 SALVAR NA NUVEM"):
                if f_nome:
                    dados = [f_nome, aplicar_mascara_data(f_nasc), f_asc, aplicar_mascara_tel(f_tel), f_mail, f_rua, f_num, f_comp, f_bair, f_cep]
                    requests.post(WEBAPP_URL, json={"action": "append", "data": dados})
                    st.success("✅ Salvo e formulário limpo!")
                    st.rerun()

    # --- TAB 4: EDITAR E EXCLUIR ---
    with t4:
        st.subheader("Gerenciar Registro")
        if lista_nomes:
            sel = st.selectbox("Selecione o membro", lista_nomes)
            p = df[df['nome'] == sel].iloc[0]
            idx = df.index[df['nome'] == sel].tolist()[0] + 2
            
            with st.form("form_edit"):
                c1, c2 = st.columns(2)
                with c1:
                    e_nasc = st.text_input("Nascimento", value=p.get('nascimento',''))
                    e_tel = st.text_input("Telefone", value=p.get('telefone',''))
                    e_mail = st.text_input("E-mail", value=p.get('email',''))
                    # Ascendente na edição
                    l_asc = ["Raiz"] + [n for n in lista_nomes if n != sel]
                    cur_asc = p.get('ascendente','Raiz')
                    i_asc = l_asc.index(cur_asc) if cur_asc in l_asc else 0
                    e_asc = st.selectbox("Ascendente", l_asc, index=i_asc)
                with c2:
                    e_rua = st.text_input("Rua", value=p.get('rua',''))
                    e_num = st.text_input("Nº", value=p.get('num',''))
                    e_ba = st.text_input("Bairro", value=p.get('bairro',''))
                    e_ce = st.text_input("CEP", value=p.get('cep',''))
                    e_co = st.text_input("Complemento", value=p.get('complemento',''))
                
                b1, b2 = st.columns(2)
                if b1.form_submit_button("💾 SALVAR ALTERAÇÕES"):
                    up = [sel, e_nasc, e_asc, e_tel, e_mail, e_rua, e_num, e_co, e_ba, e_ce]
                    requests.post(WEBAPP_URL, json={"action": "edit", "row": idx, "data": up})
                    st.success("✅ Atualizado!")
                    st.rerun()
                if b2.form_submit_button("🗑️ EXCLUIR REGISTRO"):
                    requests.post(WEBAPP_URL, json={"action": "edit", "row": idx, "data": [""] * 10})
                    st.warning("Membro removido.")
                    st.rerun()

    st.sidebar.button("Sair", on_click=lambda: st.session_state.update({"logado": False}))
