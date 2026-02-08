import streamlit as st
import pandas as pd
import requests
import re
from urllib.parse import quote
from datetime import datetime
from fpdf import FPDF

# CONFIGURAÇÃO
st.set_page_config(page_title="Portal Família Buscapé", page_icon="🌳", layout="wide")

WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzWJ_nDGDe4a81O5BDx3meMbVJjlcMpJoxoO05lilysWJaj_udqeXqvfYFgzvWPlC-Omw/exec"
CSV_URL = "https://docs.google.com/spreadsheets/d/1jrtIP1lN644dPqY0HPGGwPWQGyYwb8nWsUigVK3QZio/export?format=csv"

# --- FUNÇÕES ---
def limpar_numero(v): return re.sub(r'\D', '', str(v))

def aplicar_mascara_tel(v):
    n = limpar_numero(v)
    return f"({n[:2]}) {n[2:7]}-{n[7:]}" if len(n) == 11 else v

def aplicar_mascara_data(v):
    n = limpar_numero(v)
    return f"{n[:2]}/{n[2:4]}/{n[4:]}" if len(n) == 8 else v

# --- LOGIN ---
if 'logado' not in st.session_state: st.session_state.logado = False
if not st.session_state.logado:
    st.title("🌳 Portal Família Buscapé")
    senha = st.text_input("Senha", type="password")
    if st.button("ENTRAR"):
        if senha == "buscape2026":
            st.session_state.logado = True
            st.rerun()
        else: st.error("Senha incorreta.")
else:
    @st.cache_data(ttl=2)
    def carregar():
        try:
            df = pd.read_csv(CSV_URL, dtype=str).fillna("")
            df.columns = [c.strip().lower() for c in df.columns]
            return df
        except: return pd.DataFrame()

    df = carregar()
    lista_nomes = sorted(df['nome'].tolist()) if not df.empty else []

    st.title("🌳 Portal Família Buscapé")
    t1, t2, t3, t4 = st.tabs(["🔍 Membros", "🎂 Aniversários", "➕ Cadastrar", "✏️ Editar"])

    # --- TAB 1: MEMBROS ---
    with t1:
        st.subheader("Membros da Família")
        if not df.empty:
            for i, r in df.iterrows():
                label = f"👤 {r['nome']} | 📅 {r['nascimento']} | 📞 {r['telefone']}"
                with st.expander(label):
                    c1, c2, c3 = st.columns([2, 2, 1])
                    with c1:
                        st.write(f"**Ascendente:** {r['ascendente']}")
                        st.write(f"**E-mail:** {r['email']}")
                    with c2:
                        if r['rua']:
                            st.write(f"🏠 {r['rua']}, {r['num']} - {r['bairro']}")
                            link_maps = f"https://www.google.com/maps/search/?api=1&query={quote(f'{r['rua']}, {r['num']}, Brazil')}"
                            st.link_button("📍 Abrir no Maps", link_maps)
                    with c3:
                        tel_puro = limpar_numero(r['telefone'])
                        if len(tel_puro) >= 10:
                            st.link_button("💬 WhatsApp", f"https://wa.me/55{tel_puro}")

    # --- TAB 2: ANIVERSÁRIOS 🎂 ---
    with t2:
        st.subheader("🎂 Aniversariantes de Fevereiro")
        mes_hoje = "02" # Fixado em fevereiro conforme seu teste
        niver_list = []
        if not df.empty:
            for i, r in df.iterrows():
                d = r['nascimento']
                puro = limpar_numero(d)
                mes = d.split("/")[1] if "/" in d else (puro[2:4] if len(puro) >= 4 else "")
                if mes == mes_hoje:
                    niver_list.append({"dia": d.split("/")[0] if "/" in d else puro[:2], "nome": r['nome']})
            if niver_list:
                for n in sorted(niver_list, key=lambda x: x['dia']):
                    st.write(f"🎂 **Dia {n['dia']}** - {n['nome']}")
            else: st.info("Nenhum aniversariante encontrado para este mês.")

    # --- TAB 3: CADASTRO ---
    with t3:
        st.subheader("Novo Membro")
        with st.form("form_novo", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                f_nome = st.text_input("Nome")
                f_nasc = st.text_input("Data (DDMMAAAA)")
                f_asc = st.selectbox("Ascendente", ["Raiz"] + lista_nomes)
            with col2:
                f_tel = st.text_input("Telefone (DDD + Numero)")
                f_rua = st.text_input("Rua")
                f_num = st.text_input("Nº")
            
            if st.form_submit_button("SALVAR"):
                if f_nome:
                    dados = [f_nome, aplicar_mascara_data(f_nasc), f_asc, aplicar_mascara_tel(f_tel), "", f_rua, f_num, "", "", ""]
                    requests.post(WEBAPP_URL, json={"action": "append", "data": dados})
                    st.success("✅ Salvo com sucesso!")
                    st.rerun()

    # --- TAB 4: EDITAR E EXCLUIR ---
    with t4:
        st.subheader("Gerenciar Registro")
        if lista_nomes:
            sel = st.selectbox("Escolha quem deseja gerenciar", lista_nomes)
            p = df[df['nome'] == sel].iloc[0]
            idx = df.index[df['nome'] == sel].tolist()[0] + 2 # Linha na planilha
            
            with st.form("form_edit"):
                st.info(f"Editando: {sel}")
                c1, c2 = st.columns(2)
                with c1:
                    e_nasc = st.text_input("Nascimento", value=p['nascimento'])
                    e_tel = st.text_input("Telefone", value=p['telefone'])
                with c2:
                    e_rua = st.text_input("Rua", value=p['rua'])
                    e_num = st.text_input("Nº", value=p['num'])
                
                col_btn1, col_btn2 = st.columns(2)
                if col_btn1.form_submit_button("💾 SALVAR ALTERAÇÕES"):
                    up = [sel, e_nasc, p['ascendente'], e_tel, p['email'], e_rua, e_num, "", p['bairro'], p['cep']]
                    requests.post(WEBAPP_URL, json={"action": "edit", "row": idx, "data": up})
                    st.success("Atualizado!")
                    st.rerun()
                
                # O BOTÃO DE EXCLUSÃO ESTÁ AQUI
                if col_btn2.form_submit_button("🗑️ EXCLUIR REGISTRO"):
                    requests.post(WEBAPP_URL, json={"action": "edit", "row": idx, "data": [""] * 10})
                    st.warning(f"O registro de {sel} foi removido.")
                    st.rerun()
        else:
            st.warning("Nenhum membro cadastrado.")

    st.sidebar.button("Sair", on_click=lambda: st.session_state.update({"logado": False}))
