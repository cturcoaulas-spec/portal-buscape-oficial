import streamlit as st
import pandas as pd
import requests

# CONFIGURAÇÕES DE PÁGINA
st.set_page_config(page_title="Portal Família Buscapé", page_icon="🌳", layout="wide")

# ESTILO VISUAL CUSTOMIZADO
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { 
        width: 100%; 
        border-radius: 8px; 
        height: 3em; 
        background-color: #2e7d32; 
        color: white;
        font-weight: bold;
    }
    .stDataFrame { border: 1px solid #e6e9ef; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🌳 Portal Família Buscapé")
st.subheader("Sistema Unificado de Genealogia")

# LINKS DE CONEXÃO (SUAS CHAVES MESTRAS)
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzDd11VRMTQSvd3MDNZgok8qV4o_y4s0KhBaAJQFC0HZtg36mpydMTVmPQXg34lZp_RCQ/exec"
CSV_URL = "https://docs.google.com/spreadsheets/d/1jrtIP1lN644dPqY0HPGGwPWQGyYwb8nWsUigVK3QZio/export?format=csv"

def carregar_dados():
    try:
        # Lê os dados em tempo real da nuvem (Google Sheets)
        df = pd.read_csv(CSV_URL, dtype=str).fillna("")
        # Limpa resíduos de formatação (como .0 em números)
        for col in df.columns:
            df[col] = df[col].astype(str).str.replace(r'\.0$', '', regex=True)
        return df
    except Exception as e:
        return pd.DataFrame(columns=["Nome", "Nascimento", "Ascendente", "Telefone", "Email", "Rua", "Num", "Comp", "Bairro", "CEP"])

# Carregar os dados atuais da planilha
df = carregar_dados()

# --- MENU DE NAVEGAÇÃO ---
menu = st.sidebar.radio("Navegação:", ["👥 Ver Família", "📝 Novo Cadastro"])

# --- 1. ABA DE VISUALIZAÇÃO ---
if menu == "👥 Ver Família":
    st.header("Membros Cadastrados")
    if not df.empty and len(df) > 0:
        st.dataframe(df, use_container_width=True)
        st.success(f"Total de familiares na base: {len(df)}")
    else:
        st.warning("A base de dados ainda está vazia na nuvem.")
        st.info("Dica: Use a aba de cadastro para adicionar o primeiro membro.")

# --- 2. ABA DE CADASTRO AUTOMÁTICO ---
elif menu == "📝 Novo Cadastro":
    st.header("Cadastrar Novo Membro")
    st.write("Insira os dados abaixo. Eles serão salvos automaticamente na Planilha Google.")
    
    with st.form("form_novo_membro", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            nome = st.text_input("Nome Completo")
            nasc = st.text_input("Data de Nascimento (Ex: 01/01/1980)")
            # Cria lista de ascendentes baseada nos nomes já existentes
            opcoes_asc = ["Raiz"] + sorted(df["Nome"].unique().tolist()) if not df.empty else ["Raiz"]
            asc = st.selectbox("Ascendente (Pai/Mãe)", opcoes_asc)
            tel = st.text_input("Telefone/WhatsApp")
        with c2:
            mail = st.text_input("E-mail")
            rua = st.text_input("Rua/Endereço")
            col_n, col_c = st.columns([1, 2])
            num = col_n.text_input("Nº")
            comp = col_c.text_input("Comp.")
            bairro = st.text_input("Bairro")
            cep = st.text_input("CEP")
        
        # BOTÃO DE ENVIO
        enviar = st.form_submit_button("CADASTRAR NA NUVEM")
        
        if enviar:
            if nome and nasc:
                # Prepara a lista para o Google Sheets (Exatamente 10 colunas)
                dados_para_envio = [nome, nasc, asc, tel, mail, rua, num, comp, bairro, cep]
                try:
                    # O "Pulo do Gato": Envia para o App Script que você criou
                    post_resposta = requests.post(WEBAPP_URL, json=dados_para_envio)
                    
                    if post_resposta.status_code == 200:
                        st.success(f"Parabéns! {nome} foi adicionado com sucesso.")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("Erro ao salvar no Google. Verifique a conexão.")
                except Exception as erro:
                    st.error(f"Falha na comunicação com a nuvem: {erro}")
            else:
                st.warning("Os campos 'Nome' e 'Nascimento' são obrigatórios.")

# --- RODAPÉ ---
st.sidebar.markdown("---")
st.sidebar.info("Portal Família Buscapé v3.0 - 2026")
