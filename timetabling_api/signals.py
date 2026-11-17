"""Sinais de banco de dados para garantir integridade referencial e ACID no SQLite3."""

from django.db.backends.signals import connection_created
from django.dispatch import receiver


@receiver(connection_created)
def configurar_sqlite_acid(sender, connection, **kwargs) -> None:
    """Ativa chaves estrangeiras e modo WAL em toda conexão SQLite3."""
    if connection.vendor != "sqlite":
        return
    with connection.cursor() as cursor:
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.execute("PRAGMA journal_mode = WAL;")
        cursor.execute("PRAGMA synchronous = NORMAL;")
