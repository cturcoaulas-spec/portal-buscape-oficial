import streamlit as st
import pandas as pd
import requests
import re
from urllib.parse import quote
from datetime import datetime

# CONFIGURAÇÃO
st.set_page_config(page_title="Portal Família Buscapé", page_icon="🌳", layout="wide")

WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzDd11VRMTQSvd3MDNZgok8qV4o_y4s0KhBaAJQFC0HZtg36mpydMTVmPQXg34lZp_RCQ/exec"
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
    @st.cache_data(ttl=5)
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

    # --- TAB 1: VER FAMÍLIA (COM WHATSAPP E CHAMADA) ---
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
                        st.write("**Contato:**")
                        if len(tel_puro) >= 10:
                            # Botão WhatsApp
                            link_wa = f"https://wa.me/55{tel_puro}"
                            st.link_button("💬 WhatsApp", link_wa)
                            # Botão Chamada
                            link_tel = f"tel:+55{tel_puro}"
                            st.link_button("📞 Ligar", link_tel)

    # --- TAB 2: AGENDA ---
    with t2:
        st.subheader("🎂 Aniversariantes do Mês")
        mes_atual = datetime.now().strftime("%m")
        niver_mes = []
        if not df.empty:
            for i, r in df.iterrows():
                data = r.get('nascimento','')
                if len(data) >= 5 and data[3:5] == mes_atual:
                    niver_mes.append(f"**Dia {data[:2]}** - {r['nome']}")
            
            if niver_mes:
                for n in niver_mes: st.write(n)
            else: st.write("Nenhum aniversário este mês.")

    # --- TAB 3: CADASTRO ---
    with t3:
        st.subheader("Novo Integrante")
        with st.form("form_novo", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                f_nome = st.text_input("Nome")
                f_nasc = st.text_input("Nascimento (DDMMAAAA)")
                f_asc  = st.selectbox("Ascendente", ["Raiz"] + lista_nomes)
                f_tel  = st.text_input("Telefone (DDD + Número)")
            with col2:
                f_mail = st.text_input("E-mail")
                f_rua  = st.text_input("Rua")
                f_num  = st.text_input("Nº")
                f_bair = st.text_input("Bairro")
                f_cep  = st.text_input("CEP")
            if st.form_submit_button("SALVAR NA NUVEM"):
                if f_nome:
                    dados = [f_nome, aplicar_mascara_data(f_nasc), f_asc, aplicar_mascara_tel(f_tel), f_mail, f_rua, f_num, "", f_bair, f_cep]
                    requests.post(WEBAPP_URL, json={"action": "append", "data": dados})
                    st.success("✅ Salvo com sucesso!")
                    st.rerun()

    # --- TAB 4: EDITAR E EXCLUIR ---
    with t4:
        st.subheader("Gerenciar Dados")
        if lista_nomes:
            sel = st.selectbox("Selecione o membro", lista_nomes)
            p = df[df['nome'] == sel].iloc[0]
            idx = df.index[df['nome'] == sel].tolist()[0] + 2
            
            with st.form("form_edit"):
                c1, c2 = st.columns(2)
                with c1:
                    e_nasc = st.text_input("Nascimento", value=p.get('nascimento',''))
                    lista_asc = ["Raiz"] + [n for n in lista_nomes if n != sel]
                    asc_atual = p.get('ascendente','Raiz')
                    idx_asc = lista_asc.index(asc_atual) if asc_atual in lista_asc else 0
                    e_asc = st.selectbox("Ascendente", lista_asc, index=idx_asc)
                    e_tel = st.text_input("Telefone", value=p.get('telefone',''))
                with c2:
                    e_mail = st.text_input("E-mail", value=p.get('email',''))
                    e_ru = st.text_input("Rua", value=p.get('rua',''))
                    e_nu = st.text_input("Nº", value=p.get('num',''))
                    e_ba = st.text_input("Bairro", value=p.get('bairro',''))
                    e_ce = st.text_input("CEP", value=p.get('cep',''))
                
                col_btn1, col_btn2 = st.columns(2)
                if col_btn1.form_submit_button("💾 ATUALIZAR"):
                    up = [sel, e_nasc, e_asc, e_tel, e_mail, e_ru, e_nu, "", e_ba, e_ce]
                    requests.post(WEBAPP_URL, json={"action": "edit", "row": idx, "data": up})
                    st.success("✅ Atualizado!")
                    st.rerun()
                
                if col_btn2.form_submit_button("🗑️ EXCLUIR MEMBRO"):
                    requests.post(WEBAPP_URL, json={"action": "edit", "row": idx, "data": [""] * 10})
                    st.warning(f"O membro {sel} foi removido.")
                    st.rerun()

    st.sidebar.button("Sair", on_click=lambda: st.session_state.update({"logado": False}))
