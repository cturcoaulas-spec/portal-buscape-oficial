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
    if len(n) == 11: return f"({n[:2]}) {n[2:7]}-{n[7:11]}"
    if len(n) == 10: return f"({n[:2]}) {n[2:6]}-{n[6:10]}"
    return v

def mask_data(v):
    n = limpar(v)
    if len(n) == 8: return f"{n[:2]}/{n[2:4]}/{n[4:8]}"
    return v

def gerar_pdf(dados):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(200, 10, "Relatório Família Buscapé", ln=True, align="C")
    pdf.ln(5)
    for _, r in dados.iterrows():
        pdf.set_font("Arial", "B", 11)
        pdf.cell(0, 8, f"Nome: {r.get('nome','-')}", ln=True)
        pdf.set_font("Arial", size=10)
        pdf.cell(0, 6, f"Nascimento: {r.get('nascimento','-')} | Tel: {r.get('telefone','-')}", ln=True)
        pdf.cell(0, 6, f"E-mail: {r.get('email','-')}", ln=True)
        end = f"{r.get('rua','-')}, {r.get('num','-')} - {r.get('bairro','-')} | CEP: {r.get('cep','-')}"
        pdf.cell(0, 6, f"Endereço: {end}", ln=True)
        pdf.ln(3); pdf.line(10, pdf.get_y(), 200, pdf.get_y()); pdf.ln(3)
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

    # SIDEBAR
    with st.sidebar:
        st.title("🔔 Notificações")
        hoje = datetime.now().strftime("%d/%m")
        niver_hoje = [r['nome'] for _, r in df_m.iterrows() if str(r.get('nascimento','')).startswith(hoje)]
        for n in niver_hoje: st.success(f"🎂 Hoje: {n}")
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
            with col2.expander(f"👤 {r.get('nome','-')} | 📅 {r.get('nascimento','-')}"):
                c_info, c_links = st.columns([3, 1])
                with c_info:
                    st.write(f"💍 **Cônjuge:** {r.get('conjuge','-')}")
                    st.write(f"📞 **Tel:** {r.get('telefone','-')} | 🌳 **Vínculo:** {r.get('ascendente','-')}")
                    st.write(f"🏠 {r.get('rua','-')}, {r.get('num','-')} - {r.get('bairro','-')} (CEP: {r.get('cep','-')})")
                    st.write(f"✉️ **E-mail:** {r.get('email','-')}")
                with c_links:
                    t_l = limpar(r.get('telefone',''))
                    if len(t_l) >= 10:
                        st.link_button("💬 WhatsApp", f"https://wa.me/55{t_l}")
                        st.link_button("📞 Ligar", f"tel:{t_l}")
                    if r.get('rua'):
                        end_mapa = quote(f"{r['rua']}, {r['num']}, {r['bairro']}, {r['cep']}")
                        st.link_button("📍 Ver Mapa", f"https://www.google.com/maps/search/?api=1&query={end_mapa}")

        if sel_ids:
            pdf = gerar_pdf(df_m.loc[sel_ids])
            c_topo.download_button("📥 BAIXAR PDF DOS SELECIONADOS", pdf, "familia_buscape.pdf")

    # --- TAB 3: MURAL ---
    with tabs[2]:
        st.subheader("📢 Mural de Avisos")
        # Usando a linha 2 para armazenar 3 avisos
        avs = [df_todo.iloc[0].get('email','Vazio'), df_todo.iloc[0].get('rua','Vazio'), df_todo.iloc[0].get('num','Vazio')]
        cols = st.columns(3)
        for i in range(3): cols[i].warning(f"**Aviso {i+1}**\n\n{avs[i]}")
        
        st.divider()
        with st.form("mural_gestao"):
            v1 = st.text_input("Aviso 1", value=avs[0])
            v2 = st.text_input("Aviso 2", value=avs[1])
            v3 = st.text_input("Aviso 3", value=avs[2])
            cb1, cb2 = st.columns(2)
            if cb1.form_submit_button("💾 Salvar Avisos"):
                requests.post(WEBAPP_URL, json={"action":"edit", "row":2, "data":["AVISO","","","",v1, v2, v3, "","",""]})
                st.success("Mural atualizado!"); st.rerun()
            if cb2.form_submit_button("🗑️ Limpar Mural"):
                requests.post(WEBAPP_URL, json={"action":"edit", "row":2, "data":["AVISO","","","", "Vazio", "Vazio", "Vazio", "","",""]})
                st.rerun()

    # --- TAB 4: CADASTRAR ---
    with tabs[3]:
        with st.form("cad_novo", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                f_n, f_d, f_t = st.text_input("Nome Completo"), st.text_input("Nasc (DDMMAAAA)"), st.text_input("Telefone")
                f_v = st.radio("Vínculo", ["Filho(a) de", "Cônjuge de"], horizontal=True)
                f_ref = st.selectbox("Referência", ["Raiz"] + nomes_lista)
            with c2:
                f_e, f_ru, f_nu, f_ba, f_ce = st.text_input("E-mail"), st.text_input("Rua"), st.text_input("Nº"), st.text_input("Bairro"), st.text_input("CEP")
            if st.form_submit_button("💾 SALVAR CADASTRO"):
                vinc = f"{f_v} {f_ref}" if f_ref != "Raiz" else "Raiz"
                conj = f_ref if "Cônjuge" in f_v else ""
                requests.post(WEBAPP_URL, json={"action":"append", "data":[f_n, mask_data(f_d), vinc, mask_tel(f_t), f_e, f_ru, f_nu, conj, f_ba, f_ce]})
                st.success("Salvo!"); st.rerun()

    # --- TAB 5: GERENCIAR ---
    with tabs[4]:
        esc = st.selectbox("Selecione para editar", ["--"] + nomes_lista)
        if esc != "--":
            m = df_m[df_m['nome'] == esc].iloc[0]
            idx = df_m.index[df_m['nome'] == esc].tolist()[0] + 2
            with st.form("edit_geren"):
                c1, c2 = st.columns(2)
                with c1:
                    e_n, e_d, e_t = st.text_input("Nome", value=esc, disabled=True), st.text_input("Nasc", m.get('nascimento','')), st.text_input("Tel", m.get('telefone',''))
                    e_v = st.text_input("Vínculo", m.get('ascendente',''))
                    e_conj = st.selectbox("Cônjuge", [""] + nomes_lista, index=nomes_lista.index(m.get('conjuge',''))+1 if m.get('conjuge','') in nomes_lista else 0)
                with c2:
                    e_e, e_ru, e_nu, e_ba, e_ce = st.text_input("E-mail", m.get('email','')), st.text_input("Rua", m.get('rua','')), st.text_input("Nº", m.get('num','')), st.text_input("Bairro", m.get('bairro','')), st.text_input("CEP", m.get('cep',''))
                
                b1, b2 = st.columns(2)
                if b1.form_submit_button("💾 ATUALIZAR"):
                    requests.post(WEBAPP_URL, json={"action":"edit", "row":idx, "data":[esc, mask_data(e_d), e_v, mask_tel(e_t), e_e, e_ru, e_nu, e_conj, e_ba, e_ce]})
                    st.success("Atualizado!"); st.rerun()
                if b2.form_submit_button("🗑️ EXCLUIR"):
                    requests.post(WEBAPP_URL, json={"action":"edit", "row":idx, "data":[""]*10})
                    st.rerun()

    st.sidebar.button("🚪 Sair", on_click=lambda: st.session_state.update({"logado": False}))
