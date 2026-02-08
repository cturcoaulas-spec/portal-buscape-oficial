import streamlit as st
import pandas as pd
import requests
import re
import unicodedata
import time
from urllib.parse import quote
from datetime import datetime
from fpdf import FPDF

# 1. CONFIGURAÇÃO MOBILE E ESTILO (BLINDADO)
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
        else: st.error("Senha incorreta! Peça a senha para a Valéria.")
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
                ("1. Boas-vindas!", "Este portal foi criado pela Valeria para ser o nosso ponto de encontro oficial. Aqui, nossa historia e nossos contatos estao protegidos e sempre a mao."),
                ("2. O que sao as Abas?", "Membros: Nossa agenda viva.\nNiver: Onde celebramos a vida a cada mes.\nMural: Nosso quadro de avisos coletivo.\nNovo: Para a familia crescer.\nGerenciar: Para manter tudo organizado.\nArvore: Onde vemos quem somos e de onde viemos."),
                ("3. Integracoes Magicas", "WhatsApp: Fale com o parente sem precisar salvar o numero.\nMapa: O GPS do seu telemovel abre direto na porta da casa dele!"),
                ("4. Responsabilidade", "Lembre-se: o que voce apaga aqui, apaga para todos. Use com carinho!"),
                ("5. No seu Telemovel", "Android: No Chrome, clique nos 3 pontinhos e 'Adicionar a tela inicial'.\niPhone: No Safari, clique no icone de partilhar e 'Adicionar a Tela de Inicio'.")
            ]
            for title, body in sections:
                pdf_m.set_font("Arial", "B", 12); pdf_m.cell(0, 10, title, ln=True)
                pdf_m.set_font("Arial", "", 11); pdf_m.multi_cell(0, 7, body); pdf_m.ln(4)
            pdf_m.ln(5); pdf_m.set_font("Arial", "B", 12); pdf_m.cell(0, 10, "SENHA DE ACESSO: buscape2026", ln=True, align="C")
            manual_out = pdf_m.output(dest='S').encode('latin-1')
            st.download_button("📥 BAIXAR MANUAL ATUALIZADO", manual_out, "Manual_Buscape.pdf")
            
        st.divider(); st.button("🚪 Sair", on_click=lambda: st.session_state.update({"logado": False}))

    st.title("🌳 Família Buscapé")
    tabs = st.tabs(["🔍 Membros", "🎂 Niver", "📢 Mural", "➕ Novo", "✏️ Gerenciar", "🌳 Árvore", "📖 Manual"])

    with tabs[0]: # 1. Membros
        sel_ids = []; c_topo = st.container()
        for i, r in df_m.iterrows():
            col_sel, col_exp = st.columns([0.2, 3.8])
            if col_sel.checkbox("", key=f"sel_{i}"): sel_ids.append(i)
            nome_at = r.get('nome','').strip()
            with col_exp.expander(f"👤 {nome_at} | 🎂 {r.get('nascimento','-')}"):
                ci, cl = st.columns([3, 1])
                with ci:
                    conj_b = str(r.get('conjuge','')).strip(); vinc_b = str(r.get('vinculo','')).strip(); parc = ""
                    if conj_b.lower() not in ["", "nan", "false", "0", "sim"]: parc = conj_b
                    elif "Cônjuge de" in vinc_b: parc = vinc_b.replace("Cônjuge de", "").strip()
                    else:
                        recip = df_m[df_m['conjuge'].str.strip() == nome_at]['nome'].tolist()
                        if recip: parc = recip[0]
                    if parc and parc != nome_at: st.write(f"💍 **Cônjuge:** {parc}")
                    else: st.write("**Cônjuge:** Nenhum")
                    vinc_f = vinc_b
                    if vinc_b and vinc_b != "Raiz" and "Cônjuge" not in vinc_b and "Filho" not in vinc_b:
                        vinc_f = f"Filho(a) de {vinc_b}"
                    st.write(f"📞 **Tel:** {mask_tel(r.get('telefone','-'))} | 🌳 **Vínculo:** {vinc_f}")
                    st.write(f"🏠 {r.get('rua','-')}, {r.get('num','-')} ({r.get('cep','-')})")
                with cl:
                    t_c = limpar(r.get('telefone',''))
                    if len(t_c) >= 10: st.link_button("💬 Zap", f"https://wa.me/55{t_c}"); st.link_button("📞 Ligar", f"tel:{t_c}")
                    if r.get('rua'): st.link_button("📍 Mapa", f"https://www.google.com/maps/search/?api=1&query={quote(f'{r.get('rua','')},{r.get('num','')},{r.get('cep','')}')}")
        if sel_ids: c_topo.download_button("📥 PDF SELECIONADOS", gerar_pdf_membros(df_m.loc[sel_ids]), "familia.pdf")

    with tabs[1]: # 2. Aniversários
        m_at = datetime.now().month; st.subheader(f"🎂 {MESES_BR[m_at]}")
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
            b_s, b_l = st.columns(2)
            if b_s.form_submit_button("💾 SALVAR"): requests.post(WEBAPP_URL, json={"action":"edit", "row":2, "data":["AVISO","","","",v1, v2, v3, "","",""]}); st.rerun()
            if b_l.form_submit_button("🗑️ LIMPAR"): requests.post(WEBAPP_URL, json={"action":"edit", "row":2, "data":["AVISO","","","","Vazio","Vazio","Vazio","","",""]}); st.rerun()

    with tabs[3]: # 4. Cadastrar
        with st.form("c_f", clear_on_submit=True):
            ca, cb = st.columns(2)
            with ca: nc, dc, tc = st.text_input("Nome *"), st.text_input("Nasc *"), st.text_input("Tel"); vc = st.radio("Vínculo", ["Filho(a) de", "Cônjuge de"], horizontal=True); rc = st.selectbox("Ref *", ["Raiz"] + nomes_lista)
            with cb: mc, ru, nu = st.text_input("Email"), st.text_input("Rua"), st.text_input("Nº"); ba, ce = st.text_input("Bairro"), st.text_input("CEP")
            if st.form_submit_button("💾 SALVAR"): requests.post(WEBAPP_URL, json={"action":"append", "data":[nc, mask_data(dc), f"{vc} {rc}" if rc!="Raiz" else "Raiz", mask_tel(tc), mc, ru, nu, rc if "Cônjuge" in vc else "", ba, ce]}); st.rerun()

    with tabs[4]: # 5. Gerenciar (COM CORREÇÃO DE ERRO)
        esc = st.selectbox("Editar", ["--"] + nomes_lista)
        if esc != "--":
            resultado_busca = df_m[df_m['nome'] == esc]
            if not resultado_busca.empty:
                m = resultado_busca.iloc[0]
                indices = df_todo.index[df_todo['nome'] == esc].tolist()
                if indices:
                    idx = indices[0] + 2
                    with st.form("g_f"):
                        c1, c2 = st.columns(2)
                        with c1: 
                            st.text_input("Nome", value=esc, disabled=True)
                            ed, et = st.text_input("Nasc", m.get('nascimento','')), st.text_input("Tel", m.get('telefone',''))
                            ev = st.radio("Tipo", ["Filho(a) de", "Cônjuge de"], index=1 if "Cônjuge" in str(m.get('vinculo','')) else 0)
                            er = st.selectbox("Ref", ["Raiz"] + nomes_lista)
                        with c2: em, ru, nu = st.text_input("Email", m.get('email','')), st.text_input("Rua", m.get('rua','')), st.text_input("Nº", m.get('num','')); ba, ce = st.text_input("Bairro", m.get('bairro','')), st.text_input("CEP", m.get('cep',''))
                        b1, b2 = st.columns(2)
                        if b1.form_submit_button("💾 ATUALIZAR"): 
                            requests.post(WEBAPP_URL, json={"action":"edit", "row":idx, "data":[esc, mask_data(ed), f"{ev} {er}", mask_tel(et), em, ru, nu, er if "Cônjuge" in ev else "", ba, ce]})
                            st.success("Atualizado!"); time.sleep(1); st.rerun()
                        if b2.form_submit_button("🗑️ EXCLUIR"): 
                            requests.post(WEBAPP_URL, json={"action":"edit", "row":idx, "data":[""]*10})
                            st.warning("Excluído!"); time.sleep(1); st.rerun()
                else: st.error("Não foi possível localizar o índice desta pessoa.")
            else: st.warning("Dados não encontrados. Tente atualizar.")

    with tabs[5]: # 6. Árvore
        st.subheader("🌳 Organograma da Família")
        dot = 'digraph G { rankdir=LR; node [shape=box, style=filled, fillcolor="#E1F5FE", fontname="Arial", fontsize=10]; edge [color="#546E7A"];'
        for _, row in df_m.iterrows():
            n, v = str(row['nome']).strip(), str(row['vinculo']).strip()
            if v != "Raiz":
                ref = v.split(" de ")[-1] if " de " in v else v
                dot += f'"{ref}" -> "{n}" [style={"dashed" if "Cônjuge" in v else "solid"}];'
            else: dot += f'"{n}" [fillcolor="#C8E6C9"];'
        st.graphviz_chart(dot + '}')

    with tabs[6]: # 7. Manual Atualizado
        st.markdown("### 📖 Manual de Uso - Família Buscapé")
        st.info("**1. Boas-vindas!**\nEste portal foi criado pela Valéria para ser o nosso ponto de encontro oficial. Aqui, nossa história e nossos contatos estão protegidos e sempre à mão.")
        st.markdown("---")
        st.markdown("**2. O que são as Abas?**")
        st.write("- **Membros:** Nossa agenda viva. - **Niver:** Onde celebramos a vida. - **Mural:** Nosso quadro de avisos.")
        st.write("- **Novo:** Para a família crescer. - **Gerenciar:** Para manter tudo organizado. - **Árvore:** De onde viemos.")
        st.markdown("---")
        st.markdown("**3. Integrações Mágicas**")
        st.success("WhatsApp: Fale com o parente sem precisar salvar o número. Mapa: O GPS do celular abre direto na porta da casa dele!")
        st.markdown("---")
        st.markdown("**4. Responsabilidade**")
        st.warning("Lembre-se: o que você apaga aqui, apaga para todos. Use com carinho!")
        st.markdown("---")
        st.markdown("**5. Como colocar na tela do Celular**")
        st.markdown("""
        Se quiser o ícone da árvore direto na tela do seu celular para facilitar o acesso:
        - **No Android (Chrome):** Clique nos **3 pontinhos** no canto superior direito e escolha **'Adicionar à tela inicial'**.
        - **No iPhone (Safari):** Clique no ícone de **compartilhar** (quadradinho com uma seta) e escolha **'Adicionar à Tela de Início'**.
        """)
        st.markdown(f"<div style='text-align:center; padding:20px; background:#f0f2f6; border-radius:10px;'><b>SENHA DE ACESSO:</b><br><h2 style='color:#ff4b4b;'>buscape2026</h2></div>", unsafe_allow_html=True)
