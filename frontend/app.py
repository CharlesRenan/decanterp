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

def render_logo_svg(width="50px", color="#C57A57"):
    return f'<svg width="{width}" height="{width}" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M30 20 V80 C30 90 40 95 50 85 L80 50 C90 40 80 20 60 20 Z" stroke="{color}" stroke-width="8" fill="none"/><path d="M30 50 L60 20" stroke="{color}" stroke-width="8" stroke-linecap="round"/><circle cx="35" cy="85" r="5" fill="{color}"/></svg>'

def apply_custom_style():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
        .stApp { background-color: #0F172A; }
        .big-font { font-family: 'Inter', sans-serif !important; font-size: 36px !important; font-weight: 600 !important; color: #FFFFFF !important; margin-top: 40px !important; margin-bottom: 20px !important; line-height: 1.2 !important; }
        
        .card-container { border-radius: 12px; padding: 24px; margin-bottom: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .card-blue { background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%); border: 1px solid #3B82F6; color: white; }
        .card-red { background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%); border: 1px solid #EF4444; color: white; }
        .card-green { background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%); border: 1px solid #10B981; color: white; }
        .card-dark { background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%); border: 1px solid #F59E0B; color: white; }
        .card-title { font-size: 13px !important; font-weight: 600 !important; color: #94A3B8 !important; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }
        .card-value { font-size: 32px; font-weight: 700 !important; color: #FFFFFF; margin-top: 0px; }
        
        div[data-testid="stSidebar"] { background-color: #0F172A; border-right: 1px solid #1E293B; }
        div[data-testid="stForm"] input { background-color: #1E293B !important; border: 1px solid #334155 !important; color: white; }
        div[data-testid="stFormSubmitButton"] button { background: linear-gradient(90deg, #3B82F6 0%, #2563EB 100%) !important; color: white !important; border: none; }
        
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #1E293B;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 20px;
        }
        
        .sales-row { display: flex; align-items: center; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid #334155; }
        .sales-row:last-child { border-bottom: none; }
        .sales-left { display: flex; align-items: center; gap: 12px; }
        .avatar-circle { width: 40px; height: 40px; border-radius: 10px; background-color: #3B82F6; color: #FFFFFF; display: flex; align-items: center; justify-content: center; font-weight: 700; }
        .client-name { font-size: 14px; color: white; font-weight: 600; }
        .client-sub { font-size: 12px; color: #94A3B8; }
        .sales-val { font-size: 14px; color: white; font-weight: 700; }
        .sales-badge { font-size: 11px; padding: 2px 8px; border-radius: 12px; margin-top: 4px; display: inline-block; font-weight: 600; }
        .badge-green { background-color: rgba(16, 185, 129, 0.2); color: #34D399; }
        
        div[data-testid="stHorizontalBlock"] button[kind="secondary"] { border: 1px solid #EF4444 !important; background-color: rgba(239, 68, 68, 0.1) !important; color: #EF4444 !important; }
        div[data-testid="stHorizontalBlock"] button[kind="secondary"]:hover { background-color: #EF4444 !important; color: white !important; }
        
        div[data-testid="stNumberInput"] input { min-height: 30px; padding: 5px; font-size: 14px; }
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
                sucesso = False; mensagem_erro = ""
                with st.spinner("Conectando ao sistema..."):
                    for tentativa in range(1, 4):
                        try:
                            res = requests.post(f"{API_URL}/auth/login/", json={"username": u_input, "senha": p_input, "cargo": ""}, timeout=10)
                            if res.status_code == 200: sucesso = True; break
                            else: mensagem_erro = "Credenciais Inválidas"; break
                        except:
                            if tentativa < 3: time.sleep(3)
                            else: mensagem_erro = "Servidor Offline."
                if sucesso:
                    data = res.json(); st.session_state['logado'] = True; st.session_state['usuario'] = data['usuario']; st.session_state['cargo'] = data['cargo']; st.success("Login OK!"); time.sleep(0.5); st.rerun()
                else: st.error(mensagem_erro)

def sistema_erp():
    with st.sidebar:
        logo_path = "frontend/logo.png"
        if os.path.exists(logo_path): st.markdown("<div style='margin-bottom: 25px; text-align: center;'>", unsafe_allow_html=True); st.image(logo_path, width=160); st.markdown("</div>", unsafe_allow_html=True)
        else: st.markdown(f"<div style='display:flex; align-items:center; gap:12px; margin-bottom:30px; padding-left:10px;'>{render_logo_svg(width='32px', color='#3B82F6')}<div style='font-family:Inter; font-weight:700; font-size:20px; color:white;'>Decant</div></div>", unsafe_allow_html=True)
        menu = [{"l": "Visão Geral", "i": "grid", "id": "dash"}, {"l": "PDV (Caixa)", "i": "basket", "id": "pdv"}, {"l": "Financeiro", "i": "cash-coin", "id": "fin"}, {"l": "CRM / Fidelidade", "i": "heart", "id": "crm"}, {"l": "Produtos", "i": "box-seam", "id": "prod"}, {"l": "Clientes", "i": "people", "id": "cli"}, {"l": "Fornecedores", "i": "truck", "id": "forn"}, {"l": "Preços", "i": "tags", "id": "prec"}, {"l": "Engenharia", "i": "tools", "id": "eng"}, {"l": "Planejamento", "i": "diagram-3", "id": "mrp"}, {"l": "Compras", "i": "cart", "id": "comp"}, {"l": "Produção", "i": "gear-wide-connected", "id": "fab"}, {"l": "Vendas (Adm)", "i": "graph-up-arrow", "id": "vend"}, {"l": "Relatórios", "i": "bar-chart-line", "id": "rel"}, {"l": "Configurações", "i": "gear", "id": "cfg"}]
        sel = option_menu(None, [x["l"] for x in menu], icons=[x["i"] for x in menu], default_index=0, styles={"container": {"padding": "0!important", "background-color": "transparent"},"icon": {"color": "#94A3B8", "font-size": "14px"}, "nav-link": {"font-family":"Inter", "font-weight":"500", "font-size": "14px", "text-align": "left", "margin":"5px", "--hover-color": "#1E293B", "color": "#E2E8F0"},"nav-link-selected": {"background-color": "#3B82F6", "color": "#FFFFFF", "font-weight": "600"}})
        page_id = next(x["id"] for x in menu if x["l"] == sel)
        st.markdown("<div style='margin-top: 40px'></div>", unsafe_allow_html=True)
        if st.button("Sair"): st.session_state['logado'] = False; st.rerun()

    if page_id == "dash":
        header("Visão Geral")
        d = get_data("financeiro/dashboard"); vendas = get_data("vendas"); clientes = get_data("clientes"); prods = get_data("produtos")

        c1, c2, c3, c4 = st.columns(4)
        with c1: card_html("RECEITA TOTAL", f"R$ {d.get('receita', 0):,.2f}", "Vendas + Extras", "card-blue")
        with c2: card_html("DESPESAS TOTAIS", f"R$ {d.get('despesas', 0):,.2f}", "MP + Contas Fixas", "card-red")
        with c3: card_html("LUCRO LÍQUIDO", f"R$ {d.get('lucro', 0):,.2f}", f"Margem Real: {d.get('margem', 0):.1f}%", "card-green")
        with c4: card_html("SISTEMA", "Online", "v2.0 CRM", "card-dark")
        
        st.markdown("<br>", unsafe_allow_html=True)
        c_graf, c_vendas, c_meta = st.columns([1.2, 1, 0.8])
        
        with c_graf:
            with st.container(border=True): 
                st.markdown("##### Fluxo de Caixa")
                dados = d.get('grafico', [])
                if dados: fig = px.bar(pd.DataFrame(dados), x="Mês", y="Valor", color="Tipo", barmode='group', color_discrete_map={'Entradas': '#10B981', 'Saídas': '#3B82F6'})
                else: fig = px.bar(pd.DataFrame([{"Mês":"Jan","Valor":0,"Tipo":"Entradas"}]), x="Mês", y="Valor")
                fig.update_layout(paper_bgcolor='#1E293B', plot_bgcolor='#1E293B', font_color='#94A3B8', xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#334155'), legend=dict(orientation="h", y=1.1), margin=dict(l=0, r=0, t=0, b=0), height=300)
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

        with c_vendas:
            with st.container(border=True):
                st.markdown("##### Últimas Vendas")
                map_clientes = {c['id']: c for c in clientes}
                rows_html = ""
                for v in vendas[:5]:
                    cli = map_clientes.get(v['cliente_id'], {'nome': 'Cliente', 'email': '-'})
                    rows_html += get_sales_row_html(cli['nome'], cli['email'], v['valor_total'])
                st.markdown(f"<div style='height: 300px; overflow-y: auto;'>{rows_html}</div>", unsafe_allow_html=True)

        with c_meta:
            with st.container(border=True):
                st.markdown("##### 🎯 Meta Mensal")
                receita_atual = d.get('receita', 0)
                fig_gauge = go.Figure(go.Indicator(
                    mode = "gauge+number+delta",
                    value = receita_atual,
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    title = {'text': "Alvo: R$ 10k"},
                    delta = {'reference': 10000},
                    gauge = {'axis': {'range': [None, 10000]}, 'bar': {'color': "#3B82F6"}, 'steps': [{'range': [0, 5000], 'color': "#1E293B"}, {'range': [5000, 10000], 'color': "#334155"}]}
                ))
                fig_gauge.update_layout(paper_bgcolor='#1E293B', font={'color': "white", 'family': "Inter"}, margin=dict(t=30,b=10,l=20,r=20), height=300)
                st.plotly_chart(fig_gauge, use_container_width=True)

        if vendas and prods:
            st.markdown("<br>", unsafe_allow_html=True)
            df_vendas = pd.DataFrame(vendas)
            map_prods = {p['id']: p['nome'] for p in prods}
            df_vendas['Produto'] = df_vendas['produto_id'].map(map_prods)
            g1, g2 = st.columns([1.5, 1])
            with g1:
                with st.container(border=True):
                    st.markdown("##### 🏆 Produtos Mais Vendidos")
                    top_prods = df_vendas.groupby('Produto')['valor_total'].sum().reset_index().sort_values('valor_total', ascending=False).head(5)
                    fig_bar = px.bar(top_prods, x='valor_total', y='Produto', orientation='h', text_auto='.2s', color='valor_total', color_continuous_scale='Blues')
                    fig_bar.update_layout(paper_bgcolor='#1E293B', plot_bgcolor='#1E293B', font_color='white', xaxis_title="", yaxis_title="", margin=dict(t=10, b=10), height=280)
                    st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})
            with g2:
                with st.container(border=True):
                    st.markdown("##### 💳 Meios de Pagamento")
                    pg = df_vendas.groupby('metodo_pagamento')['valor_total'].sum().reset_index()
                    fig_pie = px.pie(pg, values='valor_total', names='metodo_pagamento', hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
                    fig_pie.update_layout(paper_bgcolor='#1E293B', font_color='white', margin=dict(t=10, b=10), height=280)
                    st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})

    elif page_id == "pdv":
        header("Frente de Caixa (PDV)"); clis = get_data("clientes"); prods = get_data("produtos"); pas = [p for p in prods if p['tipo'] == 'Produto Acabado']
        c1, c2 = st.columns([1.5, 1])
        with c1:
            st.markdown("##### 🛒 Adicionar Itens")
            lista_clientes = [c['nome'] for c in clis] if clis else []
            cli_sel = st.selectbox("👤 Cliente", lista_clientes) if lista_clientes else None
            if not lista_clientes: st.warning("Cadastre um cliente na aba 'Clientes' primeiro.")
            
            with st.container(border=True):
                k1, k2 = st.columns([3, 1]); p = k1.selectbox("Produto", [x['nome'] for x in pas]) if pas else None; q = k2.number_input("Qtd", 1.0)
                if st.button("Adicionar Item", use_container_width=True): 
                    obj = next(x for x in pas if x['nome']==p); pr = obj['custo']*2; 
                    st.session_state['carrinho'].append({"id":obj['id'],"nome":obj['nome'],"qtd":q,"total":q*pr, "custo": obj['custo'], "preco_unitario": pr}); st.rerun()
        
        with c2:
            st.markdown("##### 🧾 Cupom & Lucro")
            if st.session_state['carrinho']:
                with st.container(border=True):
                    for i, item in enumerate(st.session_state['carrinho']):
                        col_nome, col_qtd, col_val, col_del = st.columns([3, 1.5, 1.5, 0.8])
                        col_nome.write(f"**{item['nome']}**")
                        nova_qtd = col_qtd.number_input("Qtd", min_value=1.0, value=float(item['qtd']), key=f"qtd_{i}", label_visibility="collapsed")
                        if nova_qtd != item['qtd']:
                            st.session_state['carrinho'][i]['qtd'] = nova_qtd
                            st.session_state['carrinho'][i]['total'] = nova_qtd * item['preco_unitario']
                            st.rerun()
                        col_val.write(f"R${item['total']:.0f}")
                        if col_del.button("🗑️", key=f"del_{i}"):
                            st.session_state['carrinho'].pop(i)
                            st.rerun()
                            
                total_venda = sum(item['total'] for item in st.session_state['carrinho'])
                custo_venda = sum(item['custo'] * item['qtd'] for item in st.session_state['carrinho'])
                lucro = total_venda - custo_venda
                margem = (lucro / total_venda * 100) if total_venda > 0 else 0
                st.divider()
                col_lucro, col_margem = st.columns(2)
                col_lucro.metric("Lucro Previsto", f"R$ {lucro:.2f}")
                col_margem.metric("Margem", f"{margem:.1f}%")
                st.progress(min(int(margem), 100))
                if st.button("✅ FINALIZAR VENDA", type="primary", use_container_width=True): 
                    if cli_sel:
                        cid = next(x['id'] for x in clis if x['nome']==cli_sel)
                        requests.post(f"{API_URL}/vendas/pdv/", json={"cliente_id":cid,"itens":[{"produto_id":i['id'],"quantidade":i['qtd'],"valor_total":i['total']} for i in st.session_state['carrinho']],"metodo_pagamento":"Pix"})
                        st.session_state['carrinho']=[]; st.success("Venda Realizada!"); time.sleep(1); st.rerun()
                    else: st.error("Selecione um cliente!")
            else: st.info("O carrinho está vazio.")

    elif page_id == "cli":
        header("Clientes")
        c1, c2 = st.columns([1, 2])
        with c1:
            st.markdown("##### Novo Cliente")
            with st.form("new_cli"):
                n = st.text_input("Nome"); e = st.text_input("Email"); t = st.text_input("Telefone")
                if st.form_submit_button("Cadastrar"):
                    requests.post(f"{API_URL}/clientes/", json={"nome":n, "email":e, "telefone":t}); st.success("Cliente cadastrado!"); time.sleep(1); st.rerun()
        with c2:
            st.markdown("##### Lista de Clientes")
            clis = get_data("clientes")
            if clis: st.dataframe(pd.DataFrame(clis)[['id','nome','email','telefone']], use_container_width=True, hide_index=True)
            else: st.info("Nenhum cliente cadastrado.")

    elif page_id == "fin":
        header("Gestão Financeira")
        t1, t2 = st.tabs(["📝 Novo Lançamento", "📜 Contas"])
        with t1:
            with st.form("frm_fin"):
                c1, c2 = st.columns(2); desc = c1.text_input("Descrição"); tipo = c2.selectbox("Tipo", ["Despesa", "Receita"])
                c3, c4 = st.columns(2); valor = c3.number_input("Valor (R$)", min_value=0.01); cat = c4.selectbox("Categoria", ["Custos Fixos", "Despesa Variável", "Impostos", "Receita Extra", "Investimento"])
                c5, c6 = st.columns(2); dt_venc = c5.date_input("Vencimento"); pago = c6.checkbox("Já foi pago?")
                if st.form_submit_button("Salvar Lançamento"):
                    requests.post(f"{API_URL}/financeiro/lancamento/", json={"descricao": desc, "tipo": tipo, "categoria": cat, "valor": valor, "data_vencimento": str(dt_venc), "pago": pago}); st.success("Lançado!"); st.rerun()
        with t2:
            lancamentos = get_data("financeiro/lancamentos")
            if lancamentos: st.dataframe(pd.DataFrame(lancamentos), use_container_width=True)

    elif page_id == "forn":
        header("Fornecedores")
        with st.form("nf"):
            n = st.text_input("Empresa"); p = st.number_input("Prazo Entrega (dias)", 1)
            if st.form_submit_button("Salvar"): requests.post(f"{API_URL}/fornecedores/", json={"nome":n,"prazo_entrega_dias":p}); st.success("OK"); st.rerun()
        st.divider()
        st.dataframe(pd.DataFrame(get_data("fornecedores")), use_container_width=True)

    elif page_id == "prod": 
        header("Produtos"); prods = get_data("produtos"); t1, t2, t3 = st.tabs(["Estoque", "Kardex", "Novo"])
        with t1: st.dataframe(pd.DataFrame(prods), use_container_width=True)
        with t2: st.dataframe(pd.DataFrame(get_data("estoque/kardex")), use_container_width=True)
        with t3:
            with st.form("np"):
                n = st.text_input("Nome"); t = st.selectbox("Tipo", ["Materia Prima", "Produto Acabado"]); e = st.number_input("Estoque"); c = st.number_input("Custo")
                loc = st.text_input("Localização Física", placeholder="Ex: Corredor A, Prateleira 2")
                if st.form_submit_button("Salvar"): requests.post(f"{API_URL}/produtos/", json={"nome":n,"tipo":t,"unidade":"Un","estoque_atual":e,"custo":c, "localizacao": loc}); st.success("Salvo!"); st.rerun()

    elif page_id == "fab": header("Chão de Fábrica"); st.info("Use o app para registrar produção."); st.dataframe(pd.DataFrame(get_data("producao/historico/")), use_container_width=True)
    
    # --- ABA RELATÓRIOS TURBINADA (NOVO!) ---
    elif page_id == "rel": 
        header("Relatórios de Inteligência")
        
        # Filtro de Data Global para a aba
        c1, c2 = st.columns(2)
        ini = c1.date_input("Data Início", value=date.today().replace(day=1))
        fim = c2.date_input("Data Fim", value=date.today())
        
        t1, t2, t3 = st.tabs(["📊 DRE Gerencial", "📄 Relatórios PDF", "📦 Estoque & Lotes"])
        
        # 1. DRE (Calculado na hora)
        with t1:
            if st.button("Gerar DRE"):
                # Chama o backend para calcular
                dre = requests.get(f"{API_URL}/relatorios/dre?inicio={ini}&fim={fim}").json()
                
                # Visualização em Cascata (Waterfall)
                fig = go.Figure(go.Waterfall(
                    name = "20", orientation = "v", measure = ["relative", "relative", "total", "relative", "total", "relative", "total"],
                    x = ["Receita Bruta", "Impostos", "Receita Líquida", "Custos Variáveis", "Margem Contrib.", "Despesas Fixas", "Lucro Líquido"],
                    textposition = "outside",
                    text = [f"{dre['receita_bruta']}", f"-{dre['impostos']}", f"{dre['receita_liquida']}", f"-{dre['custos_variaveis']}", f"{dre['margem_contribuicao']}", f"-{dre['despesas_fixas']}", f"{dre['lucro_liquido']}"],
                    y = [dre['receita_bruta'], -dre['impostos'], dre['receita_liquida'], -dre['custos_variaveis'], dre['margem_contribuicao'], -dre['despesas_fixas'], dre['lucro_liquido']],
                    connector = {"line":{"color":"rgb(63, 63, 63)"}},
                ))
                fig.update_layout(title = "Demonstrativo de Resultado (DRE)", showlegend = False, paper_bgcolor='#1E293B', plot_bgcolor='#1E293B', font={'color': "white"})
                st.plotly_chart(fig, use_container_width=True)
                
                # Tabela detalhada
                st.markdown("### Detalhamento")
                st.dataframe(pd.DataFrame([dre]).T.rename(columns={0: "Valor (R$)"}), use_container_width=True)

        # 2. PDFs Oficiais
        with t2:
            st.markdown("##### Baixar Relatórios Oficiais")
            c_pdf1, c_pdf2 = st.columns(2)
            
            with c_pdf1:
                st.info("📄 Relatório de Vendas")
                if st.button("Baixar PDF Vendas"):
                    pdf = requests.get(f"{API_URL}/relatorios/vendas_pdf?inicio={ini}&fim={fim}")
                    if pdf.status_code == 200:
                        st.download_button("⬇️ Salvar Arquivo", pdf.content, "vendas.pdf", "application/pdf")
                    else:
                        st.error("Erro ao gerar PDF")

            with c_pdf2:
                st.info("📦 Estoque Valorado")
                if st.button("Baixar PDF Estoque"):
                    pdf = requests.get(f"{API_URL}/relatorios/estoque_pdf")
                    if pdf.status_code == 200:
                        st.download_button("⬇️ Salvar Arquivo", pdf.content, "estoque_valorado.pdf", "application/pdf")
                    else:
                        st.error("Erro ao gerar PDF")

        # 3. Estoque Simples (Antigo)
        with t3: 
             d = get_data("relatorios/estoque/")
             if d: st.dataframe(pd.DataFrame(d['itens']), use_container_width=True)
    # ----------------------------------------

    elif page_id == "mrp": header("Planejamento"); st.warning("Cadastre fórmulas na engenharia.")
    elif page_id == "eng": header("Engenharia"); st.info("Cadastro de fórmulas.")
    elif page_id == "comp": header("Compras"); st.dataframe(pd.DataFrame(get_data("compras")))
    elif page_id == "prec": header("Preços"); st.dataframe(pd.DataFrame(get_data("cotacoes")))
    elif page_id == "vend": header("Vendas"); st.dataframe(pd.DataFrame(get_data("vendas")))
    
    elif page_id == "cfg": 
        header("Configurações")
        st.warning("⚠️ Atenção: Esta ação apagará TODOS os dados para atualizar o banco de dados.")
        if st.button("🗑️ RESETAR SISTEMA AGORA", type="primary"):
            try:
                with st.spinner("Apagando dados e recriando tabelas..."):
                    res = requests.delete(f"{API_URL}/sistema/resetar_dados/")
                    if res.status_code == 200: st.success("✅ Sistema resetado com sucesso!"); time.sleep(2); st.rerun()
                    else: st.error(f"Erro ao resetar: {res.text}")
            except Exception as e: st.error(f"Erro de conexão: {e}")

if st.session_state['logado']: sistema_erp()
else: tela_login()