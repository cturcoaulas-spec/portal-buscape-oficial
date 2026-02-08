import streamlit as st
import pandas as pd
import requests
import re
import unicodedata
from urllib.parse import quote
from datetime import datetime
from fpdf import FPDF
import time

# 1. CONFIGURAÇÃO BÁSICA (SEM CSS QUE PODE ESCONDER AS TELAS)
st.set_page_config(page_title="Família Buscapé", page_icon="🌳", layout="wide")

# CONFIGURAÇÕES DE LINKS
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzWJ_nDGDe4a81O5BDx3meMbVJjlcMpJoxoO05lilysWJaj_udqeXqvfYFgzvWPlC-Omw/exec"
CSV_URL = "https://docs.google.com/spreadsheets/d/1jrtIP1lN644dPqY0HPGGwPWQGyYwb8nWsUigVK3QZio/export?format=csv"
MESES_BR = ["", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

def limpar(v): return re.sub(r'\D', '', str(v))
def mask_tel(v):
    n = limpar(str(v))[:11]
    if len(n) == 11: return f"({n[:2]}) {n[2:7]}-{n[7:11]}"
    if len(n) == 10: return f"({n[:2]}) {n[2:6]}-{n[6:10]}"
    return n if n else "-"

# 2. LOGICA DE LOGIN
if 'logado' not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.title("🌳 Portal Família Buscapé")
    st.write("Seja bem-vindo ao nosso espaço!")
    psw = st.text_input("Digite a senha da família:", type="password")
    if st.button("ACESSAR PORTAL"):
        if psw == "buscape2026":
            st.session_state.logado = True
            st.rerun()
        else:
            st.error("Senha incorreta!")
else:
    # --- CARREGAR DADOS ---
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
        except Exception as e:
            st.error(f"Erro ao carregar dados: {e}")
            return pd.DataFrame()

    df_todo = carregar()
    df_m = df_todo[df_todo['nome'].str.strip() != ""].sort_values(by='nome').copy()
    nomes_lista = sorted([n.strip() for n in df_m['nome'].unique().tolist() if n.strip()])

    # --- MENU LATERAL ---
    with st.sidebar:
        st.header("🎂 Notificações")
        hoje_dm = datetime.now().strftime("%d/%m")
        niver_hoje = [r['nome'] for _, r in df_m.iterrows() if str(r.get('nascimento','')).startswith(hoje_dm)]
        if niver_hoje:
            for n in niver_hoje: st.success(f"🎂 Aniversário: {n}")
        else:
            st.info("Nenhum aniversário hoje.")
        
        st.divider()
        if st.button("📄 MANUAL DE USO (PDF)"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", "B", 16)
            pdf.cell(200, 10, "Manual do Usuario - Familia Buscape", ln=True, align="C")
            pdf.ln(10)
            
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, "1. BEM-VINDOS!", ln=True)
            pdf.set_font("Arial", "", 11)
            pdf.multi_cell(0, 7, "Este portal foi criado pela Valeria para unir a nossa familia. Aqui guardamos nossos contatos e nossa historia.")
            
            pdf.ln(5)
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, "2. RESPONSABILIDADE", ln=True)
            pdf.set_font("Arial", "", 11)
            pdf.multi_cell(0, 7, "IMPORTANTE: Este e um sistema coletivo. O que voce edita ou apaga muda para TODOS. Use com carinho e preencha seus dados corretamente!")
            
            pdf.ln(5)
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, "3. FUNCIONALIDADES", ln=True)
            pdf.set_font("Arial", "", 11)
            pdf.multi_cell(0, 7, "Membros: Veja contatos e use o GPS.\nNiver: Veja quem faz anos.\nMural: Avisos importantes.\nArvore: Nossa genealogia.")
            
            pdf.ln(5)
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, "4. NO CELULAR", ln=True)
            pdf.set_font("Arial", "", 11)
            pdf.multi_cell(0, 7, "Android (Chrome): 3 pontinhos > Instalar aplicativo.\niPhone (Safari): Compartilhar > Adicionar a Tela de Inicio.")

            st.download_button("📥 Baixar Manual PDF", pdf.output(dest='S').encode('latin-1'), "Manual_Buscape.pdf")

        st.divider()
        if st.button("🚪 Sair"):
            st.session_state.logado = False
            st.rerun()

    # --- ABAS PRINCIPAIS ---
    st.title("🌳 Família Buscapé")
    t1, t2, t3, t4, t5, t6 = st.tabs(["Membros", "Aniversários", "Mural", "Cadastrar", "Gerenciar", "Árvore"])

    with t1: # MEMBROS
        st.subheader("Nossa Família")
        for i, r in df_m.iterrows():
            nome_at = r.get('nome','').strip()
            with st.expander(f"👤 {nome_at}"):
                c_inf, c_btn = st.columns([3, 1])
                with c_inf:
                    # Lógica do Cônjuge
                    conj = str(r.get('conjuge','')).strip()
                    vinc = str(r.get('vinculo','')).strip()
                    parc = conj if (conj and conj.lower() != "nenhum") else ""
                    if not parc and "Cônjuge de" in vinc:
                        parc = vinc.replace("Cônjuge de", "").strip()
                    if not parc:
                        busca = df_m[df_m['conjuge'].str.strip() == nome_at]['nome'].tolist()
                        if busca: parc = busca[0]
                    
                    if parc: st.write(f"💍 **Cônjuge:** {parc}")
                    st.write(f"📞 **Tel:** {mask_tel(r.get('telefone','-'))}")
                    st.write(f"🏠 {r.get('rua','-')}, {r.get('num','-')}")
                    st.write(f"🌳 **Vínculo:** {vinc}")
                with c_btn:
                    tel_limpo = limpar(r.get('telefone',''))
                    if len(tel_limpo) >= 10:
                        st.link_button("💬 Zap", f"https://wa.me/55{tel_limpo}")
                    if r.get('rua'):
                        st.link_button("📍 Mapa", f"https://www.google.com/maps/search/?api=1&query={quote(f'{r.get('rua')},{r.get('num')}')}")

    with t2: # ANIVERSARIOS
        mes_f = datetime.now().month
        st.subheader(f"🎂 Aniversariantes de {MESES_BR[mes_f]}")
        for _, r in df_m.iterrows():
            d = str(r.get('nascimento',''))
            if "/" in d and int(d.split('/')[1]) == mes_f:
                st.info(f"🎈 Dia {d.split('/')[0]} - {r['nome']}")

    with t3: # MURAL
        st.subheader("📢 Mural de Recados")
        try:
            m1 = df_todo.iloc[0].get('email','Recado 1')
            m2 = df_todo.iloc[0].get('rua','Recado 2')
            m3 = df_todo.iloc[0].get('num','Recado 3')
        except:
            m1, m2, m3 = "Vazio", "Vazio", "Vazio"
        st.warning(f"1️⃣ {m1}\n\n2️⃣ {m2}\n\n3️⃣ {m3}")
        with st.form("form_mural"):
            n1 = st.text_input("Aviso 1", m1)
            n2 = st.text_input("Aviso 2", m2)
            n3 = st.text_input("Aviso 3", m3)
            if st.form_submit_button("💾 Salvar Avisos"):
                requests.post(WEBAPP_URL, json={"action":"edit", "row":2, "data":["AVISO","","","",n1, n2, n3, "","",""]})
                st.success("Salvo!")
                st.rerun()

    with t4: # CADASTRAR
        st.subheader("➕ Novo Membro")
        with st.form("form_cad"):
            nome_n = st.text_input("Nome Completo *")
            nasc_n = st.text_input("Nascimento (DD/MM/AAAA) *")
            tel_n = st.text_input("Telefone")
            vinc_tipo = st.radio("Vínculo", ["Filho(a) de", "Cônjuge de"], horizontal=True)
            vinc_ref = st.selectbox("Referência", ["Raiz"] + nomes_lista)
            if st.form_submit_button("💾 Salvar"):
                v_total = f"{vinc_tipo} {vinc_ref}" if vinc_ref != "Raiz" else "Raiz"
                requests.post(WEBAPP_URL, json={"action":"append", "data":[nome_n, nasc_n, v_total, tel_n, "", "", "", "", "", ""]})
                st.success("Adicionado!")
                st.rerun()

    with t5: # GERENCIAR
        st.subheader("✏️ Editar ou Excluir")
        quem = st.selectbox("Escolha alguém", ["--"] + nomes_lista)
        if quem != "--":
            m_dados = df_m[df_m['nome'] == quem].iloc[0]
            linha = df_todo.index[df_todo['nome'] == quem].tolist()[0] + 2
            with st.form("form_edit"):
                new_tel = st.text_input("Telefone", m_dados['telefone'])
                new_rua = st.text_input("Rua", m_dados['rua'])
                if st.form_submit_button("💾 Atualizar"):
                    requests.post(WEBAPP_URL, json={"action":"edit", "row":linha, "data":[quem, m_dados['nascimento'], m_dados['vinculo'], new_tel, "", new_rua, "", "", "", ""]})
                    st.rerun()
                if st.form_submit_button("🗑️ EXCLUIR"):
                    requests.post(WEBAPP_URL, json={"action":"edit", "row":linha, "data":[""]*10})
                    st.rerun()

    with t6: # ARVORE
        st.subheader("🌳 Nossa Árvore")
        dot = 'digraph G { rankdir=LR; node [shape=box, style=filled, fillcolor="#E1F5FE", fontname="Arial"];'
        for _, row in df_m.iterrows():
            n, v = row['nome'].strip(), row['vinculo'].strip()
            if v != "Raiz":
                ref = v.split(" de ")[-1] if " de " in v else v
                dot += f'"{ref}" -> "{n}";'
            else:
                dot += f'"{n}" [fillcolor="#C8E6C9"];'
        st.graphviz_chart(dot + '}')
