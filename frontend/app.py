import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from streamlit_option_menu import option_menu
from datetime import datetime, date
import os
import time

# --- CONFIGURAÇÃO MANUAL (LINK DO SEU BACKEND) ---
API_URL = "https://api-decant-oficial.onrender.com"

print(f"🔗 CONECTANDO O ERP EM: {API_URL}")

st.set_page_config(page_title="Decant ERP", page_icon="💧", layout="wide")

if 'carrinho' not in st.session_state: st.session_state['carrinho'] = []
if 'logado' not in st.session_state: st.session_state['logado'] = False
if 'usuario' not in st.session_state: st.session_state['usuario'] = ""
if 'cargo' not in st.session_state: st.session_state['cargo'] = ""

def apply_custom_style():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
        .stApp { background-color: #0F172A; }
        .big-font { font-family: 'Inter', sans-serif !important; font-size: 36px !important; font-weight: 600 !important; color: #FFFFFF !important; margin-top: 40px !important; margin-bottom: 20px !important; line-height: 1.2 !important; }
        .card-container { border-radius: 12px; padding: 24px; margin-bottom: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border: 1px solid rgba(255,255,255,0.05); }
        .card-blue { background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%); border-top: 4px solid #3B82F6; color: white; }
        .card-green { background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%); border-top: 4px solid #10B981; color: white; }
        .card-purple { background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%); border-top: 4px solid #8B5CF6; color: white; }
        .card-red { background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%); border-top: 4px solid #EF4444; color: white; }
        .card-title { font-size: 13px !important; font-weight: 600 !important; color: #94A3B8 !important; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }
        .card-value { font-size: 32px; font-weight: 700 !important; color: #FFFFFF; margin-top: 0px; }
        div[data-testid="stSidebar"] { background-color: #0F172A; border-right: 1px solid #1E293B; }
        .sales-box { background-color: #1E293B; border-radius: 12px; padding: 20px; height: 380px; overflow-y: auto; border: 1px solid #334155; }
        .sales-row { display: flex; align-items: center; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid #334155; }
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

def card_html(titulo, valor, subtexto, cor="card-blue"): 
    st.markdown(f"<div class='card-container {cor}'><div class='card-title'>{titulo}</div><div class='card-value'>{valor}</div><div style='font-size:12px; margin-top:10px; opacity:0.8'>{subtexto}</div></div>", unsafe_allow_html=True)

def header(titulo): st.markdown(f"<div class='big-font'>{titulo}</div>", unsafe_allow_html=True)

def tela_login():
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.markdown("<br><br><h2 style='text-align:center; color:white'>Decant ERP</h2>", unsafe_allow_html=True)
        with st.form("login_form"):
            u = st.text_input("Usuário"); p = st.text_input("Senha", type="password")
            if st.form_submit_button("ENTRAR"):
                try:
                    res = requests.post(f"{API_URL}/auth/login/", json={"username": u, "senha": p, "cargo": ""})
                    if res.status_code == 200:
                        data = res.json(); st.session_state['logado'] = True; st.session_state['usuario'] = data['usuario']; st.session_state['cargo'] = data['cargo']; st.rerun()
                    else: st.error("Erro Login")
                except: st.error("Erro Conexão")

def sistema_erp():
    with st.sidebar:
        st.markdown("<h3 style='color:white; text-align:center'>Decant</h3>", unsafe_allow_html=True)
        menu = [{"l": "Visão Geral", "i": "grid", "id": "dash"}, {"l": "PDV (Caixa)", "i": "basket", "id": "pdv"}, {"l": "Financeiro", "i": "cash-coin", "id": "fin"}, {"l": "CRM", "i": "heart", "id": "crm"}, {"l": "Produtos", "i": "box-seam", "id": "prod"}, {"l": "Clientes", "i": "people", "id": "cli"}, {"l": "Fornecedores", "i": "truck", "id": "forn"}, {"l": "Engenharia", "i": "tools", "id": "eng"}, {"l": "Planejamento", "i": "diagram-3", "id": "mrp"}, {"l": "Compras", "i": "cart", "id": "comp"}, {"l": "Produção", "i": "gear-wide-connected", "id": "fab"}, {"l": "Relatórios", "i": "bar-chart-line", "id": "rel"}, {"l": "Config", "i": "gear", "id": "cfg"}]
        sel = option_menu(None, [x["l"] for x in menu], icons=[x["i"] for x in menu], default_index=0)
        page_id = next(x["id"] for x in menu if x["l"] == sel)
        if st.button("Sair"): st.session_state['logado'] = False; st.rerun()

    if page_id == "dash":
        header("Visão Geral")
        vendas = get_data("vendas"); prods = get_data("produtos"); clis = get_data("clientes"); lancamentos = get_data("financeiro/lancamentos")
        receita = sum(v['valor_total'] for v in vendas); ticket = (receita / len(vendas)) if vendas else 0
        lucro = receita - sum(l['valor'] for l in lancamentos if l['tipo'] == "Despesa" and l['pago'])
        
        c1, c2, c3, c4 = st.columns(4)
        with c1: card_html("RECEITA", f"R$ {receita:,.2f}", "Total", "card-blue")
        with c2: card_html("LUCRO", f"R$ {lucro:,.2f}", "Real", "card-green")
        with c3: card_html("TICKET MÉDIO", f"R$ {ticket:,.2f}", "Por Venda", "card-purple")
        with c4: card_html("CLIENTES", str(len(clis)), "Ativos", "card-red")
        
        if vendas and prods:
            df = pd.DataFrame(vendas); map_p = {p['id']: p['nome'] for p in prods}
            df['Produto'] = df['produto_id'].map(map_p)
            st.markdown("<br>", unsafe_allow_html=True)
            g1, g2 = st.columns([1.5, 1])
            with g1:
                top = df.groupby('Produto')['valor_total'].sum().reset_index().sort_values('valor_total', ascending=False).head(5)
                fig = px.bar(top, x='valor_total', y='Produto', orientation='h', color='valor_total', color_continuous_scale='Blues'); st.plotly_chart(fig, use_container_width=True)
            with g2:
                pg = df.groupby('metodo_pagamento')['valor_total'].sum().reset_index()
                fig2 = px.pie(pg, values='valor_total', names='metodo_pagamento', hole=0.4); st.plotly_chart(fig2, use_container_width=True)

    elif page_id == "prod":
        header("Produtos"); prods = get_data("produtos")
        t1, t2, t3 = st.tabs(["Estoque", "Kardex", "Novo"])
        with t1: st.dataframe(pd.DataFrame(prods), use_container_width=True) if prods else st.info("Vazio")
        with t2: st.dataframe(pd.DataFrame(get_data("estoque/kardex")), use_container_width=True)
        with t3:
            with st.form("np"):
                n = st.text_input("Nome"); t = st.selectbox("Tipo", ["Materia Prima", "Produto Acabado"]); e = st.number_input("Estoque"); c = st.number_input("Custo")
                if st.form_submit_button("Salvar"): requests.post(f"{API_URL}/produtos/", json={"nome":n,"tipo":t,"unidade":"Un","estoque_atual":e,"custo":c}); st.success("OK"); st.rerun()

    elif page_id == "eng":
        header("Engenharia (Fórmulas)"); prods = get_data("produtos")
        c1, c2 = st.columns([1, 2])
        with c1:
            with st.form("nf"):
                nm = st.text_input("Nome da Fórmula"); pf = st.selectbox("Produto Final", [p['nome'] for p in prods if p['tipo'] == 'Produto Acabado'])
                if st.form_submit_button("Criar Fórmula"): 
                    pid = next(p['id'] for p in prods if p['nome'] == pf)
                    requests.post(f"{API_URL}/formulas/", json={"nome":nm,"produto_final_id":pid}); st.success("Criada!")
        with c2:
            forms = get_data("formulas")
            if forms:
                f_sel = st.selectbox("Selecione a Fórmula", [f['nome'] for f in forms])
                fid = next(f['id'] for f in forms if f['nome'] == f_sel)
                res = requests.post(f"{API_URL}/planejamento/calcular/?formula_id={fid}&quantidade_producao=1").json()
                if res.get('materiais'): st.dataframe(pd.DataFrame(res['materiais'])[['ingrediente', 'necessario', 'custo_unit']], use_container_width=True)
                with st.form("add_item"):
                    mp = st.selectbox("Adicionar MP", [p['nome'] for p in prods if p['tipo'] == 'Materia Prima'])
                    q = st.number_input("Quantidade"); 
                    if st.form_submit_button("Adicionar"):
                        mid = next(p['id'] for p in prods if p['nome'] == mp)
                        requests.post(f"{API_URL}/formulas/itens/", json={"formula_id":fid,"materia_prima_id":mid,"quantidade":q}); st.rerun()

    elif page_id == "mrp":
        header("Planejamento (MRP)"); forms = get_data("formulas")
        if forms:
            f = st.selectbox("Fórmula", [x['nome'] for x in forms]); q = st.number_input("Qtd a Produzir", 10.0)
            if st.button("Calcular Necessidade"):
                fid = next(x['id'] for x in forms if x['nome']==f)
                res = requests.post(f"{API_URL}/planejamento/calcular/?formula_id={fid}&quantidade_producao={q}").json()
                st.write(f"Custo Estimado: R$ {res['custo_total']:.2f}")
                st.dataframe(pd.DataFrame(res['materiais']), use_container_width=True)
        else: st.warning("Cadastre fórmulas na Engenharia primeiro.")

    elif page_id == "fab":
        header("Chão de Fábrica"); forms = get_data("formulas")
        if forms:
            st.markdown("##### Registrar Produção")
            with st.form("reg_prod"):
                f = st.selectbox("O que foi produzido?", [x['nome'] for x in forms])
                q = st.number_input("Quantidade Real", 1.0)
                l = st.text_input("Lote Gerado", f"L{datetime.now().strftime('%m%d')}")
                v = st.date_input("Validade")
                if st.form_submit_button("Confirmar Produção"):
                    fid = next(x['id'] for x in forms if x['nome']==f)
                    requests.post(f"{API_URL}/producao/confirmar_lote/", json={"formula_id":fid,"quantidade":q,"lote_final":l,"validade_final":str(v)})
                    st.success("Estoque Atualizado!"); st.rerun()
            st.divider(); st.markdown("**Histórico de Produção**")
            ops = get_data("producao/historico/")
            if ops: st.dataframe(pd.DataFrame(ops), use_container_width=True)
        else: st.warning("Necessário cadastrar fórmulas na Engenharia.")

    elif page_id == "rel":
        header("Relatórios"); t1, t2 = st.tabs(["Estoque", "Lotes"])
        with t1: 
             d = get_data("relatorios/estoque/")
             if d: st.dataframe(pd.DataFrame(d['itens']), use_container_width=True)
        with t2: st.dataframe(pd.DataFrame(get_data("relatorios/lotes_vencimento/")), use_container_width=True)

    # (Abas restantes resumidas)
    elif page_id == "pdv":
        header("PDV"); clis = get_data("clientes"); prods = get_data("produtos"); pas = [p for p in prods if p['tipo'] == 'Produto Acabado']
        c1, c2 = st.columns([2,1])
        with c1:
            c = st.selectbox("Cliente", [x['nome'] for x in clis]) if clis else None
            p = st.selectbox("Produto", [x['nome'] for x in pas]) if pas else None
            q = st.number_input("Qtd", 1)
            if st.button("Add"): 
                obj = next(x for x in pas if x['nome']==p); pr = obj['custo']*2
                st.session_state['carrinho'].append({"id":obj['id'],"nome":obj['nome'],"qtd":q,"total":q*pr})
        with c2:
            st.write(pd.DataFrame(st.session_state['carrinho'])); 
            if st.button("Finalizar"): 
                cid = next(x['id'] for x in clis if x['nome']==c)
                requests.post(f"{API_URL}/vendas/pdv/", json={"cliente_id":cid,"itens":[{"produto_id":i['id'],"quantidade":i['qtd'],"valor_total":i['total']} for i in st.session_state['carrinho']],"metodo_pagamento":"Pix"})
                st.session_state['carrinho']=[]; st.success("Venda OK")

    elif page_id == "cli":
        header("Clientes"); 
        with st.form("nc"): 
            n=st.text_input("Nome"); e=st.text_input("Email"); 
            if st.form_submit_button("Salvar"): requests.post(f"{API_URL}/clientes/", json={"nome":n,"email":e,"telefone":""}); st.rerun()
        st.dataframe(pd.DataFrame(get_data("clientes")), use_container_width=True)
    elif page_id == "crm": header("CRM"); st.dataframe(pd.DataFrame(get_data("crm/oportunidades")))
    elif page_id == "fin": header("Financeiro"); st.dataframe(pd.DataFrame(get_data("financeiro/lancamentos")))
    elif page_id == "comp": header("Compras"); st.dataframe(pd.DataFrame(get_data("compras")))
    elif page_id == "forn": header("Fornecedores"); st.dataframe(pd.DataFrame(get_data("fornecedores")))
    elif page_id == "cfg": header("Config"); st.button("Resetar Dados", on_click=lambda: requests.delete(f"{API_URL}/sistema/resetar_dados/"))

if st.session_state['logado']: sistema_erp()
else: tela_login()