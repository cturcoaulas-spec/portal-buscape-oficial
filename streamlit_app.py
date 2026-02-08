import streamlit as st
import pandas as pd
import requests
import re
import unicodedata
import time
from urllib.parse import quote
from datetime import datetime
from fpdf import FPDF

# 1. CONFIGURAÇÃO MOBILE E ESTILO
st.set_page_config(page_title="Família Buscapé", page_icon="🌳", layout="wide")

st.markdown("""
    <style>
    [data-baseweb="tab-list"] { gap: 8px; overflow-x: auto; }
    [data-baseweb="tab"] { padding: 10px; border-radius: 10px; background: #f0f2f6; min-width: 110px; }
    button { height: 3.5em !important; font-weight: bold !important; border-radius: 12px !important; width: 100% !important; }
    .stExpander { border-radius: 12px !important; border: 1px solid #ddd !important; }
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

def mask_data(v):
    n = limpar(str(v))
    if len(n) == 8: return f"{n[:2]}/{n[2:4]}/{n[4:8]}"
    return v

def gerar_pdf_membros(dados):
    pdf = FPDF()
    pdf.add_page(); pdf.set_font("Arial", "B", 14)
    pdf.cell(200, 10, "Relatorio Familia Buscape", ln=True, align="C")
    for _, r in dados.iterrows():
        pdf.set_font("Arial", "B", 11); pdf.cell(0, 8, f"Nome: {r.get('nome','-')}", ln=True)
        pdf.set_font("Arial", size=10); pdf.cell(0, 6, f"Nasc: {r.get('nascimento','-')} | Tel: {mask_tel(r.get('telefone','-'))}", ln=True)
        pdf.cell(0, 6, f"End: {r.get('rua','-')}, {r.get('num','-')} ({r.get('cep','-')})", ln=True)
        pdf.ln(4); pdf.line(10, pdf.get_y(), 200, pdf.get_y()); pdf.ln(4)
    return pdf.output(dest='S').encode('latin-1')

# --- LOGIN ---
if 'logado' not in st.session_state: st.session_state.logado = False
if not st.session_state.logado:
    st.title("🌳 Portal Família Buscapé")
    st.info("Digite a senha da família para entrar:")
    psw = st.text_input("Senha de Acesso", type="password")
    if st.button("ENTRAR NO PORTAL"):
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
            # Limpeza crucial: remove espaços extras dos nomes
            if 'nome' in df.columns: df['nome'] = df['nome'].str.strip()
            mapa = {'nome':'nome','nascimento':'nascimento','vinculo':'vinculo','ascendente':'vinculo','telefone':'telefone','email':'email','rua':'rua','num':'num','numero':'num','conjuge':'conjuge','conjugue':'conjuge','bairro':'bairro','cep':'cep'}
            return df.rename(columns=mapa)
        except: return pd.DataFrame()

    df_todo = carregar()
    df_m = df_todo[df_todo['nome'].str.strip() != ""].sort_values(by='nome').copy()
    nomes_lista = sorted([n for n in df_m['nome'].unique().tolist() if n])

    with st.sidebar:
        st.title("🔔 Notificações")
        hoje_dm = datetime.now().strftime("%d/%m")
        niver_hoje = [r['nome'] for _, r in df_m.iterrows() if str(r.get('nascimento','')).startswith(hoje_dm)]
        if niver_hoje:
            for n in niver_hoje: st.success(f"🎂 Hoje: {n}")
        else: st.info("Sem aniversários hoje")
        
        st.divider()
        if st.button("📄 Gerar Guia de Uso (PDF)"):
            pdf_m = FPDF(); pdf_m.add_page()
            pdf_m.set_font("Arial", "B", 16); pdf_m.cell(200, 10, "Manual Familia Buscape", ln=True, align="C"); pdf_m.ln(10)
            sections = [
                ("1. Boas-vindas!", "Portal oficial da Familia Buscape. Protecao e uniao."),
                ("2. O que sao as Abas?", "Membros, Niver, Mural, Novo, Gerenciar, Arvore."),
                ("3. Integracoes", "WhatsApp e Mapa direto pelo portal."),
                ("4. Responsabilidade", "O que voce apaga, apaga para todos!"),
                ("5. No Celular", "Android: Adicionar a tela inicial. iPhone: Adicionar a Tela de Inicio.")
            ]
            for t, b in sections:
                pdf_m.set_font("Arial", "B", 12); pdf_m.cell(0, 10, t, ln=True)
                pdf_m.set_font("Arial", "", 11); pdf_m.multi_cell(0, 7, b); pdf_m.ln(4)
            manual_out = pdf_m.output(dest='S').encode('latin-1')
            st.download_button("📥 BAIXAR MANUAL", manual_out, "Manual_Buscape.pdf")
            
        if st.button("🔄 Atualizar Dados"): st.cache_data.clear(); st.rerun()
        st.divider(); st.button("🚪 Sair", on_click=lambda: st.session_state.update({"logado": False}))

    st.title("🌳 Família Buscapé")
    tabs = st.tabs(["🔍 Membros", "🎂 Niver", "📢 Mural", "➕ Novo", "✏️ Gerenciar", "🌳 Árvore", "📖 Manual"])

    with tabs[0]: # 1. Membros
        for i, r in df_m.iterrows():
            with st.expander(f"👤 {r['nome']} | 🎂 {r.get('nascimento','-')}"):
                ci, cl = st.columns([3, 1])
                with ci:
                    st.write(f"📞 **Tel:** {mask_tel(r.get('telefone','-'))}")
                    st.write(f"🏠 {r.get('rua','-')}, {r.get('num','-')}")
                with cl:
                    t_c = limpar(r.get('telefone',''))
                    if len(t_c) >= 10: st.link_button("💬 Zap", f"https://wa.me/55{t_c}")
                    if r.get('rua'): st.link_button("📍 Mapa", f"https://www.google.com/maps/search/?api=1&query={quote(f'{r.get('rua','')},{r.get('num','')}')}")

    with tabs[1]: # 2. Aniversários
        m_at = datetime.now().month
        st.subheader(f"🎂 Aniversariantes de {MESES_BR[m_at]}")
        for _, r in df_m.iterrows():
            dt = str(r.get('nascimento',''))
            if "/" in dt and int(dt.split('/')[1]) == m_at: st.info(f"🎈 Dia {dt.split('/')[0]} - {r['nome']}")

    with tabs[2]: # 3. Mural
        try: avs = [df_todo.iloc[0].get('email','Vazio'), df_todo.iloc[0].get('rua','Vazio'), df_todo.iloc[0].get('num','Vazio')]
        except: avs = ["Vazio", "Vazio", "Vazio"]
        cols = st.columns(3)
        for idx in range(3): cols[idx].warning(f"**Aviso {idx+1}**\n\n{avs[idx]}")
        with st.form("m_f"):
            v1, v2, v3 = st.text_input("A1", avs[0]), st.text_input("A2", avs[1]), st.text_input("A3", avs[2])
            if st.form_submit_button("💾 SALVAR"): requests.post(WEBAPP_URL, json={"action":"edit", "row":2, "data":["AVISO","","","",v1, v2, v3, "","",""]}); st.rerun()

    with tabs[3]: # 4. Cadastrar
        with st.form("c_f", clear_on_submit=True):
            nc, dc, tc = st.text_input("Nome *"), st.text_input("Nasc *"), st.text_input("Tel")
            vc = st.radio("Vínculo", ["Filho(a) de", "Cônjuge de"], horizontal=True)
            rc = st.selectbox("Ref *", ["Raiz"] + nomes_lista)
            if st.form_submit_button("💾 SALVAR NOVO"):
                requests.post(WEBAPP_URL, json={"action":"append", "data":[nc, mask_data(dc), f"{vc} {rc}" if rc!="Raiz" else "Raiz", mask_tel(tc), "", "", "", "", "", ""]})
                st.success("Enviado! Aguarde 2 min para atualizar."); time.sleep(1); st.rerun()

    with tabs[4]: # 5. Gerenciar (REFORÇADO)
        esc = st.selectbox("Selecione para Editar", ["--"] + nomes_lista)
        if esc != "--":
            m = df_m[df_m['nome'] == esc]
            if not m.empty:
                m = m.iloc[0]
                idx_list = df_todo.index[df_todo['nome'] == esc].tolist()
                if idx_list:
                    idx = idx_list[0] + 2
                    with st.form("g_f"):
                        ed = st.text_input("Nasc", m.get('nascimento',''))
                        et = st.text_input("Tel", m.get('telefone',''))
                        if st.form_submit_button("💾 ATUALIZAR"):
                            requests.post(WEBAPP_URL, json={"action":"edit", "row":idx, "data":[esc, mask_data(ed), m.get('vinculo',''), mask_tel(et), m.get('email',''), m.get('rua',''), m.get('num',''), "", "", ""]})
                            st.success("Feito! Aguarde 2 min."); time.sleep(1); st.rerun()
                else: st.error("Erro ao localizar índice.")
            else: st.warning("Dados não encontrados. Clique no botão 'Atualizar Dados' na barra lateral.")

    with tabs[5]: # 6. Árvore
        dot = 'digraph G { rankdir=LR; node [shape=box, style=filled, fillcolor="#E1F5FE"];'
        for _, row in df_m.iterrows():
            n, v = str(row['nome']), str(row['vinculo'])
            if " de " in v:
                ref = v.split(" de ")[-1]
                dot += f'"{ref}" -> "{n}";'
        st.graphviz_chart(dot + '}')

    with tabs[6]: # 7. Manual
        st.markdown("### 📖 Guia Rápido")
        st.info("Senha: **buscape2026**")
        st.write("1. **Atualizar:** Se mudar algo e não aparecer, use o botão 'Atualizar Dados' na lateral.")
        st.write("2. **Instalar:** No Chrome (Android) use 'Adicionar à tela inicial'. No Safari (iPhone) use 'Adicionar à Tela de Início'.")
