import streamlit as st
import pandas as pd
import requests
import re
import unicodedata
import time
from urllib.parse import quote
from datetime import datetime
from fpdf import FPDF

# 1. CONFIGURAÇÃO (DEVE SER A PRIMEIRA LINHA)
st.set_page_config(page_title="Família Buscapé", page_icon="🌳", layout="wide")

# 2. BLOCO DE SEGURANÇA E ESTILO (ESCONDE MENU E CÓDIGO)
st.markdown("""
    <style>
    /* TRAVAS DE SEGURANÇA: Esconde menus de desenvolvedor */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    [data-testid="stToolbar"] {visibility: hidden !important;}
    button[title="View source cast"] {display: none;}
    
    /* ESTILO DO PORTAL (MOBILE FIRST) */
    .stApp { margin-top: -60px; }
    [data-baseweb="tab-list"] { gap: 8px; overflow-x: auto; }
    [data-baseweb="tab"] { padding: 10px; border-radius: 10px; background: #f0f2f6; min-width: 110px; }
    button { height: 3.5em !important; font-weight: bold !important; border-radius: 12px !important; width: 100% !important; }
    .stExpander { border-radius: 12px !important; border: 1px solid #ddd !important; }
    </style>
    """, unsafe_allow_html=True)
