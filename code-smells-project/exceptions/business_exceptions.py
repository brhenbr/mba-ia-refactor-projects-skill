class BusinessException(Exception):
    """Erro de regra de negócio esperado (400 por padrão)."""

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class NotFoundException(BusinessException):
    def __init__(self, message="Recurso não encontrado"):
        super().__init__(message, status_code=404)


class ForbiddenException(BusinessException):
    def __init__(self, message="Sem permissão"):
        super().__init__(message, status_code=403)
