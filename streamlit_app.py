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
    nomes_lista = sorted([n.strip() for n in df_m['nome'].unique().tolist() if n.strip()])

    with st.sidebar:
        st.title("🔔 Notificações")
        hoje_dm = datetime.now().strftime("%d/%m")
        niver_hoje = [r['nome'] for _, r in df_m.iterrows() if str(r.get('nascimento','')).startswith(hoje_dm)]
        if niver_hoje:
            for n in niver_hoje: st.success(f"🎂 Hoje: {n}")
        else: st.info("Sem notificações hoje")
        st.divider()
        st.button("🚪 Sair", on_click=lambda: st.session_state.update({"logado": False}))

    st.title("🌳 Família Buscapé")
    tabs = st.tabs(["🔍 Membros", "🎂 Aniversários", "📢 Mural", "➕ Cadastrar", "✏️ Gerenciar"])

    # --- TAB 1: MEMBROS ---
    with tabs[0]:
        for i, r in df_m.iterrows():
            with st.expander(f"👤 {r.get('nome','-')} | 🎂 {r.get('nascimento','-')}"):
                ci, cl = st.columns([3, 1])
                with ci:
                    # LÓGICA CORRIGIDA: Verifica se é cônjuge pelo vínculo OU pelo campo cônjuge
                    vinc_texto = str(r.get('ascendente',''))
                    conj_val = str(r.get('conjuge','')).strip()
                    
                    if "Cônjuge" in vinc_texto or (conj_val != "" and conj_val.lower() != "nan"):
                        st.write(f"💍 **Cônjuge:** {conj_val if conj_val else 'Informado no Vínculo'}")
                    else:
                        st.write(f"❌ **Cônjuge:** Nenhum")
                    
                    st.write(f"📞 **Tel:** {r.get('telefone','-')} | 🌳 **Vínculo:** {vinc_texto}")
                    st.write(f"🏠 {r.get('rua','-')}, {r.get('num','-')} - {r.get('bairro','-')} ({r.get('cep','-')})")
                    st.write(f"✉️ **E-mail:** {r.get('email','-')}")
                with cl:
                    t_c = limpar(r.get('telefone',''))
                    if len(t_c) >= 10:
                        st.link_button("💬 WhatsApp", f"https://wa.me/55{t_c}")
                        st.link_button("📞 Ligar", f"tel:{t_c}")

    # --- TAB 2: ANIVERSÁRIOS ---
    with tabs[1]:
        m_atual = datetime.now().month
        st.subheader(f"🎂 Aniversariantes de {MESES_BR[m_atual]}")
        tem_niver = False
        for _, r in df_m.iterrows():
            dt = str(r.get('nascimento',''))
            if "/" in dt:
                partes = dt.split('/')
                if len(partes) >= 2 and int(partes[1]) == m_atual:
                    st.info(f"🎈 Dia {partes[0]} - {r['nome']}")
                    tem_niver = True
        if not tem_niver: st.write("Nenhum aniversariante este mês.")

    # --- TAB 4: CADASTRAR ---
    with tabs[3]:
        with st.form("f_novo", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            with col_a:
                n_c = st.text_input("Nome Completo *")
                d_c = st.text_input("Nascimento (DDMMAAAA) *")
                t_c = st.text_input("Telefone (DDD + Número)")
                v_c = st.radio("Vínculo", ["Filho(a) de", "Cônjuge de"], horizontal=True)
                r_c = st.selectbox("Referência *", ["Raiz"] + nomes_lista)
            with col_b:
                m_c = st.text_input("E-mail"), st.text_input("Rua"), st.text_input("Nº")
                ba_c, ce_c = st.text_input("Bairro"), st.text_input("CEP")
            
            if st.form_submit_button("💾 SALVAR CADASTRO"):
                if n_c.strip().lower() in [n.lower() for n in nomes_lista]:
                    st.error("❌ Este nome já existe!")
                elif not n_c or not d_c:
                    st.error("⚠️ Preencha Nome e Nascimento!")
                else:
                    fd, ft = mask_data(d_c), mask_tel(t_c)
                    vinc = f"{v_c} {r_c}" if r_c != "Raiz" else "Raiz"
                    conj = r_c if "Cônjuge" in v_c else ""
                    requests.post(WEBAPP_URL, json={"action":"append", "data":[n_c, fd, vinc, ft, m_c[0], m_c[1], m_c[2], conj, ba_c, ce_c]})
                    st.success("✅ CADASTRO REALIZADO COM SUCESSO!")
                    time.sleep(2); st.rerun()

    # --- TAB 5: GERENCIAR ---
    with tabs[4]:
        escolha = st.selectbox("Selecione para editar", ["--"] + nomes_lista)
        if escolha != "--":
            m = df_m[df_m['nome'] == escolha].iloc[0]
            idx_pl = df_todo.index[df_todo['nome'] == escolha].tolist()[0] + 2
            with st.form("f_edit_geren"):
                col1, col2 = st.columns(2)
                with col1:
                    e_n = st.text_input("Nome", value=m.get('nome',''), disabled=True)
                    e_d = st.text_input("Nascimento (DDMMAAAA) *", value=m.get('nascimento',''))
                    e_t = st.text_input("Telefone", value=m.get('telefone',''))
                    idx_v = 1 if "Cônjuge" in m.get('ascendente','') else 0
                    e_v_t = st.radio("Vínculo", ["Filho(a) de", "Cônjuge de"], horizontal=True, index=idx_v)
                    ref_at = m.get('ascendente','').split(' de ')[-1] if ' de ' in m.get('ascendente','') else "Raiz"
                    idx_r = (nomes_lista.index(ref_at)+1) if ref_at in nomes_lista else 0
                    e_ref = st.selectbox("Referência *", ["Raiz"] + nomes_lista, index=idx_r)
                with col2:
                    e_m, e_ru, e_nu = st.text_input("E-mail", m.get('email','')), st.text_input("Rua", m.get('rua','')), st.text_input("Nº", m.get('num',''))
                    e_ba, e_ce = st.text_input("Bairro", m.get('bairro','')), st.text_input("CEP", m.get('cep',''))
                if st.form_submit_button("💾 ATUALIZAR"):
                    v_e = f"{e_v_t} {e_ref}" if e_ref != "Raiz" else "Raiz"
                    c_e = e_ref if "Cônjuge" in e_v_t else ""
                    requests.post(WEBAPP_URL, json={"action":"edit", "row":idx_pl, "data":[escolha, mask_data(e_d), v_e, mask_tel(e_t), e_m, e_ru, e_nu, c_e, e_ba, e_ce]})
                    st.success("✅ ATUALIZAÇÃO REALIZADA COM SUCESSO!")
                    time.sleep(2); st.rerun()
                if st.form_submit_button("🗑️ EXCLUIR"):
                    requests.post(WEBAPP_URL, json={"action":"edit", "row":idx_pl, "data":[""]*10})
                    st.success("🗑️ EXCLUÍDO COM SUCESSO!"); time.sleep(2); st.rerun()
