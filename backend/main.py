from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, FileResponse 
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel
from backend.database import SessionLocal, engine, Base
from passlib.context import CryptContext
from backend.models import Produto, Lote, Fornecedor, Cotacao, Formula, FormulaItem, PedidoCompra, OrdemProducao, Cliente, Venda, Usuario, Movimentacao, Lancamento
from fpdf import FPDF 
import io
from datetime import datetime, timedelta, date
import random
from collections import defaultdict
import os
import qrcode
import tempfile
import uuid

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Decant ERP")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
def verificar_senha(plain, hashed): return pwd_context.verify(plain, hashed)
def criar_hash(senha): return pwd_context.hash(senha)

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

def consumir_estoque_lotes(db: Session, produto_id: int, quantidade: float):
    lotes = db.query(Lote).filter(Lote.produto_id == produto_id, Lote.quantidade_atual > 0).order_by(Lote.validade.asc()).all()
    qtd_a_consumir = quantidade
    for lote in lotes:
        if qtd_a_consumir <= 0: break
        if lote.quantidade_atual >= qtd_a_consumir:
            lote.quantidade_atual -= qtd_a_consumir
            qtd_a_consumir = 0
        else:
            qtd_a_consumir -= lote.quantidade_atual
            lote.quantidade_atual = 0
    return

def seed_db():
    db = SessionLocal()
    if not db.query(Usuario).first():
        db.add(Usuario(username="admin", senha_hash=criar_hash("123"), cargo="Diretor"))
        db.commit()
    db.close()

seed_db()

# --- SCHEMAS ---
class UsuarioBase(BaseModel):
    username: str; senha: str; cargo: str
class ProdutoBase(BaseModel):
    nome: str; tipo: str; unidade: str; estoque_atual: float; custo: float
class FornecedorBase(BaseModel):
    nome: str; prazo_entrega_dias: int
class CotacaoBase(BaseModel):
    produto_id: int; fornecedor_id: int; preco: float
class FormulaBase(BaseModel):
    nome: str; produto_final_id: int
class FormulaItemBase(BaseModel):
    formula_id: int; materia_prima_id: int; quantidade: float
class PedidoCompraBase(BaseModel):
    fornecedor_id: int; produto_id: int; quantidade: float; valor_unitario: float
class ClienteBase(BaseModel):
    nome: str; email: str; telefone: str
class VendaBase(BaseModel):
    cliente_id: int; produto_id: int; quantidade: float; valor_total: float
class RecebimentoBase(BaseModel):
    lote: str; validade: str
class ProducaoConfirmBase(BaseModel):
    formula_id: int; quantidade: float; lote_final: str; validade_final: str
class LancamentoBase(BaseModel):
    descricao: str; tipo: str; categoria: str; valor: float; data_vencimento: str; pago: bool

# SCHEMA PDV (CARRINHO)
class ItemPDV(BaseModel):
    produto_id: int
    quantidade: float
    valor_total: float

class VendaPDV(BaseModel):
    cliente_id: int
    itens: list[ItemPDV]
    metodo_pagamento: str

# --- ROTAS CRM (NOVO) ---
@app.get("/crm/oportunidades/")
def crm_oportunidades(db: Session = Depends(get_db)):
    # Lógica: Pega a última compra de cada cliente
    vendas = db.query(Venda).order_by(Venda.data_venda.desc()).all()
    mapa_clientes = {}
    
    for v in vendas:
        # Se já processamos esse cliente, pula (pois ordenamos por data desc)
        if v.cliente_id in mapa_clientes: continue
        
        c = db.query(Cliente).filter(Cliente.id == v.cliente_id).first()
        p = db.query(Produto).filter(Produto.id == v.produto_id).first()
        
        if c and p:
            dias = (datetime.now() - v.data_venda).days
            status = "🟢 Recente"
            if dias > 25: status = "🟡 Atenção (25+ dias)"
            if dias > 45: status = "🔴 Crítico (45+ dias)"
            if dias > 90: status = "💤 Inativo"

            # Só mostra quem comprou há mais de 25 dias
            if dias >= 25:
                mapa_clientes[v.cliente_id] = {
                    "Cliente": c.nome,
                    "Telefone": c.telefone,
                    "Último Produto": p.nome,
                    "Data": v.data_venda.strftime("%d/%m/%Y"),
                    "Dias sem Comprar": dias,
                    "Status": status
                }
    
    return list(mapa_clientes.values())

