import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from streamlit_option_menu import option_menu
from datetime import datetime, date
import os
import time

# --- CONFIGURAÇÃO MANUAL (MANTENDO A CONEXÃO QUE FUNCIONOU) ---
# Se o seu link for diferente, ajuste aqui.
API_URL = "https://api-decant-oficial.onrender.com"

# Rastreamento de Log
print(f"\n🚀 --- INICIANDO SISTEMA ---")
print(f"🔗 CONECTANDO EM: {API_URL}")
print(f"🌍 --------------------------\n")

st.set_page_config(page_title="Decant ERP", page_icon="💧", layout="wide")

# Inicialização de Estado
if 'carrinho' not in st.session_state: st.session_state['carrinho'] = []
if 'logado' not in st.session_state: st.session_state['logado'] = False
if 'usuario' not in st.session_state: st.session_state['usuario'] = ""
if 'cargo' not in st.session_state: st.session_state['cargo'] = ""

# --- ESTILOS VISUAIS ---
def render_logo_svg(width="50px", color="#C57A57"):
    return f'<svg width="{width}" height="{width}" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M30 20 V80 C30 90 40 95 50 85 L80 50 C90 40 80 20 60 20 Z" stroke="{color}" stroke-width="8" fill="none"/><path d="M30 50 L60 20" stroke="{color}" stroke-width="8" stroke-linecap="round"/><circle cx="35" cy="85" r="5" fill="{color}"/></svg>'

