import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


class Config:
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-key-change-in-prod")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-key-change-in-prod")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    CORS_ORIGINS = [o for o in os.getenv("CORS_ORIGINS", "").split(",") if o]


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///loja.db")


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")

    @staticmethod
    def validate():
        """Chamado explicitamente por create_app() ao selecionar este ambiente,
        não na importação do módulo (que aconteceria mesmo rodando em dev/test)."""
        obrigatorias = ["SECRET_KEY", "JWT_SECRET_KEY", "DATABASE_URL"]
        faltando = [var for var in obrigatorias if not os.getenv(var)]
        if faltando:
            raise RuntimeError(f"Variáveis obrigatórias em produção não configuradas: {', '.join(faltando)}")


class TestingConfig(Config):
    TESTING = True
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}
