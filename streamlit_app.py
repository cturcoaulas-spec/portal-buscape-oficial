import streamlit as st
import pandas as pd
import requests

# CONFIGURAÇÃO DE INTERFACE
st.set_page_config(page_title="Família Buscapé", page_icon="🌳", layout="centered")

# LINKS DE CONEXÃO
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzDd11VRMTQSvd3MDNZgok8qV4o_y4s0KhBaAJQFC0HZtg36mpydMTVmPQXg34lZp_RCQ/exec"
CSV_URL = "https://docs.google.com/spreadsheets/d/1jrtIP1lN644dPqY0HPGGwPWQGyYwb8nWsUigVK3QZio/export?format=csv"

# --- SEGURANÇA ---
if 'logado' not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.title("🌳 Portal Buscapé")
    senha = st.text_input("Senha de Acesso", type="password")
    if st.button("ACESSAR"):
        if senha == "buscape2026":
            st.session_state.logado = True
            st.rerun()
        else:
            st.error("Senha incorreta.")
else:
    def carregar_dados():
        try:
            # Lendo com cache para evitar lentidão
            df = pd.read_csv(CSV_URL, dtype=str).fillna("")
            df.columns = [c.strip().lower() for c in df.columns]
            return df
        except:
            return pd.DataFrame(columns=["nome", "nascimento", "ascendente", "telefone", "email", "rua", "num", "comp", "bairro", "cep"])

    df = carregar_dados()
    # Criamos a lista de nomes para a rolagem (selectbox)
    lista_nomes = sorted(df['nome'].unique().tolist()) if not df.empty else []
    opcoes_rolagem = ["Raiz"] + lista_nomes

    st.title("🌳 Portal Família Buscapé")
    aba1, aba2, aba3 = st.tabs(["🔍 Consultar", "➕ Novo Cadastro", "✏️ Editar"])

    with aba1:
        st.subheader("Lista da Família")
        st.dataframe(df, use_container_width=True, hide_index=True)

    with aba2:
        st.subheader("Novo Cadastro")
        with st.form("form_novo", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                nome = st.text_input("Nome Completo")
                nasc = st.text_input("Nascimento")
                # AQUI VOLTOU A JANELA DE ROLAGEM:
                asc = st.selectbox("Ascendente (Pai/Mãe)", opcoes_rolagem)
                tel = st.text_input("Telefone")
                mail = st.text_input("E-mail")
            with c2:
                rua = st.text_input("Rua")
                num = st.text_input("Nº")
                comp = st.text_input("Complemento")
                bairro = st.text_input("Bairro")
                cep = st.text_input("CEP")
            
            if st.form_submit_button("SALVAR NOVO"):
                if nome:
                    dados = [nome, nasc, asc, tel, mail, rua, num, comp, bairro, cep]
                    requests.post(WEBAPP_URL, json={"action": "append", "data": dados})
                    st.success(f"{nome} foi adicionado!")
                    st.rerun()

    with aba3:
        st.subheader("Editar Cadastro")
        if not df.empty:
            nome_sel = st.selectbox("Quem você quer editar?", lista_nomes)
            pessoa = df[df['nome'] == nome_sel].iloc[0]
            idx = df.index[df['nome'] == nome_sel].tolist()[0] + 2

            with st.form("form_editar"):
                col1, col2 = st.columns(2)
                with col1:
                    ed_nasc = st.text_input("Nascimento", value=pessoa.get('nascimento', ''))
                    # AQUI TAMBÉM VOLTOU A ROLAGEM NA EDIÇÃO:
                    # Tentamos encontrar a posição atual do ascendente na lista
                    try:
                        index_atual = opcoes_rolagem.index(pessoa.get('ascendente', 'Raiz'))
                    except:
                        index_atual = 0
                    ed_asc = st.selectbox("Ascendente", opcoes_rolagem, index=index_atual)
                    
                    ed_tel = st.text_input("Telefone", value=pessoa.get('telefone', ''))
                    ed_mail = st.text_input("E-mail", value=pessoa.get('email', ''))
                with col2:
                    ed_rua = st.text_input("Rua", value=pessoa.get('rua', ''))
                    ed_num = st.text_input("Nº", value=pessoa.get('num', ''))
                    ed_comp = st.text_input("Complemento", value=pessoa.get('comp', ''))
                    ed_bair = st.text_input("Bairro", value=pessoa.get('bairro', ''))
                    ed_cep = st.text_input("CEP", value=pessoa.get('cep', ''))
                
                if st.form_submit_button("ATUALIZAR DADOS"):
                    dados_up = [nome_sel, ed_nasc, ed_asc, ed_tel, ed_mail, ed_rua, ed_num, ed_comp, ed_bair, ed_cep]
                    requests.post(WEBAPP_URL, json={"action": "edit", "row": idx, "data": dados_up})
                    st.success(f"Dados de {nome_sel} atualizados!")
                    st.rerun()
