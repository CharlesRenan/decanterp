import os
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, Boolean, Date, DateTime, extract
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date
from passlib.context import CryptContext
from fastapi.middleware.cors import CORSMiddleware
import io
from starlette.responses import StreamingResponse

# --- IMPORTAÇÕES PARA PDF AVANÇADO (RELATÓRIOS) ---
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# --- CONFIGURAÇÃO BANCO E APP ---
DATABASE_URL = "sqlite:///./decant_erp.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

# --- MODELOS (TABELAS) ---
class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    senha_hash = Column(String)
    cargo = Column(String)

class Cliente(Base):
    __tablename__ = "clientes"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String)
    email = Column(String)
    telefone = Column(String)

class Fornecedor(Base):
    __tablename__ = "fornecedores"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String)
    prazo_entrega_dias = Column(Integer)

class Produto(Base):
    __tablename__ = "produtos"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    tipo = Column(String) 
    unidade = Column(String)
    estoque_atual = Column(Float, default=0.0)
    custo = Column(Float, default=0.0)
    localizacao = Column(String, default="Geral")

class Formula(Base):
    __tablename__ = "formulas"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String)
    produto_final_id = Column(Integer, ForeignKey("produtos.id"))
    itens = relationship("FormulaItem", back_populates="formula")

class FormulaItem(Base):
    __tablename__ = "formula_itens"
    id = Column(Integer, primary_key=True, index=True)
    formula_id = Column(Integer, ForeignKey("formulas.id"))
    materia_prima_id = Column(Integer, ForeignKey("produtos.id"))
    quantidade = Column(Float)
    formula = relationship("Formula", back_populates="itens")

class Venda(Base):
    __tablename__ = "vendas"
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"))
    produto_id = Column(Integer, ForeignKey("produtos.id"))
    quantidade = Column(Float)
    valor_total = Column(Float)
    data_venda = Column(DateTime, default=datetime.now)
    metodo_pagamento = Column(String)
    grupo_id = Column(String)

class LancamentoFinanceiro(Base):
    __tablename__ = "financeiro"
    id = Column(Integer, primary_key=True, index=True)
    descricao = Column(String)
    tipo = Column(String)
    categoria = Column(String)
    valor = Column(Float)
    data_vencimento = Column(String)
    pago = Column(Boolean, default=False)
    data_lancamento = Column(Date, default=date.today) # Novo campo útil para filtros

class Compra(Base):
    __tablename__ = "compras"
    id = Column(Integer, primary_key=True, index=True)
    fornecedor_id = Column(Integer, ForeignKey("fornecedores.id"))
    produto_id = Column(Integer, ForeignKey("produtos.id"))
    quantidade = Column(Float)
    valor_unitario = Column(Float)
    status = Column(String, default="Pendente")
    data_pedido = Column(DateTime, default=datetime.now)

class Cotacao(Base):
    __tablename__ = "cotacoes"
    id = Column(Integer, primary_key=True, index=True)
    produto_id = Column(Integer, ForeignKey("produtos.id"))
    fornecedor_id = Column(Integer, ForeignKey("fornecedores.id"))
    preco = Column(Float)
    data_cotacao = Column(DateTime, default=datetime.now)

class ProducaoHistorico(Base):
    __tablename__ = "producao_historico"
    id = Column(Integer, primary_key=True, index=True)
    formula_id = Column(Integer)
    produto_nome = Column(String)
    quantidade_produzida = Column(Float)
    lote_gerado = Column(String)
    data_producao = Column(DateTime, default=datetime.now)

class Kardex(Base):
    __tablename__ = "kardex"
    id = Column(Integer, primary_key=True, index=True)
    produto_id = Column(Integer)
    tipo_movimento = Column(String)
    quantidade = Column(Float)
    data_movimento = Column(DateTime, default=datetime.now)

class Lote(Base):
    __tablename__ = "lotes"
    id = Column(Integer, primary_key=True, index=True)
    produto_id = Column(Integer, ForeignKey("produtos.id"))
    codigo_lote = Column(String)
    quantidade_inicial = Column(Float)
    quantidade_atual = Column(Float)
    validade = Column(String)
    data_entrada = Column(DateTime, default=datetime.now)

