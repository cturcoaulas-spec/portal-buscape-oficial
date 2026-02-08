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

# --- FUNÇÕES DE TRATAMENTO ---
def limpar_numero(v):
    return re.sub(r'\D', '', str(v))

def aplicar_mascara_tel(v):
    n = limpar_numero(v)
    # Se digitar 11 números (com DDD), formata: (99) 99999-9999
    if len(n) == 11: return f"({n[:2]}) {n[2:7]}-{n[7:]}"
    # Se digitar 10 números (fixo), formata: (99) 9999-9999
    if len(n) == 10: return f"({n[:2]}) {n[2:6]}-{n[6:]}"
    return v

def aplicar_mascara_data(v):
    n = limpar_numero(v)
    # Formata DDMMAAAA para DD/MM/AAAA
    if len(n) == 8: return f"{n[:2]}/{n[2:4]}/{n[4:]}"
    return v

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
                tel_exibir = r.get('telefone','-')
                tel_puro = limpar_numero(tel_exibir)
                label = f"👤 {r.get('nome','-')} | 📅 {r.get('nascimento','-')} | 📞 {tel_exibir}"
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

    # --- TAB 2: AGENDA (INTELIGENTE) ---
    with t2:
        st.subheader("🎂 Aniversariantes do Mês")
        mes_hoje = datetime.now().strftime("%m")
        niver_list = []
        if not df.empty:
            for i, r in df.iterrows():
                d = r.get('nascimento','')
                puro = limpar_numero(d)
                dia, mes = "", ""
                if "/" in d and len(d) >= 5:
                    partes = d.split("/")
                    dia, mes = partes[0], partes[1]
                elif len(puro) == 8:
                    dia, mes = puro[:2], puro[2:4]
                
                if mes == mes_hoje:
                    niver_list.append({"dia": dia, "nome": r['nome']})
            
            if niver_list:
                niver_list = sorted(niver_list, key=lambda x: x['dia'])
                for n in niver_list:
                    st.write(f"✨ **Dia {n['dia']}** - {n['nome']}")
            else: st.info("Nenhum aniversário este mês.")

    # --- TAB 3: CADASTRO ---
    with t3:
        st.subheader("Novo Integrante")
        st.info("💡 Digite apenas números no Nascimento e Telefone. O sistema formatará sozinho!")
        with st.form("form_novo", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                f_nome = st.text_input("Nome Completo")
                f_nasc = st.text_input("Nascimento (Ex: 08021990)")
                f_asc = st.selectbox("Ascendente", ["Raiz"] + lista_nomes)
            with col2:
                f_tel = st.text_input("Telefone com DDD (Ex: 31988887777)")
                f_mail = st.text_input("E-mail")
                f_rua = st.text_input("Rua")
                f_num = st.text_input("Número")
                f_bair = st.text_input("Bairro")
                f_cep = st.text_input("CEP")
            
            if st.form_submit_button("💾 SALVAR NA NUVEM"):
                if f_nome and f_nasc:
                    # A Mágica acontece aqui: formata antes de enviar
                    data_final = aplicar_mascara_data(f_nasc)
                    tel_final = aplicar_mascara_tel(f_tel)
                    dados = [f_nome, data_final, f_asc, tel_final, f_mail, f_rua, f_num, "", f_bair, f_cep]
                    requests.post(WEBAPP_URL, json={"action": "append", "data": dados})
                    st.success(f"✅ {f_nome} salvo com sucesso!")
                    st.rerun()

    # --- TAB 4: EDITAR ---
    with t4:
        st.subheader("Gerenciar Membros")
        if lista_nomes:
            sel = st.selectbox("Selecione para alterar", lista_nomes)
            p = df[df['nome'] == sel].iloc[0]
            idx = df.index[df['nome'] == sel].tolist()[0] + 2
            
            with st.form("form_edit"):
                c1, c2 = st.columns(2)
                with c1:
                    e_nasc = st.text_input("Nascimento", value=p.get('nascimento',''))
                    l_asc = ["Raiz"] + [n for n in lista_nomes if n != sel]
                    cur_asc = p.get('ascendente','Raiz')
                    i_asc = l_asc.index(cur_asc) if cur_asc in l_asc else 0
                    e_asc = st.selectbox("Ascendente", l_asc, index=i_asc)
                    e_tel = st.text_input("Telefone", value=p.get('telefone',''))
                with c2:
                    e_mail = st.text_input("E-mail", value=p.get('email',''))
                    e_rua = st.text_input("Rua", value=p.get('rua',''))
                    e_num = st.text_input("Nº", value=p.get('num',''))
                    e_bair = st.text_input("Bairro", value=p.get('bairro',''))
                    e_cep = st.text_input("CEP", value=p.get('cep',''))
                
                b1, b2 = st.columns(2)
                if b1.form_submit_button("💾 SALVAR ALTERAÇÕES"):
                    # Formata na edição também caso o usuário mude
                    data_e = aplicar_mascara_data(e_nasc) if len(limpar_numero(e_nasc))==8 else e_nasc
                    tel_e = aplicar_mascara_tel(e_tel) if len(limpar_numero(e_tel))>=10 else e_tel
                    up = [sel, data_e, e_asc, tel_e, e_mail, e_rua, e_num, "", e_bair, e_cep]
                    requests.post(WEBAPP_URL, json={"action": "edit", "row": idx, "data": up})
                    st.success("✅ Atualizado!")
                    st.rerun()
