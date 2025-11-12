import psycopg
from contextlib import contextmanager
from typing import Generator
from app.config import settings


@contextmanager
def get_db() -> Generator[psycopg.Connection, None, None]:
    """Database connection context manager."""
    conn = psycopg.connect(settings.database_url)
    try:
        yield conn
    finally:
        conn.close()


def get_db_cursor():
    """Get database cursor for dependency injection."""
    with get_db() as conn:
        with conn.cursor() as cur:
            yield cur
