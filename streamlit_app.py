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

MESES_BR = ["", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

# --- FUNÇÕES DE TRATAMENTO ---
def limpar(v): return re.sub(r'\D', '', str(v))

def aplicar_mask_tel(v):
    n = limpar(v)
    if len(n) >= 11: return f"({n[:2]}) {n[2:7]}-{n[7:11]}"
    if len(n) == 10: return f"({n[:2]}) {n[2:6]}-{n[6:10]}"
    return v

def aplicar_mask_data(v):
    n = limpar(v)
    if len(n) == 8: return f"{n[:2]}/{n[2:4]}/{n[4:8]}"
    return v

def gerar_pdf(dados):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(200, 10, "Relatório Família Buscapé", ln=True, align="C")
    for _, r in dados.iterrows():
        pdf.set_font("Arial", "B", 11)
        pdf.cell(0, 8, f"Nome: {r.get('nome','-')}", ln=True)
        pdf.set_font("Arial", size=10)
        pdf.cell(0, 6, f"Nasc: {r.get('nascimento','-')} | Tel: {r.get('telefone','-')} | E-mail: {r.get('email','-')}", ln=True)
        pdf.cell(0, 6, f"End: {r.get('rua','-')}, {r.get('num','-')} - {r.get('bairro','-')} CEP: {r.get('cep','-')}", ln=True)
        pdf.ln(4); pdf.line(10, pdf.get_y(), 200, pdf.get_y()); pdf.ln(4)
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
        try:
            df = pd.read_csv(CSV_URL, dtype=str).fillna("")
            df.columns = [c.strip().lower() for c in df.columns]
            return df
        except: return pd.DataFrame()

    df_todo = carregar()
    df_m = df_todo[df_todo['nome'].str.strip() != ""].sort_values(by='nome').copy()
    nomes_lista = df_m['nome'].tolist()

    # --- SIDEBAR (NOTIFICAÇÕES) ---
    with st.sidebar:
        st.title("🔔 Notificações")
        hoje = datetime.now().strftime("%d/%m")
        niver_hoje = [r['nome'] for _, r in df_m.iterrows() if str(r.get('nascimento','')).startswith(hoje)]
        if niver_hoje:
            for n in niver_hoje: st.success(f"🎂 Hoje: {n}")
        else:
            st.info("Sem notificações hoje") # Voltei com a frase que você gosta!
        st.divider()

    st.title("🌳 Família Buscapé")
    tabs = st.tabs(["🔍 Membros", "🎂 Aniversários", "📢 Mural", "➕ Cadastrar", "✏️ Gerenciar"])

    # --- TAB 1: MEMBROS ---
    with tabs[0]:
        sel_ids = []
        c_topo = st.container()
        for i, r in df_m.iterrows():
            c1, c2 = st.columns([0.2, 3.8])
            if c1.checkbox("", key=f"chk_{i}"): sel_ids.append(i)
            with c2.expander(f"👤 {r.get('nome','-')} | 📅 {r.get('nascimento','-')}"):
                col_i, col_l = st.columns([3, 1])
                with col_i:
                    st.write(f"💍 **Cônjuge:** {r.get('conjuge','-')}")
                    st.write(f"📞 **Tel:** {r.get('telefone','-')} | 🌳 **Vínculo:** {r.get('ascendente','-')}")
                    st.write(f"🏠 {r.get('rua','-')}, {r.get('num','-')} - {r.get('bairro','-')} (CEP: {r.get('cep','-')})")
                    st.write(f"✉️ **E-mail:** {r.get('email','-')}")
                with col_l:
                    t_l = limpar(r.get('telefone',''))
                    if len(t_l) >= 10:
                        st.link_button("💬 WhatsApp", f"https://wa.me/55{t_l}")
                        st.link_button("📞 Ligar", f"tel:{t_l}")
                    if r.get('rua'):
                        end_full = quote(f"{r['rua']}, {r['num']}, {r['bairro']}, {r['cep']}")
                        st.link_button("📍 Ver Mapa", f"https://www.google.com/maps/search/?api=1&query={end_full}")

        if sel_ids:
            pdf = gerar_pdf(df_m.loc[sel_ids])
            c_topo.download_button("📥 BAIXAR PDF SELECIONADOS", pdf, "familia.pdf")

    # --- TAB 2: ANIVERSÁRIOS ---
    with tabs[1]:
        m_at = datetime.now().month
        st.subheader(f"🎂 Aniversariantes de {MESES_BR[m_at]}")
        encontrou = False
        for _, r in df_m.iterrows():
            d = str(r.get('nascimento',''))
            # Ajuste para identificar o mês em formatos DD/MM/AAAA ou DDMMAAAA
            if f"/{m_at:02d}/" in d or (len(limpar(d))>=4 and limpar(d)[2:4] == f"{m_at:02d}"):
                st.info(f"🎈 Dia {d[:2]} - {r['nome']}")
                encontrou = True
        if not encontrou: st.write("Nenhum aniversariante este mês.")

    # --- TAB 3: MURAL ---
    with tabs[2]:
        st.subheader("📢 Mural de Avisos")
        avs = [df_todo.iloc[0].get('email','Vazio'), df_todo.iloc[0].get('rua','Vazio'), df_todo.iloc[0].get('num','Vazio')]
        cols = st.columns(3)
        for i in range(3): cols[i].warning(f"**Aviso {i+1}**\n\n{avs[i]}")
        st.divider()
        with st.form("mural_admin"):
            v1, v2, v3 = st.text_input("Aviso 1", avs[0]), st.text_input("Aviso 2", avs[1]), st.text_input("Aviso 3", avs[2])
            if st.form_submit_button("💾 Salvar Avisos"):
                requests.post(WEBAPP_URL, json={"action":"edit", "row":2, "data":["AVISO","","","",v1, v2, v3, "","",""]})
                st.rerun()

    # --- TAB 4: CADASTRAR ---
    with tabs[3]:
        with st.form("f_cad", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                n, d, t = st.text_input("Nome Completo"), st.text_input("Nasc (DDMMAAAA)"), st.text_input("Telefone")
                v = st.radio("Vínculo", ["Filho(a) de", "Cônjuge de"], horizontal=True)
                ref = st.selectbox("Pessoa de Referência", ["Raiz"] + nomes_lista)
            with c2:
                mail, ru, nu, ba, ce = st.text_input("E-mail"), st.text_input("Rua"), st.text_input("Nº"), st.text_input("Bairro"), st.text_input("CEP")
            if st.form_submit_button("💾 SALVAR CADASTRO"):
                vinc = f"{v} {ref}" if ref != "Raiz" else "Raiz"
                cj = ref if "Cônjuge" in v else ""
                requests.post(WEBAPP_URL, json={"action":"append", "data":[n, aplicar_mask_data(d), vinc, aplicar_mask_tel(t), mail, ru, nu, cj, ba, ce]})
                st.success("Salvo!"); st.rerun()

    # --- TAB 5: GERENCIAR (LAYOUT ESPELHADO) ---
    with tabs[4]:
        escolha = st.selectbox("Selecione para editar", ["--"] + nomes_lista)
        if escolha != "--":
            m = df_m[df_m['nome'] == escolha].iloc[0]
            idx = df_m.index[df_m['nome'] == escolha].tolist()[0] + 2
            with st.form("f_geren"):
                c1, c2 = st.columns(2)
                with c1:
                    e_n = st.text_input("Nome", value=m.get('nome',''), disabled=True)
                    e_d = st.text_input("Nascimento", m.get('nascimento',''))
                    e_t = st.text_input("Telefone", m.get('telefone',''))
                    e_v = st.text_input("Vínculo", m.get('ascendente',''))
                    e_cj = st.selectbox("Cônjuge", [""] + nomes_lista, index=nomes_lista.index(m.get('conjuge',''))+1 if m.get('conjuge','') in nomes_lista else 0)
                with c2:
                    e_e = st.text_input("E-mail", m.get('email',''))
                    e_ru = st.text_input("Rua", m.get('rua',''))
                    e_nu = st.text_input("Nº", m.get('num',''))
                    e_ba = st.text_input("Bairro", m.get('bairro',''))
                    e_ce = st.text_input("CEP", m.get('cep',''))
                if st.form_submit_button("💾 ATUALIZAR"):
                    requests.post(WEBAPP_URL, json={"action":"edit", "row":idx, "data":[escolha, aplicar_mask_data(e_d), e_v, aplicar_mask_tel(e_t), e_e, e_ru, e_nu, e_cj, e_ba, e_ce]})
                    st.success("Atualizado!"); st.rerun()
                if st.form_submit_button("🗑️ EXCLUIR"):
                    requests.post(WEBAPP_URL, json={"action":"edit", "row":idx, "data":[""]*10})
                    st.rerun()

    st.sidebar.button("🚪 Sair", on_click=lambda: st.session_state.update({"logado": False}))
