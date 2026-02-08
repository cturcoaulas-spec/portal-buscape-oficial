import streamlit as st
import pandas as pd
import requests
import re
import time
import unicodedata
from urllib.parse import quote
from datetime import datetime
from fpdf import FPDF

# 1. CONFIGURAÇÃO E CSS PARA CELULAR (MOBILE FIRST)
st.set_page_config(page_title="Família Buscapé", page_icon="🌳", layout="wide")

st.markdown("""
    <style>
    /* Ajustes para Celular */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; overflow-x: auto; }
    .stTabs [data-baseweb="tab"] { 
        padding: 8px 12px; 
        background-color: #f0f2f6; 
        border-radius: 10px;
        min-width: 100px;
    }
    button { height: 3em !important; width: 100% !important; border-radius: 10px !important; }
    .stExpander { border-radius: 15px !important; border: 1px solid #ddd !important; }
    </style>
    """, unsafe_allow_html=True)

WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzWJ_nDGDe4a81O5BDx3meMbVJjlcMpJoxoO05lilysWJaj_udqeXqvfYFgzvWPlC-Omw/exec"
CSV_URL = "https://docs.google.com/spreadsheets/d/1jrtIP1lN644dPqY0HPGGwPWQGyYwb8nWsUigVK3QZio/export?format=csv"

