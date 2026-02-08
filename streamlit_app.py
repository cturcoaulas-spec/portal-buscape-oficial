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

MESES = ["", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

# --- FUNÇÕES ---
def limpar(v): return re.sub(r'\D', '', str(v))
def mask_tel(v):
    n = limpar(v)
    return f"({n[:2]}) {n[2:7]}-{n[7:11]}" if len(n) >= 11 else v
def mask_data(v):
    n = limpar(v)
    return f"{n[:2]}/{n[2:4]}/{n[4:8]}" if len(n) >= 8 else v

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
    df_m = df_todo[df_todo['nome'].str.strip() != ""].sort_values(by='nome').copy()
    nomes_lista = df_m['nome'].tolist()

    st.sidebar.title("🔔 Notificações")
    hoje = datetime.now().strftime("%d/%m")
    niver_hoje = [r['nome'] for _, r in df_m.iterrows() if str(r.get('nascimento','')).startswith(hoje)]
    for n in niver_hoje: st.sidebar.success(f"🎂 Hoje: {n}")

    st.title("🌳 Família Buscapé")
    tabs = st.tabs(["🔍 Membros", "🎂 Aniversários", "📢 Mural", "➕ Cadastrar", "✏️ Gerenciar"])

    # --- TAB 1: MEMBROS (COM MAPS E WHATSAPP) ---
    with tabs[0]:
        sel_ids = []
        c_topo = st.container()
        for i, r in df_m.iterrows():
            col1, col2 = st.columns([0.2, 3.8])
            if col1.checkbox("", key=f"chk_{i}"): sel_ids.append(i)
            with col2.expander(f"👤 {r.get('nome','-')} | {r.get('telefone','-')}"):
                c_a, c_b = st.columns(2)
                with c_a:
                    st.write(f"💍 **Cônjuge:** {r.get('conjuge','-')}")
                    st.write(f"🌳 **Pai/Mãe:** {r.get('ascendente','-')}")
                    st.write(f"📞 {r.get('telefone','-')}")
                with c_b:
                    rua, n_rua, bai = r.get('rua',''), r.get('num',''), r.get('bairro','')
                    st.write(f"🏠 {rua}, {n_rua} - {bai}")
                    st.write(f"📍 CEP: {r.get('cep','-')}")
                    # BOTÕES DE LINK
                    t_l = limpar(r.get('telefone',''))
                    c_z, c_m = st.columns(2)
                    if len(t_l) >= 10: c_z.link_button("💬 WhatsApp", f"https://wa.me/55{t_l}")
                    if rua:
                        q_map = quote(f"{rua}, {n_rua}, {bai}")
                        c_m.link_button("📍 Google Maps", f"https://www.google.com/maps/search/?api=1&query={q_map}")

        if sel_ids:
            pdf = gerar_pdf(df_m.loc[sel_ids])
            c_topo.download_button("📥 BAIXAR PDF DOS SELECIONADOS", pdf, "familia.pdf")

    # --- TAB 2: ANIVERSÁRIOS ---
    with tabs[1]:
        m_at = datetime.now().month
        st.subheader(f"🎂 Aniversariantes de {MESES[m_at]}")
        for _, r in df_m.iterrows():
            data = str(r.get('nascimento',''))
            if f"/{m_at:02d}/" in data: st.info(f"🎈 **{data[:5]}** - {r['nome']}")

    # --- TAB 3: MURAL (COM GESTÃO COMPLETA) ---
    with tabs[2]:
        st.subheader("📢 Mural de Avisos")
        av = [df_todo.iloc[0].get('email',''), df_todo.iloc[0].get('rua',''), df_todo.iloc[0].get('num','')]
        cols = st.columns(3)
        for i in range(3): 
            with cols[i]: st.warning(f"**Aviso {i+1}**\n\n{av[i]}")
        
        st.divider()
        st.subheader("📝 Publicar ou Editar Avisos")
        with st.form("mural_form"):
            n_v1 = st.text_input("Aviso 1", value=av[0])
            n_v2 = st.text_input("Aviso 2", value=av[1])
            n_v3 = st.text_input("Aviso 3", value=av[2])
            c_b1, c_b2 = st.columns(2)
            if c_b1.form_submit_button("💾 Salvar Avisos"):
                requests.post(WEBAPP_URL, json={"action":"edit", "row":2, "data":["AVISO","","","",n_v1, n_v2, n_v3, "","",""]})
                st.success("Mural atualizado!"); st.rerun()
            if c_b2.form_submit_button("🗑️ Limpar Mural"):
                requests.post(WEBAPP_URL, json={"action":"edit", "row":2, "data":["AVISO","","","", "Vazio", "Vazio", "Vazio", "","",""]})
                st.rerun()

    # --- TAB 4: CADASTRAR (LAYOUT 2 COLUNAS) ---
    with tabs[3]:
        st.subheader("➕ Novo Cadastro")
        with st.form("cad_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                f_n, f_d, f_t = st.text_input("Nome Completo"), st.text_input("Nascimento (DDMMAAAA)"), st.text_input("Telefone")
                f_v = st.radio("Vínculo", ["Filho(a) de", "Cônjuge de"], horizontal=True)
                f_ref = st.selectbox("Pessoa de Referência", ["Raiz"] + nomes_lista)
            with c2:
                f_e, f_ru, f_nu, f_ba, f_ce = st.text_input("E-mail"), st.text_input("Rua"), st.text_input("Nº"), st.text_input("Bairro"), st.text_input("CEP")
            if st.form_submit_button("💾 SALVAR"):
                v_f = f"{f_v} {f_ref}" if f_ref != "Raiz" else "Raiz"
                c_f = f_ref if "Cônjuge" in f_v else ""
                requests.post(WEBAPP_URL, json={"action":"append", "data":[f_n, mask_data(f_d), v_f, mask_tel(f_t), f_e, f_ru, f_nu, c_f, f_ba, f_ce]})
                st.success("Cadastrado!"); st.rerun()

    # --- TAB 5: GERENCIAR (EDIÇÃO COMPLETA) ---
    with tabs[4]:
        esc = st.selectbox("Escolha o membro", ["--"] + nomes_lista)
        if esc != "--":
            m = df_m[df_m['nome'] == esc].iloc[0]
            idx = df_m.index[df_m['nome'] == esc].tolist()[0] + 2
            with st.form("edit_form"):
                c1, c2 = st.columns(2)
                with c1:
                    e_n, e_t, e_c = st.text_input("Nasc", m.get('nascimento','')), st.text_input("Tel", m.get('telefone','')), st.text_input("Cônjuge", m.get('conjuge',''))
                    e_e = st.text_input("E-mail", m.get('email',''))
                with c2:
                    e_r, e_nu, e_b, e_ce = st.text_input("Rua", m.get('rua','')), st.text_input("Nº", m.get('num','')), st.text_input("Bairro", m.get('bairro','')), st.text_input("CEP", m.get('cep',''))
                if st.form_submit_button("💾 ATUALIZAR"):
                    requests.post(WEBAPP_URL, json={"action":"edit", "row":idx, "data":[esc, mask_data(e_n), m.get('ascendente',''), mask_tel(e_t), e_e, e_r, e_nu, e_c, e_b, e_ce]})
