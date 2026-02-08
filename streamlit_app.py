import streamlit as st
import pandas as pd
import requests
import re

# 1. CONFIGURAÇÃO DE TELA LARGA (Para visualizar todo o cadastro)
st.set_page_config(page_title="Portal Família Buscapé", page_icon="🌳", layout="wide")

# 2. CONEXÃO - COLOQUE SEU LINK /EXEC AQUI
# Sem este link real, o erro "MissingSchema" continuará acontecendo.
WEBAPP_URL = "COLE_AQUI_SEU_LINK_DO_GOOGLE_SCRIPT_QUE_TERMINA_EM_EXEC"
CSV_URL = "https://docs.google.com/spreadsheets/d/1jrtIP1lN644dPqY0HPGGwPWQGyYwb8nWsUigVK3QZio/export?format=csv"

# 3. FUNÇÕES DE MÁSCARA AUTOMÁTICA
def masc_tel(v):
    n = re.sub(r'\D', '', str(v))
    if len(n) == 11: return f"({n[:2]}) {n[2:7]}-{n[7:]}"
    if len(n) == 10: return f"({n[:2]}) {n[2:6]}-{n[6:]}"
    return v

def masc_data(v):
    n = re.sub(r'\D', '', str(v))
    if len(n) == 8: return f"{n[:2]}/{n[2:4]}/{n[4:]}"
    return v

# 4. SISTEMA DE LOGIN
if 'logado' not in st.session_state: st.session_state.logado = False
if not st.session_state.logado:
    st.title("🌳 Portal Família Buscapé")
    senha = st.text_input("Digite a Senha de Acesso:", type="password")
    if st.button("ENTRAR"):
        if senha == "buscape2026":
            st.session_state.logado = True
            st.rerun()
        else: st.error("Senha incorreta.")
else:
    # 5. CARREGAMENTO DE DADOS
    def carregar():
        try:
            df = pd.read_csv(CSV_URL, dtype=str).fillna("")
            df.columns = [c.strip().lower() for c in df.columns]
            return df
        except: return pd.DataFrame()

    df = carregar()
    nomes_lista = sorted(df['nome'].tolist()) if not df.empty else []

    st.title("🌳 Portal Família Buscapé")
    
    # 6. ABAS DE NAVEGAÇÃO
    tab1, tab2, tab3 = st.tabs(["🔍 Ver Cadastro Completo", "➕ Novo Membro", "✏️ Editar Dados"])

    # --- ABA 1: VISUALIZAÇÃO ---
    with tab1:
        st.subheader("Planilha de Dados da Família")
        st.dataframe(df, use_container_width=True, hide_index=True)

    # --- ABA 2: CADASTRO ---
    with tab2:
        st.subheader("Cadastrar Novo Integrante")
        with st.form("form_novo", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                f_nome = st.text_input("Nome Completo")
                f_nasc = st.text_input("Nascimento (DDMMAAAA)")
                f_asc  = st.selectbox("Ascendente", ["Raiz"] + nomes_lista)
                f_tel  = st.text_input("Telefone")
                f_mail = st.text_input("E-mail")
            with c2:
                f_rua  = st.text_input("Rua/Endereço")
                f_num  = st.text_input("Número")
                f_comp = st.text_input("Complemento")
                f_bair = st.text_input("Bairro")
                f_cep  = st.text_input("CEP")
            
            # BOTÃO DE SUBMIT OBRIGATÓRIO
            if st.form_submit_button("SALVAR NA NUVEM"):
                if f_nome and WEBAPP_URL.startswith("http"):
                    # Organiza exatamente as 10 colunas da sua planilha
                    dados = [f_nome, masc_data(f_nasc), f_asc, masc_tel(f_tel), f_mail, f_rua, f_num, f_comp, f_bair, f_cep]
                    try:
                        requests.post(WEBAPP_URL, json={"action": "append", "data": dados})
                        st.success("✅ Enviado com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro de conexão: {e}")
                else:
                    st.warning("Verifique se o nome foi preenchido e se a URL do Script na linha 12 está correta.")

    # --- ABA 3: EDIÇÃO ---
    with tab3:
        st.subheader("Atualizar Dados Existentes")
        if nomes_lista:
            sel = st.selectbox("Escolha quem deseja editar:", nomes_lista)
            p = df[df['nome'] == sel].iloc[0]
            idx_planilha = df.index[df['nome'] == sel].tolist()[0] + 2
            
            with st.form("form_edit"):
                e1, e2 = st.columns(2)
                with e1:
                    e_nasc = st.text_input("Nascimento", value=p.get('nascimento', ''))
                    e_tel  = st.text_input("Telefone", value=p.get('telefone', ''))
                    e_mail = st.text_input("E-mail", value=p.get('email', ''))
                with e2:
                    e_rua  = st.text_input("Rua", value=p.get('rua', ''))
                    e_num  = st.text_input("Nº", value=p.get('num', ''))
                    e_bair = st.text_input("Bairro", value=p.get('bairro', ''))
                    e_cep  = st.text_input("CEP", value=p.get('cep', ''))
                
                # BOTÃO DE SUBMIT OBRIGATÓRIO
                if st.form_submit_button("ATUALIZAR DADOS"):
                    # Mantém a integridade das 10 colunas
                    up = [sel, masc_data(e_nasc), p.get('ascendente','Raiz'), masc_tel(e_tel), e_mail, e_rua, e_num, p.get('comp',''), e_bair, e_cep]
                    try:
                        requests.post(WEBAPP_URL, json={"action": "edit", "row": idx_planilha, "data": up})
                        st.success("✅ Dados atualizados!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao atualizar: {e}")

    # RODAPÉ
    st.sidebar.button("Sair do Portal", on_click=lambda: st.session_state.update({"logado": False}))