MESES_BR = ["", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

# --- FUNÇÕES DE SUPORTE (INALTERADAS) ---
def limpar(v): return re.sub(r'\D', '', str(v))
def mask_tel(v):
    n = limpar(v)
    if len(n) == 11: return f"({n[:2]}) {n[2:7]}-{n[7:11]}"
    if len(n) == 10: return f"({n[:2]}) {n[2:6]}-{n[6:10]}"
    return v
def mask_data(v):
    n = limpar(v)
    if len(n) == 8: return f"{n[:2]}/{n[2:4]}/{n[4:8]}"
    return v
def gerar_pdf(dados):
    pdf = FPDF()
    pdf.add_page(); pdf.set_font("Arial", "B", 14)
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
            df.columns = [norm(c) for c in df.columns]
            mapa = {'nome':'nome','nascimento':'nascimento','vinculo':'vinculo','ascendente':'vinculo',
                    'telefone':'telefone','email':'email','rua':'rua','num':'num','numero':'num',
                    'conjuge':'conjuge', 'conjugue':'conjuge', 'bairro':'bairro','cep':'cep'}
            df = df.rename(columns=mapa)
            return df
        except: return pd.DataFrame()

    df_todo = carregar()
    df_m = df_todo[df_todo['nome'].str.strip() != ""].sort_values(by='nome').copy()
    nomes_lista = sorted([n.strip() for n in df_m['nome'].unique().tolist() if n.strip()])

    with st.sidebar:
        st.title("🔔 Notificações")
        hoje_dm = datetime.now().strftime("%d/%m")
        niver_hoje = [r['nome'] for _, r in df_m.iterrows() if str(r.get('nascimento','')).startswith(hoje_dm)]
        if niver_hoje:
            for n in niver_hoje: st.success(f"🎂 Hoje: {n}")
        else: st.info("Sem notificações hoje")
        st.divider()
        st.button("🚪 Sair", on_click=lambda: st.session_state.update({"logado": False}))

    st.title("🌳 Família Buscapé")
    # ADICIONADA A 6ª ABA: ÁRVORE
    tabs = st.tabs(["🔍 Membros", "🎂 Aniversários", "📢 Mural", "➕ Cadastrar", "✏️ Gerenciar", "🌳 Árvore"])

    # --- TAB 1: MEMBROS (TRANCADA) ---
    with tabs[0]:
        sel_ids = []
        c_topo = st.container()
        for i, r in df_m.iterrows():
            col_sel, col_exp = st.columns([0.2, 3.8])
            if col_sel.checkbox("", key=f"sel_{i}"): sel_ids.append(i)
            nome_at = r.get('nome','').strip()
            with col_exp.expander(f"👤 {nome_at} | 🎂 {r.get('nascimento','-')}"):
                ci, cl = st.columns([3, 1])
                with ci:
                    conj_bruto = str(r.get('conjuge','')).strip()
                    vinc_bruto = str(r.get('vinculo','')).strip()
                    parceiro = ""
                    if conj_bruto.lower() not in ["", "nan", "false", "0", "none"]: parceiro = conj_bruto
                    if not parceiro and "Cônjuge de" in vinc_bruto: parceiro = vinc_bruto.replace("Cônjuge de", "").strip()
                    if not parceiro:
                        recip = df_m[(df_m['conjuge'].str.strip() == nome_at) | (df_m['vinculo'].str.contains(f"Cônjuge de {nome_at}", case=False, na=False))]['nome'].tolist()
                        if recip: parceiro = recip[0]
                    if parceiro and parceiro != nome_at: st.write(f"💍 **Cônjuge:** {parceiro}")
                    else: st.write(f"**Cônjuge:** Nenhum")
                    vinc_f = vinc_bruto
                    if vinc_bruto and vinc_bruto != "Raiz" and "Cônjuge" not in vinc_bruto and "Filho" not in vinc_bruto:
                        vinc_f = f"Filho(a) de {vinc_bruto}"
                    st.write(f"📞 **Tel:** {r.get('telefone','-')} | 🌳 **Vínculo:** {vinc_f}")
                    st.write(f"🏠 {r.get('rua','-')}, {r.get('num','-')} - {r.get('bairro','-')} ({r.get('cep','-')})")
                    st.write(f"✉️ **E-mail:** {r.get('email','-')}")
                with cl:
                    t_c = limpar(r.get('telefone',''))
                    if len(t_c) >= 10:
                        st.link_button("💬 WhatsApp", f"https://wa.me/55{t_c}"); st.link_button("📞 Ligar", f"tel:{t_c}")
                    rua_v = str(r.get('rua','')).strip()
                    if rua_v and rua_v.lower() not in ["", "nan"]:
                        end_f = f"{rua_v}, {r.get('num','')}, {r.get('bairro','')}, {r.get('cep','')}"
                        st.link_button("📍 Mapa", f"https://www.google.com/maps/search/?api=1&query={quote(end_f)}")
        if sel_ids:
            p_data = gerar_pdf(df_m.loc[sel_ids])
            c_topo.download_button("📥 BAIXAR PDF SELECIONADOS", p_data, "familia_buscape.pdf")

    # --- TAB 2, 3, 4 e 5 (TOTALMENTE TRANCADAS) ---
    with tabs[1]:
        m_at = datetime.now().month
        st.subheader(f"🎂 Aniversariantes de {MESES_BR[m_at]}")
        encontrou = False
        for _, r in df_m.iterrows():
            dt = str(r.get('nascimento',''))
            if "/" in dt and int(dt.split('/')[1]) == m_at:
                st.info(f"🎈 Dia {dt.split('/')[0]} - {r['nome']}"); encontrou = True
        if not encontrou: st.write("Sem aniversariantes.")

    with tabs[2]:
        st.subheader("📢 Mural de Avisos")
        try: avs = [df_todo.iloc[0].get('email','Vazio'), df_todo.iloc[0].get('rua','Vazio'), df_todo.iloc[0].get('num','Vazio')]
        except: avs = ["Vazio", "Vazio", "Vazio"]
        cols = st.columns(3)
        for idx in range(3): cols[idx].warning(f"**Aviso {idx+1}**\n\n{avs[idx]}")
        st.divider()
        with st.form("mural_f"):
            v1, v2, v3 = st.text_input("Aviso 1", avs[0]), st.text_input("Aviso 2", avs[1]), st.text_input("Aviso 3", avs[2])
            if st.form_submit_button("💾 Salvar Avisos"):
                requests.post(WEBAPP_URL, json={"action":"edit", "row":2, "data":["AVISO","","","",v1, v2, v3, "","",""]})
                st.success("✅ MURAL ATUALIZADO!"); time.sleep(1); st.rerun()

    with tabs[3]:
        with st.form("f_cad", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            with col_a:
                nc, dc, tc = st.text_input("Nome Completo *"), st.text_input("Nasc (DDMMAAAA) *"), st.text_input("Telefone")
                vc = st.radio("Vínculo", ["Filho(a) de", "Cônjuge de"], horizontal=True)
                rc = st.selectbox("Referência *", ["Raiz"] + nomes_lista)
            with col_b:
                mc, ru, nu = st.text_input("E-mail"), st.text_input("Rua"), st.text_input("Nº")
                ba, ce = st.text_input("Bairro"), st.text_input("CEP")
            if st.form_submit_button("💾 SALVAR CADASTRO"):
                if nc.strip().lower() in [n.lower() for n in nomes_lista]: st.error("❌ Nome já existe!")
                elif not nc or not dc: st.error("⚠️ Nome/Nasc obrigatórios!")
                else:
                    v_fin = f"{vc} {rc}" if rc != "Raiz" else "Raiz"
                    requests.post(WEBAPP_URL, json={"action":"append", "data":[nc, mask_data(dc), v_fin, mask_tel(tc), mc, ru, nu, rc if "Cônjuge" in vc else "", ba, ce]})
                    st.success("✅ SALVO!"); time.sleep(1); st.rerun()

    with tabs[4]:
        esc = st.selectbox("Selecione para editar", ["--"] + nomes_lista)
        if esc != "--":
            m = df_m[df_m['nome'] == esc].iloc[0]; idx_pl = df_todo.index[df_todo['nome'] == esc].tolist()[0] + 2
            with st.form("f_ger"):
                c1, c2 = st.columns(2)
                with c1:
                    st.text_input("Nome", value=m.get('nome',''), disabled=True)
                    ed, et = st.text_input("Nasc *", value=m.get('nascimento','')), st.text_input("Tel", value=m.get('telefone',''))
                    ev = st.radio("Vínculo", ["Filho(a) de", "Cônjuge de"], horizontal=True, index=1 if "Cônjuge" in m.get('vinculo','') else 0)
                    er = st.selectbox("Referência *", ["Raiz"] + nomes_lista)
                with c2:
                    em, erua, enum = st.text_input("E-mail", m.get('email','')), st.text_input("Rua", m.get('rua','')), st.text_input("Nº", m.get('num',''))
                    eba, ece = st.text_input("Bairro", m.get('bairro','')), st.text_input("CEP", m.get('cep',''))
                if st.form_submit_button("💾 ATUALIZAR"):
                    requests.post(WEBAPP_URL, json={"action":"edit", "row":idx_pl, "data":[esc, mask_data(ed), f"{ev} {er}" if er != "Raiz" else "Raiz", mask_tel(et), em, erua, enum, er if "Cônjuge" in ev else "", eba, ece]})
                    st.success("✅ ATUALIZADO!"); time.sleep(1); st.rerun()

    # --- TAB 6: ARVORE GENEALÓGICA (NOVA) ---
    with tabs[5]:
        st.subheader("🌳 Estrutura por Raízes")
        raizes = df_m[df_m['vinculo'].str.lower() == 'raiz']
        
        for _, raiz in raizes.iterrows():
            with st.container():
                st.markdown(f"### 🏷️ Raiz: {raiz['nome']}")
                # Busca descendentes (quem tem o nome da raiz no vinculo)
                desc = df_m[df_m['vinculo'].str.contains(raiz['nome'], case=False)]
                if not desc.empty:
                    for _, d in desc.iterrows():
                        tipo = "💍 Cônjuge" if "Cônjuge" in d['vinculo'] else "👶 Filho(a)"
                        st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;**{tipo}:** {d['nome']}")
                else:
                    st.write("Sem descendentes cadastrados.")
                st.divider()
