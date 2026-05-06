"""
database.py - Conexión a SQL Server con pymssql
Usa context manager para evitar fugas de conexión.
"""
import pymssql
from contextlib import contextmanager
from decimal import Decimal
from config import DB_CONFIG


def get_connection():
    """Abre y retorna una conexión a SQL Server."""
    return pymssql.connect(
        server=DB_CONFIG['server'],
        port=DB_CONFIG['port'],
        user=DB_CONFIG['username'],
        password=DB_CONFIG['password'],
        database=DB_CONFIG['database'],
        charset='UTF-8',
        login_timeout=10,
        timeout=30,
    )


@contextmanager
def db_connection():
    """
    Context manager seguro para conexiones DB.
    Garantiza que la conexión siempre se cierre, incluso ante excepciones.

    Uso:
        with db_connection() as (conn, cursor):
            cursor.execute(...)
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        yield conn, cursor
        conn.commit()
    except Exception:
        if conn:
            try:
                conn.rollback()
            except Exception:
                pass
        raise
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


def to_int(value):
    """
    Convierte Decimal o int a int.
    SQL Server a través de pymssql retorna Decimal, esta función
    normaliza el valor a int para compatibilidad.
    """
    if isinstance(value, Decimal):
        return int(value)
    if isinstance(value, int):
        return value
    return None


def sp_result(row):
    """
    Interpreta la fila de retorno estándar de los Stored Procedures del CRM.

    Todos los SPs de este proyecto devuelven (codigo, mensaje) donde:
      - codigo < 50000  → éxito real (es el ID del registro creado/actualizado)
      - codigo >= 50000 → error del SP (50001 = duplicado, 50002 = no encontrado, etc.)

    Retorna una tupla (id_or_none, mensaje, is_error):
      - is_error=True  → el SP reportó un error, id_or_none=None
      - is_error=False → operación exitosa, id_or_none=int con el ID real
    """
    if row is None:
        return None, "Sin respuesta del servidor.", True
    codigo = to_int(row[0])
    mensaje = row[1] if len(row) > 1 else ""
    if codigo is not None and codigo >= 50000:
        return None, mensaje, True
    return codigo, mensaje, False
