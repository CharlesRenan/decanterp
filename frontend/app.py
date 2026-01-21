import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
from streamlit_option_menu import option_menu
from datetime import datetime, date
import os
import time

# --- CONFIGURAÇÃO ---
API_URL = "https://api-decant-oficial.onrender.com"

st.set_page_config(page_title="Decant ERP", page_icon="💧", layout="wide")

if 'carrinho' not in st.session_state: st.session_state['carrinho'] = []
if 'logado' not in st.session_state: st.session_state['logado'] = False
if 'usuario' not in st.session_state: st.session_state['usuario'] = ""
if 'cargo' not in st.session_state: st.session_state['cargo'] = ""

def render_logo_svg(width="50px", color="#EC4899"):
    # Logo Rosa/Roxo para combinar
    return f'<svg width="{width}" height="{width}" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M30 20 V80 C30 90 40 95 50 85 L80 50 C90 40 80 20 60 20 Z" stroke="{color}" stroke-width="8" fill="none"/><path d="M30 50 L60 20" stroke="{color}" stroke-width="8" stroke-linecap="round"/><circle cx="35" cy="85" r="5" fill="{color}"/></svg>'

def apply_custom_style():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
        
        /* Fundo Principal */
        .stApp { background-color: #0E0E0E; }
        
        /* Sidebar (Fundo Escuro) */
        div[data-testid="stSidebar"] { 
            background-color: #141414; 
            border-right: 1px solid #262626;
        }

        /* Títulos Brancos */
        h1, h2, h3, h4, h5, h6, strong { color: #FFFFFF !important; }
        p, div, label, span { color: #E0E0E0; }

        /* Estilo do Botão SAIR (Gradiente Roxo/Rosa) */
        div[data-testid="stButton"] button { 
            background: linear-gradient(90deg, #A855F7 0%, #EC4899 100%) !important; 
            color: white !important; 
            border: none; border-radius: 12px; font-weight: 700; font-size: 16px;
            padding: 0.8rem;
            transition: transform 0.2s;
        }
        div[data-testid="stButton"] button:hover {
            transform: scale(1.02);
            box-shadow: 0 0 15px rgba(236, 72, 153, 0.5);
        }

        /* Cards e Inputs (Estilo Matte) */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #1C1C1C;
            border: none; border-radius: 20px; padding: 25px;
        }
        div[data-testid="stForm"] input, div[data-testid="stTextInput"] input, div[data-testid="stNumberInput"] input, div[data-testid="stSelectbox"] > div > div { 
            background-color: #262626 !important; border: 1px solid #333 !important; color: #FFFFFF !important; border-radius: 12px !important;
        }
        .big-font { font-size: 32px !important; font-weight: 800 !important; color: #FFFFFF !important; margin-top: 20px; margin-bottom: 30px; }
    </style>
    """, unsafe_allow_html=True)

apply_custom_style()

def get_data(endpoint):
    try:
        endpoint = endpoint.strip("/")
        resp = requests.get(f"{API_URL}/{endpoint}/")
        if resp.status_code == 200: return resp.json()
        return [] 
    except: return [] 

def header(titulo): st.markdown(f"<div class='big-font'>{titulo}</div>", unsafe_allow_html=True)

def tela_login():
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown(f"<div style='display:flex; flex-direction:column; align-items:center; gap: 15px; margin-bottom: 30px;'>{render_logo_svg(width='70px', color='#E879F9')}<h2 style='margin:0; color:white !important;'>Decant ERP</h2></div>", unsafe_allow_html=True)
            with st.form("login_form"):
                u_input = st.text_input("Usuário", placeholder="admin")
                p_input = st.text_input("Senha", type="password", placeholder="••••••")
                st.markdown("<br>", unsafe_allow_html=True)
                submit = st.form_submit_button("ENTRAR")
                if submit:
                    sucesso = False; mensagem_erro = ""
                    with st.spinner("Autenticando..."):
                        for tentativa in range(1, 4):
                            try:
                                res = requests.post(f"{API_URL}/auth/login/", json={"username": u_input, "senha": p_input, "cargo": ""}, timeout=10)
                                if res.status_code == 200: sucesso = True; break
                                else: mensagem_erro = "Acesso Negado."; break
                            except:
                                if tentativa < 3: time.sleep(3)
                                else: mensagem_erro = "Sem conexão."
                    if sucesso:
                        data = res.json(); st.session_state['logado'] = True; st.session_state['usuario'] = data['usuario']; st.session_state['cargo'] = data['cargo']; st.rerun()
                    else: st.error(mensagem_erro)

def sistema_erp():
    with st.sidebar:
        # Logo maior e mais espaçado
        st.markdown(f"<div style='display:flex; align-items:center; gap:12px; margin-bottom:40px; padding-left:10px; padding-top:20px;'>{render_logo_svg(width='32px', color='#E879F9')}<div style='font-family:Inter; font-weight:800; font-size:24px; color:white;'>Decant</div></div>", unsafe_allow_html=True)
        
        menu = [{"l": "Dashboard", "i": "grid-fill", "id": "dash"}, {"l": "PDV (Caixa)", "i": "cart-fill", "id": "pdv"}, {"l": "Produtos", "i": "box-seam-fill", "id": "prod"}, {"l": "Clientes", "i": "people-fill", "id": "cli"}, {"l": "Financeiro", "i": "wallet-fill", "id": "fin"}, {"l": "Relatórios", "i": "bar-chart-fill", "id": "rel"}, {"l": "CRM", "i": "heart-fill", "id": "crm"}, {"l": "Produção", "i": "gear-wide-connected", "id": "fab"}, {"l": "Compras", "i": "bag-fill", "id": "comp"}, {"l": "Engenharia", "i": "tools", "id": "eng"}, {"l": "Planejamento", "i": "diagram-3", "id": "mrp"}, {"l": "Fornecedores", "i": "truck", "id": "forn"}, {"l": "Vendas Adm", "i": "graph-up", "id": "vend"}, {"l": "Config", "i": "sliders", "id": "cfg"}]
        
        # --- AQUI ESTÁ A CORREÇÃO DA SIDEBAR ---
        sel = option_menu(
            menu_title=None,
            options=[x["l"] for x in menu],
            icons=[x["i"] for x in menu],
            default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "transparent"},
                "icon": {"color": "#FFFFFF", "font-size": "16px"}, # Ícone Branco e Maior
                "nav-link": {
                    "font-family": "Inter",
                    "font-size": "16px", # AUMENTADO PARA 16PX
                    "text-align": "left",
                    "margin": "6px",
                    "color": "#FFFFFF", # TEXTO BRANCO PURO
                    "--hover-color": "#262626"
                },
                "nav-link-selected": {
                    "background-color": "#EC4899", # Cor de fundo sólida (fallback)
                    "background-image": "linear-gradient(90deg, #A855F7 0%, #EC4899 100%)", # GRADIENTE IGUAL AO SAIR
                    "color": "#FFFFFF",
                    "font-weight": "700",
                    "border-radius": "10px" # Bordas arredondadas na seleção
                }
            }
        )
        page_id = next(x["id"] for x in menu if x["l"] == sel)
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button("SAIR DO SISTEMA", use_container_width=True): st.session_state['logado'] = False; st.rerun()

    # --- CONTEÚDO (Mantido, mas focado na sidebar agora) ---
    if page_id == "dash": header("Visão Geral"); st.info("Conteúdo do Dashboard aqui...")
    elif page_id == "pdv": header("PDV - Caixa"); st.info("Conteúdo do PDV aqui...")
    elif page_id == "prod": header("Produtos"); st.info("Conteúdo de Produtos aqui...")
    elif page_id == "cli": header("Clientes"); st.info("Conteúdo de Clientes aqui...")
    elif page_id == "fin": header("Financeiro"); st.info("Conteúdo Financeiro aqui...")
    elif page_id == "rel": header("Relatórios"); st.info("Relatórios aqui...")
    elif page_id == "crm": header("CRM"); st.info("CRM aqui...")
    elif page_id == "fab": header("Produção"); st.info("Produção aqui...")
    elif page_id == "comp": header("Compras"); st.info("Compras aqui...")
    elif page_id == "eng": header("Engenharia"); st.info("Engenharia aqui...")
    elif page_id == "mrp": header("Planejamento"); st.info("Planejamento aqui...")
    elif page_id == "forn": header("Fornecedores"); st.info("Fornecedores aqui...")
    elif page_id == "vend": header("Vendas"); st.info("Vendas aqui...")
    elif page_id == "cfg": 
        header("Configurações")
        if st.button("RESETAR DADOS"): requests.delete(f"{API_URL}/sistema/resetar_dados/"); st.success("Resetado!")

if st.session_state['logado']: sistema_erp()
else: tela_login()