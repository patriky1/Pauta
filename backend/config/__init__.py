# Carrega o Celery junto com o Django para que `shared_task` use a app do projeto.
# Sem o pacote instalado o site continua funcionando (so a coleta agendada fica parada).
try:
    from .celery import app as celery_app
except ImportError:  # pragma: no cover
    celery_app = None

__all__ = ("celery_app",)