Base.metadata.create_all(bind=engine)

# --- SCHEMAS ---
class UsuarioBase(BaseModel):
    username: str
    senha: str
    cargo: str

class ProdutoBase(BaseModel):
    nome: str
    tipo: str
    unidade: str
    estoque_atual: float
    custo: float
    localizacao: str = "Geral"

class ClienteBase(BaseModel):
    nome: str
    email: str
    telefone: str

class FormulaItemBase(BaseModel):
    formula_id: int
    materia_prima_id: int
    quantidade: float

class FormulaBase(BaseModel):
    nome: str
    produto_final_id: int

class VendaItem(BaseModel):
    produto_id: int
    quantidade: float
    valor_total: float

class VendaCreate(BaseModel):
    cliente_id: int
    itens: List[VendaItem]
    metodo_pagamento: str

class LancamentoBase(BaseModel):
    descricao: str
    tipo: str
    categoria: str
    valor: float
    data_vencimento: str
    pago: bool

class CompraBase(BaseModel):
    produto_id: int
    fornecedor_id: int
    quantidade: float
    valor_unitario: float

class CotacaoBase(BaseModel):
    produto_id: int
    fornecedor_id: int
    preco: float

class FornecedorBase(BaseModel):
    nome: str
    prazo_entrega_dias: int

class ProducaoConfirmacao(BaseModel):
    formula_id: int
    quantidade: float
    lote_final: str
    validade_final: str

class ProcessarCompra(BaseModel):
    lote: str
    validade: str

def verificar_senha(senha_plana, senha_hash):
    return pwd_context.verify(senha_plana, senha_hash)

def registrar_kardex(db: Session, prod_id: int, tipo: str, qtd: float):
    k = Kardex(produto_id=prod_id, tipo_movimento=tipo, quantidade=qtd)
    db.add(k); db.commit()

# --- ENDPOINTS ---

@app.post("/auth/login/")
def login(u: UsuarioBase, db: Session = Depends(get_db)):
    if u.username == "admin" and u.senha == "123":
        return {"msg": "OK", "cargo": "Diretor", "usuario": "admin"}
    user = db.query(Usuario).filter(Usuario.username == u.username).first()
    if not user or not verificar_senha(u.senha, user.senha_hash):
        raise HTTPException(401, "Credenciais inválidas")
    return {"msg": "OK", "cargo": user.cargo, "usuario": user.username}

@app.post("/usuarios/")
def criar_usuario(u: UsuarioBase, db: Session = Depends(get_db)):
    hash_s = pwd_context.hash(u.senha)
    novo = Usuario(username=u.username, senha_hash=hash_s, cargo=u.cargo)
    db.add(novo); db.commit(); db.refresh(novo)
    return novo

@app.get("/usuarios/")
def listar_usuarios(db: Session = Depends(get_db)):
    return db.query(Usuario).all()

@app.post("/produtos/")
def criar_produto(p: ProdutoBase, db: Session = Depends(get_db)):
    db_p = Produto(nome=p.nome, tipo=p.tipo, unidade=p.unidade, estoque_atual=p.estoque_atual, custo=p.custo, localizacao=p.localizacao)
    db.add(db_p); db.commit(); db.refresh(db_p)
    registrar_kardex(db, db_p.id, "Estoque Inicial", p.estoque_atual)
    return db_p

@app.get("/produtos/")
def listar_produtos(db: Session = Depends(get_db)):
    return db.query(Produto).all()

@app.post("/clientes/")
def criar_cliente(c: ClienteBase, db: Session = Depends(get_db)):
    novo = Cliente(nome=c.nome, email=c.email, telefone=c.telefone)
    db.add(novo); db.commit(); db.refresh(novo)
    return novo

@app.get("/clientes/")
def listar_clientes(db: Session = Depends(get_db)):
    return db.query(Cliente).all()