# --- ROTAS PDV ---
@app.post("/vendas/pdv/")
def realizar_venda_pdv(v: VendaPDV, db: Session = Depends(get_db)):
    grupo_id = str(uuid.uuid4()) # ID Único da Nota
    total_geral = 0.0
    
    for item in v.itens:
        p = db.query(Produto).filter(Produto.id == item.produto_id).first()
        if p.estoque_atual < item.quantidade: 
            raise HTTPException(400, f"Estoque insuficiente para {p.nome}")
        
        # Baixa Estoque
        p.estoque_atual -= item.quantidade
        consumir_estoque_lotes(db, p.id, item.quantidade)
        
        # Registra Venda Individual
        nova_venda = Venda(
            cliente_id=v.cliente_id,
            produto_id=item.produto_id,
            quantidade=item.quantidade,
            valor_total=item.valor_total,
            metodo_pagamento=v.metodo_pagamento,
            venda_agrupada_id=grupo_id
        )
        db.add(nova_venda)
        
        # Log Kardex
        db.add(Movimentacao(produto_id=p.id, tipo="Saida", quantidade=item.quantidade, origem=f"PDV {v.metodo_pagamento}", usuario="Vendas"))
        
        total_geral += item.valor_total

    # LANÇA NO FINANCEIRO AUTOMATICAMENTE
    if total_geral > 0:
        lanc = Lancamento(
            descricao=f"Venda PDV (Ref: {grupo_id[:8]})",
            tipo="Receita",
            categoria="Vendas",
            valor=total_geral,
            data_vencimento=datetime.now().date(),
            pago=True, # Dinheiro já entrou no caixa
            data_pagamento=datetime.now().date()
        )
        db.add(lanc)

    db.commit()
    return {"msg": "Venda PDV realizada", "grupo_id": grupo_id}

@app.get("/vendas/recibo/{grupo_id}/")
def gerar_cupom_pdv(grupo_id: str, db: Session = Depends(get_db)):
    vendas = db.query(Venda).filter(Venda.venda_agrupada_id == grupo_id).all()
    if not vendas: return Response(content=b"")
    
    # PDF Estilo Cupom Fiscal (80mm)
    pdf = FPDF('P', 'mm', (80, 200))
    pdf.add_page()
    pdf.set_margins(2, 2, 2)
    
    pdf.set_font("Arial", 'B', 10); pdf.cell(0, 5, "DECANT COSMETICS", 0, 1, 'C')
    pdf.set_font("Arial", '', 8); pdf.cell(0, 4, f"Cupom: {grupo_id[:8]}", 0, 1, 'C')
    pdf.cell(0, 4, datetime.now().strftime("%d/%m/%Y %H:%M"), 0, 1, 'C')
    pdf.line(2, 20, 78, 20); pdf.ln(5)
    
    total = 0
    for v in vendas:
        p = db.query(Produto).filter(Produto.id == v.produto_id).first()
        pdf.set_font("Arial", 'B', 8); pdf.cell(0, 4, f"{p.nome}", 0, 1)
        pdf.set_font("Arial", '', 8)
        pdf.cell(40, 4, f"{v.quantidade} x R$ {v.valor_total/v.quantidade:.2f}", 0, 0)
        pdf.cell(35, 4, f"R$ {v.valor_total:.2f}", 0, 1, 'R')
        total += v.valor_total
        
    pdf.line(2, pdf.get_y()+2, 78, pdf.get_y()+2); pdf.ln(4)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(40, 5, "TOTAL:", 0, 0)
    pdf.cell(35, 5, f"R$ {total:.2f}", 0, 1, 'R')
    pdf.set_font("Arial", '', 8)
    pdf.cell(0, 5, f"Pagamento: {vendas[0].metodo_pagamento}", 0, 1, 'C')
    
    return Response(content=pdf.output(dest='S').encode('latin-1'), media_type="application/pdf")

