from exceptions import BusinessException, NotFoundException
from repositories.pedido_repository import PedidoRepository
from repositories.produto_repository import ProdutoRepository


class PedidoService:
    def __init__(self, pedido_repo=None, produto_repo=None):
        self.pedido_repo = pedido_repo or PedidoRepository()
        self.produto_repo = produto_repo or ProdutoRepository()

    def criar(self, usuario_id, itens):
        """Valida disponibilidade de todos os itens antes de persistir (evita
        gravações parciais em caso de item inválido no meio do pedido)."""
        itens_para_criar = []
        total = 0

        for item in itens:
            produto = self.produto_repo.find_by_id(item["produto_id"])
            if produto is None:
                raise BusinessException(f"Produto {item['produto_id']} não encontrado")
            if not produto.tem_estoque(item["quantidade"]):
                raise BusinessException(f"Estoque insuficiente para {produto.nome}")

            subtotal = produto.preco * item["quantidade"]
            total += subtotal
            itens_para_criar.append(
                {
                    "produto_id": produto.id,
                    "quantidade": item["quantidade"],
                    "preco_unitario": produto.preco,
                    "produto": produto,
                }
            )

        return self.pedido_repo.create(usuario_id, itens_para_criar, total)

    def buscar_por_id(self, pedido_id):
        pedido = self.pedido_repo.find_by_id(pedido_id)
        if not pedido:
            raise NotFoundException("Pedido não encontrado")
        return pedido

    def listar_por_usuario(self, usuario_id):
        return self.pedido_repo.find_by_usuario(usuario_id)

    def listar_todos(self):
        return self.pedido_repo.find_all()

    def atualizar_status(self, pedido_id, novo_status):
        pedido = self.buscar_por_id(pedido_id)
        return self.pedido_repo.update_status(pedido, novo_status)