@app.post("/vendas/pdv/")
def registrar_venda_pdv(v: VendaCreate, db: Session = Depends(get_db)):
    grupo = datetime.now().strftime("%Y%m%d%H%M%S")
    for item in v.itens:
        prod = db.query(Produto).filter(Produto.id == item.produto_id).first()
        if prod:
            if prod.estoque_atual >= item.quantidade:
                prod.estoque_atual -= item.quantidade
                registrar_kardex(db, prod.id, "Venda", -item.quantidade)
                nova_venda = Venda(cliente_id=v.cliente_id, produto_id=item.produto_id, quantidade=item.quantidade, valor_total=item.valor_total, metodo_pagamento=v.metodo_pagamento, grupo_id=grupo)
                db.add(nova_venda)
                lf = LancamentoFinanceiro(descricao=f"Venda PDV {prod.nome}", tipo="Receita", categoria="Vendas", valor=item.valor_total, data_vencimento=str(date.today()), pago=True)
                db.add(lf)
            else:
                raise HTTPException(400, f"Sem estoque para {prod.nome}")
    db.commit()
    return {"msg": "Venda OK", "grupo_id": grupo}

@app.get("/vendas/")
def listar_vendas(db: Session = Depends(get_db)):
    return db.query(Venda).order_by(Venda.id.desc()).all()

@app.get("/financeiro/lancamentos/")
def listar_financeiro(db: Session = Depends(get_db)):
    return db.query(LancamentoFinanceiro).order_by(LancamentoFinanceiro.id.desc()).all()

@app.post("/financeiro/lancamento/")
def criar_lancamento(l: LancamentoBase, db: Session = Depends(get_db)):
    novo = LancamentoFinanceiro(**l.dict())
    db.add(novo); db.commit(); db.refresh(novo)
    return novo

@app.post("/financeiro/pagar/{id}")
def pagar_conta(id: int, db: Session = Depends(get_db)):
    l = db.query(LancamentoFinanceiro).filter(LancamentoFinanceiro.id == id).first()
    if l:
        l.pago = True
        db.commit()
    return {"msg": "Pago"}

@app.get("/financeiro/dashboard/")
def dashboard(db: Session = Depends(get_db)):
    lancamentos = db.query(LancamentoFinanceiro).all()
    receita = sum([l.valor for l in lancamentos if l.tipo == 'Receita'])
    despesas = sum([l.valor for l in lancamentos if l.tipo == 'Despesa'])
    vendas = db.query(Venda).all() 
    grafico = [
        {"Mês": "Jan", "Valor": receita, "Tipo": "Entradas"},
        {"Mês": "Jan", "Valor": despesas, "Tipo": "Saídas"}
    ]
    return {"receita": receita, "despesas": despesas, "lucro": receita - despesas, "margem": ((receita-despesas)/receita*100) if receita > 0 else 0, "grafico": grafico}

# --- NOVO: Endpoint DRE (Demonstração do Resultado do Exercício) ---
@app.get("/relatorios/dre")
def relatorio_dre(inicio: str, fim: str, db: Session = Depends(get_db)):
    # Converte strings de data para objetos date
    dt_ini = datetime.strptime(inicio, "%Y-%m-%d").date()
    dt_fim = datetime.strptime(fim, "%Y-%m-%d").date()
    
    # Filtra lançamentos financeiros pela data (assumindo vencimento como data base simplificada)
    # Em um sistema real, usaria data_competencia
    lancamentos = db.query(LancamentoFinanceiro).all() 
    
    # Filtra na lista (python) por segurança de formato de data
    filtrados = [l for l in lancamentos if dt_ini <= datetime.strptime(l.data_vencimento, "%Y-%m-%d").date() <= dt_fim]
    
    receita_bruta = sum(l.valor for l in filtrados if l.categoria == 'Vendas')
    impostos = sum(l.valor for l in filtrados if l.categoria == 'Impostos')
    receita_liquida = receita_bruta - impostos
    
    custos_variaveis = sum(l.valor for l in filtrados if l.categoria in ['Matéria Prima', 'Despesa Variável'])
    margem_contribuicao = receita_liquida - custos_variaveis
    
    despesas_fixas = sum(l.valor for l in filtrados if l.categoria == 'Custos Fixos')
    lucro_liquido = margem_contribuicao - despesas_fixas
    
    return {
        "receita_bruta": receita_bruta,
        "impostos": impostos,
        "receita_liquida": receita_liquida,
        "custos_variaveis": custos_variaveis,
        "margem_contribuicao": margem_contribuicao,
        "despesas_fixas": despesas_fixas,
        "lucro_liquido": lucro_liquido
    }

