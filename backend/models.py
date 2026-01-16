from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean, Date
from sqlalchemy.orm import relationship
from backend.database import Base
from datetime import datetime

class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    senha_hash = Column(String)
    cargo = Column(String)

class Lancamento(Base):
    __tablename__ = "financeiro"
    id = Column(Integer, primary_key=True, index=True)
    descricao = Column(String)
    tipo = Column(String)
    categoria = Column(String)
    valor = Column(Float)
    data_vencimento = Column(Date)
    pago = Column(Boolean, default=False)
    data_pagamento = Column(Date, nullable=True)

class Produto(Base):
    __tablename__ = "produtos"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    tipo = Column(String)
    unidade = Column(String)
    estoque_atual = Column(Float, default=0.0)
    custo = Column(Float, default=0.0)

class Lote(Base):
    __tablename__ = "lotes"
    id = Column(Integer, primary_key=True, index=True)
    produto_id = Column(Integer, ForeignKey("produtos.id"))
    codigo = Column(String)
    validade = Column(String)
    quantidade_atual = Column(Float)
    data_entrada = Column(DateTime, default=datetime.utcnow)

class Movimentacao(Base):
    __tablename__ = "movimentacoes"
    id = Column(Integer, primary_key=True, index=True)
    produto_id = Column(Integer, ForeignKey("produtos.id"))
    tipo = Column(String)
    quantidade = Column(Float)
    origem = Column(String)
    data = Column(DateTime, default=datetime.utcnow)
    usuario = Column(String)

class Fornecedor(Base):
    __tablename__ = "fornecedores"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String)
    prazo_entrega_dias = Column(Integer)

class Cliente(Base):
    __tablename__ = "clientes"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String)
    email = Column(String)
    telefone = Column(String)

class Cotacao(Base):
    __tablename__ = "cotacoes"
    id = Column(Integer, primary_key=True, index=True)
    produto_id = Column(Integer, ForeignKey("produtos.id"))
    fornecedor_id = Column(Integer, ForeignKey("fornecedores.id"))
    preco = Column(Float)

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
    materia_prima = relationship("Produto")

class PedidoCompra(Base):
    __tablename__ = "pedidos_compra"
    id = Column(Integer, primary_key=True, index=True)
    fornecedor_id = Column(Integer, ForeignKey("fornecedores.id"))
    produto_id = Column(Integer, ForeignKey("produtos.id"))
    quantidade = Column(Float)
    valor_unitario = Column(Float)
    status = Column(String)

class OrdemProducao(Base):
    __tablename__ = "ordens_producao"
    id = Column(Integer, primary_key=True, index=True)
    formula_id = Column(Integer, ForeignKey("formulas.id"))
    quantidade_produzida = Column(Float)
    lote_codigo = Column(String)
    data_producao = Column(DateTime, default=datetime.utcnow)
    status = Column(String)

class Venda(Base):
    __tablename__ = "vendas"
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"))
    produto_id = Column(Integer, ForeignKey("produtos.id"))
    quantidade = Column(Float)
    valor_total = Column(Float)
    metodo_pagamento = Column(String) # NOVO: Pix, Crédito, Débito
    venda_agrupada_id = Column(String) # NOVO: ID único do Carrinho
    data_venda = Column(DateTime, default=datetime.utcnow)