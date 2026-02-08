import streamlit as st
import pandas as pd
import requests
import re
import unicodedata
from urllib.parse import quote
from datetime import datetime
from fpdf import FPDF
import time

# 1. CONFIGURAÇÃO BÁSICA
st.set_page_config(page_title="Família Buscapé", page_icon="🌳", layout="wide")

# CONFIGURAÇÕES DE LINKS
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzWJ_nDGDe4a81O5BDx3meMbVJjlcMpJoxoO05lilysWJaj_udqeXqvfYFgzvWPlC-Omw/exec"
CSV_URL = "https://docs.google.com/spreadsheets/d/1jrtIP1lN644dPqY0HPGGwPWQGyYwb8nWsUigVK3QZio/export?format=csv"
MESES_BR = ["", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

def limpar(v): return re.sub(r'\D', '', str(v))
def mask_tel(v):
    n = limpar(str(v))[:11]
    if len(n) == 11: return f"({n[:2]}) {n[2:7]}-{n[7:11]}"
    if len(n) == 10: return f"({n[:2]}) {n[2:6]}-{n[6:10]}"
    return n if n else "-"

def mask_data(v):
    n = limpar(str(v))
    if len(n) == 8: return f"{n[:2]}/{n[2:4]}/{n[4:8]}"
    return v

# 2. LÓGICA DE LOGIN
if 'logado' not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.title("🌳 Portal Família Buscapé")
    psw = st.text_input("Digite a senha da família:", type="password")
    if st.button("ACESSAR PORTAL"):
        if psw == "buscape2026":
            st.session_state.logado = True
            st.rerun()
        else:
            st.error("Senha incorreta!")
else:
    # --- CARREGAR DADOS ---
    @st.cache_data(ttl=2)
    def carregar():
        try:
            df = pd.read_csv(CSV_URL, dtype=str).fillna("")
            def norm(t):
                t = t.strip().lower()
                return "".join(ch for ch in unicodedata.normalize('NFKD', t) if not unicodedata.combining(ch))
            df.columns = [norm(c) for c in df.columns]
            mapa = {'nome':'nome','nascimento':'nascimento','vinculo':'vinculo','ascendente':'vinculo','telefone':'telefone','email':'email','rua':'rua','num':'num','numero':'num','conjuge':'conjuge','conjugue':'conjuge','bairro':'bairro','cep':'cep'}
            return df.rename(columns=mapa)
        except:
            return pd.DataFrame()

    df_todo = carregar()
    df_m = df_todo[df_todo['nome'].str.strip() != ""].sort_values(by='nome').copy()
    nomes_lista = sorted([n.strip() for n in df_m['nome'].unique().tolist() if n.strip()])

    with st.sidebar:
        st.header("🎂 Notificações")
        hoje_dm = datetime.now().strftime("%d/%m")
        niver_hoje = [r['nome'] for _, r in df_m.iterrows() if str(r.get('nascimento','')).startswith(hoje_dm)]
        if niver_hoje:
            for n in niver_hoje: st.success(f"🎈 Hoje: {n}")
        else: st.info("Sem aniversários hoje.")
        st.divider()
        if st.button("🚪 Sair"):
            st.session_state.logado = False
            st.rerun()

    # --- ABAS ---
    st.title("🌳 Família Buscapé")
    t1, t2, t3, t4, t5, t6 = st.tabs(["Membros", "Aniversários", "Mural", "Cadastrar", "Gerenciar", "Árvore"])

    with t1: # MEMBROS
        for i, r in df_m.iterrows():
            nome_at = r.get('nome','').strip()
            with st.expander(f"👤 {nome_at}"):
                c_inf, c_btn = st.columns([3, 1])
                with c_inf:
                    st.write(f"📞 **Tel:** {mask_tel(r.get('telefone','-'))}")
                    st.write(f"🏠 {r.get('rua','-')}, {r.get('num','-')} - {r.get('bairro','-')} ({r.get('cep','-')})")
                    st.write(f"🌳 **Vínculo:** {r.get('vinculo','-')}")
                with c_btn:
                    tel_l = limpar(r.get('telefone',''))
                    if len(tel_l) >= 10: st.link_button("💬 Zap", f"https://wa.me/55{tel_l}")
                    if r.get('rua'): st.link_button("📍 Mapa", f"https://www.google.com/maps/search/?api=1&query={quote(f'{r.get('rua')},{r.get('num')}')}")

    with t2: # NIVER
        mes_f = datetime.now().month
        st.subheader(f"🎂 Aniversariantes de {MESES_BR[mes_f]}")
        for _, r in df_m.iterrows():
            d = str(r.get('nascimento',''))
            if "/" in d and int(d.split('/')[1]) == mes_f:
                st.info(f"🎈 Dia {d.split('/')[0]} - {r['nome']}")

    with t3: # MURAL
        try:
            m1 = df_todo.iloc[0].get('email','')
            m2 = df_todo.iloc[0].get('rua','')
            m3 = df_todo.iloc[0].get('num','')
        except: m1, m2, m3 = "","",""
        with st.form("fm"):
            n1 = st.text_input("Aviso 1", m1)
            n2 = st.text_input("Aviso 2", m2)
            n3 = st.text_input("Aviso 3", m3)
            if st.form_submit_button("💾 Salvar Mural"):
                requests.post(WEBAPP_URL, json={"action":"edit", "row":2, "data":["AVISO","","","",n1, n2, n3, "","",""]})
                st.rerun()

    with t4: # CADASTRAR
        st.subheader("➕ Novo Cadastro")
        with st.form("fc", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                nome_c = st.text_input("Nome Completo *")
                nasc_c = st.text_input("Nascimento (DDMMAAAA) *")
                tel_c = st.text_input("Telefone")
                vin_t = st.radio("Vínculo", ["Filho(a) de", "Cônjuge de"], horizontal=True)
                vin_r = st.selectbox("Referência", ["Raiz"] + nomes_lista)
            with col2:
                email_c = st.text_input("E-mail")
                rua_c = st.text_input("Rua")
                num_c = st.text_input("Número")
                bai_c = st.text_input("Bairro")
                cep_c = st.text_input("CEP")
            if st.form_submit_button("💾 Salvar Novo"):
                v_final = f"{vin_t} {vin_r}" if vin_r != "Raiz" else "Raiz"
                requests.post(WEBAPP_URL, json={"action":"append", "data":[nome_c, mask_data(nasc_c), v_final, mask_tel(tel_c), email_c, rua_c, num_c, vin_r if "Cônjuge" in vin_t else "", bai_c, cep_c]})
                st.rerun()

    with t5: # GERENCIAR (CONSERTADA)
        st.subheader("✏️ Editar ou Excluir Familiar")
        quem = st.selectbox("Escolha quem você quer alterar:", ["--"] + nomes_lista)
        if quem != "--":
            m_d = df_m[df_m['nome'] == quem].iloc[0]
            linha = df_todo.index[df_todo['nome'] == quem].tolist()[0] + 2
            
            with st.form("fe"):
                st.info(f"Alterando dados de: **{quem}**")
                c1, c2 = st.columns(2)
                with c1:
                    ed_nasc = st.text_input("Data de Nascimento", m_d.get('nascimento',''))
                    ed_tel = st.text_input("Telefone", m_d.get('telefone',''))
                    ed_email = st.text_input("E-mail", m_d.get('email',''))
                    ed_vinculo = st.text_input("Vínculo (Texto)", m_d.get('vinculo',''))
                with c2:
                    ed_rua = st.text_input("Rua", m_d.get('rua',''))
                    ed_num = st.text_input("Número", m_d.get('num',''))
                    ed_bai = st.text_input("Bairro", m_d.get('bairro',''))
                    ed_cep = st.text_input("CEP", m_d.get('cep',''))
                
                ed_conj = st.text_input("Cônjuge (Se houver)", m_d.get('conjuge',''))
                
                b_edit, b_del = st.columns(2)
                if b_edit.form_submit_button("💾 ATUALIZAR DADOS"):
                    dados_editados = [quem, ed_nasc, ed_vinculo, ed_tel, ed_email, ed_rua, ed_num, ed_conj, ed_bai, ed_cep]
                    requests.post(WEBAPP_URL, json={"action":"edit", "row":linha, "data":dados_editados})
                    st.success("Dados atualizados com sucesso!")
                    time.sleep(1)
                    st.rerun()
                
                if b_del.form_submit_button("🗑️ EXCLUIR DEFINITIVAMENTE"):
                    requests.post(WEBAPP_URL, json={"action":"edit", "row":linha, "data":[""]*10})
                    st.warning("Membro excluído.")
                    time.sleep(1)
                    st.rerun()

    with t6: # ARVORE
        st.subheader("🌳 Nossa Árvore")
        dot = 'digraph G { rankdir=LR; node [shape=box, style=filled, fillcolor="#E1F5FE", fontname="Arial"];'
        for _, row in df_m.iterrows():
            n, v = row['nome'].strip(), row['vinculo'].strip()
            if v != "Raiz":
                ref = v.split(" de ")[-1] if " de " in v else v
                dot += f'"{ref}" -> "{n}";'
            else: dot += f'"{n}" [fillcolor="#C8E6C9"];'
        st.graphviz_chart(dot + '}')
