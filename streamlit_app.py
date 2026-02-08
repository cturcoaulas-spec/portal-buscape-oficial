import streamlit as st
import pandas as pd
import requests
import re
import time
import unicodedata
from urllib.parse import quote
from datetime import datetime
from fpdf import FPDF

# 1. ESTILO E ALMA DO PORTAL
st.set_page_config(page_title="Família Buscapé", page_icon="🌳", layout="wide")

st.markdown("""
    <style>
    [data-baseweb="tab-list"] { gap: 8px; overflow-x: auto; }
    [data-baseweb="tab"] { padding: 10px; border-radius: 12px; background: #fdf2f2; min-width: 110px; font-weight: bold; }
    button { height: 3.5em !important; font-weight: bold !important; border-radius: 15px !important; width: 100% !important; background-color: #f8d7da !important; color: #721c24 !important; }
    .stExpander { border-radius: 15px !important; border: 1px solid #f5c6cb !important; background-color: #fff; }
    </style>
    """, unsafe_allow_html=True)

WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzWJ_nDGDe4a81O5BDx3meMbVJjlcMpJoxoO05lilysWJaj_udqeXqvfYFgzvWPlC-Omw/exec"
CSV_URL = "https://docs.google.com/spreadsheets/d/1jrtIP1lN644dPqY0HPGGwPWQGyYwb8nWsUigVK3QZio/export?format=csv"
MESES_BR = ["", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

# --- FERRAMENTAS DE APOIO ---
def limpar(v): return re.sub(r'\D', '', str(v))
def mask_tel(v):
    n = limpar(str(v))[:11]
    if len(n) == 11: return f"({n[:2]}) {n[2:7]}-{n[7:11]}"
    if len(n) == 10: return f"({n[:2]}) {n[2:6]}-{n[6:10]}"
    return n if n else "-"

# --- PORTAL DE ENTRADA ---
if 'logado' not in st.session_state: st.session_state.logado = False
if not st.session_state.logado:
    st.title("🌳 Bem-vindos ao Lar Digital da Família Buscapé")
    st.write("Um lugar para guardar nossas raízes e cultivar nossos laços.")
    psw = st.text_input("Qual é a nossa senha secreta?", type="password")
    if st.button("ABRIR O PORTAL"):
        if psw == "buscape2026": st.session_state.logado = True; st.rerun()
        else: st.error("Senha incorreta! Peça para a Valéria.")
else:
    @st.cache_data(ttl=2)
    def carregar():
        try:
            df = pd.read_csv(CSV_URL, dtype=str).fillna("")
            def norm(t):
                t = t.strip().lower()
                return "".join(ch for ch in unicodedata.normalize('NFKD', t) if not unicodedata.combining(ch))
            df.columns = [norm(c) for c in df.columns]
            mapa = {'nome':'nome','nascimento':'nascimento','vinculo':'vinculo','ascendente':'vinculo','telefone':'telefone','email':'email','rua':'rua','num':'num','numero':'num','conjuge':'conjuge','conjugue':'conjuge','bairro':'bairro','cep':'cep'}
            return df.rename(columns=mapa)
        except: return pd.DataFrame()

    df_todo = carregar(); df_m = df_todo[df_todo['nome'].str.strip() != ""].sort_values(by='nome').copy()
    nomes_lista = sorted([n.strip() for n in df_m['nome'].unique().tolist() if n.strip()])

    with st.sidebar:
        st.title("🎂 Aniversários")
        hoje_dm = datetime.now().strftime("%d/%m")
        niver = [r['nome'] for _, r in df_m.iterrows() if str(r.get('nascimento','')).startswith(hoje_dm)]
        if niver:
            for n in niver: st.success(f"🎈 Hoje: {n}")
        else: st.info("Ninguém soprando velinhas hoje.")
        
        st.divider()
        if st.button("📜 Manual do Usuário (PDF)"):
            pdf = FPDF(); pdf.add_page(); pdf.set_font("Arial", "B", 16)
            pdf.cell(200, 10, "Manual de Uso - Familia Buscape", ln=True, align="C"); pdf.ln(10)
            
            # Texto do Manual (Organizado para evitar erros)
            secoes = [
                ("1. Boas-vindas!", "Este portal foi criado pela Valeria para ser o nosso ponto de encontro oficial. Aqui, nossa historia e nossos contatos estao protegidos e sempre a mao."),
                ("2. O que sao as Abas?", "Membros: Nossa agenda viva. \nNiver: Onde celebramos a vida a cada mes. \nMural: Nosso quadro de avisos coletivo. \nNovo: Para a familia crescer. \nGerenciar: Para manter tudo organizado. \nArvore: Onde vemos quem somos e de onde viemos."),
                ("3. Integracoes Magicas", "Clicando no botao de WhatsApp, voce fala com o parente sem precisar salvar o numero. Clicando no botao de Mapa, o GPS do seu telemovel abre direto na porta da casa dele!"),
                ("4. Responsabilidade", "Lembre-se: o que voce apaga aqui, apaga para todos. Use com carinho e mantenha seus dados sempre em dia!"),
                ("5. No seu Telemovel", "Para ter o icone da Arvore na tela inicial: No Android (Chrome) clique nos 3 pontinhos e 'Instalar'. No iPhone (Safari) clique na seta de partilhar e 'Ecra principal'.")
            ]
            for titulo, texto in secoes:
                pdf.set_font("Arial", "B", 12); pdf.cell(0, 10, titulo, ln=True)
                pdf.set_font("Arial", "", 11); pdf.multi_cell(0, 7, texto); pdf.ln(5)
            
            pdf.set_font("Arial", "B", 12); pdf.cell(0, 10, "SENHA: buscape2026", ln=True, align="C")
            st.download_button("📥 Baixar Guia em PDF", pdf.output(dest='S').encode('latin-1'), "Manual_Buscape.pdf")
            
        st.divider(); st.button("🚪 Sair", on_click=lambda: st.session_state.update({"logado": False}))

    st.title("🌳 Família Buscapé")
    tabs = st.tabs(["🔍 Membros", "🎂 Niver", "📢 Mural", "➕ Novo", "✏️ Gerenciar", "🌳 Árvore"])

    with tabs[0]: # Membros
        st.write("Aqui voce encontra toda a nossa 'tropa'. Use os botoes para falar ou visitar!")
        for i, r in df_m.iterrows():
            nome_at = r.get('nome','').strip()
            with st.expander(f"👤 {nome_at} | 🎂 {r.get('nascimento','-')}"):
                ci, cl = st.columns([3, 1])
                with ci:
                    conj_b = str(r.get('conjuge','')).strip(); vinc_b = str(r.get('vinculo','')).strip(); parc = ""
                    if conj_b.lower() not in ["", "nan", "false", "0", "none", "sim"]: parc = conj_b
                    elif "Cônjuge de" in vinc_b: parc = vinc_b.replace("Cônjuge de", "").strip()
                    else:
                        recip = df_m[df_m['conjuge'].str.strip() == nome_at]['nome'].tolist()
                        if recip: parc = recip[0]
                    if parc and parc != nome_at: st.write(f"💍 **Cônjuge:** {parc}")
                    
                    vinc_f = vinc_b
                    if vinc_b and vinc_b != "Raiz" and "Cônjuge" not in vinc_b and "Filho" not in vinc_b: vinc_f = f"Filho(a) de {vinc_b}"
                    st.write(f"📞 **Tel:** {mask_tel(r.get('telefone','-'))} | 🌳 **Vínculo:** {vinc_f}")
                    st.write(f"🏠 {r.get('rua','-')}, {r.get('num','-')} ({r.get('cep','-')})")
                with cl:
                    t_c = limpar(r.get('telefone',''))
                    if len(t_c) >= 10: 
                        st.link_button("💬 Zap", f"https://wa.me/55{t_c}")
                        st.link_button("📞 Ligar", f"tel:{t_c}")
                    if r.get('rua'): 
                        st.link_button("📍 Mapa", f"https://www.google.com/maps/search/?api=1&query={quote(f'{r.get('rua','')},{r.get('num','')},{r.get('cep','')}')}")
