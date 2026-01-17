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
        .card-container { border-radius: 12px; padding: 24px; margin-bottom: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border: 1px solid rgba(255,255,255,0.05); }
        .card-blue { background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%); border-top: 4px solid #3B82F6; color: white; }
        .card-red { background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%); border-top: 4px solid #EF4444; color: white; }
        .card-green { background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%); border-top: 4px solid #10B981; color: white; }
        .card-dark { background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%); border-top: 4px solid #F59E0B; color: white; }
        .card-title { font-size: 13px !important; font-weight: 600 !important; color: #94A3B8 !important; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }
        .card-value { font-size: 32px; font-weight: 700 !important; color: #FFFFFF; margin-top: 0px; }
        div[data-testid="stSidebar"] { background-color: #0F172A; border-right: 1px solid #1E293B; }
        div[data-testid="stSidebar"] button { border-color: #334155; color: #94A3B8; }
        div[data-testid="stForm"] input { background-color: #1E293B !important; border: 1px solid #334155 !important; color: white; }
        div[data-testid="stFormSubmitButton"] button { background: linear-gradient(90deg, #3B82F6 0%, #2563EB 100%) !important; color: white !important; border: none; }
        .sales-box { background-color: #1E293B; border-radius: 12px; padding: 20px; height: 380px; overflow-y: auto; border: 1px solid #334155; }
        .sales-header { font-size: 16px; font-weight: 700; color: white; margin-bottom: 20px; font-family: 'Inter'; }
        .sales-row { display: flex; align-items: center; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid #334155; }
        .sales-row:last-child { border-bottom: none; }
        .sales-left { display: flex; align-items: center; gap: 12px; }
        .avatar-circle { width: 40px; height: 40px; border-radius: 10px; background-color: #3B82F6; color: #FFFFFF; display: flex; align-items: center; justify-content: center; font-weight: 700; }
        .client-name { font-size: 14px; color: white; font-weight: 600; }
        .client-sub { font-size: 12px; color: #94A3B8; }
        .sales-val { font-size: 14px; color: white; font-weight: 700; }
        .sales-badge { font-size: 11px; padding: 2px 8px; border-radius: 12px; margin-top: 4px; display: inline-block; font-weight: 600; }
        .badge-green { background-color: rgba(16, 185, 129, 0.2); color: #34D399; }
        div[data-testid="stHorizontalBlock"] button[kind="secondary"] { border: none !important; background-color: transparent !important; color: #EF4444 !important; padding: 0px !important; }
        div[data-testid="stHorizontalBlock"] button[kind="secondary"]:hover { color: #FF0000 !important; background-color: rgba(239, 68, 68, 0.1) !important; }
    </style>
    """, unsafe_allow_html=True)

apply_custom_style()

def get_data(endpoint):
    try:
        endpoint = endpoint.strip("/")
        resp = requests.get(f"{API_URL}/{endpoint}/")
        if resp.status_code == 200:
            return resp.json()
        return [] 
    except:
        return [] 

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
        if not os.path.exists(logo_path): logo_path = "logo.png"
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
                        data = res.json()
                        st.session_state['logado'] = True
                        st.session_state['usuario'] = data['usuario']
                        st.session_state['cargo'] = data['cargo']
                        st.success("Login OK! Redirecionando...")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Credenciais inválidas ou Erro de Conexão com o Servidor.")
                except Exception as e:
                    st.error(f"Erro TÉCNICO de conexão: {e}")

def sistema_erp():
    with st.sidebar:
        logo_path = "frontend/logo.png"
        if not os.path.exists(logo_path): logo_path = "logo.png"
        if os.path.exists(logo_path): st.markdown("<div style='margin-bottom: 25px; text-align: center;'>", unsafe_allow_html=True); st.image(logo_path, width=160); st.markdown("</div>", unsafe_allow_html=True)
        else: st.markdown(f"<div style='display:flex; align-items:center; gap:12px; margin-bottom:30px; padding-left:10px;'>{render_logo_svg(width='32px', color='#3B82F6')}<div style='font-family:Inter; font-weight:700; font-size:20px; color:white;'>Decant</div></div>", unsafe_allow_html=True)
        
        menu = [{"l": "Visão Geral", "i": "grid", "id": "dash"}, {"l": "PDV (Caixa)", "i": "basket", "id": "pdv"}, {"l": "Financeiro", "i": "cash-coin", "id": "fin"}, {"l": "CRM / Fidelidade", "i": "heart", "id": "crm"}, {"l": "Produtos", "i": "box-seam", "id": "prod"}, {"l": "Clientes", "i": "people", "id": "cli"}, {"l": "Fornecedores", "i": "truck", "id": "forn"}, {"l": "Preços", "i": "tags", "id": "prec"}, {"l": "Engenharia", "i": "tools", "id": "eng"}, {"l": "Planejamento", "i": "diagram-3", "id": "mrp"}, {"l": "Compras", "i": "cart", "id": "comp"}, {"l": "Produção", "i": "gear-wide-connected", "id": "fab"}, {"l": "Vendas (Adm)", "i": "graph-up-arrow", "id": "vend"}, {"l": "Relatórios", "i": "bar-chart-line", "id": "rel"}, {"l": "Configurações", "i": "gear", "id": "cfg"}]
        sel = option_menu(None, [x["l"] for x in menu], icons=[x["i"] for x in menu], default_index=0, styles={"container": {"padding": "0!important", "background-color": "transparent"},"icon": {"color": "#94A3B8", "font-size": "14px"}, "nav-link": {"font-family":"Inter", "font-weight":"500", "font-size": "14px", "text-align": "left", "margin":"5px", "--hover-color": "#1E293B", "color": "#E2E8F0"},"nav-link-selected": {"background-color": "#3B82F6", "color": "#FFFFFF", "font-weight": "600"}})
        page_id = next(x["id"] for x in menu if x["l"] == sel)
        st.markdown("<div style='margin-top: 40px'></div>", unsafe_allow_html=True)
        st.markdown(f"<div style='background-color: #1E293B; padding: 10px; border-radius: 12px; margin-bottom: 10px; border: 1px solid #334155; text-align: center;'><div style='color: #94A3B8; font-size: 10px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 2px;'>Bem-vindo</div><div style='color: white; font-weight: 600; font-size: 14px;'>{st.session_state['usuario']}</div><div style='color: #3B82F6; font-size: 11px;'>{st.session_state['cargo']}</div></div>", unsafe_allow_html=True)
        if st.button("Sair / Logout", use_container_width=True): st.session_state['logado'] = False; st.rerun()

    if page_id == "crm":
        header("CRM & Fidelização")
        st.info("Aqui aparecem clientes que compraram há mais de 25 dias e podem estar precisando de novos produtos.")
        ops = get_data("crm/oportunidades")
        if ops:
            for op in ops:
                with st.container(border=True):
                    c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
                    c1.markdown(f"**👤 {op['Cliente']}**")
                    c2.write(f"🛒 Comprou: {op['Último Produto']}")
                    c3.write(f"📅 {op['Dias sem Comprar']} dias atrás ({op['Status']})")
                    fone_limpo = ''.join(filter(str.isdigit, op['Telefone'] or ""))
                    msg = f"Olá {op['Cliente']}, notamos que faz {op['Dias sem Comprar']} dias que você comprou {op['Último Produto']}. Gostaria de repor seu estoque?"
                    link_zap = f"https://wa.me/55{fone_limpo}?text={msg}"
                    if fone_limpo: c4.link_button("💬 WhatsApp", link_zap, type="primary")
                    else: c4.write("Sem Telefone")
        else: st.success("🎉 Nenhum cliente inativo no momento! Todos compraram recentemente (menos de 25 dias).")

    elif page_id == "dash":
        header("Visão Geral")
        d = get_data("financeiro/dashboard")
        c1, c2, c3, c4 = st.columns(4)
        with c1: card_html("RECEITA TOTAL", f"R$ {d.get('receita', 0):,.2f}", "Vendas + Extras", "card-blue")
        with c2: card_html("DESPESAS TOTAIS", f"R$ {d.get('despesas', 0):,.2f}", "MP + Contas Fixas", "card-red")
        with c3: card_html("LUCRO LÍQUIDO", f"R$ {d.get('lucro', 0):,.2f}", f"Margem Real: {d.get('margem', 0):.1f}%", "card-green")
        with c4: card_html("SISTEMA", "Online", "v2.0 CRM", "card-dark")
        st.markdown("<br>", unsafe_allow_html=True)
        c_graf, c_vendas = st.columns([1.6, 1])
        with c_graf:
            dados = d.get('grafico', [])
            if dados: fig = px.bar(pd.DataFrame(dados), x="Mês", y="Valor", color="Tipo", barmode='group', color_discrete_map={'Entradas': '#10B981', 'Saídas': '#3B82F6'})
            else: fig = px.bar(pd.DataFrame([{"Mês":"Jan","Valor":0,"Tipo":"Entradas"}]), x="Mês", y="Valor")
            fig.update_layout(title={'text': "Fluxo de Caixa Mensal", 'y': 0.93, 'x': 0.05, 'xanchor': 'left', 'yanchor': 'top', 'font': {'size': 16, 'color': 'white', 'family': 'Inter', 'weight': 'bold'}}, paper_bgcolor='#1E293B', plot_bgcolor='#1E293B', font_color='#94A3B8', xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#334155'), legend=dict(orientation="h", y=1.05), margin=dict(l=20, r=20, t=60, b=20), height=370)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        with c_vendas:
            vendas = get_data("vendas"); clientes = get_data("clientes"); map_clientes = {c['id']: c for c in clientes}
            rows_html = ""
            for v in vendas[:5]:
                cli = map_clientes.get(v['cliente_id'], {'nome': 'Cliente', 'email': '-'})
                rows_html += get_sales_row_html(cli['nome'], cli['email'], v['valor_total'])
            st.markdown(f"<div class='sales-box'><div class='sales-header'>Últimas Vendas</div>{rows_html}</div>", unsafe_allow_html=True)

    elif page_id == "pdv":
        header("Frente de Caixa (PDV)")
        clis = get_data("clientes"); prods = get_data("produtos")
        produtos_acabados = [p for p in prods if p['tipo'] == 'Produto Acabado']
        c_esq, c_dir = st.columns([1.5, 1])
        with c_esq:
            st.markdown("##### 🛒 Adicionar Itens")
            if not clis: st.warning("Cadastre clientes na aba 'Clientes' primeiro.")
            else:
                cli_sel = st.selectbox("Cliente", [c['nome'] for c in clis], key="pdv_cli")
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    if produtos_acabados:
                        prod_sel = c1.selectbox("Produto", [p['nome'] for p in produtos_acabados], key="pdv_prod")
                        qtd_sel = c2.number_input("Qtd", min_value=1.0, value=1.0, key="pdv_qtd")
                        if st.button("Adicionar ao Carrinho", use_container_width=True):
                            p_obj = next(p for p in produtos_acabados if p['nome'] == prod_sel)
                            existe = False
                            for item in st.session_state['carrinho']:
                                if item['id'] == p_obj['id']:
                                    item['qtd'] += qtd_sel; item['total'] = item['qtd'] * item['preco']; existe = True; break
                            if not existe:
                                preco_venda = p_obj['custo'] * 2 
                                st.session_state['carrinho'].append({"id": p_obj['id'], "nome": p_obj['nome'], "qtd": qtd_sel, "preco": preco_venda, "total": qtd_sel * preco_venda})
                            st.rerun()
                    else: st.warning("Cadastre Produtos Acabados na aba 'Produtos'.")
        with c_dir:
            st.markdown("##### 🧾 Cupom Fiscal")
            total_geral = sum([i['total'] for i in st.session_state['carrinho']])
            if st.session_state['carrinho']:
                for idx, item in enumerate(st.session_state['carrinho']):
                    c1, c2, c3 = st.columns([3, 1, 1])
                    c1.write(f"{item['qtd']}x {item['nome']}"); c2.write(f"R$ {item['total']:.2f}")
                    if c3.button("🗑️", key=f"del_cart_{idx}"): st.session_state['carrinho'].pop(idx); st.rerun()
                st.divider(); st.markdown(f"<div style='text-align:right; font-size:24px; font-weight:bold'>Total: R$ {total_geral:,.2f}</div>", unsafe_allow_html=True)
                pagamento = st.selectbox("Forma de Pagamento", ["Pix", "Cartão Crédito", "Cartão Débito", "Dinheiro"])
                if st.button("✅ FINALIZAR VENDA", type="primary", use_container_width=True):
                    cid = next(c['id'] for c in clis if c['nome'] == cli_sel)
                    payload = {"cliente_id": cid, "itens": [{"produto_id": i['id'], "quantidade": i['qtd'], "valor_total": i['total']} for i in st.session_state['carrinho']], "metodo_pagamento": pagamento}
                    res = requests.post(f"{API_URL}/vendas/pdv/", json=payload)
                    if res.status_code == 200:
                        data = res.json(); st.session_state['carrinho'] = []; st.success("Venda Realizada!")
                        pdf_bytes = requests.get(f"{API_URL}/vendas/recibo/{data['grupo_id']}/").content
                        st.download_button("🖨️ Imprimir Cupom", pdf_bytes, file_name="cupom.pdf")
                    else: st.error(f"Erro: {res.text}")
            else: st.info("Carrinho vazio.")

    elif page_id == "fin":
        header("Gestão Financeira")
        t1, t2 = st.tabs(["📝 Novo Lançamento", "📜 Contas a Pagar/Receber"])
        with t1:
            with st.form("frm_fin"):
                c1, c2 = st.columns(2); desc = c1.text_input("Descrição"); tipo = c2.selectbox("Tipo", ["Despesa", "Receita"])
                c3, c4 = st.columns(2); valor = c3.number_input("Valor (R$)", min_value=0.01); cat = c4.selectbox("Categoria", ["Custos Fixos", "Despesa Variável", "Impostos", "Receita Extra", "Investimento"])
                c5, c6 = st.columns(2); dt_venc = c5.date_input("Vencimento"); pago = c6.checkbox("Já foi pago?")
                if st.form_submit_button("Salvar Lançamento"):
                    res = requests.post(f"{API_URL}/financeiro/lancamento/", json={"descricao": desc, "tipo": tipo, "categoria": cat, "valor": valor, "data_vencimento": str(dt_venc), "pago": pago})
                    if res.status_code == 200: st.success("Lançado!"); st.rerun()
                    else: st.error("Erro")
        with t2:
            lancamentos = get_data("financeiro/lancamentos")
            if lancamentos:
                df = pd.DataFrame(lancamentos)
                st.markdown("##### Extrato")
                for index, row in df.iterrows():
                    icone = "🔴" if row['tipo'] == "Despesa" else "🟢"; status = "✅ PAGO" if row['pago'] else "⏳ PENDENTE"
                    c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
                    c1.markdown(f"**{icone} {row['descricao']}**"); c2.write(f"R$ {row['valor']:,.2f}"); c3.write(f"{row['data_vencimento']} | {status}")
                    if not row['pago']:
                        if c4.button("Pagar", key=f"pay_{row['id']}"): requests.post(f"{API_URL}/financeiro/pagar/{row['id']}"); st.rerun()
                st.divider()
            else: st.info("Nenhum lançamento financeiro.")

    elif page_id == "cli":
        header("Clientes")
        c1, c2 = st.columns([1, 2])
        with c1:
            st.markdown("##### Novo Cliente")
            with st.form("new_cli"):
                n = st.text_input("Nome"); e = st.text_input("Email"); t = st.text_input("Telefone")
                if st.form_submit_button("Cadastrar"):
                    requests.post(f"{API_URL}/clientes/", json={"nome":n, "email":e, "telefone":t}); st.success("Cliente cadastrado!"); st.rerun()
        with c2:
            st.markdown("##### Lista de Clientes")
            clis = get_data("clientes")
            if clis: st.dataframe(pd.DataFrame(clis)[['id','nome','email','telefone']], use_container_width=True, hide_index=True)
            else: st.info("Nenhum cliente cadastrado.")

    elif page_id == "prod":
        header("Inventário de Produtos")
        prods = get_data("produtos"); t1, t2, t3 = st.tabs(["📦 Estoque", "📋 Kardex", "➕ Novo"])
        with t1:
            if prods:
                df = pd.DataFrame(prods); c1, c2, c3 = st.columns(3)
                with c1: card_html("ITENS", str(len(df)), "Total", "card-blue")
                with c2: card_html("BAIXO ESTOQUE", str(len(df[df['estoque_atual'] < 50])), "Críticos", "card-red")
                total_val = sum([p.get('estoque_atual', 0) * p.get('custo', 0) for p in prods])
                with c3: card_html("VALOR TOTAL", f"R$ {total_val:,.2f}", "Em Estoque", "card-dark")
                st.markdown("<br>", unsafe_allow_html=True); df_show = df[['id','nome','tipo','unidade','estoque_atual','custo']]
                st.dataframe(df_show, use_container_width=True, hide_index=True)
            else: st.info("Sem produtos.")
        with t2:
            movs = get_data("estoque/kardex"); 
            if movs: st.dataframe(pd.DataFrame(movs), use_container_width=True, hide_index=True)
            else: st.info("Nenhuma movimentação registrada.")
        with t3:
            with st.form("np"):
                n = st.text_input("Nome"); t = st.radio("Tipo", ["Materia Prima", "Produto Acabado"]); u = st.selectbox("Unid", ["kg","L","Un"]); e = st.number_input("Estoque"); c = st.number_input("Custo")
                if st.form_submit_button("Salvar"): requests.post(f"{API_URL}/produtos/", json={"nome":n,"tipo":t,"unidade":u,"estoque_atual":e,"custo":c}); st.success("Salvo!"); st.rerun()
    elif page_id == "forn":
        header("Fornecedores")
        with st.form("nf"):
            n = st.text_input("Empresa"); p = st.number_input("Prazo"); 
            if st.form_submit_button("Salvar"): requests.post(f"{API_URL}/fornecedores/", json={"nome":n,"prazo_entrega_dias":p}); st.success("OK")
    elif page_id == "prec":
        header("Preços")
        prods = get_data("produtos"); forns = get_data("fornecedores"); cots = get_data("cotacoes")
        c1, c2 = st.columns([1,2])
        with c1:
            with st.form("prc"):
                p = st.selectbox("Item", [x['nome'] for x in prods]); f = st.selectbox("Forn.", [x['nome'] for x in forns]); v = st.number_input("Preço", 0.01)
                if st.form_submit_button("Salvar"):
                    pid = next(x['id'] for x in prods if x['nome']==p); fid = next(x['id'] for x in forns if x['nome']==f)
                    requests.post(f"{API_URL}/cotacoes/", json={"produto_id":pid,"fornecedor_id":fid,"preco":v}); st.success("OK"); st.rerun()
        with c2:
            if cots:
                p_map = {x['id']:x['nome'] for x in prods}; f_map = {x['id']:x['nome'] for x in forns}
                st.dataframe(pd.DataFrame([{"Produto":p_map.get(c['produto_id']),"Forn":f_map.get(c['fornecedor_id']),"Valor":c['preco']} for c in cots]), use_container_width=True)
    elif page_id == "eng":
        header("Engenharia")
        prods = get_data("produtos"); t1, t2 = st.tabs(["Nova", "Fichas"])
        with t1:
            if prods:
                with st.form("nf"):
                    nm = st.text_input("Nome"); pf = st.selectbox("Produto Final", [x['nome'] for x in prods if x['tipo']=='Produto Acabado'])
                    if st.form_submit_button("Criar"): 
                        pid = next(x['id'] for x in prods if x['nome']==pf)
                        requests.post(f"{API_URL}/formulas/", json={"nome":nm,"produto_final_id":pid}); st.success("Criado")
                st.markdown("---"); st.write("Adicionar Ingrediente"); forms = get_data("formulas")
                if forms:
                    f_map = {x['nome']:x['id'] for x in forms}; sel_f = st.selectbox("Fórmula", list(f_map.keys()))
                    st.info("Ingredientes Atuais:")
                    res_atual = requests.post(f"{API_URL}/planejamento/calcular/?formula_id={f_map[sel_f]}&quantidade_producao=1").json()
                    if res_atual.get('materiais'): st.dataframe(pd.DataFrame(res_atual['materiais'])[['ingrediente', 'necessario']], use_container_width=True, hide_index=True)
                    else: st.text("Vazia")
                    with st.form("ni"):
                        ing = st.selectbox("Ingrediente", [x['nome'] for x in prods if x['tipo']=='Materia Prima']); q = st.number_input("Qtd", format="%.3f")
                        if st.form_submit_button("Adicionar"):
                            iid = next(x['id'] for x in prods if x['nome']==ing)
                            requests.post(f"{API_URL}/formulas/itens/", json={"formula_id":f_map[sel_f],"materia_prima_id":iid,"quantidade":q}); st.success("OK"); st.rerun()
        with t2:
            forms = get_data("formulas")
            if forms:
                for f in forms:
                    with st.expander(f"📄 {f['nome']}", expanded=False):
                        res = requests.post(f"{API_URL}/planejamento/calcular/?formula_id={f['id']}&quantidade_producao=1").json()
                        c1, c2 = st.columns([1.5, 1])
                        with c1:
                            if res.get('materiais'):
                                try:
                                    for item in res['materiais']:
                                        cc1, cc2, cc3, cc4, cc5 = st.columns([2.5, 0.8, 0.8, 0.8, 0.5], vertical_alignment="center")
                                        cc1.write(item['ingrediente']); cc2.write(f"{item['necessario']} {item['unidade']}"); cc3.write(f"R$ {item['custo_unit']:.2f}"); cc4.write(f"R$ {item['subtotal']:.4f}")
                                        if cc5.button("🗑️", key=f"del_{item['id']}"): requests.delete(f"{API_URL}/formulas/itens/{item['id']}"); st.rerun()
                                except TypeError:
                                    for item in res['materiais']:
                                        cc1, cc2, cc3, cc4, cc5 = st.columns([2.5, 0.8, 0.8, 0.8, 0.5])
                                        cc1.write(item['ingrediente']); cc2.write(f"{item['necessario']} {item['unidade']}"); cc3.write(f"R$ {item['custo_unit']:.2f}"); cc4.write(f"R$ {item['subtotal']:.4f}")
                                        if cc5.button("🗑️", key=f"del_{item['id']}"): requests.delete(f"{API_URL}/formulas/itens/{item['id']}"); st.rerun()
                            else: st.warning("Sem ingredientes")
                        with c2:
                            st.metric("Custo Ind.", f"R$ {res.get('custo_total', 0.0):.2f}")
    elif page_id == "mrp":
        header("Planejamento"); forms = get_data("formulas")
        if forms:
            f = st.selectbox("Fórmula", [x['nome'] for x in forms]); q = st.number_input("Qtd", 100.0)
            if st.button("Calcular"):
                fid = next(x['id'] for x in forms if x['nome']==f)
                res = requests.post(f"{API_URL}/planejamento/calcular/?formula_id={fid}&quantidade_producao={q}").json()
                st.dataframe(pd.DataFrame(res['materiais']), use_container_width=True)
    elif page_id == "comp":
        header("Compras & Recebimento")
        c1, c2 = st.columns([1,1]); 
        with c1:
            st.markdown("#### 1. Novo Pedido de Compra")
            prods = get_data("produtos"); forns = get_data("fornecedores")
            with st.form("nc"):
                p = st.selectbox("Produto", [x['nome'] for x in prods]); f = st.selectbox("Fornecedor", [x['nome'] for x in forns])
                q = st.number_input("Qtd"); v = st.number_input("Valor Unit.")
                if st.form_submit_button("Gerar Pedido"):
                    pid = next(x['id'] for x in prods if x['nome']==p); fid = next(x['id'] for x in forns if x['nome']==f)
                    requests.post(f"{API_URL}/compras/", json={"produto_id":pid,"fornecedor_id":fid,"quantidade":q,"valor_unitario":v}); st.success("Enviado"); st.rerun()
        with c2:
            st.markdown("#### 2. Dar Entrada (Nota Fiscal)")
            peds = get_data("compras"); pendentes = [p for p in peds if p['status'] == 'Pendente']
            if pendentes:
                ped_options = {f"Pedido #{p['id']} - Qtd: {p['quantidade']}": p for p in pendentes}
                sel_ped = st.selectbox("Selecione o Pedido Chegando:", list(ped_options.keys()))
                if sel_ped:
                    pedido_real = ped_options[sel_ped]
                    with st.form("form_recebimento"):
                        c_lote, c_validade = st.columns(2)
                        lote = c_lote.text_input("Lote (da NF)", placeholder="Ex: L2024-55")
                        validade = c_validade.date_input("Validade", value=None)
                        if st.form_submit_button("Confirmar Entrada"):
                            if lote and validade:
                                res = requests.post(f"{API_URL}/compras/{pedido_real['id']}/processar/", json={"lote": lote, "validade": str(validade)})
                                if res.status_code == 200: st.balloons(); st.success("Estoque Atualizado!"); time.sleep(1); st.rerun()
                            else: st.warning("Preencha Lote e Validade.")
            else: st.info("Nenhum pedido pendente.")
            st.divider(); st.markdown("**Histórico Recente**")
            for pd_ in peds[:5]:
                k1, k3 = st.columns([4,1]); status_icon = "🟢" if pd_['status'] == "Recebido" else "🟠"
                k1.write(f"{status_icon} **Pedido #{pd_['id']}** | Qtd: {pd_['quantidade']}")
                pdf_bytes = requests.get(f"{API_URL}/compras/{pd_['id']}/pdf/").content
                k3.download_button("📄", pdf_bytes, file_name=f"pedido_{pd_['id']}.pdf", key=f"btn_ped_{pd_['id']}")
    elif page_id == "vend":
        header("Vendas (Administrativo)")
        c1, c2 = st.columns([1,1.5])
        with c1:
            st.markdown("#### Nova Venda")
            with st.form("nv"):
                clis = get_data("clientes"); prods = get_data("produtos")
                c = st.selectbox("Cliente", [x['nome'] for x in clis]); p = st.selectbox("Produto", [x['nome'] for x in prods if x['tipo']=='Produto Acabado'])
                q = st.number_input("Qtd", 1.0); v = st.number_input("Total R$", 1.0)
                if st.form_submit_button("Registrar Venda"):
                    cid = next(x['id'] for x in clis if x['nome']==c); pid = next(x['id'] for x in prods if x['nome']==p)
                    r = requests.post(f"{API_URL}/vendas/", json={"cliente_id":cid,"produto_id":pid,"quantidade":q,"valor_total":v})
                    if r.status_code == 200: st.success("Venda OK"); st.rerun()
                    else: st.error("Sem Estoque")
        with c2:
            vendas = get_data("vendas")
            if vendas:
                h1, h2, h3 = st.columns([1, 2, 1]); h1.write("**ID**"); h2.write("**Valor**"); h3.write("**Recibo**"); st.divider()
                for ven in vendas:
                    r1, r2, r3 = st.columns([1, 2, 1])
                    r1.write(f"#{ven['id']}"); r2.write(f"R$ {ven['valor_total']:.2f}")
                    pdf_bytes = requests.get(f"{API_URL}/vendas/{ven['id']}/pdf/").content
                    r3.download_button("📄 Baixar", pdf_bytes, key=f"btn_venda_{ven['id']}", file_name=f"recibo_{ven['id']}.pdf")
                    
    # --- AQUI ESTÁ A CORREÇÃO: ABAS QUE FALTAVAM ---
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

    elif page_id == "rel":
        header("Relatórios"); t1, t2 = st.tabs(["Estoque", "Lotes"])
        with t1: 
             d = get_data("relatorios/estoque/")
             if d: st.dataframe(pd.DataFrame(d['itens']), use_container_width=True)
        with t2: st.dataframe(pd.DataFrame(get_data("relatorios/lotes_vencimento/")), use_container_width=True)
    # -----------------------------------------------

    elif page_id == "cfg":
        header("Configurações")
        t1, t2 = st.tabs(["🛡️ Backup & Reset", "👥 Usuários"])
        with t1:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("##### 1. Backup de Segurança")
                st.info("Baixe uma cópia dos seus dados.")
                backup_data = requests.get(f"{API_URL}/sistema/backup/")
                if backup_data.status_code == 200: st.download_button("⬇️ BAIXAR BACKUP", backup_data.content, f"backup_decant_{datetime.now().strftime('%Y%m%d')}.db", "application/octet-stream", use_container_width=True)
            with c2:
                if st.session_state['usuario'] == "admin": 
                    st.markdown("##### 2. Zerar Sistema (Modo Produção)")
                    st.warning("⚠️ Cuidado! Isso apaga TODOS os dados.")
                    if st.button("🗑️ APAGAR DADOS DE TESTE", type="primary", use_container_width=True):
                        res = requests.delete(f"{API_URL}/sistema/resetar_dados/")
                        if res.status_code == 200: st.balloons(); st.success("Sistema Limpo!"); time.sleep(2); st.rerun()
                else: st.info("Área restrita.")
        with t2:
            st.markdown("##### Criar Novo Usuário")
            with st.form("new_user"):
                u = st.text_input("Usuário"); s = st.text_input("Senha", type="password"); c = st.selectbox("Cargo", ["Diretor", "Gerente de Produção", "Assistente Administrativo"])
                if st.form_submit_button("Criar Acesso"):
                    res = requests.post(f"{API_URL}/usuarios/", json={"username":u, "senha":s, "cargo":c})
                    if res.status_code == 200: st.success(f"Usuário {u} criado!"); st.rerun()
                    else: st.error("Erro ao criar.")
            st.divider(); st.markdown("**Usuários Ativos**"); us = get_data("usuarios")
            if us: st.dataframe(pd.DataFrame(us)[['id', 'username', 'cargo']], use_container_width=True)

if st.session_state['logado']: sistema_erp()
else: tela_login()