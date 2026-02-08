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

# --- FUNÇÕES DE LIMPEZA E MÁSCARA ---
def formatar_tel(v):
    n = re.sub(r'\D', '', str(v)) # Remove letras e símbolos
    if len(n) >= 11: return f"({n[:2]}) {n[2:7]}-{n[7:11]}"
    if len(n) == 10: return f"({n[:2]}) {n[2:6]}-{n[6:10]}"
    return v

def formatar_data(v):
    n = re.sub(r'\D', '', str(v))
    if len(n) == 8: return f"{n[:2]}/{n[2:4]}/{n[4:]}"
    return v

# --- LOGIN ---
if 'logado' not in st.session_state: st.session_state.logado = False
if not st.session_state.logado:
    st.title("🌳 Portal Família Buscapé")
    senha = st.text_input("Senha de Acesso", type="password")
    if st.button("ENTRAR"):
        if senha == "buscape2026": st.session_state.logado = True; st.rerun()
        else: st.error("Senha incorreta.")
else:
    @st.cache_data(ttl=2)
    def carregar():
        try:
            df = pd.read_csv(CSV_URL, dtype=str).fillna("")
            df.columns = [c.strip().lower() for c in df.columns]
            return df[df['nome'].str.strip() != ""]
        except: return pd.DataFrame()

    df = carregar()
    lista_nomes = sorted(df['nome'].tolist()) if not df.empty else []

    st.title("🌳 Portal Família Buscapé")
    t1, t2, t3, t4 = st.tabs(["🔍 Lista de Membros", "📅 Aniversários", "➕ Novo Cadastro", "✏️ Gerenciar/Editar"])

    # --- TAB 1: MEMBROS ---
    with t1:
        st.subheader("Visualização dos Membros")
        if not df.empty:
            for i, r in df.iterrows():
                with st.expander(f"👤 {r.get('nome','-')} | 📅 {r.get('nascimento','-')}"):
                    c1, c2, c3 = st.columns([2, 2, 1])
                    with c1:
                        st.write(f"📞 **Telefone:** {r.get('telefone','-')}")
                        st.write(f"✉️ **E-mail:** {r.get('email','-')}")
                        st.write(f"🌳 **Ascendente:** {r.get('ascendente','-')}")
                    with c2:
                        end = f"{r.get('rua','-')}, {r.get('num','-')} {r.get('complemento','')}"
                        st.write(f"🏠 **Endereço:** {end}")
                        st.write(f"📍 **Bairro/CEP:** {r.get('bairro','-')} | {r.get('cep','-')}")
                    with c3:
                        tel_p = re.sub(r'\D', '', r.get('telefone',''))
                        if len(tel_p) >= 10: st.link_button("💬 WhatsApp", f"https://wa.me/55{tel_p}")
        else: st.info("Nenhum registro encontrado.")

    # --- TAB 2: ANIVERSÁRIOS ---
    with t2:
        st.subheader("Aniversariantes")
        mes_h = datetime.now().strftime("%m")
        niver_list = []
        if not df.empty:
            for _, r in df.iterrows():
                d = r.get('nascimento',''); p = re.sub(r'\D', '', d)
                m = d.split("/")[1] if "/" in d else (p[2:4] if len(p)>=4 else "")
                if m == mes_h: niver_list.append({"dia": d.split("/")[0] if "/" in d else p[:2], "nome": r.get('nome','')})
            if niver_list:
                for n in sorted(niver_list, key=lambda x: x['dia']):
                    st.write(f"🎂 **Dia {n['dia']}** - {n['nome']}")
            else: st.info("Sem aniversários este mês.")

    # --- TAB 3: CADASTRO ---
    with t3:
        st.subheader("Cadastrar Novo Familiar")
        with st.form("f_novo", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                f_n = st.text_input("Nome Completo")
                f_d = st.text_input("Nascimento (Só números)")
                f_a = st.selectbox("Ascendente", ["Raiz"] + lista_nomes)
                f_t = st.text_input("Telefone (Com DDD)")
            with col2:
                f_e = st.text_input("E-mail")
                f_r = st.text_input("Rua")
                f_u = st.text_input("Nº")
                f_c = st.text_input("Complemento")
                f_b = st.text_input("Bairro")
                f_ce = st.text_input("CEP")
            
            if st.form_submit_button("💾 SALVAR CADASTRO"):
                if f_n in lista_nomes: st.error("⚠️ Este nome já existe!")
                elif f_n:
                    dados = [f_n, formatar_data(f_d), f_a, formatar_tel(f_t), f_e, f_r, f_u, f_c, f_b, f_ce]
                    requests.post(WEBAPP_URL, json={"action": "append", "data": dados})
                    st.success("✅ Salvo com sucesso!"); st.rerun()

    # --- TAB 4: EDITAR ---
    with t4:
        st.subheader("Editar ou Excluir Registro")
        opcoes = ["-- Escolha um Membro --"] + lista_nomes
        s_m = st.selectbox("Selecione quem deseja alterar:", opcoes)
        
        if s_m != "-- Escolha um Membro --":
            p_d = df[df['nome'] == s_m].iloc[0]
            idx = df.index[df['nome'] == s_m].tolist()[0] + 2
            with st.form("f_edit"):
                c1, c2 = st.columns(2)
                with c1:
                    e_d = st.text_input("Nascimento", value=p_d.get('nascimento',''))
                    e_t = st.text_input("Telefone", value=p_d.get('telefone',''))
                    e_e = st.text_input("E-mail", value=p_d.get('email',''))
                    e_a = st.text_input("Ascendente", value=p_d.get('ascendente',''))
                with c2:
                    e_r = st.text_input("Rua", value=p_d.get('rua',''))
                    e_u = st.text_input("Nº", value=p_d.get('num',''))
                    e_c = st.text_input("Complemento", value=p_d.get('complemento',''))
                    e_b = st.text_input("Bairro", value=p_d.get('bairro',''))
                    e_ce = st.text_input("CEP", value=p_d.get('cep',''))
                
                b1, b2 = st.columns(2)
                if b1.form_submit_button("💾 ATUALIZAR DADOS"):
                    up = [s_m, formatar_data(e_d), e_a, formatar_tel(e_t), e_e, e_r, e_u, e_c, e_b, e_ce]
                    requests.post(WEBAPP_URL, json={"action": "edit", "row": idx, "data": up}); st.rerun()
                if b2.form_submit_button("🗑️ EXCLUIR MEMBRO"):
                    requests.post(WEBAPP_URL, json={"action": "edit", "row": idx, "data": [""] * 10}); st.rerun()

    st.sidebar.button("Sair", on_click=lambda: st.session_state.update({"logado": False}))
