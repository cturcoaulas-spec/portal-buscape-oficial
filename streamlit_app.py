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

# 2. BLINDAGEM EQUILIBRADA (NÃO APAGA AS ABAS)
st.markdown("""
    <style>
    .viewerBadge_container__1QSob, .stAppDeployButton, #MainMenu { display: none !important; }
    [data-testid="stStatusWidget"], [data-testid="stToolbar"], [data-testid="stDecoration"] { display: none !important; }
    footer { display: none !important; }

    /* Garante que o menu lateral apareça */
    header[data-testid="stHeader"] {
        visibility: visible !important;
        background-color: white !important;
    }

    /* Espaço para o navegador (Chrome/Safari) mostrar os 3 pontinhos */
    .block-container { padding-top: 4rem !important; }

    /* Estilo das Abas */
    [data-baseweb="tab-list"] { gap: 8px; overflow-x: auto; }
    [data-baseweb="tab"] { padding: 10px; border-radius: 10px; background: #f0f2f6; min-width: 110px; }
    button { height: 3.5em !important; font-weight: bold !important; border-radius: 12px !important; }
    </style>
    """, unsafe_allow_html=True)

# LINKS DE INTEGRAÇÃO
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzWJ_nDGDe4a81O5BDx3meMbVJjlcMpJoxoO05lilysWJaj_udqeXqvfYFgzvWPlC-Omw/exec"
CSV_URL = "https://docs.google.com/spreadsheets/d/1jrtIP1lN644dPqY0HPGGwPWQGyYwb8nWsUigVK3QZio/export?format=csv"
MESES_BR = ["", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

# --- FUNÇÕES SUPORTE ---
def normalizar(t):
    return "".join(ch for ch in unicodedata.normalize('NFKD', str(t).lower()) if not unicodedata.combining(ch)).strip()

def limpar(v): return re.sub(r'\D', '', str(v))

def mask_tel(v):
    n = limpar(str(v))[:11]
    if len(n) == 11: return f"({n[:2]}) {n[2:7]}-{n[7:11]}"
    if len(n) == 10: return f"({n[:2]}) {n[2:6]}-{n[6:10]}"
    return n if n else "-"

def mask_data(d):
    d = limpar(str(d))
    if len(d) == 8: return f"{d[:2]}/{d[2:4]}/{d[4:]}"
    return d

def gerar_pdf_membros(dados):
    pdf = FPDF()
    pdf.add_page(); pdf.set_font("Arial", "B", 14)
    pdf.cell(200, 10, "Relatorio Oficial - Familia Buscape", ln=True, align="C"); pdf.ln(5)
    for _, r in dados.iterrows():
        pdf.set_font("Arial", "B", 11); pdf.cell(0, 8, f"Nome: {r.get('nome','-')}", ln=True)
        pdf.set_font("Arial", size=10); pdf.cell(0, 6, f"Nasc: {r.get('nascimento','-')} | Tel: {mask_tel(r.get('telefone','-'))}", ln=True)
        pdf.cell(0, 6, f"End: {r.get('rua','-')}, {r.get('num','-')} - {r.get('bairro','-')}", ln=True)
        pdf.ln(2); pdf.line(10, pdf.get_y(), 200, pdf.get_y()); pdf.ln(4)
    return pdf.output(dest='S').encode('latin-1')

@st.cache_data(ttl=2)
def carregar_dados():
    try:
        df = pd.read_csv(CSV_URL, dtype=str).fillna("")
        mapa_novo = {}
        for c in df.columns:
            cn = normalizar(c)
            if 'nome' in cn: mapa_novo[c] = 'nome'
            elif 'nasc' in cn: mapa_novo[c] = 'nascimento'
            elif 'vinc' in cn or 'ascend' in cn: mapa_novo[c] = 'vinculo'
            elif 'tel' in cn: mapa_novo[c] = 'telefone'
            elif 'rua' in cn: mapa_novo[c] = 'rua'
            elif 'num' in cn: mapa_novo[c] = 'num'
            elif 'bair' in cn: mapa_novo[c] = 'bairro'
            elif 'cep' in cn: mapa_novo[c] = 'cep'
            elif 'emai' in cn: mapa_novo[c] = 'email'
        df = df.rename(columns=mapa_novo)
        return df if 'nome' in df.columns else pd.DataFrame()
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
    if df_todo.empty: st.error("⚠️ Erro ao carregar dados.")
    else:
        df_m = df_todo[df_todo['nome'] != ""].sort_values(by='nome').copy()
        nomes_lista = sorted(df_m['nome'].unique().tolist())
        mes_at = datetime.now().month

        with st.sidebar:
            st.title("⚙️ Painel")
            st.subheader("🔔 Notificações")
            niver_mes = [f"🎂 {str(r['nascimento']).split('/')[0]} - {r['nome']}" for _, r in df_m.iterrows() if '/' in str(r['nascimento']) and int(str(r['nascimento']).split('/')[1]) == mes_at]
            if niver_mes:
                for n in niver_mes: st.write(n)
            else: st.write("Sem avisos para este mês.")
            st.divider()
            if st.button("🔄 Sincronizar"): st.cache_data.clear(); st.rerun()
            st.button("🚪 Sair", on_click=lambda: st.session_state.update({"logado": False}))

        st.title("🌳 Família Buscapé")
        tabs = st.tabs(["🔍 Membros", "🎂 Niver", "📢 Mural", "➕ Novo", "✏️ Gerenciar", "🌳 Árvore", "📖 Manual"])

        with tabs[0]: # 1. Membros
            sel_ids = []; c_topo = st.container()
            for i, r in df_m.iterrows():
                col_sel, col_exp = st.columns([0.15, 3.85])
                if col_sel.checkbox("", key=f"sel_{i}"): sel_ids.append(i)
                with col_exp.expander(f"👤 {r['nome']} | 🎂 {r.get('nascimento','-')}"):
                    ci, cl = st.columns([3, 1])
                    with ci:
                        st.write(f"📞 Tel: {mask_tel(r.get('telefone','-'))}")
                        st.write(f"🏠 End: {r.get('rua','-')}, {r.get('num','-')} - {r.get('bairro','-')}")
                        st.write(f"🌳 Vínculo: {r.get('vinculo','-')}")
                    with cl:
                        t = limpar(r.get('telefone',''))
                        if len(t) >= 10: st.link_button("💬 Zap", f"https://wa.me/55{t}")
                        rua = str(r.get('rua', '')).strip()
                        if rua and rua != "-": st.link_button("📍 Mapa", f"https://www.google.com/maps/search/?api=1&query={quote(f'{rua},{r.get('num','')}')}")
            if sel_ids: c_topo.download_button("📥 PDF SELECIONADOS", gerar_pdf_membros(df_m.loc[sel_ids]), "familia.pdf")

        with tabs[1]: # 2. Niver
            st.subheader(f"🎂 Aniversariantes de {MESES_BR[mes_at]}")
            for _, r in df_m.iterrows():
                dt = str(r.get('nascimento',''))
                if "/" in dt and int(dt.split('/')[1]) == mes_at: st.info(f"🎈 Dia {dt.split('/')[0]} - {r['nome']}")

        with tabs[2]: # 3. Mural
            try: avs = [df_todo.iloc[0].get('email','Vazio'), df_todo.iloc[0].get('rua','Vazio'), df_todo.iloc[0].get('num','Vazio')]
            except: avs = ["Vazio", "Vazio", "Vazio"]
            cols = st.columns(3)
            for idx in range(3): cols[idx].warning(f"**Aviso {idx+1}**\n\n{avs[idx]}")
            with st.form("m_f"):
                v1, v2, v3 = st.text_input("A1", avs[0]), st.text_input("A2", avs[1]), st.text_input("A3", avs[2])
                if st.form_submit_button("💾 SALVAR MURAL"): 
                    requests.post(WEBAPP_URL, json={"action":"edit", "row":2, "data":["AVISO","","","",v1, v2, v3, "","",""]}); st.success("Salvo!"); time.sleep(1); st.rerun()

        with tabs[3]: # 4. Novo
            with st.form("c_f", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1: 
                    nc = st.text_input("Nome Completo *"); dc = st.text_input("Nasc (ex: 09021980) *"); tc = st.text_input("Tel")
                    em = st.text_input("E-mail"); vc = st.radio("Vínculo", ["Filho(a) de", "Cônjuge de"], key="vinc_novo")
                with c2:
                    ru = st.text_input("Rua"); nu = st.text_input("Nº"); ba = st.text_input("Bairro")
                    ce = st.text_input("CEP"); rc = st.selectbox("Referência", ["Raiz"] + nomes_lista, key="ref_novo")
                if st.form_submit_button("💾 SALVAR NOVO MEMBRO"):
                    dt_f = mask_data(dc)
                    requests.post(WEBAPP_URL, json={"action":"append", "data":[nc, dt_f, f"{vc} {rc}" if rc!="Raiz" else "Raiz", tc, em, ru, nu, rc if "Cônjuge" in vc else "", ba, ce]})
                    st.success("🎉 Membro Cadastrado!"); time.sleep(2); st.rerun()

        with tabs[4]: # 5. Gerenciar
            st.subheader("✏️ Editar ou Excluir Membro")
            esc = st.selectbox("Escolha quem deseja alterar", ["--"] + nomes_lista)
            if esc != "--":
                m_busca = df_m[df_m['nome'] == esc]
                if not m_busca.empty:
                    m = m_busca.iloc[0]; idx = df_todo.index[df_todo['nome'] == esc].tolist()[0] + 2
                    with st.form("g_f"):
                        g1, g2 = st.columns(2)
                        with g1:
                            st.text_input("Nome", value=esc, disabled=True)
                            ed = st.text_input("Nascimento", value=m.get('nascimento','')); et = st.text_input("Telefone", value=m.get('telefone',''))
                            ee = st.text_input("E-mail", value=m.get('email',''))
                        with g2:
                            er = st.text_input("Rua", value=m.get('rua','')); en = st.text_input("Nº", value=m.get('num',''))
                            eb = st.text_input("Bairro", value=m.get('bairro',''))
                            tipo_vinc = st.radio("Novo Vínculo", ["Filho(a) de", "Cônjuge de"], horizontal=True, key="edit_vinc")
                            ref_vinc = st.selectbox("Nova Referência", ["Raiz"] + nomes_lista, key="edit_ref")
                        b1, b2 = st.columns(2)
                        if b1.form_submit_button("💾 SALVAR ALTERAÇÕES"):
                            dt_edit = mask_data(ed)
                            novo_vinc_final = f"{tipo_vinc} {ref_vinc}" if ref_vinc != "Raiz" else "Raiz"
                            requests.post(WEBAPP_URL, json={"action":"edit", "row":idx, "data":[esc, dt_edit, novo_vinc_final, et, ee, er, en, ref_vinc if "Cônjuge" in tipo_vinc else "", eb, m.get('cep','')]})
                            st.success("Atualizado!"); time.sleep(1); st.rerun()
                        if b2.form_submit_button("🗑️ EXCLUIR MEMBRO"):
                            requests.post(WEBAPP_URL, json={"action":"edit", "row":idx, "data":[""]*10}); st.warning("Excluído!"); time.sleep(1); st.rerun()

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

        with tabs[6]: # 7. Manual (TEXTO COMPLETO)
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
