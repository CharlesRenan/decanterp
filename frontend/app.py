import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from streamlit_option_menu import option_menu
from datetime import datetime, date
import os
import time

# --- CONFIGURAÇÃO MANUAL ---
API_URL = "https://api-decant-oficial.onrender.com"

print(f"🔗 CONECTANDO O ERP EM: {API_URL}")

st.set_page_config(page_title="Decant ERP", page_icon="💧", layout="wide")

if 'carrinho' not in st.session_state: st.session_state['carrinho'] = []
if 'logado' not in st.session_state: st.session_state['logado'] = False
if 'usuario' not in st.session_state: st.session_state['usuario'] = ""
if 'cargo' not in st.session_state: st.session_state['cargo'] = ""

def render_logo_svg(width="50px", color="#C57A57"):
    return f'<svg width="{width}" height="{width}" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M30 20 V80 C30 90 40 95 50 85 L80 50 C90 40 80 20 60 20 Z" stroke="{color}" stroke-width="8" fill="none"/><path d="M30 50 L60 20" stroke="{color}" stroke-width="8" stroke-linecap="round"/><circle cx="35" cy="85" r="5" fill="{color}"/></svg>'

def apply_custom_style():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
        .stApp { background-color: #0F172A; }
        .big-font { font-family: 'Inter', sans-serif !important; font-size: 36px !important; font-weight: 600 !important; color: #FFFFFF !important; margin-top: 40px !important; margin-bottom: 20px !important; line-height: 1.2 !important; }
        
        /* CARDS DO TOPO (Receita, Lucro...) */
        .card-container { border-radius: 12px; padding: 24px; margin-bottom: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .card-blue { background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%); border: 1px solid #3B82F6; color: white; }
        .card-red { background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%); border: 1px solid #EF4444; color: white; }
        .card-green { background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%); border: 1px solid #10B981; color: white; }
        .card-dark { background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%); border: 1px solid #F59E0B; color: white; }
        .card-title { font-size: 13px !important; font-weight: 600 !important; color: #94A3B8 !important; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }
        .card-value { font-size: 32px; font-weight: 700 !important; color: #FFFFFF; margin-top: 0px; }
        
        /* MENU LATERAL */
        div[data-testid="stSidebar"] { background-color: #0F172A; border-right: 1px solid #1E293B; }
        div[data-testid="stSidebar"] button { border-color: #334155; color: #94A3B8; }
        div[data-testid="stForm"] input { background-color: #1E293B !important; border: 1px solid #334155 !important; color: white; }
        div[data-testid="stFormSubmitButton"] button { background: linear-gradient(90deg, #3B82F6 0%, #2563EB 100%) !important; color: white !important; border: none; }
        
        /* --- ESTILO UNIFICADO DAS CAIXAS (Vendas e Gráficos) --- */
        .box-padrao { 
            background-color: #1E293B; 
            border-radius: 12px; 
            padding: 20px; 
            height: 420px; /* Altura fixa para alinhar tudo */
            border: 1px solid #334155; 
            overflow: hidden; /* Garante que nada saia da borda */
            display: flex;
            flex-direction: column;
        }
        
        .box-header { font-size: 16px; font-weight: 700; color: white; margin-bottom: 15px; font-family: 'Inter'; }
        
        /* Ajustes específicos para a lista de vendas */
        .sales-scroll { overflow-y: auto; flex-grow: 1; }
        .sales-row { display: flex; align-items: center; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid #334155; }
        .sales-row:last-child { border-bottom: none; }
        .sales-left { display: flex; align-items: center; gap: 12px; }
        .avatar-circle { width: 40px; height: 40px; border-radius: 10px; background-color: #3B82F6; color: #FFFFFF; display: flex; align-items: center; justify-content: center; font-weight: 700; }
        .client-name { font-size: 14px; color: white; font-weight: 600; }
        .client-sub { font-size: 12px; color: #94A3B8; }
        .sales-val { font-size: 14px; color: white; font-weight: 700; }
        .sales-badge { font-size: 11px; padding: 2px 8px; border-radius: 12px; margin-top: 4px; display: inline-block; font-weight: 600; }
        .badge-green { background-color: rgba(16, 185, 129, 0.2); color: #34D399; }
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
    st.markdown(f"<div class='card-container {cor}'><div class='card-title'>{titulo}</div><div class='card-value'>{valor}</div><div style='font-size:12px; margin-top:10px; opacity:0.8'>{subtexto}</div></div>", unsafe_allow_html=True)

def get_sales_row_html(nome, email, valor):
    iniciais = nome[:2].upper() if nome else "??"
    return f"<div class='sales-row'><div class='sales-left'><div class='avatar-circle'>{iniciais}</div><div class='client-info'><span class='client-name'>{nome}</span><span class='client-sub'>{email}</span></div></div><div class='sales-right'><div class='sales-val'>R$ {valor:,.2f}</div><div class='sales-badge badge-green'>+1.5%</div></div></div>"

def header(titulo): st.markdown(f"<div class='big-font'>{titulo}</div>", unsafe_allow_html=True)

def tela_login():
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        logo_path = "frontend/logo.png"
        if os.path.exists(logo_path): st.image(logo_path, use_container_width=True)
        else: st.markdown(f"<div style='display:flex; flex-direction:column; align-items:center;'>{render_logo_svg(width='80px', color='#3B82F6')}<div class='login-title'>Decant ERP</div></div>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            u_input = st.text_input("Usuário", placeholder="admin")
            p_input = st.text_input("Senha", type="password", placeholder="••••••")
            submit = st.form_submit_button("ENTRAR")
            if submit:
                try:
                    res = requests.post(f"{API_URL}/auth/login/", json={"username": u_input, "senha": p_input, "cargo": ""})
                    if res.status_code == 200:
                        data = res.json(); st.session_state['logado'] = True; st.session_state['usuario'] = data['usuario']; st.session_state['cargo'] = data['cargo']; st.rerun()
                    else: st.error("Acesso Negado")
                except: st.error("Erro Conexão")

def sistema_erp():
    with st.sidebar:
        logo_path = "frontend/logo.png"
        if os.path.exists(logo_path): st.markdown("<div style='margin-bottom: 25px; text-align: center;'>", unsafe_allow_html=True); st.image(logo_path, width=160); st.markdown("</div>", unsafe_allow_html=True)
        else: st.markdown(f"<div style='display:flex; align-items:center; gap:12px; margin-bottom:30px; padding-left:10px;'>{render_logo_svg(width='32px', color='#3B82F6')}<div style='font-family:Inter; font-weight:700; font-size:20px; color:white;'>Decant</div></div>", unsafe_allow_html=True)
        
        menu = [{"l": "Visão Geral", "i": "grid", "id": "dash"}, {"l": "PDV (Caixa)", "i": "basket", "id": "pdv"}, {"l": "Financeiro", "i": "cash-coin", "id": "fin"}, {"l": "CRM", "i": "heart", "id": "crm"}, {"l": "Produtos", "i": "box-seam", "id": "prod"}, {"l": "Clientes", "i": "people", "id": "cli"}, {"l": "Fornecedores", "i": "truck", "id": "forn"}, {"l": "Preços", "i": "tags", "id": "prec"}, {"l": "Engenharia", "i": "tools", "id": "eng"}, {"l": "Planejamento", "i": "diagram-3", "id": "mrp"}, {"l": "Compras", "i": "cart", "id": "comp"}, {"l": "Produção", "i": "gear-wide-connected", "id": "fab"}, {"l": "Vendas (Adm)", "i": "graph-up-arrow", "id": "vend"}, {"l": "Relatórios", "i": "bar-chart-line", "id": "rel"}, {"l": "Configurações", "i": "gear", "id": "cfg"}]
        sel = option_menu(None, [x["l"] for x in menu], icons=[x["i"] for x in menu], default_index=0, styles={"container": {"padding": "0!important", "background-color": "transparent"},"icon": {"color": "#94A3B8", "font-size": "14px"}, "nav-link": {"font-family":"Inter", "font-weight":"500", "font-size": "14px", "text-align": "left", "margin":"5px", "--hover-color": "#1E293B", "color": "#E2E8F0"},"nav-link-selected": {"background-color": "#3B82F6", "color": "#FFFFFF", "font-weight": "600"}})
        page_id = next(x["id"] for x in menu if x["l"] == sel)
        st.markdown("<div style='margin-top: 40px'></div>", unsafe_allow_html=True)
        if st.button("Sair"): st.session_state['logado'] = False; st.rerun()

    if page_id == "dash":
        header("Visão Geral")
        d = get_data("financeiro/dashboard"); vendas = get_data("vendas"); clientes = get_data("clientes"); prods = get_data("produtos")

        # 1. Cards Topo (Mantidos)
        c1, c2, c3, c4 = st.columns(4)
        with c1: card_html("RECEITA TOTAL", f"R$ {d.get('receita', 0):,.2f}", "Vendas + Extras", "card-blue")
        with c2: card_html("DESPESAS TOTAIS", f"R$ {d.get('despesas', 0):,.2f}", "MP + Contas Fixas", "card-red")
        with c3: card_html("LUCRO LÍQUIDO", f"R$ {d.get('lucro', 0):,.2f}", f"Margem Real: {d.get('margem', 0):.1f}%", "card-green")
        with c4: card_html("SISTEMA", "Online", "v2.0 CRM", "card-dark")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 2. Primeira Linha: Fluxo e Lista de Vendas
        c_graf, c_vendas = st.columns([1.6, 1])
        
        # Bloco Fluxo de Caixa (Corrigido)
        with c_graf:
            dados = d.get('grafico', [])
            if dados: fig = px.bar(pd.DataFrame(dados), x="Mês", y="Valor", color="Tipo", barmode='group', color_discrete_map={'Entradas': '#10B981', 'Saídas': '#3B82F6'})
            else: fig = px.bar(pd.DataFrame([{"Mês":"Jan","Valor":0,"Tipo":"Entradas"}]), x="Mês", y="Valor")
            # Fundo Transparente para a cor da caixa aparecer
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#94A3B8', xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#334155'), legend=dict(orientation="h", y=1.1), margin=dict(l=20, r=20, t=20, b=20), height=340)
            # Injeta o gráfico dentro da caixa HTML
            graph_html = fig.to_html(include_plotlyjs='cdn', full_html=False, config={'displayModeBar': False})
            st.markdown(f"""<div class='box-padrao'><div class='box-header'>Fluxo de Caixa Mensal</div>{graph_html}</div>""", unsafe_allow_html=True)

        # Bloco Lista de Vendas
        with c_vendas:
            rows_html = ""
            map_clientes = {c['id']: c for c in clientes}
            for v in vendas[:5]:
                cli = map_clientes.get(v['cliente_id'], {'nome': 'Cliente', 'email': '-'})
                rows_html += get_sales_row_html(cli['nome'], cli['email'], v['valor_total'])
            st.markdown(f"<div class='box-padrao'><div class='box-header'>Últimas Vendas</div><div class='sales-scroll'>{rows_html}</div></div>", unsafe_allow_html=True)

        # 3. Segunda Linha: Produtos e Pagamentos (Corrigido)
        if vendas and prods:
            st.markdown("<br>", unsafe_allow_html=True)
            df_vendas = pd.DataFrame(vendas)
            map_prods = {p['id']: p['nome'] for p in prods}
            df_vendas['Produto'] = df_vendas['produto_id'].map(map_prods)
            g1, g2 = st.columns([1.5, 1])
            
            with g1:
                top_prods = df_vendas.groupby('Produto')['valor_total'].sum().reset_index().sort_values('valor_total', ascending=False).head(5)
                fig_bar = px.bar(top_prods, x='valor_total', y='Produto', orientation='h', text_auto='.2s', color='valor_total', color_continuous_scale='Blues')
                fig_bar.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white', xaxis_title="", yaxis_title="", margin=dict(t=20, b=20, l=20, r=20), height=340)
                html_bar = fig_bar.to_html(include_plotlyjs='cdn', full_html=False, config={'displayModeBar': False})
                st.markdown(f"""<div class='box-padrao'><div class='box-header'>🏆 Produtos Mais Vendidos</div>{html_bar}</div>""", unsafe_allow_html=True)
                
            with g2:
                pg = df_vendas.groupby('metodo_pagamento')['valor_total'].sum().reset_index()
                fig_pie = px.pie(pg, values='valor_total', names='metodo_pagamento', hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
                fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color='white', margin=dict(t=20, b=20), height=340)
                html_pie = fig_pie.to_html(include_plotlyjs='cdn', full_html=False, config={'displayModeBar': False})
                st.markdown(f"""<div class='box-padrao'><div class='box-header'>💳 Meios de Pagamento</div>{html_pie}</div>""", unsafe_allow_html=True)

    # --- RESTANTE DO SISTEMA (ABAS FUNCIONAIS) ---
    elif page_id == "pdv":
        header("Frente de Caixa (PDV)"); clis = get_data("clientes"); prods = get_data("produtos"); pas = [p for p in prods if p['tipo'] == 'Produto Acabado']
        c1, c2 = st.columns([1.5, 1])
        with c1:
            st.markdown("##### 🛒 Adicionar Itens"); cli_sel = st.selectbox("Cliente", [c['nome'] for c in clis]) if clis else None
            with st.container(border=True):
                k1, k2 = st.columns([3, 1]); p = k1.selectbox("Produto", [x['nome'] for x in pas]) if pas else None; q = k2.number_input("Qtd", 1.0)
                if st.button("Adicionar"): obj = next(x for x in pas if x['nome']==p); pr = obj['custo']*2; st.session_state['carrinho'].append({"id":obj['id'],"nome":obj['nome'],"qtd":q,"total":q*pr})
        with c2:
            st.markdown("##### 🧾 Cupom"); st.write(pd.DataFrame(st.session_state['carrinho']))
            if st.button("FINALIZAR VENDA", type="primary"): 
                cid = next(x['id'] for x in clis if x['nome']==cli_sel)
                requests.post(f"{API_URL}/vendas/pdv/", json={"cliente_id":cid,"itens":[{"produto_id":i['id'],"quantidade":i['qtd'],"valor_total":i['total']} for i in st.session_state['carrinho']],"metodo_pagamento":"Pix"})
                st.session_state['carrinho']=[]; st.success("OK!"); st.rerun()

    elif page_id == "prod": header("Produtos"); st.dataframe(pd.DataFrame(get_data("produtos")), use_container_width=True)
    elif page_id == "fab": header("Chão de Fábrica"); st.info("Use o app para registrar produção."); st.dataframe(pd.DataFrame(get_data("producao/historico/")), use_container_width=True)
    elif page_id == "rel": header("Relatórios"); st.dataframe(pd.DataFrame(get_data("relatorios/estoque/")['itens']), use_container_width=True)
    elif page_id == "cli": header("Clientes"); st.dataframe(pd.DataFrame(get_data("clientes")), use_container_width=True)
    elif page_id == "mrp": header("Planejamento"); st.warning("Cadastre fórmulas na engenharia.")
    elif page_id == "eng": header("Engenharia"); st.info("Cadastro de fórmulas.")
    elif page_id == "fin": header("Financeiro"); st.dataframe(pd.DataFrame(get_data("financeiro/lancamentos")))
    elif page_id == "comp": header("Compras"); st.dataframe(pd.DataFrame(get_data("compras")))
    elif page_id == "forn": header("Fornecedores"); st.dataframe(pd.DataFrame(get_data("fornecedores")))
    elif page_id == "prec": header("Preços"); st.dataframe(pd.DataFrame(get_data("cotacoes")))
    elif page_id == "vend": header("Vendas"); st.dataframe(pd.DataFrame(get_data("vendas")))
    elif page_id == "cfg": header("Config"); st.button("Resetar", on_click=lambda: requests.delete(f"{API_URL}/sistema/resetar_dados/"))

if st.session_state['logado']: sistema_erp()
else: tela_login()