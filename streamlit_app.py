import streamlit as st
import pandas as pd
import requests
import re

# CONFIGURAÇÃO DE INTERFACE E PWA
st.set_page_config(page_title="Portal Família Buscapé", page_icon="🌳", layout="centered")

# --- CONFIGURAÇÃO DE CONEXÃO ---
# IMPORTANTE: Substitua o link abaixo pela sua URL do Google Script (que termina em /exec)
WEBAPP_URL = "COLE_AQUI_SEU_LINK_DO_GOOGLE_SCRIPT"
CSV_URL = "https://docs.google.com/spreadsheets/d/1jrtIP1lN644dPqY0HPGGwPWQGyYwb8nWsUigVK3QZio/export?format=csv"

# FUNÇÕES DE MÁSCARA AUTOMÁTICA
def aplicar_mascara_tel(v):
    nums = re.sub(r'\D', '', str(v))
    if len(nums) == 11: return f"({nums[:2]}) {nums[2:7]}-{nums[7:]}"
    if len(nums) == 10: return f"({nums[:2]}) {nums[2:6]}-{nums[6:]}"
    return v

def aplicar_mascara_data(v):
    nums = re.sub(r'\D', '', str(v))
    if len(nums) == 8: return f"{nums[:2]}/{nums[2:4]}/{nums[4:]}"
    return v

# --- SISTEMA DE SEGURANÇA ---
if 'logado' not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.title("🌳 Portal Família Buscapé")
    st.subheader("🔒 Acesso Restrito")
    senha = st.text_input("Senha de Acesso:", type="password")
    if st.button("ENTRAR NO PORTAL"):
        if senha == "buscape2026":
            st.session_state.logado = True
            st.rerun()
        else:
            st.error("Senha incorreta. Verifique com o administrador.")
else:
    # --- APP PRINCIPAL (LOGADO) ---
    def carregar_dados():
        try:
            df = pd.read_csv(CSV_URL, dtype=str).fillna("")
            df.columns = [c.strip().lower() for c in df.columns]
            return df
        except:
            return pd.DataFrame(columns=["nome", "nascimento", "ascendente", "telefone", "email", "rua", "num", "comp", "bairro", "cep"])

    df = carregar_dados()
    nomes_existentes = sorted(df['nome'].unique().tolist()) if not df.empty else []
    opcoes_ascendente = ["Raiz"] + nomes_existentes

    st.title("🌳 Portal Buscapé")
    
    tab1, tab2, tab3 = st.tabs(["🔍 Consultar", "➕ Novo Cadastro", "✏️ Editar Cadastro"])

    # --- ABA 1: CONSULTA ---
    with tab1:
        st.subheader("Membros da Família")
        busca = st.text_input("🔍 Pesquisar por nome, cidade ou parente:")
        if busca:
            df_mostrar = df[df.apply(lambda row: busca.lower() in row.astype(str).str.lower().values, axis=1)]
        else:
            df_mostrar = df
        
        st.dataframe(df_mostrar, use_container_width=True, hide_index=True)

    # --- ABA 2: NOVO CADASTRO ---
    with tab2:
        st.subheader("Adicionar Novo Membro")
        with st.form("form_novo", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                nome = st.text_input("Nome Completo")
                nasc = st.text_input("Data de Nascimento (Ex: 01011980)")
                asc = st.selectbox("Ascendente (Pai/Mãe)", opcoes_ascendente)
                tel = st.text_input("Telefone (Com DDD)")
            with col2:
                mail = st.text_input("E-mail")
                rua = st.text_input("Rua/Endereço")
                num = st.text_input("Nº")
                bair = st.text_input("Bairro")
                cep = st.text_input("CEP")
            
            if st.form_submit_button("CADASTRAR NA NUVEM"):
                if nome and nasc:
                    nasc_f = aplicar_mascara_data(nasc)
                    tel_f = aplicar_mascara_tel(tel)
                    dados_envio = [nome, nasc_f, asc, tel_f, mail, rua, num, "", bair, cep]
                    
                    try:
                        resp = requests.post(WEBAPP_URL, json={"action": "append", "data": dados_envio})
                        if resp.status_code == 200:
                            st.success(f"✅ {nome} foi adicionado!")
                            st.rerun()
                        else:
                            st.error("❌ Erro no Google Script. Verifique a Implantação.")
                    except:
                        st.error("❌ Erro de conexão. Verifique se a URL está correta.")

    # --- ABA 3: EDIÇÃO ---
    with tab3:
        st.subheader("Atualizar Dados")
        if not df.empty:
            nome_selecionado = st.selectbox("Selecione quem editar:", nomes_existentes)
            dados_pessoa = df[df['nome'] == nome_selecionado].iloc[0]
            linha_planilha = df.index[df['nome'] == nome_selecionado].tolist()[0] + 2

            with st.form("form_editar"):
                c1, c2 = st.columns(2)
                with c1:
                    ed_nasc = st.text_input("Nascimento", value=dados_pessoa.get('nascimento', ''))
                    try: idx_asc = opcoes_ascendente.index(dados_pessoa.get('ascendente', 'Raiz'))
                    except: idx_asc = 0
                    ed_asc = st.selectbox("Ascendente", opcoes_ascendente, index=idx_asc)
                    ed_tel = st.text_input("Telefone", value=dados_pessoa.get('telefone', ''))
                    ed_mail = st.text_input("E-mail", value=dados_pessoa.get('email', ''))
                with c2:
                    ed_rua = st.text_input("Rua", value=dados_pessoa.get('rua', ''))
                    ed_num = st.text