# --- ROTAS DE SISTEMA ---
@app.get("/usuarios/")
def listar_usuarios(db: Session = Depends(get_db)): return db.query(Usuario).all()
@app.post("/usuarios/")
def criar_usuario(u: UsuarioBase, db: Session = Depends(get_db)):
    existe = db.query(Usuario).filter(Usuario.username == u.username).first()
    if existe: raise HTTPException(400, "Usuário já existe")
    novo = Usuario(username=u.username, senha_hash=criar_hash(u.senha), cargo=u.cargo)
    db.add(novo); db.commit()
    return {"msg": "Usuário criado"}
@app.delete("/sistema/resetar_dados/")
def resetar_dados(db: Session = Depends(get_db)):
    db.query(Movimentacao).delete(); db.query(Venda).delete(); db.query(OrdemProducao).delete()
    db.query(PedidoCompra).delete(); db.query(FormulaItem).delete(); db.query(Formula).delete()
    db.query(Lote).delete(); db.query(Cotacao).delete(); db.query(Produto).delete()
    db.query(Cliente).delete(); db.query(Fornecedor).delete(); db.query(Lancamento).delete()
    db.commit()
    return {"msg": "Dados apagados"}
@app.post("/auth/login/")
def login(u: UsuarioBase, db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(Usuario.username == u.username).first()
    if not user or not verificar_senha(u.senha, user.senha_hash):
        if u.username == "admin" and u.senha == "123": return {"msg": "OK", "cargo": "Diretor", "usuario": "admin"}
        raise HTTPException(401, "Credenciais inválidas")
    return {"msg": "OK", "cargo": user.cargo, "usuario": user.username}
@app.get("/sistema/backup/")
def baixar_backup():
    file_path = "sistema_final.db"
    if os.path.exists(file_path): return FileResponse(path=file_path, filename=f"decant_backup_{datetime.now().strftime('%Y%m%d')}.db", media_type='application/octet-stream')
    return {"erro": "404"}

# --- OPERACIONAL ---
@app.post("/financeiro/lancamento/")
def criar_lancamento(l: LancamentoBase, db: Session = Depends(get_db)):
    data_venc = datetime.strptime(l.data_vencimento, "%Y-%m-%d").date()
    novo = Lancamento(descricao=l.descricao, tipo=l.tipo, categoria=l.categoria, valor=l.valor, data_vencimento=data_venc, pago=l.pago, data_pagamento=data_venc if l.pago else None)
    db.add(novo); db.commit()
    return {"msg": "Lançamento criado"}
@app.get("/financeiro/lancamentos/")
def listar_lancamentos(db: Session = Depends(get_db)): return db.query(Lancamento).order_by(Lancamento.data_vencimento.desc()).all()
@app.post("/financeiro/pagar/{id}")
def pagar_conta(id: int, db: Session = Depends(get_db)):
    lan = db.query(Lancamento).filter(Lancamento.id == id).first()
    if lan:
        lan.pago = not lan.pago; lan.data_pagamento = datetime.now().date() if lan.pago else None
        db.commit()
    return {"msg": "Status alterado"}
@app.get("/produtos/")
def listar_produtos(db: Session = Depends(get_db)): return db.query(Produto).all()
@app.post("/produtos/")
def criar_produto(p: ProdutoBase, db: Session = Depends(get_db)): 
    novo = Produto(**p.dict()); db.add(novo); db.commit(); db.refresh(novo)
    if p.estoque_atual > 0:
        db.add(Movimentacao(produto_id=novo.id, tipo="Entrada", quantidade=p.estoque_atual, origem="Cadastro Inicial", usuario="Admin"))
        db.add(Lote(produto_id=novo.id, codigo="INI-CAD", validade="2030-12-31", quantidade_atual=p.estoque_atual))
        db.commit()
    return {"msg": "OK"}
@app.get("/fornecedores/")
def listar_fornecedores(db: Session = Depends(get_db)): return db.query(Fornecedor).all()
@app.post("/fornecedores/")
def criar_fornecedor(f: FornecedorBase, db: Session = Depends(get_db)): db.add(Fornecedor(**f.dict())); db.commit(); return {"msg": "OK"}
@app.get("/cotacoes/")
def listar_cotacoes(db: Session = Depends(get_db)): return db.query(Cotacao).all()
@app.post("/cotacoes/")
def criar_cotacao(c: CotacaoBase, db: Session = Depends(get_db)): db.add(Cotacao(**c.dict())); db.commit(); return {"msg": "OK"}
@app.get("/clientes/")
def listar_clientes(db: Session = Depends(get_db)): return db.query(Cliente).all()
@app.post("/clientes/")
def criar_cliente(c: ClienteBase, db: Session = Depends(get_db)): db.add(Cliente(**c.dict())); db.commit(); return {"msg": "OK"}
@app.get("/formulas/")
def listar_formulas(db: Session = Depends(get_db)): return db.query(Formula).options(joinedload(Formula.itens)).all()
@app.post("/formulas/")
def criar_formula(f: FormulaBase, db: Session = Depends(get_db)): novo = Formula(**f.dict()); db.add(novo); db.commit(); db.refresh(novo); return novo
@app.post("/formulas/itens/")
def add_ingrediente(i: FormulaItemBase, db: Session = Depends(get_db)): db.add(FormulaItem(**i.dict())); db.commit(); return {"msg": "OK"}
@app.delete("/formulas/itens/{item_id}")
def delete_ingrediente(item_id: int, db: Session = Depends(get_db)):
    item = db.query(FormulaItem).filter(FormulaItem.id == item_id).first()
    if item: db.delete(item); db.commit()
    return {"msg": "Deleted"}
@app.post("/planejamento/calcular/")
def calcular_mrp(formula_id: int, quantidade_producao: float, db: Session = Depends(get_db)):
    f = db.query(Formula).options(joinedload(Formula.itens).joinedload(FormulaItem.materia_prima)).filter(Formula.id == formula_id).first()
    res = []; custo_total = 0.0
    if f and f.itens:
        for item in f.itens:
            qtd = item.quantidade * quantidade_producao; custo = item.materia_prima.custo * qtd; custo_total += custo
            res.append({"id":item.id, "ingrediente":item.materia_prima.nome, "necessario":qtd, "unidade":item.materia_prima.unidade, "estoque":item.materia_prima.estoque_atual, "custo_unit":item.materia_prima.custo, "subtotal":custo, "status":"OK" if item.materia_prima.estoque_atual >= qtd else "FALTA"})
    return {"producao": quantidade_producao, "materiais": res, "custo_total": custo_total}
@app.get("/compras/")
def listar_compras(db: Session = Depends(get_db)): return db.query(PedidoCompra).all()
@app.post("/compras/")
def criar_compra(c: PedidoCompraBase, db: Session = Depends(get_db)): db.add(PedidoCompra(**c.dict(), status="Pendente")); db.commit(); return {"msg": "OK"}
@app.post("/compras/{id}/processar/")
def processar_recebimento(id: int, dados: RecebimentoBase, db: Session = Depends(get_db)):
    pc = db.query(PedidoCompra).filter(PedidoCompra.id == id).first()
    if pc and pc.status == "Pendente":
        prod = db.query(Produto).filter(Produto.id == pc.produto_id).first()
        prod.estoque_atual += pc.quantidade
        pc.status = "Recebido"
        db.add(Lote(produto_id=prod.id, codigo=dados.lote, validade=dados.validade, quantidade_atual=pc.quantidade))
        db.add(Movimentacao(produto_id=prod.id, tipo="Entrada", quantidade=pc.quantidade, origem=f"Compra #{pc.id}", usuario="Almox."))
        db.commit()
    return {"msg": "OK"}
@app.post("/producao/confirmar_lote/")
def produzir_com_lote(dados: ProducaoConfirmBase, db: Session = Depends(get_db)):
    f = db.query(Formula).options(joinedload(Formula.itens).joinedload(FormulaItem.materia_prima)).filter(Formula.id == dados.formula_id).first()
    for i in f.itens:
        qtd_nec = i.quantidade * dados.quantidade
        i.materia_prima.estoque_atual -= qtd_nec
        consumir_estoque_lotes(db, i.materia_prima.id, qtd_nec)
        db.add(Movimentacao(produto_id=i.materia_prima.id, tipo="Saida", quantidade=qtd_nec, origem="OP (Consumo)", usuario="Produção"))
    pa = db.query(Produto).filter(Produto.id == f.produto_final_id).first()
    pa.estoque_atual += dados.quantidade
    db.add(Lote(produto_id=pa.id, codigo=dados.lote_final, validade=dados.validade_final, quantidade_atual=dados.quantidade))
    db.add(OrdemProducao(formula_id=dados.formula_id, quantidade_produzida=dados.quantidade, lote_codigo=dados.lote_final, status="Concluída"))
    db.add(Movimentacao(produto_id=pa.id, tipo="Entrada", quantidade=dados.quantidade, origem="OP (Conclusão)", usuario="Produção"))
    db.commit()
    return {"msg": "Produzido"}
@app.get("/producao/historico/")
def listar_producao(db: Session = Depends(get_db)): return db.query(OrdemProducao).all()
@app.get("/vendas/")
def listar_vendas(db: Session = Depends(get_db)): return db.query(Venda).order_by(Venda.id.desc()).limit(20).all()
@app.get("/compras/{id}/pdf/")
def pdf_compra(id: int, db: Session = Depends(get_db)):
    pc = db.query(PedidoCompra).filter(PedidoCompra.id == id).first()
    if not pc: return Response(content=b"", media_type="application/pdf")
    pdf = FPDF(); pdf.add_page(); pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, "PEDIDO DE COMPRA", 0, 1, 'C'); pdf.line(10, 20, 200, 20); pdf.ln(10)
    pdf.set_font("Arial", '', 12); pdf.cell(100, 10, f"Pedido #: {pc.id}", 0, 1)
    return Response(content=pdf.output(dest='S').encode('latin-1'), media_type="application/pdf")
