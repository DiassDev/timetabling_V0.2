"""Configuração do app timetabling_api."""

from django.apps import AppConfig


class TimetablingApiConfig(AppConfig):
    """Inicializa o app e registra sinais de integridade do SQLite3."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "timetabling_api"

    def ready(self) -> None:
        from . import signals  # noqa: F401
