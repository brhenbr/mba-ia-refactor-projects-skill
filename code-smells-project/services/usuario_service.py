from exceptions import BusinessException, NotFoundException
from models.usuario import Usuario
from repositories.usuario_repository import UsuarioRepository


class UsuarioService:
    def __init__(self, usuario_repo=None):
        self.usuario_repo = usuario_repo or UsuarioRepository()

    def listar(self):
        return self.usuario_repo.find_all()

    def buscar_por_id(self, usuario_id):
        usuario = self.usuario_repo.find_by_id(usuario_id)
        if not usuario:
            raise NotFoundException("Usuário não encontrado")
        return usuario

    def registrar(self, dados):
        if self.usuario_repo.find_by_email(dados["email"]):
            raise BusinessException("Email já cadastrado", status_code=409)

        usuario = Usuario(nome=dados["nome"], email=dados["email"], tipo="cliente")
        usuario.set_senha(dados["senha"])
        return self.usuario_repo.create(usuario)

    def autenticar(self, email, senha):
        usuario = self.usuario_repo.find_by_email(email)
        if not usuario or not usuario.checar_senha(senha):
            raise BusinessException("Email ou senha inválidos", status_code=401)
        return usuario
