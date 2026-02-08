import streamlit as st
import pandas as pd
import requests
import re
import time
from urllib.parse import quote
from datetime import datetime
from fpdf import FPDF

# CONFIGURAÇÃO
st.set_page_config(page_title="Família Buscapé", page_icon="🌳", layout="wide")

WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzWJ_nDGDe4a81O5BDx3meMbVJjlcMpJoxoO05lilysWJaj_udqeXqvfYFgzvWPlC-Omw/exec"
CSV_URL = "https://docs.google.com/spreadsheets/d/1jrtIP1lN644dPqY0HPGGwPWQGyYwb8nWsUigVK3QZio/export?format=csv"

MESES_BR = ["", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

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
    pdf.cell(200, 10, "Relatorio Familia Buscape", ln=True, align="C")
    for _, r in dados.iterrows():
        pdf.set_font("Arial", "B", 11)
        pdf.cell(0, 8, f"Nome: {r.get('nome','-')}", ln=True)
        pdf.set_font("Arial", size=10)
        pdf.cell(0, 6, f"Nasc: {r.get('nascimento','-')} | Tel: {r.get('telefone','-')}", ln=True)
        end = f"{r.get('rua','-')}, {r.get('num','-')} - {r.get('bairro','-')} | CEP: {r.get('cep','-')}"
        pdf.cell(0, 6, f"End: {end}", ln=True)
        pdf.ln(4); pdf.line(10, pdf.get_y(), 200, pdf.get_y()); pdf.ln(4)
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
    nomes_lista = sorted([n.strip() for n in df_m['nome'].unique().tolist() if n.strip()])

    with st.sidebar:
        st.title("🔔 Notificações")
        hoje = datetime.now().strftime("%d/%m")
        niver_hoje = [r['nome'] for _, r in df_m.iterrows() if str(r.get('nascimento','')).startswith(hoje)]
        if niver_hoje:
            for n in niver_hoje: st.success(f"🎂 Hoje: {n}")
        else: st.info("Sem notificações hoje")
        st.divider()
        st.button("🚪 Sair", on_click=lambda: st.session_state.update({"logado": False}))

    st.title("🌳 Família Buscapé")
    tabs = st.tabs(["🔍 Membros", "🎂 Aniversários", "📢 Mural", "➕ Cadastrar", "✏️ Gerenciar"])

    # --- TAB 1: MEMBROS ---
    with tabs[0]:
        sel_ids = []
        c_topo = st.container()
        for i, r in df_m.iterrows():
            col1, col2 = st.columns([0.2, 3.8])
            if col1.checkbox("", key=f"chk_{i}"): sel_ids.append(i)
            
            # Título Limpo com Bolo
            with col2.expander(f"👤 {r.get('nome','-')} | 🎂 {r.get('nascimento','-')}"):
                ci, cl = st.columns([3, 1])
                with ci:
                    # LÓGICA DO ÍCONE SOLICITADA
                    conj_val = str(r.get('conjuge','')).strip()
                    # Se for vazio ou "nan", mostra X. Se tiver nome, mostra Aliança.
                    if conj_val == "" or conj_val.lower() == "nan":
                        st.write(f"❌ **Cônjuge:** Nenhum")
                    else:
                        st.write(f"💍 **Cônjuge:** {conj_val}")
                    
                    st.write(f"📞 **Tel:** {r.get('telefone','-')} | 🌳 **Vínculo:** {r.get('ascendente','-')}")
                    st.write(f"🏠 {r.get('rua','-')}, {r.get('num','-')} - {r.get('bairro','-')} ({r.get('cep','-')})")
                    st.write(f"✉️ **E-mail:** {r.get('email','-')}")
                with cl:
                    t_c = limpar(r.get('telefone',''))
                    if len(t_c) >= 10:
                        st.link_button("💬 WhatsApp", f"https://wa.me/55{t_c}")
                        st.link_button("📞 Ligar", f"tel:{t_c}")
                    if r.get('rua'):
                        loc = quote(f"{r['rua']}, {r['num']}, {r['bairro']}, {r['cep']}")
                        st.link_button("📍 Mapa", f"https://www.google.com/maps/search/?api=1&query={loc}")

    # --- TAB 4: CADASTRAR ---
    with tabs[3]:
        st.subheader("➕ Novo Cadastro")
        with st.form("f_novo", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            with col_a:
                n_c = st.text_input("Nome Completo *")
                d_c = st.text_input("Nascimento (DDMMAAAA) *")
                t_c = st.text_input("Telefone (DDD + Número)")
                v_c = st.radio("Vínculo", ["Filho(a) de", "Cônjuge de"], horizontal=True)
                r_c = st.selectbox("Referência *", ["Raiz"] + nomes_lista)
            with col_b:
                m_c = st.text_input("E-mail")
                ru_c, nu_c = st.text_input("Rua"), st.text_input("Nº")
                ba_c, ce_c = st.text_input("Bairro"), st.text_input("CEP")
            
            if st.form_submit_button("💾 SALVAR CADASTRO"):
                # TRAVA DE DUPLICIDADE REFORÇADA
                if n_c.strip().lower() in [n.lower() for n in nomes_lista]:
                    st.error(f"❌ Erro: O nome '{n_c}' já está na base de dados!")
                elif not n_c or not d_c or not r_c:
                    st.error("⚠️ Nome, Nascimento e Referência são obrigatórios!")
                else:
                    fd, ft = mask_data(d_c), mask_tel(t_c)
                    vinc = f"{v_c} {r_c}" if r_c != "Raiz" else "Raiz"
                    conj = r_c if "Cônjuge" in v_c else ""
                    res = requests.post(WEBAPP_URL, json={"action":"append", "data":[n_c, fd, vinc, ft, m_c, ru_c, nu_c, conj, ba_c, ce_c]})
                    if res.status_code == 200:
                        st.success("✅ CADASTRO REALIZADO COM SUCESSO!")
                        time.sleep(2)
                        st.rerun()

    # --- TAB 5: GERENCIAR ---
    with tabs[4]:
        st.subheader("✏️ Editar ou Excluir")
        escolha = st.selectbox("Selecione para editar", ["--"] + nomes_lista)
        if escolha != "--":
            m = df_m[df_m['nome'] == escolha].iloc[0]
            idx_pl = df_todo.index[df_todo['nome'] == escolha].tolist()[0] + 2
            
            with st.form("f_edit_mirror"):
                col1, col2 = st.columns(2)
                with col1:
                    e_n = st.text_input("Nome Completo *", value=m.get('nome',''), disabled=True)
                    e_d = st.text_input("Nascimento (DDMMAAAA) *", value=m.get('nascimento',''))
                    e_t = st.text_input("Telefone (DDD + Número)", value=m.get('telefone',''))
                    idx_v = 1 if "Cônjuge" in m.get('ascendente','') else 0
                    e_v_t = st.radio("Vínculo", ["Filho(a) de", "Cônjuge de"], horizontal=True, index=idx_v)
                    ref_at = m.get('ascendente','').split(' de ')[-1] if ' de ' in m.get('ascendente','') else "Raiz"
                    idx_r = (nomes_lista.index(ref_at)+1) if ref_at in nomes_lista else 0
                    e_ref = st.selectbox("Referência *", ["Raiz"] + nomes_lista, index=idx_r)
                with col2:
                    e_m = st.text_input("E-mail", value=m.get('email',''))
                    e_ru = st.text_input("Rua", value=m.get('rua',''))
                    e_nu = st.text_input("Nº", value=m.get('num',''))
                    e_ba = st.text_input("Bairro", value=m.get('bairro',''))
                    e_ce = st.text_input("CEP", value=m.get('cep',''))
                
                b1, b2 = st.columns(2)
                if b1.form_submit_button("💾 ATUALIZAR DADOS"):
                    v_final = f"{e_v_t} {e_ref}" if e_ref != "Raiz" else "Raiz"
                    c_final = e_ref if "Cônjuge" in e_v_t else ""
                    requests.post(WEBAPP_URL, json={"action":"edit", "row":idx_pl, "data":[escolha, mask_data(e_d), v_final, mask_tel(e_t), e_m, e_ru, e_nu, c_final, e_ba, e_ce]})
                    st.success("✅ ATUALIZAÇÃO REALIZADA COM SUCESSO!")
                    time.sleep(2)
                    st.rerun()
                if b2.form_submit_button("🗑️ EXCLUIR"):
                    requests.post(WEBAPP_URL, json={"action":"edit", "row":idx_pl, "data":[""]*10})
                    st.success("🗑️ EXCLUÍDO COM SUCESSO!")
                    time.sleep(2)
                    st.rerun()
