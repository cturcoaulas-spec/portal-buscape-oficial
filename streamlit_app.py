import streamlit as st
import pandas as pd
import requests
import re
import unicodedata
from urllib.parse import quote
from datetime import datetime
from fpdf import FPDF

# 1. CONFIGURAÇÃO E BLINDAGEM DE INTERFACE (ESCONDE BOTÕES DE CÓDIGO)
st.set_page_config(page_title="Família Buscapé", page_icon="🌳", layout="wide")

st.markdown("""
    <style>
    /* Esconde o Menu de Hambúrguer, o Footer e o Header de Edição */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDecoration {display:none;}
    
    /* Estilo das Abas e Botões Mobile */
    [data-baseweb="tab-list"] { gap: 8px; overflow-x: auto; }
    [data-baseweb="tab"] { padding: 10px; border-radius: 12px; background: #fdf2f2; min-width: 110px; font-weight: bold; }
    button { height: 3.5em !important; font-weight: bold !important; border-radius: 15px !important; width: 100% !important; background-color: #f8d7da !important; color: #721c24 !important; }
    .stExpander { border-radius: 15px !important; border: 1px solid #f5c6cb !important; background-color: #fff; }
    </style>
    """, unsafe_allow_html=True)

WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzWJ_nDGDe4a81O5BDx3meMbVJjlcMpJoxoO05lilysWJaj_udqeXqvfYFgzvWPlC-Omw/exec"
CSV_URL = "https://docs.google.com/spreadsheets/d/1jrtIP1lN644dPqY0HPGGwPWQGyYwb8nWsUigVK3QZio/export?format=csv"
MESES_BR = ["", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

# --- FUNÇÕES DE SUPORTE ---
def limpar(v): return re.sub(r'\D', '', str(v))
def mask_tel(v):
    n = limpar(str(v))[:11]
    if len(n) == 11: return f"({n[:2]}) {n[2:7]}-{n[7:11]}"
    if len(n) == 10: return f"({n[:2]}) {n[2:6]}-{n[6:10]}"
    return n if n else "-"

# --- LOGIN ---
if 'logado' not in st.session_state: st.session_state.logado = False
if not st.session_state.logado:
    st.title("🌳 Família Buscapé")
    psw = st.text_input("Senha da Família", type="password")
    if st.button("ENTRAR"):
        if psw == "buscape2026": st.session_state.logado = True; st.rerun()
        else: st.error("Senha incorreta!")
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
        else: st.info("Sem notificações hoje.")
        
        st.divider()
        if st.button("📜 Guia de Uso (PDF)"):
            pdf = FPDF(); pdf.add_page(); pdf.set_font("Arial", "B", 16)
            pdf.cell(200, 10, "Manual Familia Buscape", ln=True, align="C"); pdf.ln(10)
            pdf.set_font("Arial", "B", 12); pdf.cell(0, 10, "1. Responsabilidade Coletiva", ln=True)
            pdf.set_font("Arial", "", 11); pdf.multi_cell(0, 7, "Este e um espaco da Familia Buscape. O que voce edita ou apaga muda para todos. Use com carinho!")
            pdf.ln(10); pdf.cell(0, 10, "SENHA DE ACESSO: buscape2026", ln=True, align="C")
            st.download_button("📥 Baixar Guia PDF", pdf.output(dest='S').encode('latin-1'), "Guia_Buscape.pdf")
            
        st.divider(); st.button("🚪 Sair", on_click=lambda: st.session_state.update({"logado": False}))

    st.title("🌳 Família Buscapé")
    tabs = st.tabs(["🔍 Membros", "🎂 Niver", "📢 Mural", "➕ Novo", "✏️ Gerenciar", "🌳 Árvore"])

    with tabs[0]: # Aba Membros com Lógica de Cônjuge Blindada
        for i, r in df_m.iterrows():
            nome_at = r.get('nome','').strip()
            with st.expander(f"👤 {nome_at} | 🎂 {r.get('nascimento','-')}"):
                ci, cl = st.columns([3, 1])
                with ci:
                    # Lógica para garantir que André e Afonso se reconheçam mutuamente
                    conj_b = str(r.get('conjuge','')).strip()
                    vinc_b = str(r.get('vinculo','')).strip()
                    parc = ""
                    if conj_b.lower() not in ["", "nan", "false", "0", "sim", "nenhum"]: parc = conj_b
                    elif "Cônjuge de" in vinc_b: parc = vinc_b.replace("Cônjuge de", "").strip()
                    else:
                        # Busca se alguém apontou este membro como cônjuge
                        recip = df_m[(df_m['conjuge'].str.strip() == nome_at) | (df_m['vinculo'].str.contains(f"Cônjuge de {nome_at}", case=False, na=False))]['nome'].tolist()
                        if recip: parc = recip[0]
                    
                    if parc and parc != nome_at: st.write(f"💍 **Cônjuge:** {parc}")
                    else: st.write("**Cônjuge:** Nenhum")
                    
                    vinc_f = vinc_b
                    if vinc_b and vinc_b != "Raiz" and "Cônjuge" not in vinc_b and "Filho" not in vinc_b:
                        vinc_f = f"Filho(a) de {vinc_b}"
                    st.write(f"📞 **Tel:** {mask_tel(r.get('telefone','-'))} | 🌳 **Vínculo:** {vinc_f}")
                with cl:
                    t_c = limpar(r.get('telefone',''))
                    if len(t_c) >= 10:
                        st.link_button("💬 Zap", f"https://wa.me/55{t_c}")
                        st.link_button("📞 Ligar", f"tel:{t_c}")
                    if r.get('rua'):
                        st.link_button("📍 Mapa", f"https://www.google.com/maps/search/?api=1&query={quote(f'{r.get('rua','')},{r.get('num','')},{r.get('cep','')}')}")

    with tabs[1]: # Niver
        m_at = datetime.now().month; st.subheader(f"🎂 {MESES_BR[m_at]}")
        for _, r in df_m.iterrows():
            dt = str(r.get('nascimento',''))
            if "/" in dt and int(dt.split('/')[1]) == m_at: st.info(f"🎈 Dia {dt.split('/')[0]} - {r['nome']}")

    with tabs[2]: # Mural
        try: avs = [df_todo.iloc[0].get('email',''), df_todo.iloc[0].get('rua',''), df_todo.iloc[0].get('num','')]
        except: avs = ["","",""]
        cols = st.columns(3)
        for idx in range(3): cols[idx].warning(f"**Aviso {idx+1}**\n\n{avs[idx]}")
        with st.form("m_f"):
            v1, v2, v3 = st.text_input("A1", avs[0]), st.text_input("A2", avs[1]), st.text_input("A3", avs[2])
            if st.form_submit_button("💾 Salvar"): requests.post(WEBAPP_URL, json={"action":"edit", "row":2, "data":["AVISO","","","",v1, v2, v3, "","",""]}); st.rerun()

    with tabs[3]: # Novo
        with st.form("c_f", clear_on_submit=True):
            ca, cb = st.columns(2)
            with ca: nc, dc, tc = st.text_input("Nome *"), st.text_input("Nasc *"), st.text_input("Tel"); vc = st.radio("Vínculo", ["Filho(a) de", "Cônjuge de"], horizontal=True); rc = st.selectbox("Ref *", ["Raiz"] + nomes_lista)
            with cb: mc, ru, nu = st.text_input("Email"), st.text_input("Rua"), st.text_input("Nº")
            if st.form_submit_button("💾 Salvar"):
                v_f = f"{vc} {rc}" if rc != "Raiz" else "Raiz"
                requests.post(WEBAPP_URL, json={"action":"append", "data":[nc, dc, v_f, tc, mc, ru, nu, rc if "Cônjuge" in vc else "", "", ""]}); st.rerun()

    with tabs[4]: # Gerenciar
        esc = st.selectbox("Editar", ["--"] + nomes_lista)
        if esc != "--":
            m = df_m[df_m['nome'] == esc].iloc[0]; idx = df_todo.index[df_todo['nome'] == esc].tolist()[0] + 2
            with st.form("g_f"):
                c1, c2 = st.columns(2)
                with c1: st.text_input("Nome", value=esc, disabled=True); ed, et = st.text_input("Nasc", m['nascimento']), st.text_input("Tel", m['telefone'])
                with c2: em, ru, nu = st.text_input("Email", m['email']), st.text_input("Rua", m['rua']), st.text_input("Nº", m['num'])
                b1, b2 = st.columns(2)
                if b1.form_submit_button("💾 Atualizar"): requests.post(WEBAPP_URL, json={"action":"edit", "row":idx, "data":[esc, ed, m['vinculo'], et, em, ru, nu, m.get('conjuge',''), "", ""]}); st.rerun()
                if b2.form_submit_button("🗑️ Excluir"): requests.post(WEBAPP_URL, json={"action":"edit", "row":idx, "data":[""]*10}); st.rerun()

    with tabs[5]: # Árvore
        st.subheader("🌳 Nossa Árvore")
        dot = 'digraph G { rankdir=LR; node [shape=box, style=filled, fillcolor="#E1F5FE", fontname="Arial", fontsize=10]; edge [color="#546E7A"];'
        for _, row in df_m.iterrows():
            n, v = row['nome'].strip(), row['vinculo'].strip()
            if v != "Raiz":
                ref = v.split(" de ")[-1] if " de " in v else v
                dot += f'"{ref}" -> "{n}" [style={"dashed" if "Cônjuge" in v else "solid"}];'
            else: dot += f'"{n}" [fillcolor="#C8E6C9"];'
        st.graphviz_chart(dot + '}')
