from database import db
from utils import agora_utc

STATUS_VALIDOS = ["pendente", "aprovado", "enviado", "entregue", "cancelado"]


class Pedido(db.Model):
    __tablename__ = "pedidos"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    status = db.Column(db.String(50), nullable=False, default="pendente")
    total = db.Column(db.Float, nullable=False, default=0)
    criado_em = db.Column(db.DateTime, default=agora_utc)

    usuario = db.relationship("Usuario", backref="pedidos")
    itens = db.relationship("ItemPedido", backref="pedido", cascade="all, delete-orphan")

    def pertence_a(self, usuario_id):
        return self.usuario_id == usuario_id

    def to_dict(self):
        return {
            "id": self.id,
            "usuario_id": self.usuario_id,
            "status": self.status,
            "total": self.total,
            "criado_em": self.criado_em.isoformat() if self.criado_em else None,
            "itens": [item.to_dict() for item in self.itens],
        }
