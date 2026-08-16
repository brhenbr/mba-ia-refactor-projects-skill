from sqlalchemy import func

from database import db
from models.pedido import Pedido

FATURAMENTO_MINIMO_DESCONTO_ALTO = 10000
DESCONTO_ALTO = 0.1
FATURAMENTO_MINIMO_DESCONTO_MEDIO = 5000
DESCONTO_MEDIO = 0.05
FATURAMENTO_MINIMO_DESCONTO_BAIXO = 1000
DESCONTO_BAIXO = 0.02


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
        if faturamento > FATURAMENTO_MINIMO_DESCONTO_ALTO:
            return faturamento * DESCONTO_ALTO
        if faturamento > FATURAMENTO_MINIMO_DESCONTO_MEDIO:
            return faturamento * DESCONTO_MEDIO
        if faturamento > FATURAMENTO_MINIMO_DESCONTO_BAIXO:
            return faturamento * DESCONTO_BAIXO
        return 0
