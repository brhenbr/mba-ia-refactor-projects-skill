from sqlalchemy.orm import joinedload, selectinload

from database import db
from models.pedido import Pedido
from models.item_pedido import ItemPedido


class PedidoRepository:
    def _query_com_itens(self):
        # Eager loading evita N+1: 1 query para pedidos + itens + produtos relacionados
        return Pedido.query.options(selectinload(Pedido.itens).joinedload(ItemPedido.produto))

    def find_all(self):
        return self._query_com_itens().all()

    def find_by_id(self, pedido_id):
        return self._query_com_itens().filter_by(id=pedido_id).first()

    def find_by_usuario(self, usuario_id):
        return self._query_com_itens().filter_by(usuario_id=usuario_id).all()

    def create(self, usuario_id, itens_para_criar, total):
        """Cria pedido + itens em uma única transação atômica."""
        pedido = Pedido(usuario_id=usuario_id, status="pendente", total=total)
        db.session.add(pedido)
        db.session.flush()  # obtém pedido.id sem commitar

        for item in itens_para_criar:
            db.session.add(
                ItemPedido(
                    pedido_id=pedido.id,
                    produto_id=item["produto_id"],
                    quantidade=item["quantidade"],
                    preco_unitario=item["preco_unitario"],
                )
            )
            item["produto"].estoque -= item["quantidade"]

        db.session.commit()
        return pedido

    def update_status(self, pedido, novo_status):
        pedido.status = novo_status
        db.session.commit()
        return pedido
