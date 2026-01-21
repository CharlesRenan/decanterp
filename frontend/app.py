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

def render_logo_svg(width="50px", color="#E879F9"):
    # Logo agora em tom Roxo/Rosa para combinar com a ref
    return f'<svg width="{width}" height="{width}" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M30 20 V80 C30 90 40 95 50 85 L80 50 C90 40 80 20 60 20 Z" stroke="{color}" stroke-width="8" fill="none"/><path d="M30 50 L60 20" stroke="{color}" stroke-width="8" stroke-linecap="round"/><circle cx="35" cy="85" r="5" fill="{color}"/></svg>'

def apply_custom_style():
    st.markdown("""
    <style>
        /* FONTE */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
        
        /* --- TEMA MATTE BLACK --- */
        
        /* Fundo Principal (Preto Fosco Profundo) */
        .stApp { background-color: #0E0E0E; }
        
        /* Sidebar (Um pouco mais clara que o fundo) */
        div[data-testid="stSidebar"] { 
            background-color: #141414; 
            border-right: 1px solid #262626;
        }

        /* Títulos */
        h1, h2, h3, h4, h5, h6 { color: #FFFFFF !important; font-weight: 600 !important; }
        p, div, label, span { color: #A0A0A0; }
        
        .big-font { 
            font-size: 24px !important; 
            font-weight: 600 !important; 
            color: #FFFFFF !important; 
            margin-top: 15px !important; 
            margin-bottom: 25px !important; 
        }

        /* --- CARDS (ESTILO ELEMENTOR) --- */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #1C1C1C; /* Cinza Card */
            border: none; /* Sem borda, visual limpo */
            border-radius: 20px; /* Borda bem redonda */
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3); /* Sombra difusa */
        }

        /* KPI Cards (Topo) */
        .card-container {
            background-color: #1C1C1C;
            border-radius: 20px;
            padding: 20px;
            border: 1px solid transparent; /* Sem borda visível */
            position: relative;
        }
        
        /* Detalhe colorido sutil no topo do card */
        .card-accent {
            width: 30px; height: 4px; border-radius: 2px; margin-bottom: 10px;
        }
        .acc-purple { background: linear-gradient(90deg, #C084FC, #E879F9); }
        .acc-blue { background: linear-gradient(90deg, #60A5FA, #3B82F6); }
        .acc-green { background: linear-gradient(90deg, #4ADE80, #22C55E); }
        
        .card-title { font-size: 12px; font-weight: 500; color: #737373; margin-bottom: 5px; }
        .card-value { font-size: 26px; font-weight: 700; color: #FFFFFF; margin-top: 0px; }
        .card-sub { font-size: 11px; color: #525252; margin-top: 5px; }

        /* --- INPUTS & FORMS (MODERNOS) --- */
        div[data-testid="stForm"] input, div[data-testid="stTextInput"] input, div[data-testid="stNumberInput"] input, div[data-testid="stDateInput"] input, div[data-testid="stSelectbox"] > div > div { 
            background-color: #262626 !important; 
            border: none !important; 
            color: #E5E5E5 !important; 
            border-radius: 12px !important;
            padding-left: 15px;
        }
        
        /* BOTÕES (GRADIENTE ROXO/ROSA DA REFERÊNCIA) */
        div[data-testid="stFormSubmitButton"] button, div[data-testid="stButton"] button { 
            background: linear-gradient(90deg, #A855F7 0%, #EC4899 100%) !important; 
            color: white !important; 
            border: none; border-radius: 12px; font-weight: 600;
            padding: 0.6rem 1.2rem;
            transition: transform 0.2s;
        }
        div[data-testid="stFormSubmitButton"] button:hover, div[data-testid="stButton"] button:hover {
            transform: scale(1.02);
            box-shadow: 0 0 20px rgba(236, 72, 153, 0.4);
        }
        
        /* Botão Secundário (Lixeira) */
        div[data-testid="stHorizontalBlock"] button[kind="secondary"] { 
            background: #262626 !important; border: none !important; color: #EF4444 !important; 
        }

        /* --- TABELAS --- */
        .sales-row { display: flex; align-items: center; justify-content: space-between; padding: 15px 0; border-bottom: 1px solid #262626; }
        .sales-row:last-child { border-bottom: none; }
        .avatar-circle { width: 32px; height: 32px; border-radius: 50%; background: #262626; color: #E5E5E5; display: flex; align-items: center; justify-content: center; font-size: 10px; font-weight: 700; margin-right: 15px; }
        .client-name { color: #FFFFFF !important; font-weight: 500; font-size: 13px; }
        .client-sub { font-size: 11px; color: #737373 !important; }
        
        /* Menu Ativo */
        .nav-link-selected {
            background: linear-gradient(90deg, rgba(168, 85, 247, 0.1), transparent) !important;
            border-left: 3px solid #E879F9 !important;
            color: #FFFFFF !important;
        }
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

def card_html(titulo, valor, subtexto, tipo="purple"): 
    cor = "acc-purple" if tipo == "purple" else ("acc-blue" if tipo == "blue" else "acc-green")
    st.markdown(f"<div class='card-container'><div class='card-accent {cor}'></div><div class='card-title'>{titulo}</div><div class='card-value'>{valor}</div><div class='card-sub'>{subtexto}</div></div>", unsafe_allow_html=True)

def get_sales_row_html(nome, email, valor):
    iniciais = nome[:2].upper() if nome else "??"
    return f"<div class='sales-row'><div style='display:flex;align-items:center;'><div class='avatar-circle'>{iniciais}</div><div class='client-info'><div class='client-name'>{nome}</div><div class='client-sub'>{email}</div></div></div><div style='font-weight:600; color:#E879F9;'>R$ {valor:,.2f}</div></div>"

def header(titulo): st.markdown(f"<div class='big-font'>{titulo}</div>", unsafe_allow_html=True)

def tela_login():
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown(f"<div style='display:flex; flex-direction:column; align-items:center; gap: 15px; margin-bottom: 30px;'>{render_logo_svg(width='60px', color='#E879F9')}<h2 style='margin:0; color:white !important; font-size: 22px;'>Decant ERP</h2></div>", unsafe_allow_html=True)
            with st.form("login_form"):
                u_input = st.text_input("Usuário", placeholder="admin")
                p_input = st.text_input("Senha", type="password", placeholder="••••••")
                st.markdown("<br>", unsafe_allow_html=True)
                submit = st.form_submit_button("Entrar", use_container_width=True)
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

def sistema_erp():
    with st.sidebar:
        st.markdown(f"<div style='display:flex; align-items:center; gap:12px; margin-bottom:30px; padding-left:15px; padding-top:20px;'>{render_logo_svg(width='26px', color='#E879F9')}<div style='font-family:Inter; font-weight:700; font-size:18px; color:white;'>Decant</div></div>", unsafe_allow_html=True)
        
        # MENU COMPLETO
        menu = [{"l": "Dashboard", "i": "grid-fill", "id": "dash"}, {"l": "PDV (Caixa)", "i": "cart-fill", "id": "pdv"}, {"l": "Produtos", "i": "box-seam-fill", "id": "prod"}, {"l": "Clientes", "i": "people-fill", "id": "cli"}, {"l": "Financeiro", "i": "wallet-fill", "id": "fin"}, {"l": "Relatórios", "i": "bar-chart-fill", "id": "rel"}, {"l": "CRM", "i": "heart-fill", "id": "crm"}, {"l": "Produção", "i": "gear-wide-connected", "id": "fab"}, {"l": "Compras", "i": "bag-fill", "id": "comp"}, {"l": "Engenharia", "i": "tools", "id": "eng"}, {"l": "Planejamento", "i": "diagram-3", "id": "mrp"}, {"l": "Fornecedores", "i": "truck", "id": "forn"}, {"l": "Vendas Adm", "i": "graph-up", "id": "vend"}, {"l": "Config", "i": "sliders", "id": "cfg"}]
        
        sel = option_menu(None, [x["l"] for x in menu], icons=[x["i"] for x in menu], default_index=0, 
            styles={
                "container": {"padding": "0!important", "background-color": "transparent"},
                "icon": {"color": "#737373", "font-size": "13px"}, 
                "nav-link": {"font-family":"Inter", "font-weight":"500", "font-size": "13px", "text-align": "left", "margin":"2px", "--hover-color": "#1C1C1C", "color": "#A0A0A0"},
            })
        page_id = next(x["id"] for x in menu if x["l"] == sel)
        
        st.markdown("<div style='margin-top: auto; padding: 20px; color: #404040; font-size: 10px; text-align: center;'>v6.0 Matte</div>", unsafe_allow_html=True)
        if st.button("Sair", use_container_width=True): st.session_state['logado'] = False; st.rerun()

    if page_id == "dash":
        header("Dashboard")
        d = get_data("financeiro/dashboard"); vendas = get_data("vendas"); clientes = get_data("clientes"); prods = get_data("produtos")
        c1, c2, c3, c4 = st.columns(4)
        with c1: card_html("RECEITA", f"R$ {d.get('receita', 0):,.2f}", "+12% vs mês ant.", "green")
        with c2: card_html("DESPESAS", f"R$ {d.get('despesas', 0):,.2f}", "Dentro da meta", "purple")
        with c3: card_html("LUCRO", f"R$ {d.get('lucro', 0):,.2f}", f"Margem: {d.get('margem', 0):.1f}%", "blue")
        with c4: card_html("STATUS", "Online", "Servidor Ativo", "purple")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # GRÁFICOS ESTILO ELEMENTOR (Curvas e Cores Neon)
        c_graf, c_vendas = st.columns([1.5, 1])
        with c_graf:
            with st.container(border=True): 
                st.markdown("#### Performance Financeira")
                dados = d.get('grafico', [])
                if dados:
                    df_g = pd.DataFrame(dados)
                    fig = px.line(df_g, x="Mês", y="Valor", color="Tipo", line_shape='spline', render_mode='svg', color_discrete_map={'Entradas': '#E879F9', 'Saídas': '#60A5FA'})
                    # Preenchimento Gradiente (Simulado)
                    fig.update_traces(fill='tozeroy', line=dict(width=3))
                else:
                    fig = px.line(pd.DataFrame([{"Mês":"Jan","Valor":0,"Tipo":"Entradas"}]), x="Mês", y="Valor")
                
                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font={'color': '#737373', 'family': 'Inter'}, xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#262626'), margin=dict(l=0, r=0, t=0, b=0), height=300, showlegend=True, legend=dict(orientation="h", y=1.1))
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

        with c_vendas:
            with st.container(border=True):
                st.markdown("#### Últimas Atividades")
                rows_html = ""
                map_clientes = {c['id']: c for c in clientes}
                for v in vendas[:5]:
                    cli = map_clientes.get(v['cliente_id'], {'nome': 'Cliente', 'email': '-'})
                    rows_html += get_sales_row_html(cli['nome'], "Venda Confirmada", v['valor_total'])
                st.markdown(f"<div style='height: 300px; overflow-y: auto;'>{rows_html}</div>", unsafe_allow_html=True)

    elif page_id == "pdv":
        header("PDV")
        clis = get_data("clientes"); prods = get_data("produtos"); pas = [p for p in prods if p['tipo'] == 'Produto Acabado']
        c1, c2 = st.columns([1.5, 1])
        with c1:
            with st.container(border=True):
                st.markdown("#### Seleção")
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
                    if st.button("FINALIZAR VENDA", type="primary", use_container_width=True): 
                        if cli_sel:
                            cid = next(x['id'] for x in clis if x['nome']==cli_sel)
                            requests.post(f"{API_URL}/vendas/pdv/", json={"cliente_id":cid,"itens":[{"produto_id":i['id'],"quantidade":i['qtd'],"valor_total":i['total']} for i in st.session_state['carrinho']],"metodo_pagamento":"Pix"})
                            st.session_state['carrinho']=[]; st.success("Venda OK!"); time.sleep(1); st.rerun()
                        else: st.error("Selecione um cliente!")
                else: st.info("Caixa Livre")

    # --- ABAS SECUNDÁRIAS ---
    elif page_id == "cli":
        header("Clientes")
        c1, c2 = st.columns([1, 1.5])
        with c1:
            with st.container(border=True):
                st.markdown("#### Cadastro Rápido")
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
        header("CRM")
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
                qtd = st.number_input("Quantidade", 100)
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
                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font={'color': '#FFFFFF'})
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