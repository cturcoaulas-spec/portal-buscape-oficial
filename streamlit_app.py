import streamlit as st
import pandas as pd
import requests
import re
import unicodedata
import time
from urllib.parse import quote
from datetime import datetime
from fpdf import FPDF

# 1. CONFIGURAÇÃO E ESTILO (MOBILE FIRST)
st.set_page_config(page_title="Família Buscapé", page_icon="🌳", layout="wide")

st.markdown("""
    <style>
    [data-baseweb="tab-list"] { gap: 8px; overflow-x: auto; }
    [data-baseweb="tab"] { padding: 10px; border-radius: 10px; background: #f0f2f6; min-width: 110px; }
    button { height: 3.5em !important; font-weight: bold !important; border-radius: 12px !important; width: 100% !important; }
    .stExpander { border-radius: 12px !important; border: 1px solid #ddd !important; }
    </style>
    """, unsafe_allow_html=True)

CSV_URL = "https://docs.google.com/spreadsheets/d/1jrtIP1lN644dPqY0HPGGwPWQGyYwb8nWsUigVK3QZio/export?format=csv"
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzWJ_nDGDe4a81O5BDx3meMbVJjlcMpJoxoO05lilysWJaj_udqeXqvfYFgzvWPlC-Omw/exec"
MESES_BR = ["", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

# --- FUNÇÕES DE SUPORTE ---
def normalizar(t):
    return "".join(ch for ch in unicodedata.normalize('NFKD', str(t).lower()) if not unicodedata.combining(ch)).strip()

def limpar(v): return re.sub(r'\D', '', str(v))

def mask_tel(v):
    n = limpar(str(v))[:11]
    if len(n) == 11: return f"({n[:2]}) {n[2:7]}-{n[7:11]}"
    if len(n) == 10: return f"({n[:2]}) {n[2:6]}-{n[6:10]}"
    return n if n else "-"

# --- CARREGAMENTO RESILIENTE ---
@st.cache_data(ttl=2)
def carregar_dados():
    try:
        df = pd.read_csv(CSV_URL, dtype=str).fillna("")
        cols_originais = df.columns
        mapa_novo = {}
        for c in cols_originais:
            c_norm = normalizar(c)
            if 'nome' in c_norm: mapa_novo[c] = 'nome'
            elif 'nasc' in c_norm: mapa_novo[c] = 'nascimento'
            elif 'vinc' in c_norm or 'ascend' in c_norm: mapa_novo[c] = 'vinculo'
            elif 'tel' in c_norm or 'zap' in c_norm: mapa_novo[c] = 'telefone'
            elif 'rua' in c_norm or 'end' in c_norm: mapa_novo[c] = 'rua'
            elif 'num' in c_norm: mapa_novo[c] = 'num'
            elif 'bair' in c_norm: mapa_novo[c] = 'bairro'
            elif 'cep' in c_norm: mapa_novo[c] = 'cep'
            elif 'emai' in c_norm: mapa_novo[c] = 'email'
            elif 'conju' in c_norm: mapa_novo[c] = 'conjuge'
        df = df.rename(columns=mapa_novo)
        if 'nome' in df.columns:
            df['nome'] = df['nome'].str.strip()
            return df
        return pd.DataFrame()
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
    if df_todo.empty:
        st.error("⚠️ Erro ao carregar dados.")
    else:
        df_m = df_todo[df_todo['nome'] != ""].sort_values(by='nome').copy()
        nomes_lista = sorted(df_m['nome'].unique().tolist())

        with st.sidebar:
            st.title("⚙️ Painel")
            if st.button("🔄 Sincronizar"): st.cache_data.clear(); st.rerun()
            st.divider()
            st.button("🚪 Sair", on_click=lambda: st.session_state.update({"logado": False}))

        st.title("🌳 Família Buscapé")
        tabs = st.tabs(["🔍 Membros", "🎂 Niver", "📢 Mural", "➕ Novo", "✏️ Gerenciar", "🌳 Árvore", "📖 Manual"])

        with tabs[0]: # 1. Membros (BOTÃO DE MAPA VOLTOU!)
            for i, r in df_m.iterrows():
                with st.expander(f"👤 {r['nome']} | 🎂 {r.get('nascimento','-')}"):
                    ci, cl = st.columns([3, 1])
                    with ci:
                        st.write(f"📞 **Tel:** {mask_tel(r.get('telefone','-'))}")
                        st.write(f"🏠 **End:** {r.get('rua','-')}, {r.get('num','-')} - {r.get('bairro','-')}")
                        st.write(f"🌳 **Vínculo:** {r.get('vinculo','-')}")
                    with cl:
                        t = limpar(r.get('telefone',''))
                        if len(t) >= 10: st.link_button("💬 Zap", f"https://wa.me/55{t}")
                        # VOLTA DO BOTÃO DE MAPA
                        end_rua = str(r.get('rua', '')).strip()
                        if end_rua and end_rua != "-" and end_rua != "":
                            endereco_full = f"{end_rua}, {r.get('num','')}, {r.get('bairro','')}"
                            st.link_button("📍 Mapa", f"https://www.google.com/maps/search/?api=1&query={quote(endereco_full)}")

        with tabs[1]: # 2. Niver
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
                if st.form_submit_button("💾 SALVAR MURAL"):
                    requests.post(WEBAPP_URL, json={"action":"edit", "row":2, "data":["AVISO","","","",v1, v2, v3, "","",""]})
                    st.success("Salvo!"); time.sleep(1); st.rerun()

        with tabs[3]: # 4. Cadastrar
            with st.form("c_f", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1: 
                    nc = st.text_input("Nome Completo *"); dc = st.text_input("Nascimento *"); tc = st.text_input("Tel")
                    em = st.text_input("E-mail"); vc = st.radio("Vínculo", ["Filho(a) de", "Cônjuge de"], key="vinc_novo")
                with c2:
                    ru = st.text_input("Rua"); nu = st.text_input("Nº"); ba = st.text_input("Bairro")
                    ce = st.text_input("CEP"); rc = st.selectbox("Referência", ["Raiz"] + nomes_lista, key="ref_novo")
                if st.form_submit_button("💾 CADASTRAR NOVO MEMBRO"):
                    requests.post(WEBAPP_URL, json={"action":"append", "data":[nc, dc, f"{vc} {rc}" if rc!="Raiz" else "Raiz", tc, em, ru, nu, rc if "Cônjuge" in vc else "", ba, ce]})
                    st.success("Cadastrado!"); time.sleep(1); st.rerun()

        with tabs[4]: # 5. Gerenciar
            st.subheader("✏️ Editar ou Excluir Membro")
            esc = st.selectbox("Selecione quem deseja alterar", ["--"] + nomes_lista)
            if esc != "--":
                m_busca = df_m[df_m['nome'] == esc]
                if not m_busca.empty:
                    m = m_busca.iloc[0]
                    idx = df_todo.index[df_todo['nome'] == esc].tolist()[0] + 2
                    with st.form("g_f"):
                        g1, g2 = st.columns(2)
                        with g1:
                            st.text_input("Nome", value=esc, disabled=True)
                            ed = st.text_input("Nascimento", value=m.get('nascimento',''))
                            et = st.text_input("Telefone", value=m.get('telefone',''))
                            ee = st.text_input("E-mail", value=m.get('email',''))
                        with g2:
                            er = st.text_input("Rua", value=m.get('rua',''))
                            en = st.text_input("Nº", value=m.get('num',''))
                            eb = st.text_input("Bairro", value=m.get('bairro',''))
                            tipo_vinc = st.radio("Novo Vínculo", ["Filho(a) de", "Cônjuge de"], horizontal=True, key="edit_vinc")
                            ref_vinc = st.selectbox("Nova Referência", ["Raiz"] + nomes_lista, key="edit_ref")
                        
                        col_btn1, col_btn2 = st.columns(2)
                        if col_btn1.form_submit_button("💾 SALVAR ALTERAÇÕES"):
                            novo_vinc_final = f"{tipo_vinc} {ref_vinc}" if ref_vinc != "Raiz" else "Raiz"
                            requests.post(WEBAPP_URL, json={"action":"edit", "row":idx, "data":[esc, ed, novo_vinc_final, et, ee, er, en, ref_vinc if "Cônjuge" in tipo_vinc else "", eb, m.get('cep','')]})
                            st.success("Atualizado!"); time.sleep(1); st.rerun()
                        if col_btn2.form_submit_button("🗑️ EXCLUIR MEMBRO"):
                            requests.post(WEBAPP_URL, json={"action":"edit", "row":idx, "data":[""]*10})
                            st.warning("Excluído!"); time.sleep(1); st.rerun()

        with tabs[5]: # 6. Árvore
            dot = 'digraph G { rankdir=LR; node [shape=box, style=filled, fillcolor="#E1F5FE", fontname="Arial"];'
            for _, row in df_m.iterrows():
                n, v = str(row['nome']), str(row.get('vinculo','Raiz'))
                if " de " in v:
                    ref = v.split(" de ")[-1]
                    dot += f'"{ref}" -> "{n}";'
                elif v == "Raiz": dot += f'"{n}" [fillcolor="#C8E6C9"];'
            st.graphviz_chart(dot + '}')

        with tabs[6]: # 7. Manual
            st.markdown("### 📖 Guia do Usuário")
            st.info("Senha: **buscape2026**")
