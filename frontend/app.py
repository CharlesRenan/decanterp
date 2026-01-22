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

# Inicialização de Variáveis de Estado
if 'carrinho' not in st.session_state: st.session_state['carrinho'] = []
if 'logado' not in st.session_state: st.session_state['logado'] = False
if 'usuario' not in st.session_state: st.session_state['usuario'] = ""
if 'cargo' not in st.session_state: st.session_state['cargo'] = ""

# Logo (Azul Vibrante para fundo escuro)
def render_logo_svg(width="50px", color="#3B82F6"):
    return f'<svg width="{width}" height="{width}" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M30 20 V80 C30 90 40 95 50 85 L80 50 C90 40 80 20 60 20 Z" stroke="{color}" stroke-width="8" fill="none"/><path d="M30 50 L60 20" stroke="{color}" stroke-width="8" stroke-linecap="round"/><circle cx="35" cy="85" r="5" fill="{color}"/></svg>'

# --- CSS PRO (Estilo "Slate Dark") ---
def apply_custom_style():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
        
        /* Fundo Geral (Slate 900) */
        .stApp { background-color: #0F172A; }
        
        /* Sidebar (Slate 950 - Um pouco mais escura) */
        div[data-testid="stSidebar"] { 
            background-color: #020617; 
            border-right: 1px solid #1E293B;
        }

        /* Títulos e Textos */
        h1, h2, h3, h4, h5, h6, strong { color: #FFFFFF !important; }
        p, div, label, span, td { color: #CBD5E1; } /* Cinza claro */
        
        /* Containers e Cards */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #1E293B; /* Slate 800 */
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }

        /* Inputs e Selects */
        div[data-testid="stForm"] input, div[data-testid="stTextInput"] input, div[data-testid="stNumberInput"] input, div[data-testid="stSelectbox"] > div > div { 
            background-color: #0F172A !important; 
            border: 1px solid #334155 !important; 
            color: #FFFFFF !important; 
            border-radius: 8px !important;
        }

        /* Botões (Azul Decant) */
        div[data-testid="stFormSubmitButton"] button, div[data-testid="stButton"] button[kind="primary"] { 
            background-color: #3B82F6 !important;
            color: white !important; 
            border: none; border-radius: 8px; font-weight: 600;
            padding: 0.5rem 1rem;
        }
        div[data-testid="stFormSubmitButton"] button:hover, div[data-testid="stButton"] button[kind="primary"]:hover {
             background-color: #2563EB !important;
        }
        
        /* Botão Secundário (Lixeira) */
        div[data-testid="stButton"] button[kind="secondary"] {
             background-color: transparent !important; 
             border: 1px solid #EF4444 !important; 
             color: #EF4444 !important;
        }

        /* Tabelas */
        .sales-row { display: flex; align-items: center; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid #334155; }
        .sales-row:last-child { border-bottom: none; }
        .avatar-circle { width: 36px; height: 36px; border-radius: 8px; background: #3B82F6; color: #FFFFFF; display: flex; align-items: center; justify-content: center; font-weight: 700; margin-right: 12px; }
        .sales-val { font-size: 14px; font-weight: 700; color: #FFFFFF; }
        
        /* Métrica Grande */
        div[data-testid="metric-container"] label { color: #94A3B8 !important; }
        div[data-testid="metric-container"] div[data-testid="stMetricValue"] { color: #FFFFFF !important; }
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

# Card KPI Padrão (Estilo Clean)
def card_html(titulo, valor, subtexto): 
    st.markdown(f"""
    <div style='text-align: center; padding: 10px;'>
        <div style='font-size: 13px; font-weight: 600; color: #94A3B8; text-transform: uppercase; margin-bottom: 5px;'>{titulo}</div>
        <div style='font-size: 28px; font-weight: 700; color: #FFFFFF;'>{valor}</div>
        <div style='font-size: 12px; color: #3B82F6; margin-top: 5px;'>{subtexto}</div>
    </div>
    """, unsafe_allow_html=True)

def get_sales_row_html(nome, email, valor):
    iniciais = nome[:2].upper() if nome else "??"
    return f"<div class='sales-row'><div style='display:flex;align-items:center;'><div class='avatar-circle'>{iniciais}</div><div><div style='color:white; font-weight:600; font-size:14px;'>{nome}</div><div style='color:#94A3B8; font-size:12px;'>{email}</div></div></div><div class='sales-val'>R$ {valor:,.2f}</div></div>"

def header(titulo): st.markdown(f"<h2 style='color:white; margin-top:10px; margin-bottom:25px;'>{titulo}</h2>", unsafe_allow_html=True)

# --- LOGIN ---
def tela_login():
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown(f"<div style='display:flex; flex-direction:column; align-items:center; gap: 15px; margin-bottom: 20px;'>{render_logo_svg(width='60px', color='#3B82F6')}<h2 style='margin:0; color:#FFFFFF !important;'>Decant ERP</h2></div>", unsafe_allow_html=True)
            with st.form("login_form"):
                u_input = st.text_input("Usuário", placeholder="admin")
                p_input = st.text_input("Senha", type="password", placeholder="••••••")
                st.markdown("<br>", unsafe_allow_html=True)
                submit = st.form_submit_button("Entrar", type="primary", use_container_width=True)
                if submit:
                    sucesso = False; mensagem_erro = ""
                    with st.spinner("Conectando..."):
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

# --- SISTEMA ---
def sistema_erp():
    with st.sidebar:
        st.markdown(f"<div style='display:flex; align-items:center; gap:12px; margin-bottom:30px; padding-left:10px; padding-top:20px;'>{render_logo_svg(width='28px', color='#3B82F6')}<div style='font-family:Inter; font-weight:700; font-size:20px; color:white;'>Decant</div></div>", unsafe_allow_html=True)
        
        menu = [{"l": "Dashboard", "i": "grid", "id": "dash"}, {"l": "PDV (Caixa)", "i": "cart", "id": "pdv"}, {"l": "Produtos", "i": "box", "id": "prod"}, {"l": "Clientes", "i": "people", "id": "cli"}, {"l": "Financeiro", "i": "wallet", "id": "fin"}, {"l": "Relatórios", "i": "bar-chart", "id": "rel"}, {"l": "CRM", "i": "heart", "id": "crm"}, {"l": "Produção", "i": "gear", "id": "fab"}, {"l": "Compras", "i": "bag", "id": "comp"}, {"l": "Engenharia", "i": "tools", "id": "eng"}, {"l": "Planejamento", "i": "diagram-3", "id": "mrp"}, {"l": "Fornecedores", "i": "truck", "id": "forn"}, {"l": "Vendas Adm", "i": "graph-up", "id": "vend"}, {"l": "Config", "i": "sliders", "id": "cfg"}]
        
        # AQUI RESOLVEMOS O VERMELHO
        sel = option_menu(
            menu_title=None,
            options=[x["l"] for x in menu],
            icons=[x["i"] for x in menu],
            default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "transparent"},
                "icon": {"color": "#94A3B8", "font-size": "14px"}, 
                "nav-link": {"font-family":"Inter", "font-size": "14px", "text-align": "left", "margin": "2px", "color": "#CBD5E1", "--hover-color": "#1E293B"},
                # FORÇA O AZUL NA SELEÇÃO
                "nav-link-selected": {"background-color": "#3B82F6", "color": "white", "font-weight": "600"}
            }
        )
        page_id = next(x["id"] for x in menu if x["l"] == sel)
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Sair", type="secondary", use_container_width=True): st.session_state['logado'] = False; st.rerun()

    # --- DASHBOARD ---
    if page_id == "dash":
        header("Visão Geral")
        d = get_data("financeiro/dashboard"); vendas = get_data("vendas"); clientes = get_data("clientes"); prods = get_data("produtos")
        
        # Cards em Container Único (Estilo Clássico)
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns(4)
            with c1: card_html("Receita", f"R$ {d.get('receita', 0):,.2f}", "+12% mês")
            with c2: card_html("Despesas", f"R$ {d.get('despesas', 0):,.2f}", "Meta OK")
            with c3: card_html("Lucro", f"R$ {d.get('lucro', 0):,.2f}", f"{d.get('margem', 0):.1f}%")
            with c4: card_html("Status", "Online", "Ativo")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        c_graf, c_vendas = st.columns([1.5, 1])
        with c_graf:
            with st.container(border=True): 
                st.markdown("#### Fluxo Financeiro")
                dados = d.get('grafico', [])
                if dados:
                    df_g = pd.DataFrame(dados)
                    fig = px.bar(df_g, x="Mês", y="Valor", color="Tipo", barmode='group', color_discrete_map={'Entradas': '#3B82F6', 'Saídas': '#64748B'})
                else:
                    fig = px.bar(pd.DataFrame([{"Mês":"Jan","Valor":0,"Tipo":"Entradas"}]), x="Mês", y="Valor")
                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font={'color': '#94A3B8'}, xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#334155'), margin=dict(l=0, r=0, t=0, b=0), height=300, showlegend=True, legend=dict(orientation="h", y=1.1))
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

        with c_vendas:
            with st.container(border=True):
                st.markdown("#### Últimas Vendas")
                rows_html = ""
                map_clientes = {c['id']: c for c in clientes}
                for v in vendas[:5]:
                    cli = map_clientes.get(v['cliente_id'], {'nome': 'Cliente', 'email': '-'})
                    rows_html += get_sales_row_html(cli['nome'], cli['email'], v['valor_total'])
                st.markdown(f"<div style='height: 300px; overflow-y: auto;'>{rows_html}</div>", unsafe_allow_html=True)

    elif page_id == "pdv":
        header("Frente de Caixa")
        clis = get_data("clientes"); prods = get_data("produtos"); pas = [p for p in prods if p['tipo'] == 'Produto Acabado']
        c1, c2 = st.columns([1.5, 1])
        with c1:
            with st.container(border=True):
                st.markdown("#### Produtos")
                lista_clientes = [c['nome'] for c in clis] if clis else []
                cli_sel = st.selectbox("Cliente", lista_clientes) if lista_clientes else None
                if not lista_clientes: st.warning("Cadastre clientes primeiro.")
                st.markdown("<br>", unsafe_allow_html=True)
                c_p, c_q, c_btn = st.columns([3, 1, 1.2])
                p = c_p.selectbox("Produto", [x['nome'] for x in pas]) if pas else None
                q = c_q.number_input("Qtd", 1.0, label_visibility="collapsed")
                if c_btn.button("Adicionar", type="primary", use_container_width=True): 
                    obj = next(x for x in pas if x['nome']==p); pr = obj['custo']*2; 
                    st.session_state['carrinho'].append({"id":obj['id'],"nome":obj['nome'],"qtd":q,"total":q*pr, "custo": obj['custo'], "preco_unitario": pr}); st.rerun()
        with c2:
            with st.container(border=True):
                st.markdown("#### Cupom")
                if st.session_state['carrinho']:
                    for i, item in enumerate(st.session_state['carrinho']):
                        c_n, c_qt, c_v, c_d = st.columns([3, 1.5, 1.5, 0.8])
                        c_n.write(f"**{item['nome']}**")
                        nq = c_qt.number_input("q", 1.0, value=float(item['qtd']), key=f"q{i}", label_visibility="collapsed")
                        if nq != item['qtd']: st.session_state['carrinho'][i]['qtd']=nq; st.session_state['carrinho'][i]['total']=nq*item['preco_unitario']; st.rerun()
                        c_v.write(f"R${item['total']:.0f}")
                        if c_d.button("X", key=f"d{i}", type="secondary"): st.session_state['carrinho'].pop(i); st.rerun()
                    st.divider()
                    tot = sum(i['total'] for i in st.session_state['carrinho'])
                    st.metric("Total", f"R$ {tot:.2f}")
                    if st.button("FINALIZAR VENDA", type="primary", use_container_width=True): 
                        if cli_sel:
                            cid = next(x['id'] for x in clis if x['nome']==cli_sel)
                            requests.post(f"{API_URL}/vendas/pdv/", json={"cliente_id":cid,"itens":[{"produto_id":i['id'],"quantidade":i['qtd'],"valor_total":i['total']} for i in st.session_state['carrinho']],"metodo_pagamento":"Pix"})
                            st.session_state['carrinho']=[]; st.success("Venda OK!"); time.sleep(1); st.rerun()
                        else: st.error("Selecione o cliente.")
                else: st.info("Carrinho vazio.")

    # --- ABAS SECUNDÁRIAS ---
    elif page_id == "cli":
        header("Clientes"); c1, c2 = st.columns([1, 1.5])
        with c1:
            with st.container(border=True):
                st.markdown("#### Novo Cadastro")
                with st.form("new_cli"):
                    n = st.text_input("Nome"); e = st.text_input("Email"); t = st.text_input("Telefone")
                    if st.form_submit_button("Salvar"): requests.post(f"{API_URL}/clientes/", json={"nome":n, "email":e, "telefone":t}); st.success("Salvo!"); st.rerun()
        with c2: st.dataframe(pd.DataFrame(get_data("clientes")), use_container_width=True)

    elif page_id == "fin":
        header("Financeiro"); t1, t2 = st.tabs(["Lançar", "Extrato"])
        with t1:
            with st.container(border=True):
                with st.form("frm_fin"):
                    desc = st.text_input("Descrição"); tipo = st.selectbox("Tipo", ["Despesa", "Receita"]); valor = st.number_input("Valor"); pg = st.checkbox("Pago?")
                    if st.form_submit_button("Registrar"): requests.post(f"{API_URL}/financeiro/lancamento/", json={"descricao": desc, "tipo": tipo, "categoria": "Geral", "valor": valor, "data_vencimento": str(date.today()), "pago": pg}); st.success("OK!"); st.rerun()
        with t2: st.dataframe(pd.DataFrame(get_data("financeiro/lancamentos")), use_container_width=True)

    elif page_id == "prod": 
        header("Produtos"); t1, t2, t3 = st.tabs(["Lista", "Kardex", "+ Novo"])
        with t1: st.dataframe(pd.DataFrame(get_data("produtos")), use_container_width=True)
        with t2: st.dataframe(pd.DataFrame(get_data("estoque/kardex")), use_container_width=True)
        with t3:
            with st.container(border=True):
                with st.form("np"):
                    n = st.text_input("Nome"); t = st.selectbox("Tipo", ["Materia Prima", "Produto Acabado"]); e = st.number_input("Estoque"); c = st.number_input("Custo"); loc = st.text_input("Localização")
                    if st.form_submit_button("Salvar"): requests.post(f"{API_URL}/produtos/", json={"nome":n,"tipo":t,"unidade":"Un","estoque_atual":e,"custo":c, "localizacao": loc}); st.success("OK"); st.rerun()

    elif page_id == "crm": header("CRM"); ops = get_data("crm/oportunidades"); st.dataframe(pd.DataFrame(ops)) if ops else st.info("Sem alertas.")
    elif page_id == "forn": header("Fornecedores"); st.dataframe(pd.DataFrame(get_data("fornecedores")), use_container_width=True)
    elif page_id == "eng": header("Engenharia"); st.dataframe(pd.DataFrame(get_data("formulas")), use_container_width=True)
    elif page_id == "mrp": header("Planejamento"); st.info("Use o módulo de MRP.")
    elif page_id == "comp": header("Compras"); st.dataframe(pd.DataFrame(get_data("compras")), use_container_width=True)
    elif page_id == "prec": header("Preços"); st.dataframe(pd.DataFrame(get_data("cotacoes")), use_container_width=True)
    elif page_id == "vend": header("Vendas (Adm)"); st.dataframe(pd.DataFrame(get_data("vendas")), use_container_width=True)
    elif page_id == "fab": header("Produção"); st.dataframe(pd.DataFrame(get_data("producao/historico/")), use_container_width=True)
    elif page_id == "rel": 
        header("Relatórios")
        c1, c2 = st.columns(2)
        ini = c1.date_input("Início", value=date.today().replace(day=1)); fim = c2.date_input("Fim", value=date.today())
        if st.button("Gerar DRE"):
            dre = requests.get(f"{API_URL}/relatorios/dre?inicio={ini}&fim={fim}").json()
            fig = go.Figure(go.Waterfall(x = ["Receita", "Impostos", "Liq", "Custos", "Margem", "Despesas", "Lucro"], y = [dre['receita_bruta'], -dre['impostos'], dre['receita_liquida'], -dre['custos_variaveis'], dre['margem_contribuicao'], -dre['despesas_fixas'], dre['lucro_liquido']], connector = {"line":{"color":"#555"}}))
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font={'color': '#FFFFFF'})
            st.plotly_chart(fig, use_container_width=True)
        if st.button("📄 PDF Vendas"): 
            pdf = requests.get(f"{API_URL}/relatorios/vendas_pdf?inicio={ini}&fim={fim}")
            if pdf.status_code==200: st.download_button("Baixar", pdf.content, "vendas.pdf", "application/pdf")

    elif page_id == "cfg": 
        header("Configurações"); 
        if st.button("🗑️ RESETAR SISTEMA", type="primary"):
            res = requests.delete(f"{API_URL}/sistema/resetar_dados/")
            if res.status_code == 200: st.success("Resetado!"); time.sleep(2); st.rerun()

if st.session_state['logado']: sistema_erp()
else: tela_login()