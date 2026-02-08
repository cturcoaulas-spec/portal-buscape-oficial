import streamlit as st
import pandas as pd
import requests
import re
import time
import unicodedata
from urllib.parse import quote
from datetime import datetime
from fpdf import FPDF

# 1. CONFIGURAÇÃO (NÃO MEXER)
st.set_page_config(page_title="Família Buscapé", page_icon="🌳", layout="wide")

WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzWJ_nDGDe4a81O5BDx3meMbVJjlcMpJoxoO05lilysWJaj_udqeXqvfYFgzvWPlC-Omw/exec"
CSV_URL = "https://docs.google.com/spreadsheets/d/1jrtIP1lN644dPqY0HPGGwPWQGyYwb8nWsUigVK3QZio/export?format=csv"

MESES_BR = ["", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

# --- FUNÇÕES DE SUPORTE ---
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

def normalizar_colunas(cols):
    # Função para tirar acentos dos nomes das colunas e evitar o KeyError
    novas = []
    for c in cols:
        c = c.strip().lower()
        c = "".join(ch for ch in unicodedata.normalize('NFKD', c) if not unicodedata.combining(ch))
        novas.append(c)
    return novas

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
            df.columns = normalizar_colunas(df.columns) # Resolve o KeyError
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

    # --- TAB 1: MEMBROS (CORREÇÃO DE ÍCONES E VÍNCULOS) ---
    with tabs[0]:
        for i, r in df_m.iterrows():
            nome_atual = r.get('nome','').strip()
            with st.expander(f"👤 {nome_atual} | 🎂 {r.get('nascimento','-')}"):
                ci, cl = st.columns([3, 1])
                with ci:
                    # Lógica de Reciprocidade: Quem tem este membro como cônjuge?
                    conj_direto = str(r.get('conjuge','')).strip()
                    quem_casou_comigo = df_m[df_m['conjuge'].str.strip() == nome_atual]['nome'].tolist()
                    
                    if conj_direto and conj_direto.lower() != "nan":
                        st.write(f"💍 **Cônjuge:** {conj_direto}")
                    elif quem_casou_comigo:
                        st.write(f"💍 **Cônjuge:** {quem_casou_comigo[0]}")
                    else:
                        st.write(f"❌ **Cônjuge:** Nenhum")
                    
                    # Vínculo: Exibe o que está na planilha (Filho(a) de... ou Cônjuge de...)
                    st.write(f"📞 **Tel:** {r.get('telefone','-')} | 🌳 **Vínculo:** {r.get('ascendente','-')}")
                    st.write(f"🏠 {r.get('rua','-')}, {r.get('num','-')} - {r.get('bairro','-')} ({r.get('cep','-')})")
                    st.write(f"✉️ **E-mail:** {r.get('email','-')}")
                with cl:
                    t_c = limpar(r.get('telefone',''))
                    if len(t_c) >= 10:
                        st.link_button("💬 WhatsApp", f"https://wa.me/55{t_c}")
                        st.link_button("📞 Ligar", f"tel:{t_c}")

    # --- TAB 2: ANIVERSÁRIOS (NÃO MEXER) ---
    with tabs[1]:
        m_at = datetime.now().month
        st.subheader(f"🎂 Aniversariantes de {MESES_BR[m_at]}")
        tem = False
        for _, r in df_m.iterrows():
            dt = str(r.get('nascimento',''))
            if "/" in dt and int(dt.split('/')[1]) == m_at:
                st.info(f"🎈 Dia {dt.split('/')[0]} - {r['nome']}")
                tem = True
        if not tem: st.write("Nenhum aniversariante este mês.")

    # --- TAB 3: MURAL (NÃO MEXER) ---
    with tabs[2]:
        st.subheader("📢 Mural de Avisos")
        try: avs = [df_todo.iloc[0].get('email','Vazio'), df_todo.iloc[0].get('rua','Vazio'), df_todo.iloc[0].get('num','Vazio')]
        except: avs = ["Vazio", "Vazio", "Vazio"]
        cols = st.columns(3)
        for idx in range(3): cols[idx].warning(f"**Aviso {idx+1}**\n\n{avs[idx]}")
        st.divider()
        with st.form("mural_gest"):
            v1, v2, v3 = st.text_input("Aviso 1", avs[0]), st.text_input("Aviso 2", avs[1]), st.text_input("Aviso 3", avs[2])
            if st.form_submit_button("💾 Salvar Avisos"):
                requests.post(WEBAPP_URL, json={"action":"edit", "row":2, "data":["AVISO","","","",v1, v2, v3, "","",""]})
                st.success("✅ MURAL ATUALIZADO!"); time.sleep(2); st.rerun()

    # --- TAB 4: CADASTRAR (NÃO MEXER) ---
    with tabs[3]:
        with st.form("f_cad_final", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            with col_a:
                n_c = st.text_input("Nome Completo *")
                d_c = st.text_input("Nascimento (DDMMAAAA) *")
                t_c = st.text_input("Telefone")
                v_c = st.radio("Vínculo", ["Filho(a) de", "Cônjuge de"], horizontal=True)
                r_c = st.selectbox("Referência *", ["Raiz"] + nomes_lista)
            with col_b:
                m_c = st.text_input("E-mail"), st.text_input("Rua"), st.text_input("Nº")
                ba_c, ce_c = st.text_input("Bairro"), st.text_input("CEP")
            if st.form_submit_button("💾 SALVAR CADASTRO"):
                if n_c.strip().lower() in [n.lower() for n in nomes_lista]: st.error("❌ Nome já existe!")
                elif not n_c or not d_c: st.error("⚠️ Preencha Nome e Nascimento!")
                else:
                    requests.post(WEBAPP_URL, json={"action":"append", "data":[n_c, mask_data(d_c), f"{v_c} {r_c}", mask_tel(t_c), m_c[0], m_c[1], m_c[2], r_c if "Cônjuge" in v_c else "", ba_c, ce_c]})
                    st.success("✅ CADASTRO REALIZADO COM SUCESSO!"); time.sleep(2); st.rerun()

    # --- TAB 5: GERENCIAR (NÃO MEXER) ---
    with tabs[4]:
        esc = st.selectbox("Selecione para editar", ["--"] + nomes_lista)
        if esc != "--":
            m = df_m[df_m['nome'] == esc].iloc[0]
            idx_pl = df_todo.index[df_todo['nome'] == esc].tolist()[0] + 2
            with st.form("f_ger_final"):
                c1, c2 = st.columns(2)
                with c1:
                    st.text_input("Nome", value=m.get('nome',''), disabled=True)
                    e_d, e_t = st.text_input("Nasc (DDMMAAAA) *", value=m.get('nascimento','')), st.text_input("Tel", value=m.get('telefone',''))
                    e_v_t = st.radio("Vínculo", ["Filho(a) de", "Cônjuge de"], horizontal=True, index=1 if "Cônjuge" in m.get('ascendente','') else 0)
                    e_ref = st.selectbox("Referência *", ["Raiz"] + nomes_lista)
                with c2:
                    e_m, e_ru, e_nu = st.text_input("E-mail", m.get('email','')), st.text_input("Rua", m.get('rua','')), st.text_input("Nº", m.get('num',''))
                    e_ba, e_ce = st.text_input("Bairro", m.get('bairro','')), st.text_input("CEP", m.get('cep',''))
                if st.form_submit_button("💾 ATUALIZAR"):
                    requests.post(WEBAPP_URL, json={"action":"edit", "row":idx_pl, "data":[esc, mask_data(e_d), f"{e_v_t} {e_ref}", mask_tel(e_t), e_m, e_ru, e_nu, e_ref if "Cônjuge" in e_v_t else "", e_ba, e_ce]})
                    st.success("✅ ATUALIZAÇÃO REALIZADA COM SUCESSO!"); time.sleep(2); st.rerun()
                if st.form_submit_button("🗑️ EXCLUIR"):
                    requests.post(WEBAPP_URL, json={"action":"edit", "row":idx_pl, "data":[""]*10})
                    st.success("🗑️ EXCLUÍDO!"); time.sleep(2); st.rerun()
