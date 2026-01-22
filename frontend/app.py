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

# Logo com a nova cor de acento (Índigo)
def render_logo_svg(width="50px", color="#8B5CF6"):
    return f'<svg width="{width}" height="{width}" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M30 20 V80 C30 90 40 95 50 85 L80 50 C90 40 80 20 60 20 Z" stroke="{color}" stroke-width="8" fill="none"/><path d="M30 50 L60 20" stroke="{color}" stroke-width="8" stroke-linecap="round"/><circle cx="35" cy="85" r="5" fill="{color}"/></svg>'

# --- ESTILO MODERN DARK ---
def apply_custom_style():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
        
        /* 1. FUNDO GERAL (DARK PROFUNDO) */
        .stApp { background-color: #09090B; }
        
        /* 2. SIDEBAR (CINZA CARVÃO) */
        div[data-testid="stSidebar"] { 
            background-color: #18181B;
            border-right: 1px solid #27272A;
        }
        
        /* Tipografia Clara */
        h1, h2, h3, h4, h5, h6, strong { color: #FFFFFF !important; }
        p, div, label, span, td { color: #A1A1AA; } /* Cinza médio para textos secundários */
        
        .big-font { 
            font-size: 28px !important; 
            font-weight: 700 !important; 
            color: #FFFFFF !important; 
            margin-top: 10px; margin-bottom: 25px;
        }

        /* 3. MENU LATERAL (CORREÇÃO E ESTILO DARK) */
        .nav-link {
            color: #A1A1AA !important;
            font-size: 14px !important;
            margin: 5px !important;
            border-radius: 10px !important;
            transition: all 0.2s;
        }
        .nav-link:hover { background-color: #27272A !important; color: #FFFFFF !important; }
        
        /* SELECIONADO: Gradiente Índigo/Roxo */
        .nav-link-selected {
            background-color: #6366F1 !important; /* Fallback */
            background-image: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%) !important;
            color: #FFFFFF !important;
            font-weight: 600 !important;
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3) !important;
        }
        .icon { font-size: 16px !important; }

        /* 4. CARDS E CONTAINERS (MODERN DARK) */
        div[data-testid="stVerticalBlockBorderWrapper"], .kpi-card {
            background-color: #18181B;
            border: 1px solid #27272A;
            border-radius: 16px;
            padding: 25px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2); /* Sombra escura para profundidade */
        }

        /* KPI Cards Styling */
        .kpi-card { position: relative; overflow: hidden; }
        .kpi-value { font-size: 30px; font-weight: 700; color: #FFFFFF; margin: 5px 0; }
        .kpi-title { font-size: 13px; font-weight: 600; color: #71717A; text-transform: uppercase; letter-spacing: 0.5px; }
        
        /* Ícone no canto */
        .kpi-icon-bg {
            position: absolute; top: 20px; right: 20px;
            color: #8B5CF6; /* Cor de destaque */
            font-size: 24px;
            opacity: 0.8;
        }

        /* INPUTS (DARK MODE) */
        div[data-testid="stForm"] input, div[data-testid="stTextInput"] input, div[data-testid="stNumberInput"] input, div[data-testid="stSelectbox"] > div > div, div[data-testid="stDateInput"] input { 
            background-color: #27272A !important; 
            border: 1px solid #3F3F46 !important; 
            color: #FFFFFF !important; 
            border-radius: 10px !important;
            min-height: 45px;
        }

        /* BOTÕES (Gradiente Índigo) */
        div[data-testid="stFormSubmitButton"] button, div[data-testid="stButton"] button[kind="primary"] { 
            background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%) !important; 
            color: white !important; 
            border: none; border-radius: 10px; font-weight: 600;
            padding: 0.6rem 1.2rem;
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.2);
            transition: all 0.2s;
        }
        div[data-testid="stFormSubmitButton"] button:hover, div[data-testid="stButton"] button[kind="primary"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 15px rgba(99, 102, 241, 0.3);
        }
        
        /* Botão Secundário (Outline) */
        div[data-testid="stButton"] button[kind="secondary"] {
            background-color: transparent !important;
            color: #8B5CF6 !important;
            border: 1px solid #8B5CF6 !important;
        }
        div[data-testid="stHorizontalBlock"] button[kind="secondary"] { /* Lixeira */
             background-color: transparent !important; border: 1px solid #EF4444 !important; color: #EF4444 !important;
        }

        /* Tabelas */
        .sales-row { display: flex; align-items: center; justify-content: space-between; padding: 15px 0; border-bottom: 1px solid #27272A; }
        .avatar-circle { width: 40px; height: 40px; border-radius: 12px; background: #27272A; color: #8B5CF6; display: flex; align-items: center; justify-content: center; font-weight: 700; margin-right: 15px; border: 1px solid #3F3F46;}
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

# Card KPI Modern Dark
def card_html(titulo, valor, icon): 
    st.markdown(f"""
    <div class='kpi-card'>
        <div class='kpi-title'>{titulo}</div>
        <div class='kpi-value'>{valor}</div>
        <div class='kpi-icon-bg'>{icon}</div>
    </div>
    """, unsafe_allow_html=True)

def get_sales_row_html(nome, email, valor):
    iniciais = nome[:2].upper() if nome else "??"
    return f"<div class='sales-row'><div style='display:flex;align-items:center;'><div class='avatar-circle'>{iniciais}</div><div><div style='color:#FFFFFF; font-weight:600; font-size:14px;'>{nome}</div><div style='color:#A1A1AA; font-size:12px;'>{email}</div></div></div><div style='font-weight:700; color:#8B5CF6;'>R$ {valor:,.2f}</div></div>"

def header(titulo): st.markdown(f"<div class='big-font'>{titulo}</div>", unsafe_allow_html=True)

# --- LOGIN (DARK) ---
def tela_login():
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown(f"<div style='display:flex; flex-direction:column; align-items:center; gap: 15px; margin-bottom: 30px;'>{render_logo_svg(width='60px', color='#8B5CF6')}<h2 style='margin:0; color:#FFFFFF !important;'>Decant ERP</h2><p>Acesso Seguro</p></div>", unsafe_allow_html=True)
            with st.form("login_form"):
                u_input = st.text_input("Usuário", placeholder="admin")
                p_input = st.text_input("Senha", type="password", placeholder="••••••")
                st.markdown("<br>", unsafe_allow_html=True)
                submit = st.form_submit_button("Entrar no Sistema", type="primary")
                if submit:
                    sucesso = False; mensagem_erro = ""
                    with st.spinner("Autenticando..."):
                        for tentativa in range(1, 4):
                            try:
                                res = requests.post(f"{API_URL}/auth/login/", json={"username": u_input, "senha": p_input, "cargo": ""}, timeout=10)
                                if res.status_code == 200: sucesso = True; break
                                else: mensagem_erro = "Credenciais inválidas."; break
                            except:
                                if tentativa < 3: time.sleep(3)
                                else: mensagem_erro = "Servidor indisponível."
                    if sucesso:
                        data = res.json(); st.session_state['logado'] = True; st.session_state['usuario'] = data['usuario']; st.session_state['cargo'] = data['cargo']; st.rerun()
                    else: st.error(mensagem_erro)

# --- SISTEMA PRINCIPAL ---
def sistema_erp():
    with st.sidebar:
        st.markdown(f"<div style='display:flex; align-items:center; gap:12px; margin-bottom:30px; padding-left:10px; padding-top:20px;'>{render_logo_svg(width='28px', color='#8B5CF6')}<div style='font-family:Inter; font-weight:700; font-size:22px; color:white;'>Decant</div></div>", unsafe_allow_html=True)
        
        menu = [{"l": "Dashboard", "i": "grid-fill", "id": "dash"}, {"l": "PDV (Caixa)", "i": "cart-fill", "id": "pdv"}, {"l": "Produtos", "i": "box-seam-fill", "id": "prod"}, {"l": "Clientes", "i": "people-fill", "id": "cli"}, {"l": "Financeiro", "i": "wallet-fill", "id": "fin"}, {"l": "Relatórios", "i": "bar-chart-fill", "id": "rel"}, {"l": "CRM", "i": "heart-fill", "id": "crm"}, {"l": "Produção", "i": "gear-wide-connected", "id": "fab"}, {"l": "Compras", "i": "bag-fill", "id": "comp"}, {"l": "Engenharia", "i": "tools", "id": "eng"}, {"l": "Planejamento", "i": "diagram-3", "id": "mrp"}, {"l": "Fornecedores", "i": "truck", "id": "forn"}, {"l": "Vendas Adm", "i": "graph-up", "id": "vend"}, {"l": "Config", "i": "sliders", "id": "cfg"}]
        
        # CSS controla o visual agora
        sel = option_menu(None, [x["l"] for x in menu], icons=[x["i"] for x in menu], default_index=0, styles={"container": {"padding": "0!important", "background-color": "transparent"}})
        page_id = next(x["id"] for x in menu if x["l"] == sel)
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Sair", type="secondary", use_container_width=True): st.session_state['logado'] = False; st.rerun()

    # --- DASHBOARD MODERN DARK ---
    if page_id == "dash":
        header("Visão Geral")
        d = get_data("financeiro/dashboard"); vendas = get_data("vendas"); clientes = get_data("clientes"); prods = get_data("produtos")
        
        c1, c2, c3, c4 = st.columns(4)
        # Ícones modernos (Material Symbols ou Emojis)
        with c1: card_html("Receita Total", f"R$ {d.get('receita', 0):,.2f}", "Payments")
        with c2: card_html("Despesas", f"R$ {d.get('despesas', 0):,.2f}", "Trending_Down")
        with c3: card_html("Lucro Líquido", f"R$ {d.get('lucro', 0):,.2f}", "Monetization_On")
        with c4: card_html("Status Sistema", "Ativo", "Dns")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        c_graf, c_vendas = st.columns([1.6, 1])
        with c_graf:
            with st.container(border=True): 
                st.markdown("#### Fluxo de Caixa")
                dados = d.get('grafico', [])
                if dados:
                    df_g = pd.DataFrame(dados)
                    # Gráfico com cores de destaque
                    fig = px.area(df_g, x="Mês", y="Valor", color="Tipo", line_shape='spline', color_discrete_map={'Entradas': '#8B5CF6', 'Saídas': '#A1A1AA'})
                    fig.update_traces(fillopacity=0.3)
                else:
                    fig = px.area(pd.DataFrame([{"Mês":"Jan","Valor":0,"Tipo":"Entradas"}]), x="Mês", y="Valor")
                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font={'color': '#A1A1AA', 'size': 12}, xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#27272A'), margin=dict(l=0, r=0, t=0, b=0), height=320, showlegend=True, legend=dict(orientation="h", y=1.05))
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

        with c_vendas:
            with st.container(border=True):
                st.markdown("#### Vendas Recentes")
                rows_html = ""
                map_clientes = {c['id']: c for c in clientes}
                for v in vendas[:5]:
                    cli = map_clientes.get(v['cliente_id'], {'nome': 'Cliente', 'email': '-'})
                    rows_html += get_sales_row_html(cli['nome'], cli['email'], v['valor_total'])
                st.markdown(f"<div style='height: 320px; overflow-y: auto;'>{rows_html}</div>", unsafe_allow_html=True)

    elif page_id == "pdv":
        header("PDV - Frente de Caixa")
        clis = get_data("clientes"); prods = get_data("produtos"); pas = [p for p in prods if p['tipo'] == 'Produto Acabado']
        c1, c2 = st.columns([1.5, 1])
        with c1:
            with st.container(border=True):
                st.markdown("#### Seleção de Produtos")
                lista_clientes = [c['nome'] for c in clis] if clis else []
                cli_sel = st.selectbox("Cliente", lista_clientes) if lista_clientes else None
                if not lista_clientes: st.warning("Cadastre clientes primeiro.")
                st.markdown("<br>", unsafe_allow_html=True)
                c_p, c_q, c_btn = st.columns([3, 1, 1.2])
                p = c_p.selectbox("Produto", [x['nome'] for x in pas]) if pas else None
                q = c_q.number_input("Qtd", 1.0, label_visibility="collapsed")
                if c_btn.button("Adicionar Item", type="primary", use_container_width=True): 
                    obj = next(x for x in pas if x['nome']==p); pr = obj['custo']*2; 
                    st.session_state['carrinho'].append({"id":obj['id'],"nome":obj['nome'],"qtd":q,"total":q*pr, "custo": obj['custo'], "preco_unitario": pr}); st.rerun()
        with c2:
            with st.container(border=True):
                st.markdown("#### Carrinho")
                if st.session_state['carrinho']:
                    for i, item in enumerate(st.session_state['carrinho']):
                        c_n, c_qt, c_v, c_d = st.columns([3, 1.5, 1.5, 0.8])
                        c_n.write(f"**{item['nome']}**")
                        nq = c_qt.number_input("q", 1.0, value=float(item['qtd']), key=f"q{i}", label_visibility="collapsed")
                        if nq != item['qtd']: st.session_state['carrinho'][i]['qtd']=nq; st.session_state['carrinho'][i]['total']=nq*item['preco_unitario']; st.rerun()
                        c_v.write(f"R${item['total']:.0f}")
                        if c_d.button("Remover", key=f"d{i}", type="secondary"): st.session_state['carrinho'].pop(i); st.rerun()
                    st.divider()
                    tot = sum(i['total'] for i in st.session_state['carrinho'])
                    st.metric("Total a Pagar", f"R$ {tot:.2f}")
                    if st.button("FINALIZAR VENDA", type="primary", use_container_width=True): 
                        if cli_sel:
                            cid = next(x['id'] for x in clis if x['nome']==cli_sel)
                            requests.post(f"{API_URL}/vendas/pdv/", json={"cliente_id":cid,"itens":[{"produto_id":i['id'],"quantidade":i['qtd'],"valor_total":i['total']} for i in st.session_state['carrinho']],"metodo_pagamento":"Pix"})
                            st.session_state['carrinho']=[]; st.success("Venda realizada com sucesso!"); time.sleep(1); st.rerun()
                        else: st.error("Selecione um cliente.")
                else: st.info("Seu carrinho está vazio.")

    # --- DEMAIS ABAS (MANTIDAS NO NOVO VISUAL) ---
    elif page_id == "cli":
        header("Gerenciar Clientes"); c1, c2 = st.columns([1, 1.5])
        with c1:
            with st.container(border=True):
                st.markdown("#### Novo Cliente")
                with st.form("new_cli"):
                    n = st.text_input("Nome Completo"); e = st.text_input("Email"); t = st.text_input("Telefone")
                    if st.form_submit_button("Salvar Cadastro", type="primary"): requests.post(f"{API_URL}/clientes/", json={"nome":n, "email":e, "telefone":t}); st.success("Salvo!"); st.rerun()
        with c2: st.dataframe(pd.DataFrame(get_data("clientes")), use_container_width=True)

    elif page_id == "fin":
        header("Controle Financeiro"); t1, t2 = st.tabs(["Novo Lançamento", "Extrato Completo"])
        with t1:
            with st.container(border=True):
                with st.form("frm_fin"):
                    desc = st.text_input("Descrição"); tipo = st.selectbox("Tipo", ["Despesa", "Receita"]); valor = st.number_input("Valor (R$)"); pg = st.checkbox("Pago?")
                    if st.form_submit_button("Registrar Lançamento", type="primary"): requests.post(f"{API_URL}/financeiro/lancamento/", json={"descricao": desc, "tipo": tipo, "categoria": "Geral", "valor": valor, "data_vencimento": str(date.today()), "pago": pg}); st.success("OK!"); st.rerun()
        with t2: st.dataframe(pd.DataFrame(get_data("financeiro/lancamentos")), use_container_width=True)

    elif page_id == "prod": 
        header("Catálogo de Produtos"); t1, t2, t3 = st.tabs(["Todos os Produtos", "Kardex (Estoque)", "+ Novo Produto"])
        with t1: st.dataframe(pd.DataFrame(get_data("produtos")), use_container_width=True)
        with t2: st.dataframe(pd.DataFrame(get_data("estoque/kardex")), use_container_width=True)
        with t3:
            with st.container(border=True):
                with st.form("np"):
                    n = st.text_input("Nome"); t = st.selectbox("Tipo", ["Materia Prima", "Produto Acabado"]); e = st.number_input("Estoque Inicial"); c = st.number_input("Custo Unitário"); loc = st.text_input("Localização")
                    if st.form_submit_button("Salvar Produto", type="primary"): requests.post(f"{API_URL}/produtos/", json={"nome":n,"tipo":t,"unidade":"Un","estoque_atual":e,"custo":c, "localizacao": loc}); st.success("OK"); st.rerun()

    elif page_id == "crm": header("CRM"); ops = get_data("crm/oportunidades"); st.dataframe(pd.DataFrame(ops)) if ops else st.info("Sem alertas de CRM.")
    elif page_id == "forn": header("Fornecedores"); st.dataframe(pd.DataFrame(get_data("fornecedores")), use_container_width=True)
    elif page_id == "eng": header("Engenharia"); st.dataframe(pd.DataFrame(get_data("formulas")), use_container_width=True)
    elif page_id == "mrp": header("Planejamento"); st.info("Módulo MRP.")
    elif page_id == "comp": header("Compras"); st.dataframe(pd.DataFrame(get_data("compras")), use_container_width=True)
    elif page_id == "prec": header("Preços"); st.dataframe(pd.DataFrame(get_data("cotacoes")), use_container_width=True)
    elif page_id == "vend": header("Vendas (Adm)"); st.dataframe(pd.DataFrame(get_data("vendas")), use_container_width=True)
    elif page_id == "fab": header("Produção"); st.dataframe(pd.DataFrame(get_data("producao/historico/")), use_container_width=True)
    elif page_id == "rel": header("Relatórios"); st.info("Central de Relatórios.")
    elif page_id == "cfg": 
        header("Configurações"); 
        with st.container(border=True):
            st.warning("Zona de Perigo")
            if st.button("RESETAR SISTEMA COMPLETO", type="primary"):
                requests.delete(f"{API_URL}/sistema/resetar_dados/"); st.success("Sistema resetado!"); time.sleep(2); st.rerun()

if st.session_state['logado']: sistema_erp()
else: tela_login()