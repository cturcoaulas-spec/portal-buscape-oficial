import streamlit as st
import pandas as pd
import requests

# CONFIGURAÇÕES
st.set_page_config(page_title="Portal Família Buscapé", page_icon="🌳", layout="wide")

# LINKS DE CONEXÃO
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzDd11VRMTQSvd3MDNZgok8qV4o_y4s0KhBaAJQFC0HZtg36mpydMTVmPQXg34lZp_RCQ/exec"
CSV_URL = "https://docs.google.com/spreadsheets/d/1jrtIP1lN644dPqY0HPGGwPWQGyYwb8nWsUigVK3QZio/export?format=csv"

def carregar_dados():
    try:
        df = pd.read_csv(CSV_URL, dtype=str).fillna("")
        for col in df.columns:
            df[col] = df[col].astype(str).str.replace(r'\.0$', '', regex=True)
        return df
    except:
        return pd.DataFrame(columns=["Nome", "Nascimento", "Ascendente", "Telefone", "Email", "Rua", "Num", "Comp", "Bairro", "CEP"])

df = carregar_dados()

# --- NAVEGAÇÃO ---
menu = st.sidebar.radio("O que deseja fazer?", ["🔍 Ver Família", "➕ Novo Cadastro", "✏️ Editar / Atualizar"])

# --- 1. VER FAMÍLIA ---
if menu == "🔍 Ver Família":
    st.header("👥 Base de Dados Buscapé")
    st.dataframe(df, use_container_width=True)
    st.button("🔄 Atualizar Lista", on_click=st.rerun)

# --- 2. NOVO CADASTRO ---
elif menu == "➕ Novo Cadastro":
    st.header("📝 Novo Cadastro na Nuvem")
    with st.form("novo_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            nome = st.text_input("Nome Completo")
            nasc = st.text_input("Nascimento")
            opcoes_asc = ["Raiz"] + sorted(df["Nome"].unique().tolist())
            asc = st.selectbox("Ascendente", opcoes_asc)
            tel = st.text_input("Telefone")
        with c2:
            mail = st.text_input("E-mail")
            rua = st.text_input("Rua")
            num = st.text_input("Nº")
            comp = st.text_input("Comp")
            bairro = st.text_input("Bairro")
            cep = st.text_input("CEP")
        
        if st.form_submit_button("CADASTRAR"):
            if nome:
                dados = [nome, nasc, asc, tel, mail, rua, num, comp, bairro, cep]
                # O comando 'APPEND' adiciona no final
                requests.post(WEBAPP_URL, json={"action": "append", "data": dados})
                st.success(f"{nome} foi adicionado!")
                st.rerun()

# --- 3. EDITAR / ATUALIZAR (OS 90% QUE FALTAVAM!) ---
elif menu == "✏️ Editar / Atualizar":
    st.header("✏️ Atualizar Dados Existentes")
    if not df.empty:
        nome_sel = st.selectbox("Selecione quem deseja editar:", sorted(df["Nome"].unique().tolist()))
        pessoa = df[df["Nome"] == nome_sel].iloc[0]
        
        # Pega o índice da linha na planilha (somamos 2 porque o Sheets começa em 1 e tem cabeçalho)
        index_linha = df.index[df['Nome'] == nome_sel].tolist()[0] + 2

        with st.form("edit_form"):
            c1, c2 = st.columns(2)
            with c1:
                e_nasc = st.text_input("Nascimento", value=pessoa['Nascimento'])
                e_asc = st.text_input("Ascendente", value=pessoa['Ascendente'])
                e_tel = st.text_input("Telefone", value=pessoa['Telefone'])
            with c2:
                e_mail = st.text_input("E-mail", value=pessoa['Email'])
                e_rua = st.text_input("Rua", value=pessoa['Rua'])
                e_num = st.text_input("Nº", value=pessoa['Num'])
                e_bairro = st.text_input("Bairro", value=pessoa['Bairro'])
                e_cep = st.text_input("CEP", value=pessoa['CEP'])
            
            if st.form_submit_button("SALVAR ALTERAÇÕES"):
                dados_editados = [nome_sel, e_nasc, e_asc, e_tel, e_mail, e_rua, e_num, pessoa['Comp'], e_bairro, e_cep]
                # O comando 'EDIT' diz ao Google qual linha mudar
                requests.post(WEBAPP_URL, json={"action": "edit", "row": index_linha, "data": dados_editados})
                st.success(f"Dados de {nome_sel} atualizados na nuvem!")
                st.rerun()