# --- NOVO: Endpoint PDF de Vendas por Período ---
@app.get("/relatorios/vendas_pdf")
def relatorio_vendas_pdf(inicio: str, fim: str, db: Session = Depends(get_db)):
    dt_ini = datetime.strptime(inicio, "%Y-%m-%d")
    dt_fim = datetime.strptime(fim, "%Y-%m-%d")
    
    # Busca vendas no período
    vendas = db.query(Venda).filter(Venda.data_venda >= dt_ini, Venda.data_venda <= dt_fim).all()
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    # Título
    elements.append(Paragraph(f"Relatório de Vendas: {inicio} a {fim}", styles['Title']))
    elements.append(Spacer(1, 12))
    
    # Tabela
    data = [["ID", "Cliente", "Produto", "Qtd", "Valor (R$)"]] # Cabeçalho
    total = 0
    for v in vendas:
        cli = db.query(Cliente).filter(Cliente.id == v.cliente_id).first()
        prod = db.query(Produto).filter(Produto.id == v.produto_id).first()
        data.append([
            str(v.id),
            cli.nome if cli else "Desconhecido",
            prod.nome if prod else "?",
            str(v.quantidade),
            f"{v.valor_total:.2f}"
        ])
        total += v.valor_total
    
    data.append(["", "", "TOTAL:", "", f"{total:.2f}"])
    
    t = Table(data)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
    ]))
    elements.append(t)
    
    doc.build(elements)
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/pdf")

# --- NOVO: Endpoint PDF Estoque Valorado ---
@app.get("/relatorios/estoque_pdf")
def relatorio_estoque_pdf(db: Session = Depends(get_db)):
    prods = db.query(Produto).all()
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    elements.append(Paragraph("Relatório de Estoque Valorado", styles['Title']))
    elements.append(Spacer(1, 12))
    
    data = [["Produto", "Local", "Qtd", "Custo", "Total"]]
    total_geral = 0
    for p in prods:
        subtotal = p.estoque_atual * p.custo
        total_geral += subtotal
        data.append([
            p.nome,
            p.localizacao,
            f"{p.estoque_atual:.2f}",
            f"R$ {p.custo:.2f}",
            f"R$ {subtotal:.2f}"
        ])
    
    data.append(["", "", "", "TOTAL:", f"R$ {total_geral:.2f}"])
    
    t = Table(data)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    elements.append(t)
    
    doc.build(elements)
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/pdf")

# --- ENDPOINTS ANTIGOS MANTIDOS ---
@app.post("/formulas/")
def criar_formula(f: FormulaBase, db: Session = Depends(get_db)):
    nova = Formula(nome=f.nome, produto_final_id=f.produto_final_id)
    db.add(nova); db.commit(); db.refresh(nova)
    return nova

@app.post("/formulas/itens/")
def add_item_formula(i: FormulaItemBase, db: Session = Depends(get_db)):
    novo = FormulaItem(**i.dict())
    db.add(novo); db.commit()
    return novo

@app.get("/formulas/")
def listar_formulas(db: Session = Depends(get_db)):
    return db.query(Formula).all()

@app.delete("/formulas/itens/{id}")
def deletar_item_formula(id: int, db: Session = Depends(get_db)):
    db.query(FormulaItem).filter(FormulaItem.id == id).delete()
    db.commit()
    return {"ok": True}

@app.post("/planejamento/calcular/")
def calcular_mrp(formula_id: int, quantidade_producao: float, db: Session = Depends(get_db)):
    itens = db.query(FormulaItem).filter(FormulaItem.formula_id == formula_id).all()
    resultado = []
    custo_total = 0
    for item in itens:
        mp = db.query(Produto).filter(Produto.id == item.materia_prima_id).first()
        necessario = item.quantidade * quantidade_producao
        custo_parcial = necessario * mp.custo
        custo_total += custo_parcial
        resultado.append({
            "id": item.id,
            "ingrediente": mp.nome,
            "unidade": mp.unidade,
            "necessario": necessario,
            "custo_unit": mp.custo,
            "subtotal": custo_parcial
        })
    return {"materiais": resultado, "custo_total": custo_total}

