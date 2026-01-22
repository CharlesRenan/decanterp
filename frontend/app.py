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

# Inicialização de estado
if 'carrinho' not in st.session_state: st.session_state['carrinho'] = []
if 'logado' not in st.session_state: st.session_state['logado'] = False
if 'usuario' not in st.session_state: st.session_state['usuario'] = ""
if 'cargo' not in st.session_state: st.session_state['cargo'] = ""

# Logo Azul Elétrico
def render_logo_svg(width="50px", color="#2563EB"):
    return f'<svg width="{width}" height="{width}" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M30 20 V80 C30 90 40 95 50 85 L80 50 C90 40 80 20 60 20 Z" stroke="{color}" stroke-width="8" fill="none"/><path d="M30 50 L60 20" stroke="{color}" stroke-width="8" stroke-linecap="round"/><circle cx="35" cy="85" r="5" fill="{color}"/></svg>'

# --- ESTILO CSS "MODERN ELECTRIC" ---
def apply_custom_style():
    st.markdown("""
    <style>
        /* Fonte Inter */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
        
        /* Fundo Principal Preto Puro */
        .stApp { background-color: #000000; }
        
        /* Sidebar Cinza Escuro */
        div[data-testid="stSidebar"] { 
            background-color: #121212; 
            border-right: 1px solid #2A2A2A;
        }

        /* Tipografia */
        h1, h2, h3, h4, h5, h6, strong, .big-font { color: #FFFFFF !important; font-weight: 600 !important; }
        p, div, label, span, td { color: #A1A1AA; } /* Cinza claro para textos secundários */
        th { color: #FFFFFF !important; } /* Cabeçalhos de tabela brancos */
        
        .big-font { 
            font-size: 28px !important; 
            margin-top: 10px; margin-bottom: 25px;
        }

        /* --- CORREÇÃO DEFINITIVA DO MENU LATERAL --- */
        /* Estes seletores visam especificamente a estrutura interna do option_menu */
        ul.nav-pills {
            background-color: transparent !important;
        }
        ul.nav-pills li.nav-item a.nav-link {
             color: #A1A1AA !important; /* Cor do ícone/texto inativo */
             font-weight: 500 !important;
             border-radius: 8px !important;
             margin: 4px 0 !important;
        }
        /* ESTADO ATIVO: Azul Elétrico Sólido */
        ul.nav-pills li.nav-item a.nav-link.active {
            background-color: #2563EB !important;
            color: #FFFFFF !important;
            font-weight: 700 !important;
        }
        /* Hover */
        ul.nav-pills li.nav-item a.nav-link:hover:not(.active) {
            background-color: #1E1E1E !important;
            color: #FFFFFF !important;
        }
        /* ------------------------------------------- */

        /* --- CARDS KPI (Estilo Limpo da Referência) --- */
        .kpi-card {
            background-color: #1E1E1E;
            border: 1px solid #2A2A2A;
            border-radius: 12px;
            padding: 20px;
        }
        .card-title { font-size: 13px; font-weight: 600; color: #A1A1AA; text-transform: uppercase; margin-bottom: 8px; }
        .card-value { font-size: 32px; font-weight: 700; color: #FFFFFF; margin: 0; }
        .card-sub { font-size: 12px; color: #2563EB; margin-top: 8px; font-weight: 500; }

        /* Containers Gerais */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #1E1E1E;
            border: 1px solid #2A2A2A;
            border-radius: 12px; padding: 20px;
        }

        /* Inputs e Selects */
        div[data-testid="stForm"] input, div[data-testid="stTextInput"] input, div[data-testid="stNumberInput"] input, div[data-testid="stSelectbox"] > div > div, div[data-testid="stDateInput"] input { 
            background-color: #121212 !important; 
            border: 1px solid #333 !important; 
            color: #FFFFFF !important; 
            border-radius: 8px !important;
            min-height: 42px;
        }

        /* Botões Azul Elétrico */
        div[data-testid="stFormSubmitButton"] button, div[data-testid="stButton"] button[kind="primary"] { 
            background-color: #2563EB !important;
            color: white !important; 
            border: none; border-radius: 8px; font-weight: 600;
            padding: 0.6rem 1.2rem; transition: all 0.2s;
        }
        div[data-testid="stFormSubmitButton"] button:hover, div[data-testid="stButton"] button[kind="primary"]:hover {
             background-color: #1D4ED8 !important; /* Azul um pouco mais escuro no hover */
        }
        
        /* Botão Secundário */
        div[data-testid="stButton"] button[kind="secondary"] {
             background-color: transparent !important; border: 1px solid #333 !important; color: #FFFFFF !important;
        }

        /* Tabelas e Listas */
        .sales-row { display: flex; align-items: center; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid #2A2A2A; }
        .avatar-circle { width: 36px; height: 36px; border-radius: 8px; background: #2563EB; color: #FFFFFF; display: flex; align-items: center; justify-content: center; font-weight: 700; margin-right: 12px; }
        .sales-val { font-size: 15px; font-weight: 700; color: #FFFFFF; }
    </style>
    """, unsafe_allow_html=True)