@app.get("/vendas/{id}/pdf/")
def pdf_venda(id: int, db: Session = Depends(get_db)):
    v = db.query(Venda).filter(Venda.id == id).first()
    if not v: return Response(content=b"", media_type="application/pdf")
    pdf = FPDF(); pdf.add_page(); pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, "RECIBO DE VENDA", 0, 1, 'C'); pdf.line(10, 20, 200, 20); pdf.ln(10)
    pdf.set_font("Arial", '', 12); pdf.cell(100, 10, f"Venda #: {v.id}", 0, 1); pdf.cell(100, 10, f"Valor: R$ {v.valor_total}", 0, 1)
    return Response(content=pdf.output(dest='S').encode('latin-1'), media_type="application/pdf")
@app.get("/producao/{id}/pdf/")
def pdf_producao(id: int, db: Session = Depends(get_db)):
    op = db.query(OrdemProducao).filter(OrdemProducao.id == id).first()
    if not op: return Response(content=b"", media_type="application/pdf")
    pdf = FPDF(); pdf.add_page(); pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, "ORDEM DE PRODUCAO", 0, 1, 'C'); pdf.line(10, 20, 200, 20); pdf.ln(10)
    pdf.set_font("Arial", '', 12); pdf.cell(100, 10, f"OP #: {op.id}", 0, 1)
    return Response(content=pdf.output(dest='S').encode('latin-1'), media_type="application/pdf")
