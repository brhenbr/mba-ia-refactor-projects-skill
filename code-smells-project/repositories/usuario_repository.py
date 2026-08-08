from database import db
from models.usuario import Usuario


class UsuarioRepository:
    def find_all(self):
        return Usuario.query.all()

    def find_by_id(self, usuario_id):
        return db.session.get(Usuario, usuario_id)

    def find_by_email(self, email):
        return Usuario.query.filter_by(email=email).first()

    def exists(self, usuario_id):
        return db.session.query(Usuario.query.filter_by(id=usuario_id).exists()).scalar()

    def create(self, usuario):
        db.session.add(usuario)
        db.session.commit()
        return usuario
