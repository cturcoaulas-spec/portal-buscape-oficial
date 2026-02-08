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

# --- FUNÇÕES DE MÁSCARA E LIMPEZA ---
def limpar_numero(v):
    return re.sub(r'\D', '', str(v))

def aplicar_mascara_tel(v):
    n = limpar_numero(v)
    if len(n) == 11:
        return f"({n[:2]}) {n[2:7]}-{n[7:]}"
    return v

def aplicar_mascara_data(v):
    n = limpar_numero(v)
    if len(n) == 8:
        return f"{n[:2]}/{n[2:4]}/{n[4:]}"
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
    @st.cache_data(ttl=2) # Reduzi o tempo para atualizar quase instantâneo
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

    # --- TAB 2: AGENDA (CORRIGIDA) ---
    with t2:
        st.subheader("🎂 Aniversariantes do Mês")
        # Pega o mês atual (ex: 02)
        mes_atual = datetime.now().strftime("%m")
        niver_mes = []
        
        if not df.empty:
            for i, r in df.iterrows():
                data = r.get('nascimento','') # Esperado: DD/MM/AAAA
                # Verifica se o mês na string da data coincide com o mês atual
                if "/" in data:
                    partes = data.split("/")
                    if len(partes) >= 2 and partes[1] == mes_atual:
                        niver_mes.append({"dia": partes[0], "nome": r['nome']})
            
            if niver_mes:
                # Ordena por dia
                niver_mes = sorted(niver_mes, key=lambda x: x['dia'])
                for n in niver_mes:
                    st.write(f"✨ **Dia {n['dia']}** - {n['nome']}")
            else:
                st.info("Nenhum aniversário encontrado para este mês.")

    # --- TAB 3: CADASTRO (COM
