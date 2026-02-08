import streamlit as st
import pandas as pd
import requests
import re
from urllib.parse import quote
from datetime import datetime
from fpdf import FPDF

# CONFIGURAÇÃO
st.set_page_config(page_title="Família Buscapé", page_icon="🌳", layout="wide")

WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzWJ_nDGDe4a81O5BDx3meMbVJjlcMpJoxoO05lilysWJaj_udqeXqvfYFgzvWPlC-Omw/exec"
CSV_URL = "https://docs.google.com/spreadsheets/d/1jrtIP1lN644dPqY0HPGGwPWQGyYwb8nWsUigVK3QZio/export?format=csv"

MESES_BR = ["", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

# --- FUNÇÕES DE TRATAMENTO ---
def limpar(v): return re.sub(r'\D', '', str(v))

def validar_e_formatar_tel(v):
    n = limpar(v)
    if len(n) == 11: return f"({n[:2]}) {n[2:7]}-{n[7:11]}"
    if len(n) == 10: return f"({n[:2]}) {n[2:6]}-{n[6:10]}"
    return None

def validar_e_formatar_data(v):
    n = limpar(v)
    if len(n) == 8: return f"{n[:2]}/{n[2:4]}/{n[4:8]}"
    return None

def gerar_pdf(dados):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(200, 10, "Relatório Família Buscapé", ln=True, align="C")
    for _, r in dados.iterrows():
        pdf.set_font("Arial", "B", 11)
        pdf.cell(0, 8, f"Nome: {r.get('nome','-')}", ln=True)
        pdf.set_font("Arial", size=10)
        pdf.cell(0, 6, f"Nasc: {r.get('nascimento','-')} | Tel: {r.get('telefone','-')} | E-mail: {r.get('email','-')}", ln=True)
        end = f"{r.get('rua','-')}, {r.get('num','-')} - {r.get('bairro','-')} | CEP: {r.get('cep','-')}"
        pdf.cell(0, 6, f"End: {end}", ln=True)
        pdf.ln(4); pdf.line(10, pdf.get_y(), 200, pdf.get_y()); pdf.ln(4)
    return pdf.output(dest='S').encode('latin-1')

# --- LOGIN ---
if 'logado' not in st.session_state: st.session_state.logado = False
if not st.session_state.logado:
    st.title("🌳 Portal Família Buscapé")
    psw = st.text_input("Senha", type="password")
    if st.button("ENTRAR"):
        if psw == "buscape2026": st.session_state.logado = True; st.rerun()
        else: st.error("Senha incorreta")
else:
    @st.cache_data(ttl=2)
    def carregar():
        try:
            df = pd.read_csv(CSV_URL, dtype=str).fillna("")
            df.columns = [c.strip().lower() for c in df.columns]
            return df
        except: return pd.DataFrame()

    df_todo = carregar()
    df_m = df_todo[df_todo['nome'].str.strip() != ""].sort_values(by='nome').copy()
    nomes_lista = df_m['nome'].tolist()

    # --- SIDEBAR ---
    with st.sidebar:
        st.title("🔔 Notificações")
        hoje = datetime.now().strftime("%d/%m")
        niver_hoje = [r['nome'] for _, r in df_m.iterrows() if str(r.get('nascimento','')).startswith(hoje)]
        if niver_hoje:
            for n in niver_hoje: st.success(f"🎂 Hoje: {n}")
        else: st.info("Sem notificações hoje")
        st.divider()
        st.button("🚪 Sair", on_click=lambda: st.session_state.update({"logado": False}))

    st.title("🌳 Família Buscapé")
    tabs = st.tabs(["🔍 Membros", "🎂 Aniversários", "📢 Mural", "➕ Cadastrar", "✏️ Gerenciar"])

    # --- TAB 1: MEMBROS ---
    with tabs[0]:
        sel_ids = []
        c_topo = st.container()
        for i, r in df_m.iterrows():
            col1, col2 = st.columns([0.2, 3.8])
            if col1.checkbox("", key=f"chk_{i}"): sel_ids.append(i)
            with col2.expander(f"👤 {r.get('nome','-')} | 📅 {r.get('nascimento','-')}"):
                ci, cl = st.columns([3, 1])
                with ci:
                    st.write(f"💍 **Cônjuge:** {r.get('conjuge','-')}")
                    st.write(f"📞 **Tel:** {r.get('telefone','-')} | 🌳 **Vínculo:** {r.get('ascendente','-')}")
                    st.write(f"🏠 {r.get('rua','-')}, {r.get('num','-')} - {r.get('bairro','-')} ({r.get('cep','-')})")
                    st.write(f"✉️ **E-mail:** {r.get('email','-')}")
                with cl:
                    t_clean = limpar(r.get('telefone',''))
                    if len(t_clean) >= 10:
                        st.link_button("💬 WhatsApp", f"https://wa.me/55{t_clean}")
                        st.link_button("📞 Ligar", f"tel:{t_clean}")
                    if r.get('rua'):
                        loc = quote(f"{r['rua']}, {r['num']}, {r['bairro']}, {r['cep']}")
                        st.link_button("📍 Mapa", f"https://www.google.com/maps/search/?api=1&query={loc}")

        if sel_ids:
            pdf_bytes = gerar_pdf(df_m.loc[sel_ids])
            c_topo.download_button("📥 BAIXAR PDF SELECIONADOS", pdf_bytes, "familia.pdf")

    # --- TAB 2: ANIVERSÁRIOS ---
    with tabs[1]:
        mes_atual = datetime.now().month
        st.subheader(f"🎂 Aniversariantes de {MESES_BR[mes_atual]}")
        any_niver = False
        for _, r in df_m.iterrows():
            dt = str(r.get('nascimento',''))
            clean_dt = limpar(dt)
            if "/" in dt:
                mes_niver = int(dt.split('/')[1]) if len(dt.split('/')) > 1 else 0
            elif len(clean_dt) == 8:
                mes_niver = int(clean_dt[2:4])
            else: mes_niver = 0
            
            if mes_niver == mes_atual:
                st.info(f"🎈 Dia {dt[:2]} - {r['nome']}")
                any_niver = True
        if not any_niver: st.write("Nenhum este mês.")

    # --- TAB 3: MURAL ---
    with tabs[2]:
        st.subheader("📢 Mural de Avisos")
        avs = [df_todo.iloc[0].get('email','Vazio'), df_todo.iloc[0].get('rua','Vazio'), df_todo.iloc[0].get('num','Vazio')]
        c_av = st.columns(3)
        for i in range(3): c_av[i].warning(f"**Aviso {i+1}**\n\n{avs[i]}")
        st.divider()
        with st.form("mural_edit"):
            v1, v2, v3 = st.text_input("Aviso 1", avs[0]), st.text_input("Aviso 2", avs[1]), st.text_input("Aviso 3", avs[2])
            b1, b2 = st.columns(2)
            if b1.form_submit_button("💾 SALVAR"):
                requests.post(WEBAPP_URL, json={"action":"edit", "row":2, "data":["AVISO","","","",v1, v2, v3, "","",""]})
                st.rerun()
            if b2.form_submit_button("🗑️ LIMPAR TUDO"):
                requests.post(WEBAPP_URL, json={"action":"edit", "row":2, "data":["AVISO","","","", "Vazio", "Vazio", "Vazio", "","",""]})
                st.rerun()

    # --- TAB 4: CADASTRAR ---
    with tabs[3]:
        with st.form("f_cadastro", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            with col_a:
                nome_c = st.text_input("Nome Completo")
                data_c = st.text_input("Nascimento (Apenas números: DDMMAAAA)", help="Ex: 08021990")
                tel_c = st.text_input("Telefone (Apenas números com DDD)", help="Ex: 11999998888")
                vinc_c = st.radio("Vínculo", ["Filho(a) de", "Cônjuge de"], horizontal=True)
                ref_c = st.selectbox("Referência", ["Raiz"] + nomes_lista)
            with col_b:
                mail_c = st.text_input("E-mail")
                rua_c, num_c = st.text_input("Rua"), st.text_input("Nº")
                bair_c, cep_c = st.text_input("Bairro"), st.text_input("CEP")
            
            if st.form_submit_button("💾 SALVAR CADASTRO"):
                f_data = validar_e_formatar_data(data_c)
                f_tel = validar_e_formatar_tel(tel_c)
                
                if not f_data: st.error("❌ Data inválida! Use 8 números (Ex: 08021990)"); st.stop()
                if not f_tel: st.error("❌ Telefone inválido! Use 10 ou 11 números"); st.stop()
                
                v_final = f"{vinc_c} {ref_c}" if ref_c != "Raiz" else "Raiz"
                c_final = ref_c if "Cônjuge" in vinc_c else ""
                requests.post(WEBAPP_URL, json={"action":"append", "data":[nome_c, f_data, v_final, f_tel, mail_c, rua_c, num_c, c_final, bair_c, cep_c]})
                st.success("✅ Cadastrado com sucesso!"); st.rerun()

    # --- TAB 5: GERENCIAR ---
    with tabs[4]:
        edit_p = st.selectbox("Selecione para editar", ["--"] + nomes_lista)
        if edit_p != "--":
            m = df_m[df_m['nome'] == edit_p].iloc[0]
            idx_planilha = df_m.index[df_m['nome'] == edit_p].tolist()[0] + 2
            with st.form("f_gerenciamento"):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.text_input("Nome", value=m.get('nome',''), disabled=True)
                    e_data = st.text_input("Nascimento", value=m.get('nascimento',''))
                    e_tel = st.text_input("Telefone", value=m.get('telefone',''))
                    e_vinc = st.text_input("Vínculo", value=m.get('ascendente',''))
                    e_conj = st.selectbox("Cônjuge", [""] + nomes_lista, index=nomes_lista.index(m.get('conjuge',''))+1 if m.get('conjuge','') in nomes_lista else 0)
                with col_b:
                    e_mail = st.text_input("E-mail", value=m.get('email',''))
                    e_rua = st.text_input("Rua", value=m.get('rua',''))
                    e_num = st.text_input("Nº", value=m.get('num',''))
                    e_bair = st.text_input("Bairro", value=m.get('bairro',''))
                    e_cep = st.text_input("CEP", value=m.get('cep',''))
                
                c_bt1, c_bt2 = st.columns(2)
                if c_bt1.form_submit_button("💾 ATUALIZAR"):
                    f_data_e = validar_e_formatar_data(e_data) or e_data
                    f_tel_e = validar_e_formatar_tel(e_tel) or e_tel
                    requests.post(WEBAPP_URL, json={"action":"edit", "row":idx_planilha, "data":[edit_p, f_data_e, e_vinc, f_tel_e, e_mail, e_rua, e_num, e_conj, e_bair, e_cep]})
                    st.success("✅ Atualizado!"); st.rerun()
                if c_bt2.form_submit_button("🗑️ EXCLUIR MEMBRO"):
                    requests.post(WEBAPP_URL, json={"action":"edit", "row":idx_planilha, "data":[""]*10})
                    st.rerun()