@app.post("/producao/confirmar_lote/")
def confirmar_producao(p: ProducaoConfirmacao, db: Session = Depends(get_db)):
    formula = db.query(Formula).filter(Formula.id == p.formula_id).first()
    produto_final = db.query(Produto).filter(Produto.id == formula.produto_final_id).first()
    itens = db.query(FormulaItem).filter(FormulaItem.formula_id == p.formula_id).all()
    for item in itens:
        mp = db.query(Produto).filter(Produto.id == item.materia_prima_id).first()
        qtd_necessaria = item.quantidade * p.quantidade
        mp.estoque_atual -= qtd_necessaria
        registrar_kardex(db, mp.id, f"Produção Lote {p.lote_final}", -qtd_necessaria)
    produto_final.estoque_atual += p.quantidade
    registrar_kardex(db, produto_final.id, f"Entrada Produção {p.lote_final}", p.quantidade)
    hist = ProducaoHistorico(formula_id=p.formula_id, produto_nome=produto_final.nome, quantidade_produzida=p.quantidade, lote_gerado=p.lote_final)
    db.add(hist)
    novo_lote = Lote(produto_id=produto_final.id, codigo_lote=p.lote_final, quantidade_inicial=p.quantidade, quantidade_atual=p.quantidade, validade=p.validade_final)
    db.add(novo_lote)
    db.commit()
    return {"msg": "Produção Confirmada"}

@app.get("/producao/historico/")
def historico_producao(db: Session = Depends(get_db)):
    return db.query(ProducaoHistorico).order_by(ProducaoHistorico.id.desc()).all()

@app.post("/compras/")
def criar_pedido_compra(c: CompraBase, db: Session = Depends(get_db)):
    novo = Compra(**c.dict())
    db.add(novo); db.commit()
    return novo

@app.get("/compras")
def listar_compras(db: Session = Depends(get_db)):
    return db.query(Compra).order_by(Compra.id.desc()).all()

@app.post("/compras/{id}/processar/")
def receber_compra(id: int, dados: ProcessarCompra, db: Session = Depends(get_db)):
    compra = db.query(Compra).filter(Compra.id == id).first()
    if compra and compra.status == "Pendente":
        compra.status = "Recebido"
        prod = db.query(Produto).filter(Produto.id == compra.produto_id).first()
        prod.estoque_atual += compra.quantidade
        prod.custo = compra.valor_unitario 
        registrar_kardex(db, prod.id, f"Compra #{id}", compra.quantidade)
        lote = Lote(produto_id=prod.id, codigo_lote=dados.lote, quantidade_inicial=compra.quantidade, quantidade_atual=compra.quantidade, validade=dados.validade)
        db.add(lote)
        fin = LancamentoFinanceiro(descricao=f"Compra MP Pedido #{id}", tipo="Despesa", categoria="Matéria Prima", valor=compra.quantidade*compra.valor_unitario, data_vencimento=str(date.today()))
        db.add(fin)
        db.commit()
    return {"ok": True}

@app.get("/compras/{id}/pdf/")
def gerar_pdf_pedido(id: int, db: Session = Depends(get_db)):
    compra = db.query(Compra).filter(Compra.id == id).first()
    prod = db.query(Produto).filter(Produto.id == compra.produto_id).first()
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)
    p.drawString(100, 800, f"PEDIDO DE COMPRA #{id}")
    p.drawString(100, 780, f"Produto: {prod.nome}")
    p.drawString(100, 760, f"Quantidade: {compra.quantidade}")
    p.drawString(100, 740, f"Valor Unit: R$ {compra.valor_unitario}")
    p.showPage()
    p.save()
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/pdf")