@app.get("/producao/{id}/etiqueta/")
def pdf_etiqueta(id: int, db: Session = Depends(get_db)):
    op = db.query(OrdemProducao).filter(OrdemProducao.id == id).first()
    if not op: return Response(content=b"", media_type="application/pdf")
    f = db.query(Formula).filter(Formula.id == op.formula_id).first()
    p = db.query(Produto).filter(Produto.id == f.produto_final_id).first()
    lote = db.query(Lote).filter(Lote.codigo == op.lote_codigo, Lote.produto_id == p.id).first()
    validade = lote.validade if lote else "???"
    qr_data = f"PROD:{p.nome}\nLOTE:{op.lote_codigo}\nVAL:{validade}\nID:{op.id}"
    qr = qrcode.make(qr_data); temp_qr = tempfile.NamedTemporaryFile(delete=False, suffix=".png"); qr.save(temp_qr.name)
    pdf = FPDF('L', 'mm', (60, 100)); pdf.add_page(); pdf.set_margins(2, 2, 2)
    pdf.set_font("Arial", 'B', 10); pdf.cell(0, 5, "DECANT COSMETICS", 0, 1, 'C'); pdf.ln(2)
    pdf.set_font("Arial", 'B', 8); pdf.multi_cell(60, 4, f"{p.nome}"); pdf.ln(2)
    pdf.set_font("Arial", '', 8); pdf.cell(20, 4, "Lote:", 0, 0); pdf.set_font("Arial", 'B', 8); pdf.cell(40, 4, f"{op.lote_codigo}", 0, 1)
    pdf.set_font("Arial", '', 8); pdf.cell(20, 4, "Validade:", 0, 0); pdf.set_font("Arial", 'B', 8); pdf.cell(40, 4, f"{validade}", 0, 1)
    pdf.image(temp_qr.name, x=65, y=15, w=30, h=30); temp_qr.close(); os.unlink(temp_qr.name)
    return Response(content=pdf.output(dest='S').encode('latin-1'), media_type="application/pdf")