apply_custom_style()

# --- FUNÇÕES AUXILIARES ---
def get_data(endpoint):
    try:
        endpoint = endpoint.strip("/")
        resp = requests.get(f"{API_URL}/{endpoint}/")
        if resp.status_code == 200: return resp.json()
        return [] 
    except: return [] 

def card_html(titulo, valor, subtexto): 
    st.markdown(f"""
    <div class='kpi-card'>
        <div class='card-title'>{titulo}</div>
        <div class='card-value'>{valor}</div>
        <div class='card-sub'>{subtexto}</div>
    </div>
    """, unsafe_allow_html=True)

def get_sales_row_html(nome, email, valor):
    iniciais = nome[:2].upper() if nome else "??"
    return f"<div class='sales-row'><div style='display:flex;align-items:center;'><div class='avatar-circle'>{iniciais}</div><div><div style='color:white; font-weight:600; font-size:14px;'>{nome}</div><div style='color:#A1A1AA; font-size:12px;'>{email}</div></div></div><div class='sales-val'>R$ {valor:,.2f}</div></div>"

def header(titulo): st.markdown(f"<div class='big-font'>{titulo}</div>", unsafe_allow_html=True)

# --- TELA DE LOGIN ---
def tela_login():
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown(f"<div style='display:flex; flex-direction:column; align-items:center; gap: 15px; margin-bottom: 30px;'>{render_logo_svg(width='60px', color='#2563EB')}<h2 style='margin:0; color:white !important; font-size:24px;'>Decant ERP</h2></div>", unsafe_allow_html=True)
            with st.form("login_form"):
                u_input = st.text_input("Usuário", placeholder="admin")
                p_input = st.text_input("Senha", type="password", placeholder="••••••")
                st.markdown("<br>", unsafe_allow_html=True)
                submit = st.form_submit_button("Acessar Sistema")
                if submit:
                    sucesso = False; mensagem_erro = ""
                    with st.spinner("Verificando credenciais..."):
                        for tentativa in range(1, 4):
                            try:
                                res = requests.post(f"{API_URL}/auth/login/", json={"username": u_input, "senha": p_input, "cargo": ""}, timeout=10)
                                if res.status_code == 200: sucesso = True; break
                                else: mensagem_erro = "Usuário ou senha incorretos."; break
                            except:
                                if tentativa < 3: time.sleep(3)
                                else: mensagem_erro = "Falha na conexão com o servidor."
                    if sucesso:
                        data = res.json(); st.session_state['logado'] = True; st.session_state['usuario'] = data['usuario']; st.session_state['cargo'] = data['cargo']; st.rerun()
                    else: st.error(mensagem_erro)