@app.get("/vendas/{id}/pdf/")
def gerar_recibo_venda(id: int, db: Session = Depends(get_db)):
    venda = db.query(Venda).filter(Venda.id == id).first()
    prod = db.query(Produto).filter(Produto.id == venda.produto_id).first()
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)
    p.drawString(100, 800, f"RECIBO DE VENDA #{id}")
    p.drawString(100, 780, f"Item: {prod.nome}")
    p.drawString(100, 760, f"Total: R$ {venda.valor_total}")
    p.showPage()
    p.save()
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/pdf")

@app.get("/vendas/recibo/{grupo_id}/")
def recibo_grupo(grupo_id: str, db: Session = Depends(get_db)):
    vendas = db.query(Venda).filter(Venda.grupo_id == grupo_id).all()
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)
    y = 800
    p.drawString(100, y, f"CUPOM NÃO FISCAL - PEDIDO {grupo_id}")
    y -= 40
    total = 0
    for v in vendas:
        prod = db.query(Produto).filter(Produto.id == v.produto_id).first()
        p.drawString(100, y, f"{v.quantidade}x {prod.nome} - R$ {v.valor_total:.2f}")
        total += v.valor_total
        y -= 20
    p.drawString(100, y-20, f"TOTAL: R$ {total:.2f}")
    p.showPage()
    p.save()
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/pdf")

@app.post("/fornecedores/")
def criar_fornecedor(f: FornecedorBase, db: Session = Depends(get_db)):
    novo = Fornecedor(**f.dict())
    db.add(novo); db.commit(); db.refresh(novo)
    return novo

@app.get("/fornecedores/")
def listar_fornecedores(db: Session = Depends(get_db)):
    return db.query(Fornecedor).all()

@app.post("/cotacoes/")
def criar_cotacao(c: CotacaoBase, db: Session = Depends(get_db)):
    novo = Cotacao(**c.dict())
    db.add(novo); db.commit()
    return novo

@app.get("/cotacoes/")
def listar_cotacoes(db: Session = Depends(get_db)):
    return db.query(Cotacao).all()

@app.get("/estoque/kardex")
def ver_kardex(db: Session = Depends(get_db)):
    return db.query(Kardex).order_by(Kardex.id.desc()).all()

@app.get("/relatorios/estoque/")
def relatorio_estoque(db: Session = Depends(get_db)):
    prods = db.query(Produto).all()
    itens = []
    for p in prods:
        itens.append({"Produto": p.nome, "Estoque": p.estoque_atual, "Unid": p.unidade, "Custo": p.custo, "Total": p.estoque_atual*p.custo, "Local": p.localizacao})
    return {"itens": itens}

@app.get("/relatorios/lotes_vencimento/")
def relatorio_lotes(db: Session = Depends(get_db)):
    return db.query(Lote).all()

@app.get("/crm/oportunidades")
def crm_oportunidades(db: Session = Depends(get_db)):
    clientes = db.query(Cliente).all()
    resultado = []
    for c in clientes:
        ultima_venda = db.query(Venda).filter(Venda.cliente_id == c.id).order_by(Venda.data_venda.desc()).first()
        if ultima_venda:
            dias = (datetime.now() - ultima_venda.data_venda).days
            if dias > 25: 
                prod = db.query(Produto).filter(Produto.id == ultima_venda.produto_id).first()
                resultado.append({
                    "Cliente": c.nome,
                    "Telefone": c.telefone,
                    "Último Produto": prod.nome,
                    "Dias sem Comprar": dias,
                    "Status": "Risco de Perda"
                })
    return resultado

@app.get("/sistema/backup/")
def baixar_backup():
    if os.path.exists("decant_erp.db"):
        return StreamingResponse(open("decant_erp.db", "rb"), media_type="application/octet-stream")
    raise HTTPException(404, "Banco não encontrado")

@app.delete("/sistema/resetar_dados/")
def resetar_tudo(db: Session = Depends(get_db)):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    hash_admin = pwd_context.hash("123")
    admin = Usuario(username="admin", senha_hash=hash_admin, cargo="Diretor")
    db.add(admin)
    db.commit()
    return {"msg": "Sistema Zerado com Sucesso"}