import streamlit as st
import pandas as pd
import requests
import re
import unicodedata
import time
from urllib.parse import quote
from datetime import datetime
from fpdf import FPDF

# 1. CONFIGURAÇÃO BÁSICA
st.set_page_config(page_title="FBUSCAPE", page_icon="🌳", layout="wide")

# 2. CSS SIMPLIFICADO (NÃO BLOQUEIA O NAVEGADOR NEM A LATERAL)
st.markdown("""
    <style>
    /* Esconde apenas o botão vermelho do Streamlit */
    .viewerBadge_container__1QSob, .stAppDeployButton { display: none !important; }
    footer { display: none !important; }
    
    /* Garante que o botão do menu lateral (hambúrguer) apareça no topo */
    header[data-testid="stHeader"] {
        visibility: visible !important;
        background-color: white !important;
    }

    /* Dá um espaço no topo para o Chrome mostrar os 3 pontinhos */
    .block-container { 
        padding-top: 3rem !important; 
    }

    /* Estilo das Abas */
    [data-baseweb="tab-list"] { gap: 8px; overflow-x: auto; }
    [data-baseweb="tab"] { padding: 10px; border-radius: 10px; background: #f0f2f6; min-width: 110px; }
    </style>
    """, unsafe_allow_html=True)

# 3. FUNÇÕES E DADOS (A LINHA DO SEU PROJETO)
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

# 4. INTERFACE
if 'logado' not in st.session_state: st.session_state.logado = False
if not st.session_state.logado:
    st.title("🌳 Portal Família Buscapé")
    psw = st.text_input("Senha", type="password")
    if st.button("ENTRAR"):
        if psw == "buscape2026": st.session_state.logado = True; st.rerun()
        else: st.error("Senha incorreta!")
else:
    df_todo = carregar_dados()
    if df_todo.empty: st.error("⚠️ Erro ao carregar os dados da planilha.")
    else:
        df_m = df_todo[df_todo['nome'] != ""].sort_values(by='nome').copy()
        
        # BARRA LATERAL (MENU HAMBÚRGUER)
        with st.sidebar:
            st.title("⚙️ Painel")
            st.subheader("🔔 Notificações")
            mes_at = datetime.now().month
            niver_mes = [f"🎂 {str(r['nascimento']).split('/')[0]} - {r['nome']}" for _, r in df_m.iterrows() if '/' in str(r['nascimento']) and int(str(r['nascimento']).split('/')[1]) == mes_at]
            if niver_mes:
                for n in niver_mes: st.write(n)
            else: st.write("Sem avisos para este mês.")
            st.divider()
            if st.button("🚪 Sair"): st.session_state.logado = False; st.rerun()

        st.title("🌳 Família Buscapé")
        tabs = st.tabs(["🔍 Membros", "🎂 Niver", "📢 Mural", "➕ Novo", "✏️ Gerenciar", "🌳 Árvore", "📖 Manual"])

        with tabs[0]: # 1. Membros
            for i, r in df_m.iterrows():
                with st.expander(f"👤 {r['nome']}"):
                    st.write(f"📞 Tel: {mask_tel(r.get('telefone','-'))}")
                    st.write(f"🏠 End: {r.get('rua','-')}, {r.get('num','-')}")
                    t = limpar(r.get('telefone',''))
                    if len(t) >= 10: st.link_button("💬 WhatsApp", f"https://wa.me/55{t}")

        with tabs[5]: # 6. Árvore (Sofia/Gabriela)
            st.subheader("🌳 Nossa Árvore")
            dot = 'digraph G { rankdir=LR; node [shape=box, style=filled, fillcolor="#E1F5FE", fontname="Arial"];'
            for _, row in df_m.iterrows():
                n, v = str(row['nome']), str(row.get('vinculo','Raiz'))
                if " de " in v:
                    ref = v.split(" de ", 1)[-1]
                    dot += f'"{ref}" -> "{n}";'
                elif v == "Raiz": dot += f'"{n}" [fillcolor="#C8E6C9"];'
            dot += '}'
            st.graphviz_chart(dot)

        with tabs[6]: # 7. Manual (COMPLETO)
            st.markdown("""
            ### 📖 Manual Familia Buscape
            1. **Boas-vindas!** Este portal foi criado pela Valeria para ser o nosso ponto de encontro oficial. 
            2. **O que sao as Abas?** **Membros:** Agenda viva. **Niver:** Aniversários. **Mural:** Avisos. **Novo:** Cadastro. **Gerenciar:** Edição. **Arvore:** Nossa história.
            3. **Integracoes:** Clique no WhatsApp para falar ou no Mapa para abrir o GPS.
            4. **No seu Telemovel:** **Android (Chrome):** use os 3 pontinhos e 'Instalar'. **iPhone (Safari):** use a seta de partilhar e 'Ecra principal'.
            ---
            **🔑 SENHA:** `buscape2026`
            """)
