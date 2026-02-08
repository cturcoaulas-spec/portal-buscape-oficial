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

# --- AUXILIARES ---
MESES = ["", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

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
        pdf.cell(0, 7, f"Tel: {r.get('telefone','-')} | Nasc: {r.get('nascimento','-')}", ln=True)
        pdf.cell(0, 7, f"End: {r.get('rua','-')}, {r.get('num','-')} - {r.get('bairro','-')}", ln=True)
        pdf.ln(5); pdf.line(10, pdf.get_y(), 200, pdf.get_y()); pdf.ln(5)
    return pdf.output(dest='S').encode('latin-1')

# --- LOGIN ---
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

    # --- NOTIFICAÇÕES (SIDEBAR) ---
    with st.sidebar:
        st.title("🔔 Notificações")
        hoje = datetime.now().strftime("%d/%m")
        niver_hoje = [r['nome'] for _, r in df_m.iterrows() if str(r.get('nascimento','')).startswith(hoje)]
        if niver_hoje:
            for n in niver_hoje: st.success(f"🎂 Aniversário Hoje: {n}")
        else: st.info("Nenhum aniversário hoje.")
        st.divider()

    st.title("🌳 Família Buscapé")
    tabs = st.tabs(["🔍 Membros", "🎂 Aniversários", "📢 Mural", "➕ Cadastrar", "✏️ Gerenciar"])

    # --- TAB 1: MEMBROS ---
    with tabs[0]:
        sel_ids = []
        c_topo = st.container()
        for i, r in df_m.iterrows():
            col1, col2 = st.columns([0.2, 3.8])
            if col1.checkbox("", key=f"chk_{i}"): sel_ids.append(i)
            with col2.expander(f"👤 {r.get('nome','-')} | {r.get('telefone','-')}"):
                st.write(f"📅 **Nasc:** {r.get('nascimento','-')} | 💍 **Cônjuge:** {r.get('conjuge','-')}")
                st.write(f"🏠 {r.get('rua','-')}, {r.get('num','-')} - {r.get('bairro','-')}")
                # BOTÕES WHATSAPP E MAPS
                t_l = limpar(r.get('telefone',''))
                c_z, c_m = st.columns(2)
                if len(t_l) >= 10: c_z.link_button("💬 WhatsApp", f"https://wa.me/55{t_l}")
                if r.get('rua'): 
                    q_m = quote(f"{r['rua']}, {r['num']}, {r['bairro']}")
                    c_m.link_button("📍 Google Maps", f"https://www.google.com/maps/search/?api=1&query={q_m}")

        if sel_ids:
            pdf = gerar_pdf(df_m.loc[sel_ids])
            c_topo.download_button("📥 BAIXAR PDF SELECIONADOS", pdf, "familia.pdf")
            st.sidebar.download_button("📥 Baixar PDF (Seleção)", pdf, "familia.pdf")

    # --- TAB 2: ANIVERSÁRIOS ---
    with tabs[1]:
        mes_atual = datetime.now().month
        st.subheader(f"🎂 Aniversariantes de {MESES[mes_atual]}")
        encontrou = False
        for _, r in df_m.iterrows():
            data = str(r.get('nascimento',''))
            if f"/{mes_atual:02d}/" in data:
                st.write(f"🎈 **{data[:5]}** - {r['nome']}")
                encontrou = True
        if not encontrou: st.write("Nenhum aniversariante neste mês.")

    # --- TAB 3: MURAL ---
    with tabs[2]:
        st.subheader("📢 Mural")
        av = [df_todo.iloc[0].get('email',''), df_todo.iloc[0].get('rua',''), df_todo.iloc[0].get('num','')]
        cols = st.columns(3)
        for i in range(3): cols[i].warning(f"**Aviso {i+1}**\n\n{av[i]}")

    # --- TAB 4: CADASTRAR ---
    with tabs[3]:
        with st.form("cad"):
            n, d, t = st.text_input("Nome"), st.text_input("Nasc (DDMMAAAA)"), st.text_input("Tel")
            r, nu, b, ce = st.text_input("Rua"), st.text_input("Nº"), st.text_input("Bairro"), st.text_input("CEP")
            if st.form_submit_button("SALVAR"):
                requests.post(WEBAPP_URL, json={"action":"append", "data":[n, mask_data(d), "Raiz", mask_tel(t), "", r, nu, "", b, ce]})
                st.success("Ok!"); st.rerun()

    # --- TAB 5: GERENCIAR (EDIÇÃO) ---
    with tabs[4]:
        esc = st.selectbox("Escolha o membro", ["--"] + nomes_lista)
        if esc != "--":
            m = df_m[df_m['nome'] == esc].iloc[0]
            idx = df_m.index[df_m['nome'] == esc].tolist()[0] + 2
            with st.form("edit"):
                e_n = st.text_input("Nascimento", m.get('nascimento',''))
                e_t = st.text_input("Telefone", m.get('telefone',''))
                e_r = st.text_input("Rua", m.get('rua',''))
                e_nu = st.text_input("Nº", m.get('num',''))
                e_b = st.text_input("Bairro", m.get('bairro',''))
                e_ce = st.text_input("CEP", m.get('cep',''))
                e_c = st.text_input("Cônjuge", m.get('conjuge',''))
                if st.form_submit_button("ATUALIZAR"):
                    requests.post(WEBAPP_URL, json={"action":"edit", "row":idx, "data":[esc, mask_data(e_n), m.get('ascendente',''), mask_tel(e_t), "", e_r, e_nu, e_c, e_b, e_ce]})
                    st.success("Atualizado!"); st.rerun()

    st.sidebar.button("Sair", on_click=lambda: st.session_state.update({"logado": False}))