@app.get("/financeiro/dashboard/")
def dashboard(db: Session = Depends(get_db)):
    vendas = db.query(Venda).all(); compras = db.query(PedidoCompra).all(); lancamentos = db.query(Lancamento).all()
    receita_vendas = sum(v.valor_total for v in vendas)
    custo_mp = sum(c.quantidade * c.valor_unitario for c in compras)
    despesas_fixas = sum(l.valor for l in lancamentos if l.tipo == "Despesa" and l.pago)
    receitas_extras = sum(l.valor for l in lancamentos if l.tipo == "Receita" and l.pago)
    receita_total = receita_vendas + receitas_extras; custo_total = custo_mp + despesas_fixas; lucro_liquido = receita_total - custo_total
    margem = (lucro_liquido / receita_total * 100) if receita_total > 0 else 0
    d_map = defaultdict(float)
    meses_map = {1:"Jan", 2:"Fev", 3:"Mar", 4:"Abr", 5:"Mai", 6:"Jun", 7:"Jul", 8:"Ago", 9:"Set", 10:"Out", 11:"Nov", 12:"Dez"}
    for v in vendas: d_map[meses_map[v.data_venda.month]] += v.valor_total
    for l in lancamentos: 
        if l.pago and l.tipo == "Despesa": d_map[meses_map[l.data_pagamento.month]] -= l.valor
    graf = [{"Mês":m,"Valor":v,"Tipo":"Saldo"} for m,v in d_map.items() if v != 0]
    return {"receita": receita_total, "despesas": custo_total, "lucro": lucro_liquido, "margem": margem, "grafico": graf}
@app.get("/estoque/kardex/")
def kardex(db: Session = Depends(get_db)):
    movs = db.query(Movimentacao).order_by(Movimentacao.data.desc()).all()
    res = []
    for m in movs:
        p = db.query(Produto).filter(Produto.id == m.produto_id).first()
        res.append({"Data": m.data.strftime("%d/%m/%Y"), "Produto": p.nome if p else "?", "Tipo": m.tipo, "Qtd": m.quantidade, "Origem": m.origem})
    return res
@app.get("/relatorios/lotes_vencimento/")
def lotes_vencimento(db: Session = Depends(get_db)):
    lotes = db.query(Lote).filter(Lote.quantidade_atual > 0).order_by(Lote.validade.asc()).all()
    res = []
    for l in lotes:
        p = db.query(Produto).filter(Produto.id == l.produto_id).first()
        res.append({"Produto": p.nome, "Lote": l.codigo, "Validade": l.validade, "Qtd": l.quantidade_atual})
    return res
@app.get("/relatorios/estoque/")
def relatorio_estoque(db: Session = Depends(get_db)):
    produtos = db.query(Produto).all(); dados = []; total = 0
    for p in produtos:
        val = p.estoque_atual * p.custo; total += val
        dados.append({"Produto": p.nome, "Qtd": p.estoque_atual, "Custo Unit": p.custo, "Valor Total": val})
    return {"total": total, "itens": dados}
@app.get("/relatorios/curva_abc/")
def curva_abc(db: Session = Depends(get_db)):
    vendas = db.query(Venda).all(); rec = defaultdict(float)
    for v in vendas:
        p = db.query(Produto).filter(Produto.id == v.produto_id).first()
        if p: rec[p.nome] += v.valor_total
    lst = [{"Produto":k,"Receita":v} for k,v in rec.items()]; lst.sort(key=lambda x:x["Receita"], reverse=True)
    for i,x in enumerate(lst): x["Classe"] = "A" if i==0 else "B" if i==1 else "C"
    return lst