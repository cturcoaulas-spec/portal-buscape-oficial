import streamlit as st
import pandas as pd
import requests
import re
import unicodedata
import time
from urllib.parse import quote
from datetime import datetime
from fpdf import FPDF

# 1. CONFIGURAÇÃO E ESTILO
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

# --- FUNÇÕES DE LIMPEZA ---
def normalizar(t):
    return "".join(ch for ch in unicodedata.normalize('NFKD', str(t).lower()) if not unicodedata.combining(ch)).strip()

def mask_tel(v):
    n = re.sub(r'\D', '', str(v))[:11]
    if len(n) == 11: return f"({n[:2]}) {n[2:7]}-{n[7:11]}"
    if len(n) == 10: return f"({n[:2]}) {n[2:6]}-{n[6:10]}"
    return n if n else "-"

# --- CARREGAMENTO RESILIENTE ---
@st.cache_data(ttl=2)
def carregar_dados():
    try:
        df = pd.read_csv(CSV_URL, dtype=str).fillna("")
        # Localizador inteligente de colunas
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
        st.error("⚠️ Não encontramos os dados. Verifique se a Planilha do Google tem a coluna 'Nome'.")
        if st.button("🔄 Tentar Sincronizar"): st.cache_data.clear(); st.rerun()
    else:
        df_m = df_todo[df_todo['nome'] != ""].sort_values(by='nome').copy()
        nomes_lista = sorted(df_m['nome'].unique().tolist())

        with st.sidebar:
            st.title("⚙️ Painel")
            if st.button("🔄 Atualizar"): st.cache_data.clear(); st.rerun()
            st.divider()
            st.button("🚪 Sair", on_click=lambda: st.session_state.update({"logado": False}))

        st.title("🌳 Família Buscapé")
        tabs = st.tabs(["🔍 Membros", "🎂 Niver", "📢 Mural", "➕ Novo", "✏️ Gerenciar", "🌳 Árvore", "📖 Manual"])

        with tabs[0]: # Membros
            for i, r in df_m.iterrows():
                with st.expander(f"👤 {r['nome']} | 🎂 {r.get('nascimento','-')}"):
                    ci, cl = st.columns([3, 1])
                    with ci:
                        st.write(f"📞 Tel: {mask_tel(r.get('telefone','-'))}")
                        st.write(f"🏠 {r.get('rua','-')}, {r.get('num','-')}")
                    with cl:
                        t = re.sub(r'\D', '', str(r.get('telefone','')))
                        if len(t) >= 10: st.link_button("💬 Zap", f"https://wa.me/55{t}")

        with tabs[1]: # Niver
            m_at = datetime.now().month
            st.subheader(f"🎂 Aniversariantes de {MESES_BR[m_at]}")
            for _, r in df_m.iterrows():
                dt = str(r.get('nascimento',''))
                if "/" in dt and len(dt.split('/')) >= 2:
                    if int(dt.split('/')[1]) == m_at: st.info(f"🎈 Dia {dt.split('/')[0]} - {r['nome']}")

        with tabs[2]: # Mural
            try: avs = [df_todo.iloc[0].get('email','Vazio'), df_todo.iloc[0].get('rua','Vazio'), df_todo.iloc[0].get('num','Vazio')]
            except: avs = ["Vazio", "Vazio", "Vazio"]
            cols = st.columns(3)
            for idx in range(3): cols[idx].warning(f"**Aviso {idx+1}**\n\n{avs[idx]}")
            with st.form("m_f"):
                v1, v2, v3 = st.text_input("A1", avs[0]), st.text_input("A2", avs[1]), st.text_input("A3", avs[2])
                if st.form_submit_button("💾 SALVAR MURAL"):
                    requests.post(WEBAPP_URL, json={"action":"edit", "row":2, "data":["AVISO","","","",v1, v2, v3, "","",""]})
                    st.success("Salvo!"); time.sleep(1); st.rerun()

        with tabs[3]: # Novo Membro
            with st.form("c_f", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1: nc = st.text_input("Nome *"); dc = st.text_input("Nascimento *"); tc = st.text_input("Tel")
                with c2: vc = st.radio("Vínculo", ["Filho(a) de", "Cônjuge de"]); rc = st.selectbox("Referência", ["Raiz"] + nomes_lista)
                if st.form_submit_button("💾 CADASTRAR"):
                    requests.post(WEBAPP_URL, json={"action":"append", "data":[nc, dc, f"{vc} {rc}" if rc!="Raiz" else "Raiz", tc, "", "", "", "", "", ""]})
                    st.success("Cadastrado!"); time.sleep(1); st.rerun()

        with tabs[4]: # Gerenciar (RESGATE DE CAMPOS)
            st.subheader("✏️ Editar")
            esc = st.selectbox("Escolha um nome", ["--"] + nomes_lista)
            if esc != "--":
                m = df_m[df_m['nome'] == esc].iloc[0]
                idx = df_todo.index[df_todo['nome'] == esc].tolist()[0] + 2
                with st.form("g_f"):
                    ed = st.text_input("Nascimento", value=m.get('nascimento',''))
                    et = st.text_input("Telefone", value=m.get('telefone',''))
                    st.write(f"Vínculo: {m.get('vinculo','-')}")
                    if st.form_submit_button("💾 SALVAR ALTERAÇÕES"):
                        requests.post(WEBAPP_URL, json={"action":"edit", "row":idx, "data":[esc, ed, m.get('vinculo',''), et, "", "", "", "", "", ""]})
                        st.success("Atualizado!"); time.sleep(1); st.rerun()

        with tabs[5]: # Árvore
            dot = 'digraph G { rankdir=LR; node [shape=box, style=filled, fillcolor="#E1F5FE"];'
            for _, row in df_m.iterrows():
                n, v = str(row['nome']), str(row.get('vinculo','Raiz'))
                if " de " in v:
                    ref = v.split(" de ")[-1]
                    dot += f'"{ref}" -> "{n}";'
            st.graphviz_chart(dot + '}')

        with tabs[6]: # Manual
            st.markdown("### 📖 Guia Rápido")
            st.info("Senha: **buscape2026**")
            st.write("1. **Atualizar:** Use o botão na lateral se algo não aparecer.")
            st.write("2. **Instalar:** No Chrome (Android) use 'Adicionar à tela inicial'. No Safari (iPhone) use 'Adicionar à Tela de Início'.")
