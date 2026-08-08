from database import db
from models.produto import Produto


class ProdutoRepository:
    def find_all(self):
        return Produto.query.all()

    def find_by_id(self, produto_id):
        return db.session.get(Produto, produto_id)

    def search(self, termo=None, categoria=None, preco_min=None, preco_max=None):
        query = Produto.query

        if termo:
            like = f"%{termo}%"
            query = query.filter(db.or_(Produto.nome.like(like), Produto.descricao.like(like)))
        if categoria:
            query = query.filter_by(categoria=categoria)
        if preco_min is not None:
            query = query.filter(Produto.preco >= preco_min)
        if preco_max is not None:
            query = query.filter(Produto.preco <= preco_max)

        return query.all()

    def create(self, dados):
        produto = Produto(**dados)
        db.session.add(produto)
        db.session.commit()
        return produto

    def update(self, produto, dados):
        for chave, valor in dados.items():
            setattr(produto, chave, valor)
        db.session.commit()
        return produto

    def delete(self, produto):
        db.session.delete(produto)
        db.session.commit()

    def decrementar_estoque(self, produto, quantidade):
        produto.estoque -= quantidade
