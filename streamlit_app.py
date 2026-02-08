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

# --- FUNÇÕES ---
def limpar(v): return re.sub(r'\D', '', str(v))
def mask_tel(v):
    n = limpar(v)
    if len(n) >= 11: return f"({n[:2]}) {n[2:7]}-{n[7:11]}"
    return v
def mask_data(v):
    n = limpar(v)
    if len(n) >= 8: return f"{n[:2]}/{n[2:4]}/{n[4:8]}"
    return v

def gerar_pdf(dados):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(200, 10, "Relatorio Familia Buscape", ln=True, align="C")
    for _, r in dados.iterrows():
        pdf.set_font("Arial", "B", 11)
        pdf.cell(0, 10, f"Membro: {r.get('nome','-')}", ln=True)
        pdf.set_font("Arial", size=10)
        pdf.cell(0, 7, f"Nasc: {r.get('nascimento','-')} | Tel: {r.get('telefone','-')}", ln=True)
        pdf.cell(0, 7, f"End: {r.get('rua','-')}, {r.get('num','-')} - {r.get('bairro','-')}", ln=True)
        pdf.ln(5); pdf.line(10, pdf.get_y(), 200, pdf.get_y()); pdf.ln(5)
    return pdf.output(dest='S').encode('latin-1')

# --- ACESSO ---
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
    df_m = df_todo[df_todo['nome'].str.strip() != ""].copy()
    nomes_lista = sorted(df_m['nome'].tolist())

    # --- SIDEBAR (NOTIFICAÇÕES E PDF) ---
    with st.sidebar:
        st.title("🔔 Notificações")
        hoje_dm = datetime.now().strftime("%d/%m")
        niver_hoje = [r['nome'] for _, r in df_m.iterrows() if str(r.get('nascimento','')).startswith(hoje_dm)]
        if niver_hoje:
            for n in niver_hoje: st.success(f"🎂 Hoje: {n}")
        else: st.info("Sem aniversários hoje.")
        st.divider()
        st.write("📥 **Exportar PDF**")
        st.caption("Marque os membros na aba 🔍 para habilitar.")

    st.title("🌳 Família Buscapé")
    tabs = st.tabs(["🔍 Membros", "🎂 Aniversários", "📢 Mural", "➕ Cadastrar", "✏️ Gerenciar"])

    # --- TAB 1: MEMBROS (COM LINKS E DADOS) ---
    with tabs[0]:
        sel_ids = []
        for i, r in df_m.iterrows():
            c1, c2 = st.columns([0.2, 3.8])
            if c1.checkbox("", key=f"check_{i}"): sel_ids.append(i)
            with c2.expander(f"👤 {r.get('nome','-')} | 📞 {r.get('telefone','-')}"):
                col_i1, col_i2, col_i3 = st.columns([2, 2, 1])
                with col_i1:
                    st.write(f"💍 **Cônjuge:** {r.get('conjuge','-')}")
                    st.write(f"🌳 **Vínculo:** {r.get('ascendente','-')}")
                    st.write(f"📅 **Nasc:** {r.get('nascimento','-')}")
                with col_i2:
                    rua, n_rua, bai = r.get('rua',''), r.get('num',''), r.get('bairro','')
                    st.write(f"🏠 {rua}, {n_rua}")
                    st.write(f"📍 {bai} | CEP: {r.get('cep','')}")
                with col_i3:
                    t_limpo = limpar(r.get('telefone',''))
                    if len(t_limpo) >= 10:
                        st.link_button("💬 Zap", f"https://wa.me/55{t_limpo}")
                    if rua:
                        q_map = quote(f"{rua}, {n_rua}, {bai}")
                        st.link_button("📍 Maps", f"https://www.google.com/maps/search/?api=1&query={q_map}")

        if sel_ids:
            pdf_data = gerar_pdf(df_m.loc[sel_ids])
            st.sidebar.download_button("📥 BAIXAR PDF SELECIONADOS", pdf_data, "familia.pdf", "application/pdf")

    # --- TAB 2: ANIVERSÁRIOS ---
    with tabs[1]:
        mes_f = datetime.now().strftime("%m")
        st.subheader(f"🎂 Aniversariantes do Mês {mes_f}")
        for _, r in df_m.iterrows():
            d = str(r.get('nascimento',''))
            if f"/{mes_f}/" in d or (len(limpar(d))>=4 and limpar(d)[2:4] == mes_f):
                st.info(f"🎈 Dia {d[:2]} - {r['nome']}")

    # --- TAB 3: MURAL (3 AVISOS) ---
    with tabs[2]:
        st.subheader("📢 Mural de Avisos")
        # Usamos a linha 2 (índice 0 do df_todo se for a primeira de dados) para estoque
        av1 = df_todo.iloc[0].get('email', 'Vazio')
        av2 = df_todo.iloc[0].get('rua', 'Vazio')
        av3 = df_todo.iloc[0].get('num', 'Vazio')
        
        c_av1, c_av2, c_av3 = st.columns(3)
        c_av1.warning(f"**Aviso 1**\n\n{av1}")
        c_av2.warning(f"**Aviso 2**\n\n{av2}")
        c_av3.warning(f"**Aviso 3**\n\n{av3}")

        st.divider()
        st.write("✏️ **Editar Mural**")
        nv1 = st.text_input("Novo Aviso 1", value=av1)
        nv2 = st.text_input("Novo Aviso 2", value=av2)
        nv3 = st.text_input("Novo Aviso 3", value=av3)
        if st.button("💾 Salvar Mural"):
            requests.post(WEBAPP_URL, json={"action": "edit", "row": 2, "data": ["AVISO","", "", "", nv1, nv2, nv3, "", "", ""]})
            st.success("Mural atualizado!"); st.rerun()

    # --- TAB 4: CADASTRAR (TODOS OS CAMPOS) ---
    with tabs[3]:
        with st.form("form_novo", clear_on_submit=True):
            f1, f2 = st.columns(2)
            with f1:
                new_n = st.text_input("Nome completo")
                new_d = st.text_input("Nascimento (DDMMAAAA)")
                new_t = st.text_input("Telefone (DDD + Número)")
                new_v = st.radio("Vínculo", ["Filho(a) de", "Cônjuge de"], horizontal=True)
                new_ref = st.selectbox("Referência na família", ["Raiz"] + nomes_lista)
            with f2:
                new_e = st.text_input("E-mail")
                new_ru = st.text_input("Rua")
                new_nu = st.text_input("Nº")
                new_ba = st.text_input("Bairro")
                new_ce = st.text_input("CEP")
            if st.form_submit_button("💾 SALVAR NOVO MEMBRO"):
                vinc_final = f"{new_v} {new_ref}" if new_ref != "Raiz" else "Raiz"
                conj_final = new_ref if "Cônjuge" in new_v else ""
                payload = [new_n, mask_data(new_d), vinc_final, mask_tel(new_t), new_e, new_ru, new_nu, conj_final, new_ba, new_ce]
                requests.post(WEBAPP_URL, json={"action": "append", "data": payload})
                st.success("Cadastrado com sucesso!"); st.rerun()

    # --- TAB 5: GERENCIAR (EDIÇÃO COMPLETA) ---
    with tabs[4]:
        escolha = st.selectbox("Selecione o membro para alterar", ["--"] + nomes_lista)
        if escolha != "--":
            m_edit = df_m[df_m['nome'] == escolha].iloc[0]
            idx_planilha = df_m.index[df_m['nome'] == escolha].tolist()[0] + 2
            with st.form("form_edit"):
                fe1, fe2 = st.columns(2)
                with fe1:
                    ed_n = st.text_input("Nascimento", m_edit.get('nascimento',''))
                    ed_t = st.text_input("Telefone", m_edit.get('telefone',''))
                    ed_c = st.text_input("Cônjuge", m_edit.get('conjuge',''))
                with fe2:
                    ed_r = st.text_input("Rua", m_edit.get('rua',''))
                    ed_nu = st.text_input("Nº", m_edit.get('num',''))
                    ed_b = st.text_input("Bairro", m_edit.get('bairro',''))
                    ed_ce = st.text_input("CEP", m_edit.get('cep',''))
                
                c_bt1, c_bt2 = st.columns(2)
                if c_bt1.form_submit_button("💾 ATUALIZAR DADOS"):
                    up_data = [escolha, mask_data(ed_n), m_edit.get('ascendente',''), mask_tel(ed_t), m_edit.get('email',''), ed_r, ed_nu, ed_c, ed_b, ed_ce]
                    requests.post(WEBAPP_URL, json={"action": "edit", "row": idx_planilha, "data": up_data})
                    st.success("Dados atualizados!"); st.rerun()
                if c_bt2.form_submit_button("🗑️ EXCLUIR MEMBRO"):
                    requests.post(WEBAPP_URL, json={"action": "edit", "row": idx_planilha, "data": [""]*10})
                    st.warning("Membro excluído."); st.rerun()

    st.sidebar.button("🚪 Sair", on_click=lambda: st.session_state.update({"logado": False}))
