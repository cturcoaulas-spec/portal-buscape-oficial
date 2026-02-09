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

# 2. BLINDAGEM CIRÚRGICA (MANTIDA DO SEU SUCESSO + AJUSTE DE RESPIRO)
st.markdown("""
    <style>
    /* ESCONDE O MANAGE APP E BOTÕES DE SISTEMA */
    .viewerBadge_container__1QSob, .stAppDeployButton, #MainMenu { display: none !important; }
    [data-testid="stStatusWidget"], [data-testid="stToolbar"], [data-testid="stDecoration"] { display: none !important; }
    footer { display: none !important; }

    /* LIBERA O TOPO PARA O NAVEGADOR (CHROME / SAFARI) */
    header[data-testid="stHeader"] {
        background-color: rgba(255, 255, 255, 0) !important;
    }
    
    /* AUMENTADO PARA 5.5rem: Isso força o Chrome a mostrar a barra de ferramentas */
    .block-container { padding-top: 5.5rem !important; }

    /* ESTILO DAS ABAS E BOTÕES - PRESERVADOS */
    [data-baseweb="tab-list"] { gap: 8px; overflow-x: auto; }
    [data-baseweb="tab"] { padding: 10px; border-radius: 10px; background: #f0f2f6; min-width: 110px; }
    button { height: 3.5em !important; font-weight: bold !important; border-radius: 12px !important; width: 100% !important; }
    .stExpander { border-radius: 12px !important; border: 1px solid #ddd !important; }
    </style>
    """, unsafe_allow_html=True)

# --- TODA A SUA PROGRAMAÇÃO INTERNA SEGUE ABAIXO SEM ALTERAÇÃO ---
# (Aqui entra o seu login, funções de máscara, carregamento de dados, etc.)

# --- INTERFACE ---
if 'logado' not in st.session_state: st.session_state.logado = False
if not st.session_state.logado:
    st.title("🌳 Portal Família Buscapé")
    psw = st.text_input("Senha", type="password")
    if st.button("ENTRAR"):
        if psw == "buscape2026": st.session_state.logado = True; st.rerun()
        else: st.error("Senha incorreta!")
else:
    df_todo = carregar_dados() # Chama sua função original
    if not df_todo.empty:
        df_m = df_todo[df_todo['nome'] != ""].sort_values(by='nome').copy()
        
        with st.sidebar:
            st.title("⚙️ Painel")
            # Suas notificações originais...
            if st.button("🚪 Sair", on_click=lambda: st.session_state.update({"logado": False})): st.rerun()

        st.title("🌳 Família Buscapé")
        
        tabs = st.tabs(["🔍 Membros", "🎂 Niver", "📢 Mural", "➕ Novo", "✏️ Gerenciar", "🌳 Árvore", "📖 Manual"])

        # Abas de 0 a 5 com seu conteúdo original...

        with tabs[6]: # 7. Manual (O TEXTO QUE VOCÊ PEDIU)
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
