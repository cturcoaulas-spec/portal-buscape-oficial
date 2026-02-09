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

# 2. BLINDAGEM CIRÚRGICA (LIBERA NAVEGADOR E BARRA LATERAL)
st.markdown("""
    <style>
    /* ESCONDE O MANAGE APP E BOTÕES DE SISTEMA */
    .viewerBadge_container__1QSob, .stAppDeployButton, #MainMenu { display: none !important; }
    [data-testid="stStatusWidget"], [data-testid="stToolbar"], [data-testid="stDecoration"] { display: none !important; }
    footer { display: none !important; }

    /* DEIXA O CABEÇALHO VISÍVEL APENAS PARA O MENU LATERAL (TRÊS BARRINHAS) */
    header[data-testid="stHeader"] {
        visibility: visible !important;
        background-color: rgba(255, 255, 255, 0) !important;
    }
    
    /* RESPIRO NO TOPO: Garante que os 3 pontinhos do Chrome e o menu lateral apareçam */
    .block-container { padding-top: 4.5rem !important; }

    /* ESTILO DAS ABAS E BOTÕES - PRESERVADOS */
    [data-baseweb="tab-list"] { gap: 8px; overflow-x: auto; }
    [data-baseweb="tab"] { padding: 10px; border-radius: 10px; background: #f0f2f6; min-width: 110px; }
    button { height: 3.5em !important; font-weight: bold !important; border-radius: 12px !important; width: 100% !important; }
    .stExpander { border-radius: 12px !important; border: 1px solid #ddd !important; }
    </style>
    """, unsafe_allow_html=True)

# LINKS DE INTEGRAÇÃO
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzWJ_nDGDe4a81O5BDx3meMbVJjlcMpJoxoO05lilysWJaj_udqeXqvfYFgzvWPlC-Omw/exec"
CSV_URL = "https://docs.google.com/spreadsheets/d/1jrtIP1lN644dPqY0HPGGwPWQGyYwb8nWsUigVK3QZio/export?format=csv"
MESES_BR = ["", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

# --- FUNÇÕES SUPORTE (MANTIDAS) ---
def normalizar(t):
    return "".join(ch for ch in unicodedata.normalize('NFKD', str(t).lower()) if not unicodedata.combining(ch)).strip()

def limpar(v): return re.sub(r'\D', '', str(v))

def mask_tel(v):
    n = limpar(str(v))[:11]
    if len(n) == 11: return f"({n[:2]}) {n[2:7]}-{n[7:11]}"
    if len(n) == 10: return f"({n[:2]}) {n[2:6]}-{n[6:10]}"
    return n if n else "-"

def mask_data(d):
    d = limpar(str(d))
    if len(d) == 8: return f"{d[:2]}/{d[2:4]}/{d[4:]}"
    return d

@st.cache_data(ttl=2)
def carregar_dados():
    try:
        df = pd.read_csv(CSV_URL, dtype=str).fillna("")
        mapa_novo = {}
        for c in df.columns:
            cn = normalizar(c)
            if 'nome' in cn: mapa_novo[c] = 'nome'
            elif 'nasc' in cn: mapa_novo[c] = 'nascimento'
            elif 'vinc' in cn or 'ascend' in cn: mapa_novo[c] = 'vinculo'
            elif 'tel' in cn: mapa_novo[c] = 'telefone'
            elif 'rua' in cn: mapa_novo[c] = 'rua'
            elif 'num' in cn: mapa_novo[c] = 'num'
            elif 'bair' in cn: mapa_novo[c] = 'bairro'
            elif 'cep' in cn: mapa_novo[c] = 'cep'
            elif 'emai' in cn: mapa_novo[c] = 'email'
        df = df.rename(columns=mapa_novo)
        if 'nome' in df.columns: df['nome'] = df['nome'].str.strip(); return df
        return pd.DataFrame()
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
    if df_todo.empty: st.error("⚠️ Erro ao carregar dados.")
    else:
        df_m = df_todo[df_todo['nome'] != ""].sort_values(by='nome').copy()
        nomes_lista = sorted(df_m['nome'].unique().tolist())
        mes_at = datetime.now().month

        with st.sidebar:
            st.title("⚙️ Painel")
            st.subheader("🔔 Notificações")
            niver_mes = []
            for _, r in df_m.iterrows():
                dt = str(r.get('nascimento',''))
                if "/" in dt:
                    p = dt.split('/')
                    if len(p) >= 2 and int(p[1]) == mes_at: niver_mes.append(f"🎂 {p[0]} - {r['nome']}")
            if niver_mes:
                st.info(f"**Aniversariantes de {MESES_BR[mes_at]}:**")
                for n in niver_mes: st.write(n)
            else: st.write("Sem avisos para este mês.")
            st.divider()
            if st.button("🔄 Sincronizar"): st.cache_data.clear(); st.rerun()
            st.button("🚪 Sair", on_click=lambda: st.session_state.update({"logado": False}))

        st.title("🌳 Família Buscapé")
        tabs = st.tabs(["🔍 Membros", "🎂 Niver", "📢 Mural", "➕ Novo", "✏️ Gerenciar", "🌳 Árvore", "📖 Manual"])

        # Aba 0 a 5 continuam com sua lógica...

        with tabs[6]: # 7. Manual (COMPLETO)
            st.markdown("""
            ### 📖 Manual Familia Buscape
            1. **Boas-vindas!** Este portal foi criado pela Valeria para ser o nosso ponto de encontro oficial. Aqui, nossa historia e nossos contatos estao protegidos e sempre a mao.
            2. **O que sao as Abas?** **Membros:** Nossa agenda viva. **Niver:** Onde celebramos a vida a cada mes. **Mural:** Nosso quadro de avisos coletivo. **Novo:** Para a familia crescer. **Gerenciar:** Para manter tudo organizado. **Arvore:** Onde vemos quem somos e de onde viemos.
            3. **Integracoes Magicas** Clicando no botao de WhatsApp, voce fala com o parente sem precisar salvar o numero. Clicando no botao de Mapa, o GPS do seu telemovel abre direto na porta da casa dele!
            4. **Responsabilidade** Lembre-se: o que voce apaga aqui, apaga para todos. Use com carinho e mantenha seus dados sempre em dia!
            5. **No seu Telemovel** **Android (Chrome):** clique nos 3 pontinhos e 'Instalar'. **iPhone (Safari):** clique na seta de partilhar e 'Ecra principal'.
            ---
            **🔑 SENHA DE ACESSO:** `buscape2026`
            ---
            **📲 DICA DE INSTALAÇÃO:** Para usar como aplicativo, use o menu do navegador e escolha 'Adicionar à tela inicial'.
            """)
