from sqlalchemy import func

from database import db
from models.pedido import Pedido


class RelatorioService:
    def vendas(self):
        total_pedidos = db.session.query(func.count(Pedido.id)).scalar()
        faturamento = db.session.query(func.sum(Pedido.total)).scalar() or 0

        contagens_por_status = dict(
            db.session.query(Pedido.status, func.count(Pedido.id)).group_by(Pedido.status).all()
        )
        pendentes = contagens_por_status.get("pendente", 0)
        aprovados = contagens_por_status.get("aprovado", 0)
        cancelados = contagens_por_status.get("cancelado", 0)

        desconto = self._calcular_desconto(faturamento)

        return {
            "total_pedidos": total_pedidos,
            "faturamento_bruto": round(faturamento, 2),
            "desconto_aplicavel": round(desconto, 2),
            "faturamento_liquido": round(faturamento - desconto, 2),
            "pedidos_pendentes": pendentes,
            "pedidos_aprovados": aprovados,
            "pedidos_cancelados": cancelados,
            "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
        }

    @staticmethod
    def _calcular_desconto(faturamento):
        if faturamento > 10000:
            return faturamento * 0.1
        if faturamento > 5000:
            return faturamento * 0.05
        if faturamento > 1000:
            return faturamento * 0.02
        return 0