def apply_custom_style():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
        .stApp { background-color: #0F172A; }
        .big-font { font-family: 'Inter', sans-serif !important; font-size: 32px !important; font-weight: 600 !important; color: #FFFFFF !important; margin-top: 20px !important; margin-bottom: 20px !important; }
        .card-container { border-radius: 12px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border: 1px solid rgba(255,255,255,0.05); background-color: #1E293B; }
        .card-value { font-size: 28px; font-weight: 700 !important; color: #FFFFFF; }
        .card-label { font-size: 12px; color: #94A3B8; text-transform: uppercase; letter-spacing: 1px; }
        /* Cores dos Cards */
        .border-blue { border-left: 4px solid #3B82F6; }
        .border-green { border-left: 4px solid #10B981; }
        .border-purple { border-left: 4px solid #8B5CF6; }
        .border-orange { border-left: 4px solid #F59E0B; }
    </style>
    """, unsafe_allow_html=True)

apply_custom_style()

# --- FUNÇÃO DE DADOS SEGURA ---
def get_data(endpoint):
    try:
        endpoint = endpoint.strip("/")
        resp = requests.get(f"{API_URL}/{endpoint}/")
        if resp.status_code == 200: return resp.json()
        return []
    except: return []

# --- COMPONENTES VISUAIS ---
def card_metric(label, value, subtext, color_class="border-blue"):
    st.markdown(f"""
    <div class="card-container {color_class}">
        <div class="card-label">{label}</div>
        <div class="card-value">{value}</div>
        <div style="font-size:11px; color:#64748B; margin-top:5px;">{subtext}</div>
    </div>
    """, unsafe_allow_html=True)

def header(titulo): st.markdown(f"<div class='big-font'>{titulo}</div>", unsafe_allow_html=True)

# --- TELA DE LOGIN (COM MODO DIAGNÓSTICO) ---
def tela_login():
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown(f"<div style='display:flex; flex-direction:column; align-items:center;'>{render_logo_svg(width='80px', color='#3B82F6')}<div style='color:white; font-size:24px; font-weight:bold; margin-top:10px'>Decant ERP</div></div>", unsafe_allow_html=True)
        with st.form("login_form"):
            u_input = st.text_input("Usuário", placeholder="admin")
            p_input = st.text_input("Senha", type="password", placeholder="••••••")
            if st.form_submit_button("ENTRAR ACESSO SEGURO"):
                try:
                    res = requests.post(f"{API_URL}/auth/login/", json={"username": u_input, "senha": p_input, "cargo": ""})
                    if res.status_code == 200:
                        data = res.json()
                        st.session_state['logado'] = True; st.session_state['usuario'] = data['usuario']; st.session_state['cargo'] = data['cargo']; st.rerun()
                    else: st.error("Acesso Negado.")
                except Exception as e: st.error(f"Erro de Conexão: {e}")

# --- SISTEMA PRINCIPAL ---
def sistema_erp():
    with st.sidebar:
        st.markdown(f"<div style='display:flex; align-items:center; gap:10px; margin-bottom:20px; padding-left:10px;'>{render_logo_svg(width='28px', color='#3B82F6')}<div style='font-weight:700; color:white;'>Decant Cloud</div></div>", unsafe_allow_html=True)
        menu = [{"l": "Dashboard BI", "i": "graph-up-arrow", "id": "dash"}, {"l": "Frente de Caixa", "i": "basket", "id": "pdv"}, {"l": "Financeiro", "i": "cash-coin", "id": "fin"}, {"l": "CRM / Fidelidade", "i": "heart", "id": "crm"}, {"l": "Produtos", "i": "box-seam", "id": "prod"}, {"l": "Clientes", "i": "people", "id": "cli"}, {"l": "Planejamento", "i": "diagram-3", "id": "mrp"}, {"l": "Compras", "i": "cart", "id": "comp"}, {"l": "Configurações", "i": "gear", "id": "cfg"}]
        sel = option_menu(None, [x["l"] for x in menu], icons=[x["i"] for x in menu], default_index=0, styles={"nav-link-selected": {"background-color": "#3B82F6"}})
        page_id = next(x["id"] for x in menu if x["l"] == sel)
        st.divider()
        st.caption(f"Logado como: {st.session_state['usuario']}")
        if st.button("Sair"): st.session_state['logado'] = False; st.rerun()

    # --- DASHBOARD INTELIGENTE (BI) ---
    if page_id == "dash":
        header("Inteligência de Negócio")
        
        # 1. Carregar Dados
        vendas = get_data("vendas")
        lancamentos = get_data("financeiro/lancamentos")
        prods = get_data("produtos")
        clientes = get_data("clientes")

        # 2. Cálculos de KPI
        receita_total = sum(v['valor_total'] for v in vendas)
        ticket_medio = (receita_total / len(vendas)) if vendas else 0
        lucro_liquido = sum(l['valor'] for l in lancamentos if l['tipo']=='Receita' and l['pago']) - sum(l['valor'] for l in lancamentos if l['tipo']=='Despesa' and l['pago'])
        
        # 3. Cards Superiores
        c1, c2, c3, c4 = st.columns(4)
        with c1: card_metric("Faturamento", f"R$ {receita_total:,.2f}", f"{len(vendas)} Vendas Realizadas", "border-blue")
        with c2: card_metric("Ticket Médio", f"R$ {ticket_medio:,.2f}", "Média por Cliente", "border-purple")
        with c3: card_metric("Lucro Caixa", f"R$ {lucro_liquido:,.2f}", "Receitas - Despesas (Pagas)", "border-green")
        with c4: card_metric("Clientes Ativos", str(len(clientes)), "Base Cadastrada", "border-orange")

        st.markdown("<br>", unsafe_allow_html=True)

        # 4. Gráficos Avançados
        if vendas:
            df_vendas = pd.DataFrame(vendas)
            # Mapa de Produtos (ID -> Nome)
            map_prods = {p['id']: p['nome'] for p in prods}
            df_vendas['Produto'] = df_vendas['produto_id'].map(map_prods)
            
            # Gráfico 1: Top Produtos (Barras)
            top_prods = df_vendas.groupby('Produto')['valor_total'].sum().reset_index().sort_values('valor_total', ascending=False).head(5)
            
            # Gráfico 2: Métodos de Pagamento (Pizza)
            pagamentos = df_vendas.groupby('metodo_pagamento')['valor_total'].sum().reset_index()

            # Layout Gráficos
            g1, g2 = st.columns([1.5, 1])
            with g1:
                st.markdown("##### 🏆 Produtos Mais Vendidos")
                fig_bar = px.bar(top_prods, x='valor_total', y='Produto', orientation='h', text_auto='.2s', color='valor_total', color_continuous_scale='Blues')
                fig_bar.update_layout(paper_bgcolor='#1E293B', plot_bgcolor='#1E293B', font_color='white', xaxis_title="Receita (R$)", yaxis_title="")
                st.plotly_chart(fig_bar, use_container_width=True)
            
            with g2:
                st.markdown("##### 💳 Meios de Pagamento")
                fig_pie = px.pie(pagamentos, values='valor_total', names='metodo_pagamento', hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
                fig_pie.update_layout(paper_bgcolor='#1E293B', font_color='white')
                st.plotly_chart(fig_pie, use_container_width=True)

            # Lista de Últimas Vendas
            st.markdown("##### 🧾 Últimas Transações")
            st.dataframe(df_vendas[['id', 'Produto', 'quantidade', 'valor_total', 'metodo_pagamento']].sort_values('id', ascending=False).head(5), use_container_width=True, hide_index=True)
        
        else:
            st.info("Ainda não há vendas registradas para gerar gráficos.")

    # --- OUTRAS ABAS (Resumidas para manter funcionalidade) ---
    elif page_id == "pdv":
        header("Frente de Caixa")
        clis = get_data("clientes"); prods = get_data("produtos")
        produtos_acabados = [p for p in prods if p['tipo'] == 'Produto Acabado']
        c1, c2 = st.columns([2, 1])
        with c1:
            cli_sel = st.selectbox("Cliente", [c['nome'] for c in clis]) if clis else None
            prod_sel = st.selectbox("Produto", [p['nome'] for p in produtos_acabados]) if produtos_acabados else None
            qtd = st.number_input("Qtd", 1)
            if st.button("Adicionar ao Carrinho"):
                p_obj = next(p for p in produtos_acabados if p['nome'] == prod_sel)
                preco = p_obj['custo'] * 2
                st.session_state['carrinho'].append({"id":p_obj['id'], "nome":p_obj['nome'], "qtd":qtd, "total":qtd*preco})
        with c2:
            st.markdown("### 🛒 Carrinho")
            total = sum(i['total'] for i in st.session_state['carrinho'])
            for i in st.session_state['carrinho']: st.write(f"{i['qtd']}x {i['nome']} - R${i['total']:.2f}")
            st.metric("Total", f"R$ {total:.2f}")
            pag = st.selectbox("Pagamento", ["Pix", "Crédito", "Débito"])
            if st.button("FINALIZAR VENDA", type="primary"):
                cid = next(c['id'] for c in clis if c['nome'] == cli_sel)
                payload = {"cliente_id": cid, "itens": [{"produto_id": i['id'], "quantidade": i['qtd'], "valor_total": i['total']} for i in st.session_state['carrinho']], "metodo_pagamento": pag}
                requests.post(f"{API_URL}/vendas/pdv/", json=payload)
                st.session_state['carrinho'] = []; st.success("Venda OK!"); time.sleep(1); st.rerun()

    elif page_id == "crm":
        header("CRM & Clientes")
        ops = get_data("crm/oportunidades")
        if ops:
            for op in ops:
                st.warning(f"🔔 {op['Cliente']} comprou {op['Último Produto']} há {op['Dias sem Comprar']} dias.")
                st.link_button("Chamar no WhatsApp", f"https://wa.me/55?text=Ola", type="primary")
        else: st.success("Todos os clientes compraram recentemente!")

    elif page_id == "fin":
        header("Financeiro")
        t1, t2 = st.tabs(["Lançar", "Extrato"])
        with t1:
            with st.form("fin"):
                d = st.text_input("Descrição"); v = st.number_input("Valor"); t = st.selectbox("Tipo", ["Receita","Despesa"]); dt = st.date_input("Data")
                if st.form_submit_button("Salvar"):
                    requests.post(f"{API_URL}/financeiro/lancamento/", json={"descricao":d,"tipo":t,"categoria":"Geral","valor":v,"data_vencimento":str(dt),"pago":True})
                    st.success("Salvo!")
        with t2:
            l = get_data("financeiro/lancamentos")
            if l: st.dataframe(pd.DataFrame(l)[['descricao','valor','tipo','data_vencimento']], use_container_width=True)

    elif page_id == "prod":
        header("Produtos")
        p = get_data("produtos")
        if p: st.dataframe(pd.DataFrame(p), use_container_width=True)
    
    elif page_id == "cli":
        header("Clientes")
        with st.form("nc"):
            n = st.text_input("Nome"); e = st.text_input("Email"); t = st.text_input("Tel")
            if st.form_submit_button("Cadastrar"): requests.post(f"{API_URL}/clientes/", json={"nome":n,"email":e,"telefone":t}); st.success("OK")
        c = get_data("clientes")
        if c: st.dataframe(pd.DataFrame(c), use_container_width=True)

if st.session_state['logado']: sistema_erp()
else: tela_login()