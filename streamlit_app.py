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

WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzWJ_nDGDe4a81O5BDx3meMbVJjlcMpJoxoO05lilysWJaj_udqeXqvfYFgzvWPlC-Omw/exec"
CSV_URL = "https://docs.google.com/spreadsheets/d/1jrtIP1lN644dPqY0HPGGwPWQGyYwb8nWsUigVK3QZio/export?format=csv"
MESES_BR = ["", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

# --- FUNÇÕES DE SUPORTE ---
def limpar_texto(t):
    if not t: return ""
    t = str(t).strip().lower()
    return "".join(ch for ch in unicodedata.normalize('NFKD', t) if not unicodedata.combining(ch))

def mask_tel(v):
    n = re.sub(r'\D', '', str(v))[:11]
    if len(n) == 11: return f"({n[:2]}) {n[2:7]}-{n[7:11]}"
    if len(n) == 10: return f"({n[:2]}) {n[2:6]}-{n[6:10]}"
    return n if n else "-"

def mask_data(v):
    n = re.sub(r'\D', '', str(v))
    if len(n) == 8: return f"{n[:2]}/{n[2:4]}/{n[4:8]}"
    return v

# --- CARREGAMENTO COM PROTEÇÃO ---
@st.cache_data(ttl=2)
def carregar_dados():
    try:
        df = pd.read_csv(CSV_URL, dtype=str).fillna("")
        # Limpa os nomes das colunas (tira acentos e espaços)
        df.columns = [limpar_texto(c) for c in df.columns]
        
        # Mapeia as colunas para nomes fixos que o código entende
        mapa = {
            'nome': 'nome', 'nascimento': 'nascimento', 'nasc': 'nascimento',
            'vinculo': 'vinculo', 'vínculo': 'vinculo', 'ascendente': 'vinculo',
            'telefone': 'telefone', 'tel': 'telefone', 'whatsapp': 'telefone',
            'email': 'email', 'rua': 'rua', 'num': 'num', 'numero': 'num',
            'bairro': 'bairro', 'cep': 'cep'
        }
        df = df.rename(columns=mapa)
        
        # Se não houver coluna 'nome', o app para aqui com aviso
        if 'nome' not in df.columns:
            st.error("Atenção: A coluna 'Nome' não foi encontrada na sua planilha!")
            return pd.DataFrame()
            
        # Limpa espaços extras nos nomes dos familiares
        df['nome'] = df['nome'].str.strip()
        return df
    except Exception as e:
        st.error(f"Erro ao conectar com a Planilha: {e}")
        return pd.DataFrame()

# --- LOGIN ---
if 'logado' not in st.session_state: st.session_state.logado = False

if not st.session_state.logado:
    st.title("🌳 Portal Família Buscapé")
    psw = st.text_input("Senha de Acesso", type="password")
    if st.button("ENTRAR NO PORTAL"):
        if psw == "buscape2026": st.session_state.logado = True; st.rerun()
        else: st.error("Senha incorreta!")
else:
    df_todo = carregar_dados()
    
    if df_todo.empty:
        st.warning("⚠️ Planilha vazia ou inacessível. Verifique se ela está 'Publicada na Web'.")
        if st.button("🔄 Tentar Novamente"): st.cache_data.clear(); st.rerun()
    else:
        # Filtra quem tem nome e ordena
        df_m = df_todo[df_todo['nome'] != ""].sort_values(by='nome').copy()
        nomes_lista = sorted(df_m['nome'].unique().tolist())

        with st.sidebar:
            st.title("⚙️ Opções")
            if st.button("🔄 Sincronizar Planilha"):
                st.cache_data.clear()
                st.rerun()
            st.divider()
            st.button("🚪 Sair", on_click=lambda: st.session_state.update({"logado": False}))

        st.title("🌳 Família Buscapé")
        tabs = st.tabs(["🔍 Membros", "🎂 Niver", "📢 Mural", "➕ Novo", "✏️ Gerenciar", "🌳 Árvore", "📖 Manual"])

        with tabs[0]: # 1. Membros
            for i, r in df_m.iterrows():
                with st.expander(f"👤 {r['nome']} | 🎂 {r.get('nascimento','-')}"):
                    ci, cl = st.columns([3, 1])
                    with ci:
                        st.write(f"📞 **Tel:** {mask_tel(r.get('telefone','-'))}")
                        st.write(f"🌳 **Vínculo:** {r.get('vinculo','Raiz')}")
                        st.write(f"🏠 {r.get('rua','-')}, {r.get('num','-')}")
                    with cl:
                        t = re.sub(r'\D', '', str(r.get('telefone','')))
                        if len(t) >= 10: st.link_button("💬 Zap", f"https://wa.me/55{t}")

        with tabs[1]: # 2. Aniversários
            m_at = datetime.now().month
            st.subheader(f"🎂 Aniversariantes de {MESES_BR[m_at]}")
            for _, r in df_m.iterrows():
                dt = str(r.get('nascimento',''))
                if "/" in dt and int(dt.split('/')[1]) == m_at:
                    st.info(f"🎈 Dia {dt.split('/')[0]} - {r['nome']}")

        with tabs[2]: # 3. Mural
            try: avs = [df_todo.iloc[0].get('email','Vazio'), df_todo.iloc[0].get('rua','Vazio'), df_todo.iloc[0].get('num','Vazio')]
            except: avs = ["Vazio", "Vazio", "Vazio"]
            cols = st.columns(3)
            for idx in range(3): cols[idx].warning(f"**Aviso {idx+1}**\n\n{avs[idx]}")
            with st.form("m_f"):
                v1, v2, v3 = st.text_input("Aviso 1", avs[0]), st.text_input("Aviso 2", avs[1]), st.text_input("Aviso 3", avs[2])
                if st.form_submit_button("💾 SALVAR NO MURAL"):
                    requests.post(WEBAPP_URL, json={"action":"edit", "row":2, "data":["AVISO","","","",v1, v2, v3, "","",""]})
                    st.success("Salvo!"); time.sleep(1); st.rerun()

        with tabs[3]: # 4. Novo Membro
            with st.form("c_f", clear_on_submit=True):
                col_a, col_b = st.columns(2)
                with col_a:
                    nc = st.text_input("Nome Completo *")
                    dc = st.text_input("Nascimento (Ex: 01/01/2000) *")
                    tc = st.text_input("Telefone com DDD")
                with col_b:
                    vc = st.radio("Vínculo", ["Filho(a) de", "Cônjuge de"], horizontal=True)
                    rc = st.selectbox("Referência na Família", ["Raiz"] + nomes_lista)
                
                if st.form_submit_button("➕ CADASTRAR AGORA"):
                    if nc and dc:
                        requests.post(WEBAPP_URL, json={"action":"append", "data":[nc, mask_data(dc), f"{vc} {rc}" if rc!="Raiz" else "Raiz", mask_tel(tc), "", "", "", "", "", ""]})
                        st.success("Cadastro enviado! Aguarde um momento."); time.sleep(2); st.rerun()
                    else: st.warning("Por favor, preencha nome e nascimento.")

        with tabs[4]: # 5. Gerenciar (PROTEÇÃO TOTAL)
            esc = st.selectbox("Selecione alguém para editar", ["--"] + nomes_lista)
            if esc != "--":
                # Busca segura que evita o erro KeyError
                m_busca = df_m[df_m['nome'] == esc]
                if not m_busca.empty:
                    m = m_busca.iloc[0]
                    idx_lista = df_todo.index[df_todo['nome'] == esc].tolist()
                    if idx_lista:
                        idx = idx_lista[0] + 2
                        with st.form("g_f"):
                            ed = st.text_input("Data de Nascimento", value=m.get('nascimento',''))
                            et = st.text_input("Telefone", value=m.get('telefone',''))
                            st.caption(f"Vínculo atual: {m.get('vinculo','-')}")
                            
                            b1, b2 = st.columns(2)
                            if b1.form_submit_button("💾 ATUALIZAR DADOS"):
                                requests.post(WEBAPP_URL, json={"action":"edit", "row":idx, "data":[esc, mask_data(ed), m.get('vinculo',''), mask_tel(et), m.get('email',''), m.get('rua',''), m.get('num',''), "", "", ""]})
                                st.success("Atualizado!"); time.sleep(1); st.rerun()
                            if b2.form_submit_button("🗑️ REMOVER DO PORTAL"):
                                requests.post(WEBAPP_URL, json={"action":"edit", "row":idx, "data":[""]*10})
                                st.warning("Membro removido."); time.sleep(1); st.rerun()

        with tabs[5]: # 6. Árvore Genealógica (PROTEÇÃO CONTRA ERRO)
            st.subheader("🌳 Nossa Árvore")
            dot = 'digraph G { rankdir=LR; node [shape=box, style=filled, fillcolor="#E1F5FE", fontname="Arial"]; edge [color="#546E7A"];'
            for _, row in df_m.iterrows():
                # Uso do .get() para nunca dar KeyError
                n = str(row.get('nome', 'Desconhecido'))
                v = str(row.get('vinculo', 'Raiz'))
                if " de " in v:
                    ref = v.split(" de ")[-1]
                    dot += f'"{ref}" -> "{n}";'
                elif v == "Raiz":
                    dot += f'"{n}" [fillcolor="#C8E6C9"];'
            st.graphviz_chart(dot + '}')

        with tabs[6]: # 7. Manual do Usuário
            st.markdown("### 📖 Guia de Uso")
            st.info("A senha da família é: **buscape2026**")
            st.write("1. **Sincronizar:** Se você mudou algo na planilha e não apareceu, clique em 'Sincronizar Planilha' na lateral.")
            st.write("2. **No Celular:** No Chrome (Android) use 'Adicionar à tela inicial'. No Safari (iPhone) use 'Adicionar à Tela de Início'.")
            st.write("3. **WhatsApp:** O botão abre a conversa direto, sem precisar salvar o contato.")
