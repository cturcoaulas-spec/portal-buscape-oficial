import streamlit as st
import pandas as pd
import requests
import re
import time
import unicodedata
from urllib.parse import quote
from datetime import datetime
from fpdf import FPDF

# 1. CONFIGURAÇÃO MOBILE (BOTÕES GRANDES PARA O DEDO)
st.set_page_config(page_title="Família Buscapé", page_icon="🌳", layout="wide")

st.markdown("""
    <style>
    [data-baseweb="tab-list"] { gap: 8px; }
    [data-baseweb="tab"] { padding: 10px; border-radius: 10px; background: #f0f2f6; min-width: 120px; }
    .stButton button { height: 3.5em !important; font-weight: bold !important; border-radius: 12px !important; }
    .stExpander { border-radius: 12px !important; }
    </style>
    """, unsafe_allow_html=True)

WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzWJ_nDGDe4a81O5BDx3meMbVJjlcMpJoxoO05lilysWJaj_udqeXqvfYFgzvWPlC-Omw/exec"
CSV_URL = "https://docs.google.com/spreadsheets/d/1jrtIP1lN644dPqY0HPGGwPWQGyYwb8nWsUigVK3QZio/export?format=csv"

MESES_BR = ["", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

# --- FUNÇÕES (INALTERADAS) ---
def limpar(v): return re.sub(r'\D', '', str(v))
def mask_tel(v):
    n = limpar(v); return f"({n[:2]}) {n[2:7]}-{n[7:11]}" if len(n)==11 else (f"({n[:2]}) {n[2:6]}-{n[6:10]}" if len(n)==10 else v)
def mask_data(v):
    n = limpar(v); return f"{n[:2]}/{n[2:4]}/{n[4:8]}" if len(n)==8 else v
def gerar_pdf(dados):
    pdf = FPDF(); pdf.add_page(); pdf.set_font("Arial", "B", 14)
    pdf.cell(200, 10, "Relatorio Familia Buscape", ln=True, align="C")
    for _, r in dados.iterrows():
        pdf.set_font("Arial", "B", 11); pdf.cell(0, 8, f"Nome: {r.get('nome','-')}", ln=True)
        pdf.set_font("Arial", size=10); pdf.cell(0, 6, f"Nasc: {r.get('nascimento','-')} | Tel: {r.get('telefone','-')}", ln=True)
        end = f"{r.get('rua','-')}, {r.get('num','-')} - {r.get('bairro','-')} ({r.get('cep','-')})"
        pdf.cell(0, 6, f"End: {end}", ln=True); pdf.ln(4); pdf.line(10, pdf.get_y(), 200, pdf.get_y()); pdf.ln(4)
    return pdf.output(dest='S').encode('latin-1')

# --- LOGIN ---
if 'logado' not in st.session_state: st.session_state.logado = False
if not st.session_state.logado:
    st.title("🌳 Portal Família Buscapé")
    psw = st.text_input("Senha", type="password")
    if st.button("ENTRAR"):
        if psw == "buscape2026": st.session_state.logado = True; st.rerun()
        else: st.error("Senha incorreta")
else:
    @st.cache_data(ttl=2)
    def carregar():
        try:
            df = pd.read_csv(CSV_URL, dtype=str).fillna("")
            def norm(t):
                t = t.strip().lower()
                return "".join(ch for ch in unicodedata.normalize('NFKD', t) if not unicodedata.combining(ch))
            df.columns = [norm(c) for c in df.columns]; mapa = {'nome':'nome','nascimento':'nascimento','vinculo':'vinculo','ascendente':'vinculo','telefone':'telefone','email':'email','rua':'rua','num':'num','numero':'num','conjuge':'conjuge','conjugue':'conjuge','bairro':'bairro','cep':'cep'}
            return df.rename(columns=mapa)
        except: return pd.DataFrame()

    df_todo = carregar(); df_m = df_todo[df_todo['nome'].str.strip() != ""].sort_values(by='nome').copy()
    nomes_lista = sorted([n.strip() for n in df_m['nome'].unique().tolist() if n.strip()])

    with st.sidebar:
        st.title("🔔 Notificações")
        hoje_dm = datetime.now().strftime("%d/%m")
        niver_hoje = [r['nome'] for _, r in df_m.iterrows() if str(r.get('nascimento','')).startswith(hoje_dm)]
        if niver_hoje:
            for n in niver_hoje: st.success(f"🎂 Hoje: {n}")
        else: st.info("Sem notificações hoje")
        st.divider(); st.button("🚪 Sair", on_click=lambda: st.session_state.update({"logado": False}))

    st.title("🌳 Família Buscapé")
    tabs = st.tabs(["🔍 Membros", "🎂 Aniversários", "📢 Mural", "➕ Cadastrar", "✏️ Gerenciar", "🌳 Árvore"])

    # --- TABS 0 A 4 (TOTALMENTE TRANCADAS) ---
    with tabs[0]: # Membros
        sel_ids = []; c_top = st.container()
        for i, r in df_m.iterrows():
            c_s, c_e = st.columns([0.2, 3.8])
            if c_s.checkbox("", key=f"s_{i}"): sel_ids.append(i)
            nome_at = r.get('nome','').strip()
            with c_e.expander(f"👤 {nome_at} | 🎂 {r.get('nascimento','-')}"):
                ci, cl = st.columns([3, 1])
                with ci:
                    conj = str(r.get('conjuge','')).strip()
                    quem = df_m[df_m['conjuge'].str.strip() == nome_at]['nome'].tolist()
                    parc = conj if conj.lower() not in ["","nan","false","0"] else (quem[0] if quem else "")
                    st.write(f"💍 **Cônjuge:** {parc}" if parc else "**Cônjuge:** Nenhum")
                    v_b = str(r.get('vinculo','')).strip()
                    st.write(f"📞 **Tel:** {r.get('telefone','-')} | 🌳 **Vínculo:** {f'Filho(a) de {v_b}' if v_b and v_b!='Raiz' and 'Filho' not in v_b and 'Cônjuge' not in v_b else v_b}")
                    st.write(f"🏠 {r.get('rua','-')}, {r.get('num','-')} - {r.get('bairro','-')}")
                with cl:
                    t = limpar(r.get('telefone',''))
                    if len(t)>=10: st.link_button("💬 Zap", f"https://wa.me/55{t}"); st.link_button("📞 Ligar", f"tel:{t}")
                    if r.get('rua'): st.link_button("📍 Mapa", f"https://www.google.com/maps/search/?api=1&query={quote(f'{r['rua']},{r['num']},{r['cep']}')}")
        if sel_ids: c_top.download_button("📥 PDF", gerar_pdf(df_m.loc[sel_ids]), "fam.pdf")

    with tabs[1]: # Aniversários
        m = datetime.now().month; st.subheader(f"🎂 {MESES_BR[m]}")
        for _, r in df_m.iterrows():
            dt = str(r.get('nascimento',''))
            if "/" in dt and int(dt.split('/')[1])==m: st.info(f"🎈 {dt.split('/')[0]} - {r['nome']}")

    with tabs[2]: # Mural
        try: avs = [df_todo.iloc[0].get('email',''), df_todo.iloc[0].get('rua',''), df_todo.iloc[0].get('num','')]
        except: avs = ["","",""]
        cols = st.columns(3)
        for idx in range(3): cols[idx].warning(f"**Aviso {idx+1}**\n\n{avs[idx]}")
        with st.form("fm"):
            v1, v2, v3 = st.text_input("A1", avs[0]), st.text_input("A2", avs[1]), st.text_input("A3", avs[2])
            if st.form_submit_button("💾 Salvar"): requests.post(WEBAPP_URL, json={"action":"edit", "row":2, "data":["AVISO","","","",v1, v2, v3, "","",""]}); st.rerun()

    with tabs[3]: # Cadastrar
        with st.form("fc"):
            c_a, c_b = st.columns(2)
            with c_a: nc, dc, tc = st.text_input("Nome *"), st.text_input("Nasc *"), st.text_input("Tel"); vc = st.radio("Vinculo", ["Filho(a) de", "Cônjuge de"], horizontal=True); rc = st.selectbox("Ref *", ["Raiz"]+nomes_lista)
            with c_b: em, ru, nu = st.text_input("E-mail"), st.text_input("Rua"), st.text_input("Nº"); ba, ce = st.text_input("Bairro"), st.text_input("CEP")
            if st.form_submit_button("💾 Salvar"): requests.post(WEBAPP_URL, json={"action":"append", "data":[nc, mask_data(dc), f"{vc} {rc}" if rc!="Raiz" else "Raiz", mask_tel(tc), em, ru, nu, rc if "Cônjuge" in vc else "", ba, ce]}); st.rerun()

    with tabs[4]: # Gerenciar
        esc = st.selectbox("Editar", ["--"]+nomes_lista)
        if esc != "--":
            m = df_m[df_m['nome']==esc].iloc[0]; idx = df_todo.index[df_todo['nome']==esc].tolist()[0]+2
            with st.form("fe"):
                c1, c2 = st.columns(2)
                with c1: st.text_input("Nome", value=esc, disabled=True); ed, et = st.text_input("Nasc", m['nascimento']), st.text_input("Tel", m['telefone']); ev = st.radio("Tipo", ["Filho(a) de", "Cônjuge de"], index=1 if "Cônjuge" in m['vinculo'] else 0); er = st.selectbox("Ref", ["Raiz"]+nomes_lista)
                with c2: em, ru, nu = st.text_input("E-mail", m['email']), st.text_input("Rua", m['rua']), st.text_input("Nº", m['num']); ba, ce = st.text_input("Bairro", m['bairro']), st.text_input("CEP", m['cep'])
                if st.form_submit_button("💾 Atualizar"): requests.post(WEBAPP_URL, json={"action":"edit", "row":idx, "data":[esc, mask_data(ed), f"{ev} {er}", mask_tel(et), em, ru, nu, er if "Cônjuge" in ev else "", ba, ce]}); st.rerun()

    # --- TAB 5: ÁRVORE GENEALÓGICA (FLUXOGRAMA SÓ NOMES) ---
    with tabs[5]:
        st.subheader("🌳 Organograma da Família")
        
        # Criando o código do Fluxograma (DOT)
        dot_code = 'digraph G { rankdir=LR; node [shape=box, style=filled, fillcolor="#E1F5FE", fontname="Arial", fontsize=10]; edge [color="#546E7A"];'
        
        for _, row in df_m.iterrows():
            nome = row['nome'].strip()
            vinc = row['vinculo'].strip()
            
            if vinc != "Raiz":
                # Extrai o nome da referência (quem vem depois do "de ")
                referencia = vinc.split(" de ")[-1] if " de " in vinc else vinc
                
                # Se for cônjuge, a linha é diferente (tracejada)
                if "Cônjuge" in vinc:
                    dot_code += f'"{referencia}" -> "{nome}" [label=" 💍", style=dashed];'
                else:
                    dot_code += f'"{referencia}" -> "{nome}";'
            else:
                # É um patriarca/matriarca (Raiz)
                dot_code += f'"{nome}" [fillcolor="#C8E6C9", style=filled];'
        
        dot_code += '}'
        
        # Renderiza o Fluxograma
        st.graphviz_chart(dot_code)
        st.info("💡 Caixas verdes são as Raízes. Linhas contínuas são filhos, tracejadas são cônjuges.")
