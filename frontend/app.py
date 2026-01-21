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

def render_logo_svg(width="50px", color="#3B82F6"):
    # Logo ajustado para fundo escuro (Sidebar)
    return f'<svg width="{width}" height="{width}" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M30 20 V80 C30 90 40 95 50 85 L80 50 C90 40 80 20 60 20 Z" stroke="{color}" stroke-width="8" fill="none"/><path d="M30 50 L60 20" stroke="{color}" stroke-width="8" stroke-linecap="round"/><circle cx="35" cy="85" r="5" fill="{color}"/></svg>'

def apply_custom_style():
    st.markdown("""
    <style>
        /* FONTE OUTFIT (MANTENDO A GEOMETRIA MODERNA) */
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
        html, body, [class*="css"] { font-family: 'Outfit', sans-serif !important; }
        
        /* --- TEMA CLEAN (BLUEBERRY STYLE) --- */
        
        /* Fundo Principal (Cinza Gelo Claro) */
        .stApp { background-color: #F3F4F6; }
        
        /* Sidebar (Azul Marinho Profundo) */
        div[data-testid="stSidebar"] { background-color: #111827; }
        
        /* Textos Gerais (Escuros para contraste no fundo claro) */
        h1, h2, h3, h4, h5, h6 { color: #1F2937 !important; font-weight: 700 !important; }
        p, div, label, span { color: #4B5563; }
        
        /* Título da Página */
        .big-font { 
            font-size: 28px !important; 
            font-weight: 700 !important; 
            color: #111827 !important; 
            margin-top: 10px !important; 
            margin-bottom: 20px !important; 
        }

        /* --- CARDS BRANCOS (SHADOW) --- */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); /* Sombra suave */
        }
        
        /* Cards KPI (Topo) */
        .card-container {
            background-color: #FFFFFF;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            border-left: 5px solid #3B82F6; /* Detalhe colorido na esquerda */
        }
        .card-title { font-size: 12px; font-weight: 600; color: #9CA3AF; text-transform: uppercase; letter-spacing: 0.5px; }
        .card-value { font-size: 28px; font-weight: 700; color: #111827; margin-top: 5px; }
        .card-sub { font-size: 12px; color: #10B981; font-weight: 500; margin-top: 5px; }

        /* INPUTS (Estilo Clean) */
        div[data-testid="stForm"] input, div[data-testid="stTextInput"] input, div[data-testid="stNumberInput"] input, div[data-testid="stDateInput"] input, div[data-testid="stSelectbox"] > div > div { 
            background-color: #FFFFFF !important; 
            border: 1px solid #D1D5DB !important; 
            color: #1F2937 !important; 
            border-radius: 8px !important;
        }
        
        /* BOTÕES (Azul Vibrante) */
        div[data-testid="stFormSubmitButton"] button, div[data-testid="stButton"] button { 
            background-color: #3B82F6 !important;
            color: white !important; 
            border: none; border-radius: 8px; font-weight: 600;
            box-shadow: 0 2px 4px rgba(59, 130, 246, 0.3);
            transition: all 0.2s;
        }
        div[data-testid="stFormSubmitButton"] button:hover, div[data-testid="stButton"] button:hover {
            background-color: #2563EB !important;
            transform: translateY(-1px);
        }
        
        /* TABELAS E LISTAS */
        .sales-row { display: flex; align-items: center; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid #F3F4F6; }
        .avatar-circle { width: 36px; height: 36px; border-radius: 10px; background: #EEF2FF; color: #4F46E5; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; margin-right: 12px; }
        .client-name { color: #1F2937 !important; font-weight: 600; font-size: 14px; }
        .client-sub { font-size: 11px; color: #6B7280 !important; }
        .sales-val { color: #1F2937 !important; font-weight: 700; font-size: 14px; }
        
        /* Botão Lixeira */
        div[data-testid="stHorizontalBlock"] button[kind="secondary"] { 
            border: 1px solid #EF4444 !important; background: #FEF2F2 !important; color: #EF4444 !important; 
        }

        /* Menu Sidebar (Ajuste de cor) */
        .nav-link { color: #9CA3AF !important; }
        .nav-link-selected { background-color: #374151 !important; color: white !important; }
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

def card_html(titulo, valor, subtexto): 
    st.markdown(f"<div class='card-container'><div class='card-title'>{titulo}</div><div class='card-value'>{valor}</div><div class='card-sub'>{subtexto}</div></div>", unsafe_allow_html=True)

def get_sales_row_html(nome, email, valor):
    iniciais = nome[:2].upper() if nome else "??"
    return f"<div class='sales-row'><div style='display:flex;align-items:center;'><div class='avatar-circle'>{iniciais}</div><div class='client-info'><div class='client-name'>{nome}</div><div class='client-sub'>{email}</div></div></div><div class='sales-val'>R$ {valor:,.2f}</div></div>"

def header(titulo): st.markdown(f"<div class='big-font'>{titulo}</div>", unsafe_allow_html=True)

def tela_login():
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        # Login em Card Branco
        with st.container(border=True):
            st.markdown(f"<div style='display:flex; flex-direction:column; align-items:center; gap: 10px; margin-bottom: 20px;'>{render_logo_svg(width='50px', color='#3B82F6')}<h2 style='margin:0;'>Decant ERP</h2><p style='font-size:12px;'>Bem-vindo de volta</p></div>", unsafe_allow_html=True)
            with st.form("login_form"):
                u_input = st.text_input("Usuário", placeholder="admin")
                p_input = st.text_input("Senha", type="password", placeholder="••••••")
                st.markdown("<br>", unsafe_allow_html=True)
                submit = st.form_submit_button("Entrar no Sistema", use_container_width=True)
                if submit:
                    sucesso = False; mensagem_erro = ""
                    with st.spinner("Conectando..."):
                        for tentativa in range(1, 4):
                            try:
                                res = requests.post(f"{API_URL}/auth/login/", json={"username": u_input, "senha": p_input, "cargo": ""}, timeout=10)
                                if res.status_code == 200: sucesso = True; break
                                else: mensagem_erro = "Dados incorretos."; break
                            except:
                                if tentativa < 3: time.sleep(3)
                                else: mensagem_erro = "Servidor Offline."
                    if sucesso:
                        data = res.json(); st.session_state['logado'] = True; st.session_state['usuario'] = data['usuario']; st.session_state['cargo'] = data['cargo']; st.rerun()
                    else: st.error(mensagem_erro)

def sistema_erp():
    with st.sidebar:
        st.markdown(f"<div style='display:flex; align-items:center; gap:12px; margin-bottom:20px; padding-left:10px; padding-top:20px;'>{render_logo_svg(width='28px', color='#60A5FA')}<div style='font-family:Outfit; font-weight:700; font-size:20px; color:white;'>Decant</div></div>", unsafe_allow_html=True)
        
        # Menu Estilizado para Fundo Escuro
        menu = [{"l": "Dashboard", "i": "grid-fill", "id": "dash"}, {"l": "PDV (Caixa)", "i": "cart-fill", "id": "pdv"}, {"l": "Produtos", "i": "box-seam-fill", "id": "prod"}, {"l": "Clientes", "i": "people-fill", "id": "cli"}, {"l": "Financeiro", "i": "wallet-fill", "id": "fin"}, {"l": "Relatórios", "i": "bar-chart-fill", "id": "rel"}, {"l": "CRM", "i": "heart-fill", "id": "crm"}, {"l": "Produção", "i": "gear-wide-connected", "id": "fab"}, {"l": "Compras", "i": "bag-fill", "id": "comp"}, {"l": "Engenharia", "i": "tools", "id": "eng"}, {"l": "Planejamento", "i": "diagram-3", "id": "mrp"}, {"l": "Fornecedores", "i": "truck", "id": "forn"}, {"l": "Vendas Adm", "i": "graph-up", "id": "vend"}, {"l": "Config", "i": "sliders", "id": "cfg"}]
        
        sel = option_menu(None, [x["l"] for x in menu], icons=[x["i"] for x in menu], default_index=0, 
            styles={
                "container": {"padding": "0!important", "background-color": "transparent"},
                "icon": {"color": "#9CA3AF", "font-size": "14px"}, 
                "nav-link": {"font-family":"Outfit", "font-weight":"500", "font-size": "13px", "text-align": "left", "margin":"2px", "--hover-color": "#1F2937", "color": "#D1D5DB"},
                "nav-link-selected": {"background-color": "#3B82F6", "color": "#FFFFFF", "font-weight": "600", "border-radius": "8px"}
            })
        page_id = next(x["id"] for x in menu if x["l"] == sel)
        
        st.markdown("<div style='margin-top: auto; padding: 20px; color: #6B7280; font-size: 10px; text-align: center;'>v5.0 Clean</div>", unsafe_allow_html=True)
        if st.button("Sair", use_container_width=True): st.session_state['logado'] = False; st.rerun()

    # --- LÓGICA DAS PÁGINAS (MANTIDA 100%) ---
    if page_id == "dash":
        header("Visão Geral")
        d = get_data("financeiro/dashboard"); vendas = get_data("vendas"); clientes = get_data("clientes"); prods = get_data("produtos")
        c1, c2, c3, c4 = st.columns(4)
        with c1: card_html("Receita Total", f"R$ {d.get('receita', 0):,.2f}", "↗ +12% este mês")
        with c2: card_html("Despesas", f"R$ {d.get('despesas', 0):,.2f}", "↘ Dentro da meta")
        with c3: card_html("Lucro Líquido", f"R$ {d.get('lucro', 0):,.2f}", f"Margem: {d.get('margem', 0):.1f}%")
        with c4: card_html("Status", "Online", "Servidor OK")
        st.markdown("<br>", unsafe_allow_html=True)
        c_graf, c_vendas, c_meta = st.columns([1.2, 1, 0.8])
        with c_graf:
            with st.container(border=True): 
                st.markdown("##### Fluxo de Caixa")
                dados = d.get('grafico', [])
                fig = px.area(pd.DataFrame(dados) if dados else pd.DataFrame([{"Mês":"Jan","Valor":0,"Tipo":"Entradas"}]), x="Mês", y="Valor", color="Tipo", line_shape='spline', color_discrete_map={'Entradas': '#10B981', 'Saídas': '#3B82F6'})
                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font={'color': '#6B7280', 'family': 'Outfit'}, xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#F3F4F6'), margin=dict(l=0, r=0, t=0, b=0), height=250, showlegend=False)
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        with c_vendas:
            with st.container(border=True):
                st.markdown("##### Vendas Recentes")
                rows_html = ""
                map_clientes = {c['id']: c for c in clientes}
                for v in vendas[:4]:
                    cli = map_clientes.get(v['cliente_id'], {'nome': 'Cliente', 'email': '-'})
                    rows_html += get_sales_row_html(cli['nome'], "Confirmado", v['valor_total'])
                st.markdown(f"<div style='height: 250px; overflow-y: auto;'>{rows_html}</div>", unsafe_allow_html=True)
        with c_meta:
            with st.container(border=True):
                st.markdown("##### Meta Mensal")
                receita_atual = d.get('receita', 0)
                fig_gauge = go.Figure(go.Indicator(mode = "gauge+number", value = receita_atual, domain = {'x': [0, 1], 'y': [0, 1]}, gauge = {'axis': {'range': [None, 10000], 'tickwidth': 1, 'tickcolor': "#333"}, 'bar': {'color': "#3B82F6"}, 'bgcolor': "#EFF6FF", 'borderwidth': 0, 'bordercolor': "#333", 'steps': [{'range': [0, 10000], 'color': "#F3F4F6"}]}))
                fig_gauge.update_layout(paper_bgcolor='rgba(0,0,0,0)', font={'color': "#1F2937", 'family': 'Outfit'}, margin=dict(t=20,b=20,l=20,r=20), height=230)
                st.plotly_chart(fig_gauge, use_container_width=True)

    elif page_id == "pdv":
        header("Frente de Caixa")
        clis = get_data("clientes"); prods = get_data("produtos"); pas = [p for p in prods if p['tipo'] == 'Produto Acabado']
        c1, c2 = st.columns([1.5, 1])
        with c1:
            with st.container(border=True):
                st.markdown("##### Selecionar")
                lista_clientes = [c['nome'] for c in clis] if clis else []
                cli_sel = st.selectbox("Cliente", lista_clientes) if lista_clientes else None
                if not lista_clientes: st.warning("Cadastre clientes primeiro.")
                st.markdown("<br>", unsafe_allow_html=True)
                c_p, c_q, c_btn = st.columns([3, 1, 1.2])
                p = c_p.selectbox("Produto", [x['nome'] for x in pas]) if pas else None
                q = c_q.number_input("Qtd", 1.0, label_visibility="collapsed")
                if c_btn.button("ADICIONAR +", use_container_width=True): 
                    obj = next(x for x in pas if x['nome']==p); pr = obj['custo']*2; 
                    st.session_state['carrinho'].append({"id":obj['id'],"nome":obj['nome'],"qtd":q,"total":q*pr, "custo": obj['custo'], "preco_unitario": pr}); st.rerun()
        with c2:
            with st.container(border=True):
                st.markdown("##### Carrinho")
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
                    if st.button("FINALIZAR VENDA", type="primary", use_container_width=True): 
                        if cli_sel:
                            cid = next(x['id'] for x in clis if x['nome']==cli_sel)
                            requests.post(f"{API_URL}/vendas/pdv/", json={"cliente_id":cid,"itens":[{"produto_id":i['id'],"quantidade":i['qtd'],"valor_total":i['total']} for i in st.session_state['carrinho']],"metodo_pagamento":"Pix"})
                            st.session_state['carrinho']=[]; st.success("Venda OK!"); time.sleep(1); st.rerun()
                        else: st.error("Selecione um cliente!")
                else: st.info("Carrinho Vazio")

    elif page_id == "cli":
        header("Clientes")
        c1, c2 = st.columns([1, 1.5])
        with c1:
            with st.container(border=True):
                st.markdown("##### Novo Cliente")
                with st.form("new_cli"):
                    n = st.text_input("Nome"); e = st.text_input("Email"); t = st.text_input("Telefone")
                    if st.form_submit_button("Salvar"): requests.post(f"{API_URL}/clientes/", json={"nome":n, "email":e, "telefone":t}); st.success("OK!"); st.rerun()
        with c2: st.dataframe(pd.DataFrame(get_data("clientes")), use_container_width=True)

    elif page_id == "fin":
        header("Financeiro"); t1, t2 = st.tabs(["Lançar", "Extrato"])
        with t1:
            with st.container(border=True):
                with st.form("frm_fin"):
                    desc = st.text_input("Descrição"); tipo = st.selectbox("Tipo", ["Despesa", "Receita"]); valor = st.number_input("Valor"); pg = st.checkbox("Pago?")
                    if st.form_submit_button("Lançar"): requests.post(f"{API_URL}/financeiro/lancamento/", json={"descricao": desc, "tipo": tipo, "categoria": "Geral", "valor": valor, "data_vencimento": str(date.today()), "pago": pg}); st.success("OK!"); st.rerun()
        with t2: st.dataframe(pd.DataFrame(get_data("financeiro/lancamentos")), use_container_width=True)

    elif page_id == "crm":
        header("CRM & Fidelidade")
        st.info("Clientes inativos há mais de 25 dias.")
        ops = get_data("crm/oportunidades")
        if ops:
            for op in ops:
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    c1.markdown(f"**{op['Cliente']}** - {op['Dias sem Comprar']} dias sem compra"); c2.button("Contatar", key=f"crm_{op['Cliente']}")
        else: st.success("Nenhum cliente em risco.")

    elif page_id == "forn":
        header("Fornecedores")
        c1, c2 = st.columns([1, 2])
        with c1: 
            with st.form("nf"):
                n = st.text_input("Empresa"); p = st.number_input("Prazo", 1)
                if st.form_submit_button("Salvar"): requests.post(f"{API_URL}/fornecedores/", json={"nome":n,"prazo_entrega_dias":p}); st.success("OK"); st.rerun()
        with c2: st.dataframe(pd.DataFrame(get_data("fornecedores")), use_container_width=True)

    elif page_id == "prod": 
        header("Produtos"); t1, t2, t3 = st.tabs(["Lista", "Kardex", "+ Novo"])
        with t1: st.dataframe(pd.DataFrame(get_data("produtos")), use_container_width=True)
        with t2: st.dataframe(pd.DataFrame(get_data("estoque/kardex")), use_container_width=True)
        with t3:
            with st.container(border=True):
                with st.form("np"):
                    n = st.text_input("Nome"); t = st.selectbox("Tipo", ["Materia Prima", "Produto Acabado"]); e = st.number_input("Estoque"); c = st.number_input("Custo"); loc = st.text_input("Localização")
                    if st.form_submit_button("Salvar"): requests.post(f"{API_URL}/produtos/", json={"nome":n,"tipo":t,"unidade":"Un","estoque_atual":e,"custo":c, "localizacao": loc}); st.success("OK"); st.rerun()

    elif page_id == "eng":
        header("Engenharia")
        t1, t2 = st.tabs(["Nova Fórmula", "Consultar"])
        with t1:
            with st.container(border=True):
                with st.form("new_form"):
                    nm = st.text_input("Nome da Fórmula"); 
                    prods = get_data("produtos"); pas = [x for x in prods if x['tipo'] == 'Produto Acabado'] if prods else []
                    pf = st.selectbox("Produto Final", [x['nome'] for x in pas]) if pas else None
                    if st.form_submit_button("Criar Fórmula") and pf: 
                        pid = next(x['id'] for x in pas if x['nome']==pf)
                        requests.post(f"{API_URL}/formulas/", json={"nome":nm,"produto_final_id":pid}); st.success("Criado!")
        with t2: st.dataframe(pd.DataFrame(get_data("formulas")), use_container_width=True)

    elif page_id == "mrp":
        header("Planejamento")
        forms = get_data("formulas")
        if forms:
            c1, c2 = st.columns([1, 2])
            with c1:
                sel_f = st.selectbox("Fórmula", [f['nome'] for f in forms])
                qtd = st.number_input("Quantidade a Produzir", 100)
                if st.button("Calcular"):
                    fid = next(f['id'] for f in forms if f['nome']==sel_f)
                    res = requests.post(f"{API_URL}/planejamento/calcular/?formula_id={fid}&quantidade_producao={qtd}").json()
                    st.session_state['mrp_res'] = res
            with c2:
                if 'mrp_res' in st.session_state:
                    st.dataframe(pd.DataFrame(st.session_state['mrp_res']['materiais']))
                    st.metric("Custo Estimado", f"R$ {st.session_state['mrp_res']['custo_total']:.2f}")

    elif page_id == "comp": header("Compras"); st.dataframe(pd.DataFrame(get_data("compras")))
    elif page_id == "prec": header("Preços"); st.dataframe(pd.DataFrame(get_data("cotacoes")))
    elif page_id == "vend": header("Vendas (Adm)"); st.dataframe(pd.DataFrame(get_data("vendas")))
    elif page_id == "fab": header("Produção"); st.dataframe(pd.DataFrame(get_data("producao/historico/")), use_container_width=True)

    elif page_id == "rel": 
        header("Inteligência")
        c1, c2 = st.columns(2)
        ini = c1.date_input("Início", value=date.today().replace(day=1)); fim = c2.date_input("Fim", value=date.today())
        t1, t2 = st.tabs(["DRE", "Downloads"])
        with t1:
            if st.button("Gerar DRE"):
                dre = requests.get(f"{API_URL}/relatorios/dre?inicio={ini}&fim={fim}").json()
                fig = go.Figure(go.Waterfall(x = ["Receita", "Impostos", "Liq", "Custos", "Margem", "Despesas", "Lucro"], y = [dre['receita_bruta'], -dre['impostos'], dre['receita_liquida'], -dre['custos_variaveis'], dre['margem_contribuicao'], -dre['despesas_fixas'], dre['lucro_liquido']], connector = {"line":{"color":"#555"}}))
                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font={'color': '#1F2937'})
                st.plotly_chart(fig, use_container_width=True)
        with t2:
            if st.button("📄 PDF Vendas"): 
                pdf = requests.get(f"{API_URL}/relatorios/vendas_pdf?inicio={ini}&fim={fim}")
                if pdf.status_code==200: st.download_button("Baixar", pdf.content, "vendas.pdf", "application/pdf")

    elif page_id == "cfg": 
        header("Configurações"); 
        if st.button("🗑️ RESETAR SISTEMA", type="primary"):
            res = requests.delete(f"{API_URL}/sistema/resetar_dados/")
            if res.status_code == 200: st.success("Sistema Resetado!"); time.sleep(2); st.rerun()

if st.session_state['logado']: sistema_erp()
else: tela_login()