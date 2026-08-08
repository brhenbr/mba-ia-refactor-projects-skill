import bcrypt

from database import db
from utils import agora_utc

TIPOS_VALIDOS = ["cliente", "admin"]


class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=False, unique=True)
    senha_hash = db.Column(db.String(255), nullable=False)
    tipo = db.Column(db.String(20), nullable=False, default="cliente")
    criado_em = db.Column(db.DateTime, default=agora_utc)

    def set_senha(self, senha):
        salt = bcrypt.gensalt(rounds=12)
        self.senha_hash = bcrypt.hashpw(senha.encode(), salt).decode()

    def checar_senha(self, senha):
        return bcrypt.checkpw(senha.encode(), self.senha_hash.encode())

    def is_admin(self):
        return self.tipo == "admin"

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "email": self.email,
            "tipo": self.tipo,
            "criado_em": self.criado_em.isoformat() if self.criado_em else None,
        }
