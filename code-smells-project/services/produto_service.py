from exceptions import NotFoundException
from repositories.produto_repository import ProdutoRepository


class ProdutoService:
    def __init__(self, produto_repo=None):
        self.produto_repo = produto_repo or ProdutoRepository()

    def listar(self):
        return self.produto_repo.find_all()

    def buscar_por_id(self, produto_id):
        produto = self.produto_repo.find_by_id(produto_id)
        if not produto:
            raise NotFoundException("Produto não encontrado")
        return produto

    def buscar(self, termo, categoria, preco_min, preco_max):
        return self.produto_repo.search(termo, categoria, preco_min, preco_max)

    def criar(self, dados):
        return self.produto_repo.create(dados)

    def atualizar(self, produto_id, dados):
        produto = self.buscar_por_id(produto_id)
        return self.produto_repo.update(produto, dados)

    def deletar(self, produto_id):
        produto = self.buscar_por_id(produto_id)
        self.produto_repo.delete(produto)
