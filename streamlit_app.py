import streamlit as st
import pandas as pd
import requests
import re
import unicodedata
import time
from urllib.parse import quote
from datetime import datetime
from fpdf import FPDF

# 1. CONFIGURAÇÃO
st.set_page_config(page_title="FBUSCAPE", page_icon="🌳", layout="wide")

# 2. BLINDAGEM E LIBERAÇÃO DO NAVEGADOR (O "PURO" DO PROJETO)
st.markdown("""
    <style>
    /* Esconde as ferramentas do Streamlit que atrapalham */
    .viewerBadge_container__1QSob, .stAppDeployButton, #MainMenu { display: none !important; }
    [data-testid="stStatusWidget"], [data-testid="stToolbar"], [data-testid="stDecoration"] { display: none !important; }
    footer { display: none !important; }

    /* FORÇA O NAVEGADOR A MOSTRAR OS CONTROLES (3 PONTINHOS) */
    header[data-testid="stHeader"] { visibility: hidden !important; }
    .block-container { padding-top: 6rem !important; }

    /* Estilo das Abas (Grandes para o dedo no celular) */
    [data-baseweb="tab-list"] { gap: 10px; overflow-x: auto; }
    [data-baseweb="tab"] { padding: 12px; border-radius: 12px; background: #f0f2f6; min-width: 130px; }
    button { height: 3.8em !important; font-weight: bold !important; border-radius: 15px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES SUPORTE ---
def normalizar(t):
    return "".join(ch for ch in unicodedata.normalize('NFKD', str(t).lower()) if not unicodedata.combining(ch)).strip()

def limpar(v): return re.sub(r'\D', '', str(v))

def mask_tel(v):
    n = limpar(str(v))[:11]
    if len(n) == 11: return f"({n[:2]}) {n[2:7]}-{n[7:11]}"
    if len(n) == 10: return f"({n[:2]}) {n[2:6]}-{n[6:10]}"
    return n if n else "-"

@st.cache_data(ttl=2)
def carregar_dados():
    try:
        url = "https://docs.google.com/spreadsheets/d/1jrtIP1lN644dPqY0HPGGwPWQGyYwb8nWsUigVK3QZio/export?format=csv"
        df = pd.read_csv(url, dtype=str).fillna("")
        mapa = {c: normalizar(c) for c in df.columns}
        df = df.rename(columns={k: 'nome' if 'nome' in v else 'nascimento' if 'nasc' in v else 'vinculo' if 'vinc' in v or 'ascend' in v else 'telefone' if 'tel' in v else 'rua' if 'rua' in v else 'num' if 'num' in v else 'bairro' if 'bair' in v else 'cep' if 'cep' in v else 'email' if 'emai' in v else k for k, v in mapa.items()})
        return df
    except: return pd.DataFrame()

# --- INTERFACE ---
if 'logado' not in st.session_state: st.session_state.logado = False
if not st.session_state.logado:
    st.title("🌳 Portal Família Buscapé")
    psw = st.text_input("Senha", type="password")
    if st.button("ENTRAR NO PORTAL"):
        if psw == "buscape2026": st.session_state.logado = True; st.rerun()
        else: st.error("Senha incorreta!")
else:
    df_todo = carregar_dados()
    if df_todo.empty: st.error("⚠️ Erro ao carregar dados.")
    else:
        df_m = df_todo[df_todo['nome'] != ""].sort_values(by='nome').copy()
        mes_at = datetime.now().month
        MESES_BR = ["", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

        st.title("🌳 Família Buscapé")
        
        # --- REESTRUTURAÇÃO TOTAL EM ABAS ---
        tabs = st.tabs(["🏠 TELA INICIAL", "🔍 MEMBROS", "🎂 NIVER", "📢 MURAL", "➕ NOVO", "✏️ GERENCIAR", "🌳 ÁRVORE", "📖 MANUAL"])

        with tabs[0]: # 1. TELA INICIAL (ANTIGA LATERAL)
            st.subheader("⚙️ Painel de Controle")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("🔄 ATUALIZAR DADOS"): st.cache_data.clear(); st.rerun()
            with c2:
                if st.button("🚪 SAIR DO APP"): st.session_state.logado = False; st.rerun()
            
            st.divider()
            st.subheader("🔔 Notificações")
            niver_mes = [f"🎂 {str(r['nascimento']).split('/')[0]} - {r['nome']}" for _, r in df_m.iterrows() if '/' in str(r['nascimento']) and int(str(r['nascimento']).split('/')[1]) == mes_at]
            if niver_mes:
                st.info(f"**Aniversariantes de {MESES_BR[mes_at]}:**")
                for n in niver_mes: st.write(n)
            else: st.write("Nenhum aniversário para este mês.")

        with tabs[1]: # 2. Membros
            for i, r in df_m.iterrows():
                with st.expander(f"👤 {r['nome']}"):
                    st.write(f"📞 Tel: {mask_tel(r.get('telefone','-'))}")
                    st.write(f"🏠 End: {r.get('rua','-')}, {r.get('num','-')}")
                    t = limpar(r.get('telefone',''))
                    if len(t) >= 10: st.link_button("💬 WhatsApp", f"https://wa.me/55{t}")

        with tabs[2]: # 3. Niver
            st.subheader(f"🎂 Todos de {MESES_BR[mes_at]}")
            for _, r in df_m.iterrows():
                dt = str(r.get('nascimento',''))
                if "/" in dt and int(dt.split('/')[1]) == mes_at: st.info(f"🎈 Dia {dt.split('/')[0]} - {r['nome']}")

        with tabs[6]: # 7. Árvore (SOFIA E GABRIELA)
            st.subheader("🌳 Nossa Árvore")
            dot = 'digraph G { rankdir=LR; node [shape=box, style=filled, fillcolor="#E1F5FE"];'
            for _, row in df_m.iterrows():
                n, v = str(row['nome']), str(row.get('vinculo','Raiz'))
                if " de " in v:
                    ref = v.split(" de ", 1)[-1]
                    dot += f'"{ref}" -> "{n}";'
                elif v == "Raiz": dot += f'"{n}" [fillcolor="#C8E6C9"];'
            dot += '}'
            st.graphviz_chart(dot)

        with tabs[7]: # 8. Manual (SEU TEXTO COMPLETO)
            st.markdown("""
            ### 📖 Manual Familia Buscape
            1. **TELA INICIAL:** Onde você sincroniza os dados e faz o logoff.
            2. **Membros:** Agenda com Zap e Mapa.
            3. **Instalação:** * No **Android**: Clique nos 3 pontinhos (⋮) do Chrome e 'Instalar'.
               * No **iPhone**: Clique no ícone de partilhar (seta) e 'Ecrã principal'.
            
            **SENHA:** `buscape2026`
            """)
