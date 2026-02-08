import streamlit as st
import pd as pd
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

# CONFIGURAÇÕES DE LINKS (Google Sheets e Script)
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzWJ_nDGDe4a81O5BDx3meMbVJjlcMpJoxoO05lilysWJaj_udqeXqvfYFgzvWPlC-Omw/exec"
CSV_URL = "https://docs.google.com/spreadsheets/d/1jrtIP1lN644dPqY0HPGGwPWQGyYwb8nWsUigVK3QZio/export?format=csv"
MESES_BR = ["", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

# FUNÇÕES DE UTILIDADE
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

# 2. SISTEMA DE ACESSO
if 'logado' not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.title("🌳 Portal Família Buscapé")
    st.subheader("Bem-vinda de volta!")
    psw = st.text_input("Senha da Família", type="password")
    if st.button("ABRIR PORTAL"):
        if psw == "buscape2026":
            st.session_state.logado = True
            st.rerun()
        else:
            st.error("Senha incorreta!")
else:
    # --- CARREGAMENTO DE DADOS ---
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
        except: return pd.DataFrame()

    df_todo = carregar()
    df_m = df_todo[df_todo['nome'].str.strip() != ""].sort_values(by='nome').copy()
    nomes_lista = sorted([n.strip() for n in df_m['nome'].unique().tolist() if n.strip()])

    # --- MENU LATERAL ---
    with st.sidebar:
        st.header("🎂 Avisos")
        hoje_dm = datetime.now().strftime("%d/%m")
        niver_hoje = [r['nome'] for _, r in df_m.iterrows() if str(r.get('nascimento','')).startswith(hoje_dm)]
        if niver_hoje:
            for n in niver_hoje: st.success(f"🎈 Hoje: {n}")
        else: st.info("Sem aniversários hoje.")
        st.divider()
        if st.button("🚪 Sair do Portal"):
            st.session_state.logado = False
            st.rerun()

    # --- INTERFACE PRINCIPAL ---
    st.title("🌳 Família Buscapé")
    t1, t2, t3, t4, t5, t6 = st.tabs(["Membros", "Aniversários", "Mural", "Novo Cadastro", "Gerenciar", "Árvore"])

    with t1: # 🔍 MEMBROS
        st.write("Dados de contato e localização.")
        for i, r in df_m.iterrows():
            nome_at = r.get('nome','').strip()
            with st.expander(f"👤 {nome_at}"):
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.write(f"📞 **Tel:** {mask_tel(r.get('telefone','-'))}")
                    st.write(f"🏠 {r.get('rua','-')}, {r.get('num','-')} - {r.get('bairro','-')}")
                    st.write(f"🌳 **Vínculo:** {r.get('vinculo','-')}")
                with c2:
                    t_limpo = limpar(r.get('telefone',''))
                    if len(t_limpo) >= 10: st.link_button("💬 Zap", f"https://wa.me/55{t_limpo}")
                    if r.get('rua'): st.link_button("📍 Mapa", f"http://google.com/maps?q={quote(f'{r.get('rua')},{r.get('num')}')}")

    with t2: # 🎂 ANIVERSÁRIOS
        mes_atual = datetime.now().month
        st.subheader(f"🎂 Aniversariantes de {MESES_BR[mes_atual]}")
        for _, r in df_m.iterrows():
            d = str(r.get('nascimento',''))
            if "/" in d and int(d.split('/')[1]) == mes_atual:
                st.info(f"🎈 Dia {d.split('/')[0]} - {r['nome']}")

    with t3: # 📢 MURAL
        try:
            m1, m2, m3 = df_todo.iloc[0].get('email',''), df_todo.iloc[0].get('rua',''), df_todo.iloc[0].get('num','')
        except: m1, m2, m3 = "","",""
        with st.form("mural_f"):
            st.subheader("Avisos para a Família")
            n1 = st.text_input("Aviso 1", m1)
            n2 = st.text_input("Aviso 2", m2)
            n3 = st.text_input("Aviso 3", m3)
            if st.form_submit_button("💾 Salvar Avisos"):
                requests.post(WEBAPP_URL, json={"action":"edit", "row":2, "data":["AVISO","","","",n1, n2, n3, "","",""]})
                st.rerun()

    with t4: # ➕ NOVO CADASTRO
        st.subheader("Adicionar Novo Familiar")
        with st.form("cad_f", clear_on_submit=True):
            ca, cb = st.columns(2)
            with ca:
                nc = st.text_input("Nome Completo *")
                dc = st.text_input("Nascimento (DDMMAAAA) *")
                tc = st.text_input("Telefone")
                vt = st.radio("Vínculo", ["Filho(a) de", "Cônjuge de"], horizontal=True)
                vr = st.selectbox("Referência", ["Raiz"] + nomes_lista)
            with cb:
                ec = st.text_input("E-mail")
                rc = st.text_input("Rua")
                uc = st.text_input("Número")
                bc = st.text_input("Bairro")
                pc = st.text_input("CEP")
            if st.form_submit_button("💾 Salvar Membro"):
                v_final = f"{vt} {vr}" if vr != "Raiz" else "Raiz"
                requests.post(WEBAPP_URL, json={"action":"append", "data":[nc, mask_data(dc), v_final, mask_tel(tc), ec, rc, uc, vr if "Cônjuge" in vt else "", bc, pc]})
                st.rerun()

    with t5: # ✏️ GERENCIAR
        st.subheader("Editar Dados Existentes")
        escolha = st.selectbox("Selecione quem deseja editar", ["--"] + nomes_lista)
        if escolha != "--":
            detalhes = df_m[df_m['nome'] == escolha].iloc[0]
            idx = df_todo.index[df_todo['nome'] == escolha].tolist()[0] + 2
            with st.form("edit_f"):
                st.warning(f"Editando: {escolha}")
                c1, c2 = st.columns(2)
                with c1:
                    e_nasc = st.text_input("Nascimento", detalhes.get('nascimento',''))
                    e_tel = st.text_input("Telefone", detalhes.get('telefone',''))
                    e_email = st.text_input("E-mail", detalhes.get('email',''))
                    e_vinc = st.text_input("Vínculo", detalhes.get('vinculo',''))
                with c2:
                    e_rua = st.text_input("Rua", detalhes.get('rua',''))
                    e_num = st.text_input("Número", detalhes.get('num',''))
                    e_bai = st.text_input("Bairro", detalhes.get('bairro',''))
                    e_cep = st.text_input("CEP", detalhes.get('cep',''))
                
                e_conj = st.text_input("Cônjuge", detalhes.get('conjuge',''))
                
                b1, b2 = st.columns(2)
                if b1.form_submit_button("💾 ATUALIZAR"):
                    requests.post(WEBAPP_URL, json={"action":"edit", "row":idx, "data":[escolha, e_nasc, e_vinc, e_tel, e_email, e_rua, e_num, e_conj, e_bai, e_cep]})
                    st.success("Atualizado!")
                    time.sleep(1)
                    st.rerun()
                if b2.form_submit_button("🗑️ EXCLUIR"):
                    requests.post(WEBAPP_URL, json={"action":"edit", "row":idx, "data":[""]*10})
                    st.rerun()

    with t6: # 🌳 ÁRVORE
        st.subheader("Nossa Árvore Genealógica")
        dot = 'digraph G { rankdir=LR; node [shape=box, style=filled, fillcolor="#E1F5FE", fontname="Arial"];'
        for _, row in df_m.iterrows():
            n, v = row['nome'].strip(), row['vinculo'].strip()
            if v != "Raiz":
                ref = v.split(" de ")[-1] if " de " in v else v
                dot += f'"{ref}" -> "{n}";'
            else: dot += f'"{n}" [fillcolor="#C8E6C9"];'
        st.graphviz_chart(dot + '}')
