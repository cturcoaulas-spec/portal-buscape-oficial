import streamlit as st
import pandas as pd
import requests
import re
import time
from urllib.parse import quote
from datetime import datetime
from fpdf import FPDF

# 1. CONFIGURAÇÃO (NÃO MEXER)
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
            # FORÇAR NOMES DE COLUNAS POR POSIÇÃO PARA EVITAR KEYERROR
            df.columns = ['nome', 'nascimento', 'vinculo', 'telefone', 'email', 'rua', 'num', 'conjuge', 'bairro', 'cep']
            return df
        except: return pd.DataFrame()

    df_todo = carregar()
    df_m = df_todo[df_todo['nome'].str.strip() != ""].sort_values(by='nome').copy()
    nomes_lista = sorted([n.strip() for n in df_m['nome'].unique().tolist() if n.strip()])

    # --- SIDEBAR ---
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

    # --- TAB 1: MEMBROS (CORREÇÃO DE RECIPROCIDADE E ÍCONES) ---
    with tabs[0]:
        for i, r in df_m.iterrows():
            nome_at = r['nome'].strip()
            with st.expander(f"👤 {nome_at} | 🎂 {r['nascimento']}"):
                ci, cl = st.columns([3, 1])
                with ci:
                    # Lógica de Cônjuge: Se eu apontei alguém OU alguém me apontou
                    c_direto = str(r['conjuge']).strip()
                    quem_me_citou = df_m[df_m['conjuge'].str.strip() == nome_at]['nome'].tolist()
                    
                    if c_direto and c_direto.lower() != "nan":
                        st.write(f"💍 **Cônjuge:** {c_direto}")
                    elif quem_me_citou:
                        st.write(f"💍 **Cônjuge:** {quem_me_citou[0]}")
                    else:
                        st.write(f"❌ **Cônjuge:** Nenhum")
                    
                    # Vínculo detalhado (Filho de... etc)
                    st.write(f"📞 **Tel:** {r['telefone']} | 🌳 **Vínculo:** {r['vinculo']}")
                    st.write(f"🏠 {r['rua']}, {r['num']} - {r['bairro']} ({r['cep']})")
                    st.write(f"✉️ **E-mail:** {r['email']}")
                with cl:
                    t_c = limpar(r['telefone'])
                    if len(t_c) >= 10:
                        st.link_button("💬 WhatsApp", f"https://wa.me/55{t_c}")
                        st.link_button("📞 Ligar", f"tel:{t_c}")

    # --- TAB 2: ANIVERSÁRIOS (NÃO MEXER) ---
    with tabs[1]:
        m_at = datetime.now().month
        st.subheader(f"🎂 Aniversariantes de {MESES_BR[m_at]}")
        tem = False
        for _, r in df_m.iterrows():
            dt = str(r['nascimento'])
            if "/" in dt and int(dt.split('/')[1]) == m_at:
                st.info(f"🎈 Dia {dt.split('/')[0]} - {r['nome']}")
                tem = True
        if not tem: st.write("Nenhum aniversariante este mês.")

    # --- TAB 3: MURAL (RESTAURADA) ---
    with tabs[2]:
        st.subheader("📢 Mural de Avisos")
        try: avs = [df_todo.iloc[0]['email'], df_todo.iloc[0]['rua'], df_todo.iloc[0]['num']]
        except: avs = ["Vazio", "Vazio", "Vazio"]
        cols = st.columns(3)
        for idx in range(3): cols[idx].warning(f"**Aviso {idx+1}**\n\n{avs[idx]}")
        st.divider()
        with st.form("mural_save"):
            v1, v2, v3 = st.text_input("Aviso 1", avs[0]), st.text_input("Aviso 2", avs[1]), st.text_input("Aviso 3", avs[2])
            if st.form_submit_button("💾 Salvar Avisos"):
                requests.post(WEBAPP_URL, json={"action":"edit", "row":2, "data":["AVISO","","","",v1, v2, v3, "","",""]})
                st.success("✅ MURAL ATUALIZADO!"); time.sleep(2); st.rerun()

    # --- TAB 4: CADASTRAR (NÃO MEXER) ---
    with tabs[3]:
        with st.form("f_cad", clear_on_submit=True):
            ca, cb = st.columns(2)
            with ca:
                nc, dc, tc = st.text_input("Nome Completo *"), st.text_input("Nascimento (DDMMAAAA) *"), st.text_input("Telefone")
                vc = st.radio("Vínculo", ["Filho(a) de", "Cônjuge de"], horizontal=True)
                rc = st.selectbox("Referência *", ["Raiz"] + nomes_lista)
            with cb:
                mc = st.text_input("E-mail"), st.text_input("Rua"), st.text_input("Nº"), st.text_input("Bairro"), st.text_input("CEP")
            if st.form_submit_button("💾 SALVAR CADASTRO"):
                if nc.strip().lower() in [n.lower() for n in nomes_lista]: st.error("❌ Nome já existe!")
                elif not nc or not dc: st.error("⚠️ Nome e Nascimento obrigatórios!")
                else:
                    v_fin = f"{vc} {rc}" if rc != "Raiz" else "Raiz"
                    c_fin = rc if "Cônjuge" in vc else ""
                    requests.post(WEBAPP_URL, json={"action":"append", "data":[nc, mask_data(dc), v_fin, mask_tel(tc), mc[0], mc[1], mc[2], c_fin, mc[3], mc[4]]})
                    st.success("✅ CADASTRO REALIZADO COM SUCESSO!"); time.sleep(2); st.rerun()

    # --- TAB 5: GERENCIAR (NÃO MEXER) ---
    with tabs[4]:
        esc = st.selectbox("Selecione para editar", ["--"] + nomes_lista)
        if esc != "--":
            m = df_m[df_m['nome'] == esc].iloc[0]
            idx_pl = df_todo.index[df_todo['nome'] == esc].tolist()[0] + 2
            with st.form("f_ger"):
                c1, c2 = st.columns(2)
                with c1:
                    st.text_input("Nome", value=m['nome'], disabled=True)
                    ed, et = st.text_input("Nascimento *", value=m['nascimento']), st.text_input("Telefone", value=m['telefone'])
                    evt = st.radio("Vínculo", ["Filho(a) de", "Cônjuge de"], horizontal=True, index=1 if "Cônjuge" in m['vinculo'] else 0)
                    erf = st.selectbox("Referência *", ["Raiz"] + nomes_lista)
                with c2:
                    em, er, en = st.text_input("E-mail", m['email']), st.text_input("Rua", m['rua']), st.text_input("Nº", m['num'])
                    eb, ec = st.text_input("Bairro", m['bairro']), st.text_input("CEP", m['cep'])
                if st.form_submit_button("💾 ATUALIZAR"):
                    v_e = f"{evt} {erf}" if erf != "Raiz" else "Raiz"
                    c_e = erf if "Cônjuge" in evt else ""
                    requests.post(WEBAPP_URL, json={"action":"edit", "row":idx_pl, "data":[esc, mask_data(ed), v_e, mask_tel(et), em, er, en, c_e, eb, ec]})
                    st.success("✅ ATUALIZAÇÃO REALIZADA COM SUCESSO!"); time.sleep(2); st.rerun()
                if b_ex := st.form_submit_button("🗑️ EXCLUIR"):
                    requests.post(WEBAPP_URL, json={"action":"edit", "row":idx_pl, "data":[""]*10})
                    st.success("🗑️ EXCLUÍDO!"); time.sleep(2); st.rerun()
                
