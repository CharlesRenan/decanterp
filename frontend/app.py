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
# API_URL = "http://127.0.0.1:8000"
API_URL = "https://api-decant-oficial.onrender.com"

st.set_page_config(page_title="Decant ERP", page_icon="💧", layout="wide")

if 'carrinho' not in st.session_state: st.session_state['carrinho'] = []
if 'logado' not in st.session_state: st.session_state['logado'] = False
if 'usuario' not in st.session_state: st.session_state['usuario'] = ""
if 'cargo' not in st.session_state: st.session_state['cargo'] = ""

def render_logo_svg(width="50px", color="#3B82F6"):
    return f'<svg width="{width}" height="{width}" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M30 20 V80 C30 90 40 95 50 85 L80 50 C90 40 80 20 60 20 Z" stroke="{color}" stroke-width="8" fill="none"/><path d="M30 50 L60 20" stroke="{color}" stroke-width="8" stroke-linecap="round"/><circle cx="35" cy="85" r="5" fill="{color}"/></svg>'

def apply_custom_style():
    st.markdown("""
    <style>
        /* Importando Fonte similar à Lufga (Outfit) */
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
        
        html, body, [class*="css"] { font-family: 'Outfit', sans-serif !important; }
        
        /* Fundo Geral Deep Dark */
        .stApp { background-color: #050505; }
        
        /* Títulos e Textos */
        .big-font { font-size: 32px !important; font-weight: 700 !important; color: #FFFFFF !important; margin-top: 20px !important; margin-bottom: 20px !important; letter-spacing: -0.5px; }
        h1, h2, h3, h4, h5, h6 { color: white !important; font-weight: 600 !important; }
        p, div, label { color: #A1A1AA !important; }
        
        /* --- CARDS NEON STYLE --- */
        /* Container Genérico com Borda Brilhante */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #101012; /* Fundo do Card */
            border: 1px solid rgba(255, 255, 255, 0.08); /* Borda sutil */
            border-radius: 16px; /* Borda bem arredondada */
            padding: 24px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.5); /* Sombra profunda */
            transition: all 0.3s ease;
        }
        
        /* Efeito Hover nos Cards (Opcional, dá vida) */
        div[data-testid="stVerticalBlockBorderWrapper"]:hover {
            border-color: rgba(59, 130, 246, 0.3); /* Brilho azul ao passar o mouse */
            box-shadow: 0 0 15px rgba(59, 130, 246, 0.1);
        }

        /* --- CARDS DO TOPO (KPIs) --- */
        .card-container {
            background: linear-gradient(145deg, #121214 0%, #0A0A0C 100%);
            border-radius: 16px;
            padding: 20px;
            border: 1px solid rgba(255,255,255,0.05);
            position: relative;
            overflow: hidden;
        }
        
        /* Efeito de "Luz" nos Cards de KPI */
        .card-container::before {
            content: "";
            position: absolute;
            top: 0; left: 0; width: 100%; height: 2px;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
        }

        .card-blue { border-bottom: 2px solid #3B82F6; }
        .card-red { border-bottom: 2px solid #EF4444; }
        .card-green { border-bottom: 2px solid #10B981; }
        .card-dark { border-bottom: 2px solid #F59E0B; }

        .card-title { font-size: 12px; font-weight: 500; color: #71717A; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; }
        .card-value { font-size: 28px; font-weight: 700; color: #FFFFFF; margin-top: 0px; letter-spacing: -1px; }
        
        /* --- SIDEBAR --- */
        div[data-testid="stSidebar"] { 
            background-color: #050505; 
            border-right: 1px solid #1F1F22; 
        }
        
        /* Botões e Inputs */
        div[data-testid="stForm"] input, div[data-testid="stTextInput"] input, div[data-testid="stNumberInput"] input, div[data-testid="stSelectbox"] > div > div { 
            background-color: #18181B !important; 
            border: 1px solid #27272A !important; 
            color: white !important; 
            border-radius: 8px !important;
        }
        
        div[data-testid="stFormSubmitButton"] button, div[data-testid="stButton"] button { 
            background: linear-gradient(90deg, #2563EB 0%, #1D4ED8 100%) !important; 
            color: white !important; 
            border: none; 
            border-radius: 8px;
            font-weight: 600;
            padding: 0.5rem 1rem;
            transition: all 0.3s;
        }
        
        div[data-testid="stFormSubmitButton"] button:hover, div[data-testid="stButton"] button:hover {
            box-shadow: 0 0 12px rgba(37, 99, 235, 0.6); /* Brilho Neon no botão */
        }

        /* Tabelas e Listas */
        .sales-row { display: flex; align-items: center; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid #27272A; }
        .sales-left { display: flex; align-items: center; gap: 12px; }
        .avatar-circle { width: 36px; height: 36px; border-radius: 50%; background: linear-gradient(135deg, #3B82F6, #2563EB); color: #FFF; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; }
        .client-name { color: #E4E4E7 !important; font-weight: 500; font-size: 14px; }
        .client-sub { font-size: 11px; color: #71717A !important; }
        .sales-val { color: #fff !important; font-weight: 600; }
        
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

def card_html(titulo, valor, subtexto, cor="card-dark"): 
    st.markdown(f"<div class='card-container {cor}'><div class='card-title'>{titulo}</div><div class='card-value'>{valor}</div><div style='font-size:11px; margin-top:8px; color: #52525B'>{subtexto}</div></div>", unsafe_allow_html=True)

def get_sales_row_html(nome, email, valor):
    iniciais = nome[:2].upper() if nome else "??"
    return f"<div class='sales-row'><div class='sales-left'><div class='avatar-circle'>{iniciais}</div><div class='client-info'><div class='client-name'>{nome}</div><div class='client-sub'>{email}</div></div></div><div class='sales-right'><div class='sales-val'>R$ {valor:,.2f}</div></div></div>"

def header(titulo): st.markdown(f"<div class='big-font'>{titulo}</div>", unsafe_allow_html=True)

# --- TELA DE LOGIN ESTILIZADA ---
def tela_login():
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        # Renderiza SVG do logo centralizado
        st.markdown(f"<div style='display:flex; flex-direction:column; align-items:center; gap: 10px;'>{render_logo_svg(width='60px', color='#3B82F6')}<h1 style='font-family:Outfit; font-size:24px; color:white; margin:0;'>Decant ERP</h1><p style='color:#52525B; font-size:12px;'>Faça login para continuar</p></div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            u_input = st.text_input("Usuário", placeholder="admin")
            p_input = st.text_input("Senha", type="password", placeholder="••••••")
            st.markdown("<br>", unsafe_allow_html=True)
            submit = st.form_submit_button("ACESSAR SISTEMA", use_container_width=True)
            
            if submit:
                sucesso = False; mensagem_erro = ""
                with st.spinner("Autenticando..."):
                    for tentativa in range(1, 4):
                        try:
                            res = requests.post(f"{API_URL}/auth/login/", json={"username": u_input, "senha": p_input, "cargo": ""}, timeout=10)
                            if res.status_code == 200: sucesso = True; break
                            else: mensagem_erro = "Dados incorretos."; break
                        except:
                            if tentativa < 3: time.sleep(3)
                            else: mensagem_erro = "Sem conexão."
                if sucesso:
                    data = res.json(); st.session_state['logado'] = True; st.session_state['usuario'] = data['usuario']; st.session_state['cargo'] = data['cargo']; st.rerun()
                else: st.error(mensagem_erro)

# --- SISTEMA PRINCIPAL ---
def sistema_erp():
    with st.sidebar:
        st.markdown(f"<div style='display:flex; align-items:center; gap:12px; margin-bottom:30px; padding-left:10px; padding-top:20px;'>{render_logo_svg(width='28px', color='#3B82F6')}<div style='font-family:Outfit; font-weight:700; font-size:20px; color:white;'>Decant</div></div>", unsafe_allow_html=True)
        
        # Menu com estilo "Clean"
        menu = [{"l": "Dashboard", "i": "grid-fill", "id": "dash"}, {"l": "PDV", "i": "cart-fill", "id": "pdv"}, {"l": "Produtos", "i": "box-seam-fill", "id": "prod"}, {"l": "Clientes", "i": "people-fill", "id": "cli"}, {"l": "Financeiro", "i": "wallet-fill", "id": "fin"}, {"l": "Produção", "i": "gear-wide-connected", "id": "fab"}, {"l": "Relatórios", "i": "bar-chart-fill", "id": "rel"}, {"l": "Config", "i": "sliders", "id": "cfg"}]
        
        sel = option_menu(None, [x["l"] for x in menu], icons=[x["i"] for x in menu], default_index=0, 
            styles={
                "container": {"padding": "0!important", "background-color": "transparent"},
                "icon": {"color": "#71717A", "font-size": "14px"}, 
                "nav-link": {"font-family":"Outfit", "font-weight":"500", "font-size": "13px", "text-align": "left", "margin":"5px", "--hover-color": "#18181B", "color": "#A1A1AA"},
                "nav-link-selected": {"background-color": "#18181B", "color": "#FFFFFF", "font-weight": "600", "border-left": "2px solid #3B82F6"}
            })
        page_id = next(x["id"] for x in menu if x["l"] == sel)
        
        st.markdown("<div style='margin-top: auto; padding: 20px; color: #52525B; font-size: 10px; text-align: center;'>v3.0 Neon Build</div>", unsafe_allow_html=True)
        if st.button("Sair", use_container_width=True): st.session_state['logado'] = False; st.rerun()

    if page_id == "dash":
        header("Visão Geral")
        d = get_data("financeiro/dashboard"); vendas = get_data("vendas"); clientes = get_data("clientes"); prods = get_data("produtos")

        # KPI Cards
        c1, c2, c3, c4 = st.columns(4)
        with c1: card_html("RECEITA", f"R$ {d.get('receita', 0):,.2f}", "+12% vs mês anterior", "card-blue")
        with c2: card_html("DESPESAS", f"R$ {d.get('despesas', 0):,.2f}", "3 contas a vencer", "card-red")
        with c3: card_html("LUCRO", f"R$ {d.get('lucro', 0):,.2f}", f"Margem: {d.get('margem', 0):.1f}%", "card-green")
        with c4: card_html("STATUS", "Online", "Servidor Operacional", "card-dark")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Gráficos Linha 1
        c_graf, c_vendas, c_meta = st.columns([1.2, 1, 0.8])
        
        with c_graf:
            with st.container(border=True): 
                st.markdown("#### Fluxo Financeiro")
                dados = d.get('grafico', [])
                if dados: 
                    fig = px.area(pd.DataFrame(dados), x="Mês", y="Valor", color="Tipo", line_shape='spline', color_discrete_map={'Entradas': '#10B981', 'Saídas': '#3B82F6'})
                else: 
                    fig = px.area(pd.DataFrame([{"Mês":"Jan","Valor":0,"Tipo":"Entradas"}]), x="Mês", y="Valor")
                
                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font={'color': '#71717A', 'family': 'Outfit'}, xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#27272A'), margin=dict(l=0, r=0, t=0, b=0), height=250, showlegend=False)
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

        with c_vendas:
            with st.container(border=True):
                st.markdown("#### Transações Recentes")
                rows_html = ""
                map_clientes = {c['id']: c for c in clientes}
                for v in vendas[:4]:
                    cli = map_clientes.get(v['cliente_id'], {'nome': 'Cliente', 'email': '-'})
                    rows_html += get_sales_row_html(cli['nome'], "Venda Confirmada", v['valor_total'])
                st.markdown(f"<div style='height: 250px; overflow-y: auto;'>{rows_html}</div>", unsafe_allow_html=True)

        with c_meta:
            with st.container(border=True):
                st.markdown("#### Meta")
                receita_atual = d.get('receita', 0)
                fig_gauge = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = receita_atual,
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    gauge = {
                        'axis': {'range': [None, 10000], 'tickwidth': 1, 'tickcolor': "#333"},
                        'bar': {'color': "#3B82F6"},
                        'bgcolor': "#18181B",
                        'borderwidth': 2,
                        'bordercolor': "#333",
                        'steps': [{'range': [0, 10000], 'color': "#18181B"}],
                        'threshold': {'line': {'color': "white", 'width': 4}, 'thickness': 0.75, 'value': 10000}
                    }
                ))
                fig_gauge.update_layout(paper_bgcolor='rgba(0,0,0,0)', font={'color': "white", 'family': "Outfit"}, margin=dict(t=20,b=20,l=20,r=20), height=230)
                st.plotly_chart(fig_gauge, use_container_width=True)

        # Gráficos Linha 2
        st.markdown("<br>", unsafe_allow_html=True)
        if vendas and prods:
            df_vendas = pd.DataFrame(vendas)
            map_prods = {p['id']: p['nome'] for p in prods}
            df_vendas['Produto'] = df_vendas['produto_id'].map(map_prods)
            
            g1, g2 = st.columns([1.5, 1])
            with g1:
                with st.container(border=True):
                    st.markdown("#### Top Produtos")
                    top_prods = df_vendas.groupby('Produto')['valor_total'].sum().reset_index().sort_values('valor_total', ascending=False).head(5)
                    fig_bar = px.bar(top_prods, x='valor_total', y='Produto', orientation='h', text_auto='.2s')
                    fig_bar.update_traces(marker_color='#3B82F6', marker_line_width=0)
                    fig_bar.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font={'color': '#A1A1AA', 'family': 'Outfit'}, xaxis_title="", yaxis_title="", margin=dict(t=0, b=0), height=200)
                    st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})
            
            with g2:
                with st.container(border=True):
                    st.markdown("#### Pagamentos")
                    pg = df_vendas.groupby('metodo_pagamento')['valor_total'].sum().reset_index()
                    fig_pie = px.pie(pg, values='valor_total', names='metodo_pagamento', hole=0.7, color_discrete_sequence=['#3B82F6', '#60A5FA', '#93C5FD'])
                    fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', font={'color': '#A1A1AA', 'family': 'Outfit'}, margin=dict(t=0, b=0, l=0, r=0), height=200, showlegend=False)
                    # Texto no meio do donut
                    fig_pie.add_annotation(text="100%", x=0.5, y=0.5, font_size=20, showarrow=False, font_color="white")
                    st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})

    elif page_id == "pdv":
        header("Terminal de Vendas")
        clis = get_data("clientes"); prods = get_data("produtos"); pas = [p for p in prods if p['tipo'] == 'Produto Acabado']
        c1, c2 = st.columns([1.5, 1])
        with c1:
            with st.container(border=True):
                st.markdown("#### Seleção")
                lista_clientes = [c['nome'] for c in clis] if clis else []
                cli_sel = st.selectbox("Cliente", lista_clientes) if lista_clientes else None
                st.markdown("<br>", unsafe_allow_html=True)
                c_p, c_q, c_btn = st.columns([3, 1, 1.2])
                p = c_p.selectbox("Produto", [x['nome'] for x in pas]) if pas else None
                q = c_q.number_input("Qtd", 1.0, label_visibility="collapsed")
                if c_btn.button("ADICIONAR +", use_container_width=True): 
                    obj = next(x for x in pas if x['nome']==p); pr = obj['custo']*2; 
                    st.session_state['carrinho'].append({"id":obj['id'],"nome":obj['nome'],"qtd":q,"total":q*pr, "custo": obj['custo'], "preco_unitario": pr}); st.rerun()
        
        with c2:
            with st.container(border=True):
                st.markdown("#### Carrinho")
                if st.session_state['carrinho']:
                    for i, item in enumerate(st.session_state['carrinho']):
                        c_n, c_qt, c_v, c_d = st.columns([3, 1.5, 1.5, 0.8])
                        c_n.write(item['nome'])
                        nq = c_qt.number_input("q", 1.0, value=float(item['qtd']), key=f"q{i}", label_visibility="collapsed")
                        if nq != item['qtd']: st.session_state['carrinho'][i]['qtd']=nq; st.session_state['carrinho'][i]['total']=nq*item['preco_unitario']; st.rerun()
                        c_v.write(f"R${item['total']:.0f}")
                        if c_d.button("x", key=f"d{i}"): st.session_state['carrinho'].pop(i); st.rerun()
                    
                    st.divider()
                    tot = sum(i['total'] for i in st.session_state['carrinho'])
                    luc = tot - sum(i['custo']*i['qtd'] for i in st.session_state['carrinho'])
                    marg = (luc/tot*100) if tot>0 else 0
                    k1, k2 = st.columns(2)
                    k1.metric("Total", f"R$ {tot:.2f}")
                    k2.metric("Margem", f"{marg:.0f}%")
                    st.progress(min(int(marg), 100))
                    
                    if st.button("FINALIZAR (F5)", type="primary", use_container_width=True):
                        cid = next(x['id'] for x in clis if x['nome']==cli_sel)
                        requests.post(f"{API_URL}/vendas/pdv/", json={"cliente_id":cid,"itens":[{"produto_id":i['id'],"quantidade":i['qtd'],"valor_total":i['total']} for i in st.session_state['carrinho']],"metodo_pagamento":"Pix"})
                        st.session_state['carrinho']=[]; st.success("Venda OK!"); time.sleep(1); st.rerun()
                else: st.info("Caixa Livre")

    # MANTENDO O RESTO FUNCIONAL
    elif page_id == "prod": header("Produtos"); t1, t2, t3 = st.tabs(["Lista", "Kardex", "+ Novo"]); st.dataframe(pd.DataFrame(get_data("produtos")), use_container_width=True) if t1 else None; st.dataframe(pd.DataFrame(get_data("estoque/kardex"))) if t2 else None
    elif page_id == "cli": header("Clientes"); st.dataframe(pd.DataFrame(get_data("clientes")), use_container_width=True)
    elif page_id == "rel": header("Relatórios"); st.info("Módulo de Inteligência em construção.")
    elif page_id == "cfg": 
        header("Configurações"); 
        if st.button("Resetar Dados", type="primary"): requests.delete(f"{API_URL}/sistema/resetar_dados/"); st.success("Resetado!"); time.sleep(2); st.rerun()

if st.session_state['logado']: sistema_erp()
else: tela_login()