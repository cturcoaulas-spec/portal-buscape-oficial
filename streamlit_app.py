import streamlit as st
import pandas as pd
import requests
import re
import unicodedata
import time
from urllib.parse import quote
from datetime import datetime
from fpdf import FPDF

# 1. CONFIGURAÇÃO (FBUSCAPE)
st.set_page_config(page_title="FBUSCAPE", page_icon="🌳", layout="wide")

# 2. BLINDAGEM E AJUSTE DE TOPO (LIBERA O NAVEGADOR)
st.markdown("""
    <style>
    .viewerBadge_container__1QSob, .stAppDeployButton, #MainMenu { display: none !important; }
    [data-testid="stStatusWidget"], [data-testid="stToolbar"], [data-testid="stDecoration"] { display: none !important; }
    footer { display: none !important; }

    header[data-testid="stHeader"] {
        background-color: rgba(255, 255, 255, 0) !important;
    }
    
    /* Respiro para a barra do navegador aparecer */
    .block-container { padding-top: 3.5rem !important; }

    /* Estilo das Abas e Botões */
    [data-baseweb="tab-list"] { gap: 8px; overflow-x: auto; }
    [data-baseweb="tab"] { padding: 10px; border-radius: 10px; background: #f0f2f6; min-width: 110px; }
    .stButton>button { height: 3.5em !important; font-weight: bold !important; border-radius: 12px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- LINKS E FUNÇÕES (PRESERVADOS) ---
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzWJ_nDGDe4a81O5BDx3meMbVJjlcMpJoxoO05lilysWJaj_udqeXqvfYFgzvWPlC-Omw/exec"
CSV_URL = "https://docs.google.com/spreadsheets/d/1jrtIP1lN644dPqY0HPGGwPWQGyYwb8nWsUigVK3QZio/export?format=csv"
MESES_BR = ["", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

def normalizar(t): return "".join(ch for ch in unicodedata.normalize('NFKD', str(t).lower()) if not unicodedata.combining(ch)).strip()
def limpar(v): return re.sub(r'\D', '', str(v))
def mask_tel(v):
    n = limpar(str(v))[:11]
    if len(n) == 11: return f"({n[:2]}) {n[2:7]}-{n[7:11]}"
    return f"({n[:2]}) {n[2:6]}-{n[6:10]}" if len(n) == 10 else n
def mask_data(d):
    d = limpar(str(d))
    return f"{d[:2]}/{d[2:4]}/{d[4:]}" if len(d) == 8 else d

@st.cache_data(ttl=2)
def carregar_dados():
    try:
        df = pd.read_csv(CSV_URL, dtype=str).fillna("")
        mapa = {c: normalizar(c) for c in df.columns}
        df = df.rename(columns={k: 'nome' if 'nome' in v else 'nascimento' if 'nasc' in v else 'vinculo' if 'vinc' in v or 'ascend' in v else 'telefone' if 'tel' in v else 'rua' if 'rua' in v else 'num' if 'num' in v else 'bairro' if 'bair' in v else 'cep' if 'cep' in v else 'email' if 'emai' in v else k for k, v in mapa.items()})
        return df
    except: return pd.DataFrame()

# --- INTERFACE ---
if 'logado' not in st.session_state: st.session_state.logado = False
if not st.session_state.logado:
    st.title("🌳 Portal Família Buscapé")
    psw = st.text_input("Senha", type="password")
    if st.button("ENTRAR"):
        if psw == "buscape2026": st.session_state.logado = True; st.rerun()
        else: st.error("Senha incorreta!")
else:
    df_todo = carregar_dados()
    if not df_todo.empty:
        df_m = df_todo[df_todo['nome'] != ""].sort_values(by='nome').copy()
        
        # --- NOVO: GUIA DE INSTALAÇÃO BASEADO NA SUA PESQUISA ---
        with st.expander("📲 CLIQUE AQUI PARA INSTALAR NO SEU CELULAR"):
            st.markdown("""
            **Para Android (Chrome):**
            1. Toque nos **3 pontinhos (⋮)** no topo do seu navegador.
            2. Escolha **'Instalar aplicativo'** ou **'Adicionar à tela inicial'**.
            
            **Para iPhone (Safari):**
            1. Toque no ícone de **Compartilhar** (quadrado com uma seta para cima).
            2. Role para baixo e toque em **'Adicionar ao Ecrã Principal'**.
            """)
            st.image("https://www.google.com/chrome/static/images/pwa/install-icon.png", width=50)

        tabs = st.tabs(["🔍 Membros", "🎂 Niver", "📢 Mural", "➕ Novo", "✏️ Gerenciar", "🌳 Árvore", "📖 Manual"])

        # ... (Restante do código das abas 1 a 6 permanece idêntico) ...

        with tabs[6]: # 7. Manual (RESTAURADO)
            st.markdown("""
            ### 📖 Manual Familia Buscape
            1. **Boas-vindas!** Este portal foi criado para ser o nosso ponto de encontro oficial.
            2. **Abas:** **Membros** (Agenda), **Niver** (Aniversários), **Mural** (Avisos), **Novo** (Cadastro), **Gerenciar** (Edição), **Árvore** (Nossa história).
            3. **Instalação:** Use o guia no topo desta página para criar o ícone no seu telemóvel.
            4. **Responsabilidade:** Mantenha seus dados atualizados e use com carinho!
            
            **SENHA:** `buscape2026`
            """)
