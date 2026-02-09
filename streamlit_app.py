import streamlit as st
import pandas as pd
import requests
import re
import unicodedata
import time
from urllib.parse import quote
from datetime import datetime
from fpdf import FPDF

# 1. CONFIGURAÇÃO (NOME DO APP)
st.set_page_config(page_title="FBUSCAPE", page_icon="🌳", layout="wide")

# 2. BLINDAGEM LEVE (SÓ O ESSENCIAL PARA NÃO SUMIR TUDO)
st.markdown("""
    <style>
    /* Esconde apenas os botões de edição para a família */
    .viewerBadge_container__1QSob, .stAppDeployButton { display: none !important; }
    footer { display: none !important; }
    
    /* Garante que o menu lateral (hambúrguer) seja clicável e visível */
    header[data-testid="stHeader"] {
        visibility: visible !important;
        background-color: white !important;
    }

    /* Espaço para o navegador (Chrome/Safari) não 'comer' o topo */
    .block-container { padding-top: 2rem !important; }

    /* Estilo das Abas */
    [data-baseweb="tab-list"] { gap: 8px; overflow-x: auto; }
    [data-baseweb="tab"] { padding: 10px; border-radius: 10px; background: #f0f2f6; min-width: 110px; }
    </style>
    """, unsafe_allow_html=True)

# LINKS DE INTEGRAÇÃO
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzWJ_nDGDe4a81O5BDx3meMbVJjlcMpJoxoO05lilysWJaj_udqeXqvfYFgzvWPlC-Omw/exec"
CSV_URL = "https://docs.google.com/spreadsheets/d/1jrtIP1lN644dPqY0HPGGwPWQGyYwb8nWsUigVK3QZio/export?format=csv"
MESES_BR = ["", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

def normalizar(t): return "".join(ch for ch in unicodedata.normalize('NFKD', str(t).lower()) if not unicodedata.combining(ch)).strip()
def limpar(v): return re.sub(r'\D', '', str(v))
def mask_tel(v):
    n = limpar(str(v))[:11]
    if len(n) == 11: return f"({n[:2]}) {n[2:7]}-{n[7:11]}"
    return f"({n[:2]}) {n[2:6]}-{n[6:10]}" if len(n) == 10 else n

@st.cache_data(ttl=2)
def carregar_dados():
    try:
        df = pd.read_csv(CSV_URL, dtype=str).fillna("")
        mapa = {c: normalizar(c) for c in df.columns}
        df = df.rename(columns={k: 'nome' if 'nome' in v else 'nascimento' if 'nasc' in v else 'vinculo' if 'vinc' in v or 'ascend' in v else 'telefone' if 'tel' in v else 'rua' if 'rua' in v else 'num' if 'num' in v else 'bairro' if 'bair' in v else 'cep' if 'cep' in v else 'email' if 'emai' in v else k for k, v in mapa.items()})
        return df
    except: return pd.DataFrame()

# --- LOGIN ---
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
        
        # BARRA LATERAL (PAINEL DE NOTIFICAÇÕES)
        with st.sidebar:
            st.title("⚙️ Painel")
            st.subheader("🔔 Notificações")
            mes_at = datetime.now().month
            for _, r in df_m.iterrows():
                dt = str(r.get('nascimento',''))
                if "/" in dt and int(dt.split('/')[1]) == mes_at:
                    st.info(f"🎂 {dt.split('/')[0]} - {r['nome']}")
            st.divider()
            if st.button("🚪 Sair"): st.session_state.logado = False; st.rerun()

        st.title("🌳 Família Buscapé")
        tabs = st.tabs(["🔍 Membros", "🌳 Árvore", "📖 Manual", "✏️ Gerenciar"])

        with tabs[0]: # 1. Membros
            for i, r in df_m.iterrows():
                with st.expander(f"👤 {r['nome']}"):
                    st.write(f"📞 Tel: {mask_tel(r.get('telefone','-'))}")
                    st.write(f"🏠 End: {r.get('rua','-')}, {r.get('num','-')}")

        with tabs[1]: # 2. Árvore (Sofia/Gabriela)
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

        with tabs[2]: # 3. Manual (TEXTO COMPLETO)
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

        with tabs[3]: # 4. Gerenciar
            st.info("Área de edição de dados.")