# --- SISTEMA PRINCIPAL ---
def sistema_erp():
    with st.sidebar:
        st.markdown(f"<div style='display:flex; align-items:center; gap:12px; margin-bottom:30px; padding-left:5px; padding-top:20px;'>{render_logo_svg(width='28px', color='#2563EB')}<div style='font-family:Inter; font-weight:700; font-size:20px; color:white;'>Decant</div></div>", unsafe_allow_html=True)
        
        # Menu Completo
        menu = [{"l": "Dashboard", "i": "grid-fill", "id": "dash"}, {"l": "PDV (Caixa)", "i": "cart-fill", "id": "pdv"}, {"l": "Produtos", "i": "box-seam-fill", "id": "prod"}, {"l": "Clientes", "i": "people-fill", "id": "cli"}, {"l": "Financeiro", "i": "wallet-fill", "id": "fin"}, {"l": "Relatórios", "i": "bar-chart-fill", "id": "rel"}, {"l": "CRM", "i": "heart-fill", "id": "crm"}, {"l": "Produção", "i": "gear-wide-connected", "id": "fab"}, {"l": "Compras", "i": "bag-fill", "id": "comp"}, {"l": "Engenharia", "i": "tools", "id": "eng"}, {"l": "Planejamento", "i": "diagram-3", "id": "mrp"}, {"l": "Fornecedores", "i": "truck", "id": "forn"}, {"l": "Vendas Adm", "i": "graph-up", "id": "vend"}, {"l": "Config", "i": "sliders", "id": "cfg"}]
        
        # O estilo do menu agora é controlado pelo CSS "Nuclear" acima
        sel = option_menu(None, [x["l"] for x in menu], icons=[x["i"] for x in menu], default_index=0, styles={"container": {"padding": "0!important", "background-color": "transparent"}})
        page_id = next(x["id"] for x in menu if x["l"] == sel)
        
        st.markdown("<br>", unsafe_allow_html=True)
        # Botão Sair (Estilo Secundário para não competir com o menu)
        if st.button("Sair", type="secondary", use_container_width=True): st.session_state['logado'] = False; st.rerun()

    # --- CONTEÚDO DAS PÁGINAS ---
    if page_id == "dash":
        header("Dashboard")
        d = get_data("financeiro/dashboard"); vendas = get_data("vendas"); clientes = get_data("clientes"); prods = get_data("produtos")
        
        # Cards Limpos
        c1, c2, c3, c4 = st.columns(4)
        with c1: card_html("Receita Total", f"R$ {d.get('receita', 0):,.2f}", "↗ 12% vs mês anterior")
        with c2: card_html("Despesas", f"R$ {d.get('despesas', 0):,.2f}", "↘ Dentro do orçamento")
        with c3: card_html("Lucro Líquido", f"R$ {d.get('lucro', 0):,.2f}", f"Margem: {d.get('margem', 0):.1f}%")
        with c4: card_html("Status", "Online", "Servidor Operacional")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        c_graf, c_vendas = st.columns([1.6, 1])
        with c_graf:
            with st.container(border=True): 
                st.markdown("#### Visão Financeira")
                dados = d.get('grafico', [])
                if dados:
                    df_g = pd.DataFrame(dados)
                    # Cores do gráfico ajustadas para a paleta
                    fig = px.area(df_g, x="Mês", y="Valor", color="Tipo", line_shape='spline', color_discrete_map={'Entradas': '#2563EB', 'Saídas': '#A1A1AA'})
                else:
                    fig = px.area(pd.DataFrame([{"Mês":"Jan","Valor":0,"Tipo":"Entradas"}]), x="Mês", y="Valor")
                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font={'color': '#A1A1AA', 'size': 13}, xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#2A2A2A'), margin=dict(l=0, r=0, t=0, b=0), height=320, showlegend=True, legend=dict(orientation="h", y=1.05))
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

        with c_vendas:
            with st.container(border=True):
                st.markdown("#### Transações Recentes")
                rows_html = ""
                map_clientes = {c['id']: c for c in clientes}
                for v in vendas[:5]:
                    cli = map_clientes.get(v['cliente_id'], {'nome': 'Cliente', 'email': '-'})
                    rows_html += get_sales_row_html(cli['nome'], cli['email'], v['valor_total'])
                st.markdown(f"<div style='height: 320px; overflow-y: auto;'>{rows_html}</div>", unsafe_allow_html=True)

    elif page_id == "pdv":
        header("Frente de Caixa (PDV)")
        clis = get_data("clientes"); prods = get_data("produtos"); pas = [p for p in prods if p['tipo'] == 'Produto Acabado']
        c1, c2 = st.columns([1.5, 1])
        with c1:
            with st.container(border=True):
                st.markdown("#### Lançar Item")
                lista_clientes = [c['nome'] for c in clis] if clis else []
                cli_sel = st.selectbox("Cliente", lista_clientes) if lista_clientes else None
                if not lista_clientes: st.warning("Necessário cadastrar clientes.")
                st.markdown("<br>", unsafe_allow_html=True)
                c_p, c_q, c_btn = st.columns([3, 1, 1.2])
                p = c_p.selectbox("Produto", [x['nome'] for x in pas]) if pas else None
                q = c_q.number_input("Qtd", 1.0, label_visibility="collapsed")
                if c_btn.button("ADICIONAR", type="primary", use_container_width=True): 
                    obj = next(x for x in pas if x['nome']==p); pr = obj['custo']*2; 
                    st.session_state['carrinho'].append({"id":obj['id'],"nome":obj['nome'],"qtd":q,"total":q*pr, "custo": obj['custo'], "preco_unitario": pr}); st.rerun()
        with c2:
            with st.container(border=True):
                st.markdown("#### Carrinho Atual")
                if st.session_state['carrinho']:
                    for i, item in enumerate(st.session_state['carrinho']):
                        c_n, c_qt, c_v, c_d = st.columns([3, 1.5, 1.5, 0.8])
                        c_n.write(item['nome'])
                        nq = c_qt.number_input("q", 1.0, value=float(item['qtd']), key=f"q{i}", label_visibility="collapsed")
                        if nq != item['qtd']: st.session_state['carrinho'][i]['qtd']=nq; st.session_state['carrinho'][i]['total']=nq*item['preco_unitario']; st.rerun()
                        c_v.write(f"R${item['total']:.0f}")
                        if c_d.button("X", key=f"d{i}", type="secondary"): st.session_state['carrinho'].pop(i); st.rerun()
                    st.divider()
                    tot = sum(i['total'] for i in st.session_state['carrinho'])
                    st.metric("Total a Pagar", f"R$ {tot:.2f}")
                    if st.button("FINALIZAR VENDA", type="primary", use_container_width=True): 
                        if cli_sel:
                            cid = next(x['id'] for x in clis if x['nome']==cli_sel)
                            requests.post(f"{API_URL}/vendas/pdv/", json={"cliente_id":cid,"itens":[{"produto_id":i['id'],"quantidade":i['qtd'],"valor_total":i['total']} for i in st.session_state['carrinho']],"metodo_pagamento":"Pix"})
                            st.session_state['carrinho']=[]; st.success("Venda realizada!"); time.sleep(1); st.rerun()
                        else: st.error("Selecione o cliente.")
                else: st.info("Aguardando itens...")

    elif page_id == "cli":
        header("Gerenciar Clientes"); c1, c2 = st.columns([1, 1.5])
        with c1:
            with st.container(border=True):
                st.markdown("#### Novo Cadastro")
                with st.form("new_cli"):
                    n = st.text_input("Nome Completo"); e = st.text_input("Email"); t = st.text_input("Telefone")
                    if st.form_submit_button("Salvar Cliente"): requests.post(f"{API_URL}/clientes/", json={"nome":n, "email":e, "telefone":t}); st.success("Salvo!"); st.rerun()
        with c2: st.dataframe(pd.DataFrame(get_data("clientes")), use_container_width=True)

    elif page_id == "fin":
        header("Controle Financeiro"); t1, t2 = st.tabs(["Lançamentos", "Extrato Completo"])
        with t1:
            with st.container(border=True):
                with st.form("frm_fin"):
                    desc = st.text_input("Descrição do Lançamento"); tipo = st.selectbox("Tipo", ["Despesa", "Receita"]); valor = st.number_input("Valor (R$)"); pg = st.checkbox("Já foi pago?")
                    if st.form_submit_button("Registrar"): requests.post(f"{API_URL}/financeiro/lancamento/", json={"descricao": desc, "tipo": tipo, "categoria": "Geral", "valor": valor, "data_vencimento": str(date.today()), "pago": pg}); st.success("Registrado!"); st.rerun()
        with t2: st.dataframe(pd.DataFrame(get_data("financeiro/lancamentos")), use_container_width=True)

    elif page_id == "prod": 
        header("Catálogo de Produtos"); t1, t2, t3 = st.tabs(["Todos os Produtos", "Kardex (Estoque)", "+ Cadastrar Novo"])
        with t1: st.dataframe(pd.DataFrame(get_data("produtos")), use_container_width=True)
        with t2: st.dataframe(pd.DataFrame(get_data("estoque/kardex")), use_container_width=True)
        with t3:
            with st.container(border=True):
                with st.form("np"):
                    n = st.text_input("Nome do Produto"); t = st.selectbox("Tipo", ["Materia Prima", "Produto Acabado"]); e = st.number_input("Estoque Inicial"); c = st.number_input("Custo Unitário"); loc = st.text_input("Localização no Estoque")
                    if st.form_submit_button("Salvar Produto"): requests.post(f"{API_URL}/produtos/", json={"nome":n,"tipo":t,"unidade":"Un","estoque_atual":e,"custo":c, "localizacao": loc}); st.success("Salvo!"); st.rerun()

    # Demais abas mantidas com layout padrão
    elif page_id == "crm": header("CRM"); st.dataframe(pd.DataFrame(get_data("crm/oportunidades")), use_container_width=True)
    elif page_id == "forn": header("Fornecedores"); st.dataframe(pd.DataFrame(get_data("fornecedores")), use_container_width=True)
    elif page_id == "eng": header("Engenharia (Fórmulas)"); st.dataframe(pd.DataFrame(get_data("formulas")), use_container_width=True)
    elif page_id == "mrp": header("Planejamento (MRP)"); st.info("Módulo de Planejamento de Necessidades.")
    elif page_id == "comp": header("Compras"); st.dataframe(pd.DataFrame(get_data("compras")), use_container_width=True)
    elif page_id == "prec": header("Precificação"); st.dataframe(pd.DataFrame(get_data("cotacoes")), use_container_width=True)
    elif page_id == "vend": header("Histórico de Vendas"); st.dataframe(pd.DataFrame(get_data("vendas")), use_container_width=True)
    elif page_id == "fab": header("Chão de Fábrica"); st.dataframe(pd.DataFrame(get_data("producao/historico/")), use_container_width=True)
    elif page_id == "rel": header("Relatórios Gerenciais"); st.info("Central de Relatórios e PDFs.")
    elif page_id == "cfg": 
        header("Configurações do Sistema"); 
        with st.container(border=True):
            st.warning("Zona de Perigo")
            if st.button("RESETAR BASE DE DADOS", type="primary"):
                requests.delete(f"{API_URL}/sistema/resetar_dados/"); st.success("Sistema resetado com sucesso!"); time.sleep(2); st.rerun()

# Lógica Principal
if st.session_state['logado']: sistema_erp()
else: tela_login()