from database import db


class ItemPedido(db.Model):
    __tablename__ = "itens_pedido"

    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey("pedidos.id"), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey("produtos.id"), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    preco_unitario = db.Column(db.Float, nullable=False)

    produto = db.relationship("Produto")

    def to_dict(self):
        return {
            "produto_id": self.produto_id,
            "produto_nome": self.produto.nome if self.produto else "Desconhecido",
            "quantidade": self.quantidade,
            "preco_unitario": self.preco_unitario,
        }
