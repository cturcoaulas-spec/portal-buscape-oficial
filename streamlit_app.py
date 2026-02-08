import streamlit as st
import pandas as pd
import requests
import re
from urllib.parse import quote
from datetime import datetime

# CONFIGURAÇÃO
st.set_page_config(page_title="Portal Família Buscapé", page_icon="🌳", layout="wide")

WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzWJ_nDGDe4a81O5BDx3meMbVJjlcMpJoxoO05lilysWJaj_udqeXqvfYFgzvWPlC-Omw/exec"
CSV_URL = "https://docs.google.com/spreadsheets/d/1jrtIP1lN644dPqY0HPGGwPWQGyYwb8nWsUigVK3QZio/export?format=csv"

# --- FUNÇÕES ---
def limpar_numero(v):
    return re.sub(r'\D', '', str(v))

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
    t1, t2, t3, t4 = st.tabs(["🔍 Ver Família", "📅 Agenda", "➕ Cadastrar", "✏️ Editar"])

    # --- TAB 1: VER FAMÍLIA ---
    with t1:
        st.subheader("Membros da Família")
        if not df.empty:
            for i, r in df.iterrows():
                tel_puro = limpar_numero(r.get('telefone',''))
                label = f"👤 {r.get('nome','-')} | 📅 {r.get('nascimento','-')} | 📞 {r.get('telefone','-')}"
                with st.expander(label):
                    c1, c2, c3 = st.columns([2, 2, 1])
                    with c1:
                        st.write(f"**Ascendente:** {r.get('ascendente','-')}")
                        st.write(f"**E-mail:** {r.get('email','-')}")
                    with c2:
                        rua, num, bairro = r.get('rua',''), r.get('num',''), r.get('bairro','')
                        if rua:
                            st.write(f"🏠 **Endereço:** {rua}, {num} - {bairro}")
                            link_maps = f"https://www.google.com/maps/search/?api=1&query={quote(f'{rua}, {num}, {bairro}, Brazil')}"
                            st.link_button("📍 Abrir no Google Maps", link_maps)
                    with c3:
                        if len(tel_puro) >= 10:
                            st.link_button("💬 WhatsApp", f"https://wa.me/55{tel_puro}")
                            st.link_button("📞 Ligar", f"tel:+55{tel_puro}")

    # --- TAB 2: AGENDA (ANIVERSARIANTES) ---
    with t2:
        st.subheader("🎂 Aniversariantes do Mês")
        mes_atual = datetime.now().strftime("%m")
        niver_mes = []
        if not df.empty:
            for i, r in df.iterrows():
                data = r.get('nascimento','')
                if "/" in data:
                    partes = data.split("/")
                    if len(partes) >= 2 and partes[1] == mes_atual:
                        niver_mes.append({"dia": partes[0], "nome": r['nome']})
            if niver_mes:
                niver_mes = sorted(niver_mes, key=lambda x: x['dia'])
                for n in niver_mes: st.write(f"✨ **Dia {n['dia']}** - {n['nome']}")
            else: st.info("Nenhum aniversário este mês.")

    # --- TAB 3: CADASTRO ---
    with t3:
        st.subheader("Novo Integrante")
        with st.form("form_novo", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                f_nome = st.text_input("Nome Completo")
                f_nasc = st.text_input("Nascimento (DDMMAAAA)")
                f_asc = st.selectbox("Ascendente", ["Raiz"] + lista_nomes)
                f_tel = st.text_input("Telefone (DDD + Número)")
            with c2:
                f_mail = st.text_input("E-mail")
                f_rua = st.text_input("Rua")
                f_num = st.text_input("Número")
                f_bair = st.text_input("Bairro")
                f_cep = st.text_input("CEP")
            
            if st.form_submit_button("SALVAR NA NUVEM"):
                if f_nome:
                    dados = [f_nome, aplicar_mascara_data(f_nasc), f_asc, aplicar_mascara_tel(f_tel), f_mail, f_rua, f_num, "", f_bair, f_cep]
                    requests.post(WEBAPP_URL, json={"action": "append", "data": dados})
                    st.success("✅ Salvo!")
                    st.rerun()

    # --- TAB 4: EDITAR ---
    with t4:
        st.subheader("Gerenciar Dados")
        if lista_nomes:
            sel = st.selectbox("Selecione para alterar", lista_nomes)
            p = df[df['nome'] == sel].iloc[0]
            idx = df.index[df['nome'] == sel].tolist()[0] + 2
            
            with st.form("form_edit"):
                c1, c2 = st.columns(2)
                with c1:
                    e_nasc = st.text_input("Nascimento", value=p.get('nascimento',''))
                    lista_asc_edit = ["Raiz"] + [n for n in lista_nomes if n != sel]
                    asc_atual = p.get('ascendente','Raiz')
                    idx_asc = lista_asc_edit.index(asc_atual) if asc_atual in lista_asc_edit else 0
                    e_asc = st.selectbox("Ascendente", lista_asc_edit, index=idx_asc)
                    e_tel = st.text_input("Telefone", value=p.get('telefone',''))
                with c2:
                    e_mail = st.text_input("E-mail", value=p.get('email',''))
                    e_ru = st.text_input("Rua", value=p.get('rua',''))
                    e_nu = st.text_input("Nº", value=p.get('num',''))
                    e_ba = st.text_input("Bairro", value=p.get('bairro',''))
                    e_ce = st.text_input("CEP", value=p.get('cep',''))
                
                b1, b2 = st.columns(2)
                if b1.form_submit_button("💾 SALVAR ALTERAÇÕES"):
                    up = [sel, e_nasc, e_asc, e_tel, e_mail, e_ru, e_nu, "", e_ba, e_ce]
                    requests.post(WEBAPP_URL, json={"action": "edit", "row": idx, "data": up})
                    st.success("✅ Atualizado!")
                    st.rerun()
                if b2.form_submit_button("🗑️ EXCLUIR"):
                    requests.post(WEBAPP_URL, json={"action": "edit", "row": idx, "data": [""] * 10})
                    st.warning("Removido.")
                    st.rerun()

    st.sidebar.button("Sair", on_click=lambda: st.session_state.update({"logado": False}))
