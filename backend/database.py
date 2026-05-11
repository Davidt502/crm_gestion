"""
database.py - Conexión a PostgreSQL (Supabase) con psycopg2
Usa context manager para evitar fugas de conexión.

BUGS CORREGIDOS:
  1. ejecutar_funcion() usaba db_connection() con cursor de TUPLAS.
     sp_result() hacía row.get('id_usuario_result') que es método de dict,
     no de tuple → AttributeError → 500 en TODOS los endpoints que crean/editan.
     FIX: cambiado a db_connection_dict() con RealDictCursor.

  2. sp_result() no conocía id_compra_result → crear/actualizar compras
     siempre retornaba is_error=True aunque el SP tuviera éxito.
     FIX: agregado id_compra_result a la lista de IDs posibles.
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()

# Configuración desde variables de entorno
DB_CONFIG = {
    'host':     os.getenv('DB_HOST', 'localhost'),
    'port':     int(os.getenv('DB_PORT', '5432')),
    'database': os.getenv('DB_NAME', 'postgres'),
    'user':     os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD'),
    'sslmode':  os.getenv('DB_SSLMODE', 'require'),
}


def get_connection():
    """Abre y retorna una conexión a PostgreSQL."""
    return psycopg2.connect(**DB_CONFIG)


@contextmanager
def db_connection():
    """
    Context manager seguro — cursor de TUPLAS.
    Usar para SELECT simples donde no se necesita sp_result().
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


@contextmanager
def db_connection_dict():
    """
    Context manager que retorna cursor con resultados como diccionarios (RealDictCursor).
    Usar siempre que el resultado deba leerse por nombre de columna.
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
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
    """Convierte valor a int de forma segura."""
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def sp_result(row):
    """
    Interpreta la fila de retorno estándar de los Stored Procedures del CRM.

    Todas las funciones del proyecto devuelven:
        TABLE(id_<modulo>_result INT, mensaje_result TEXT, is_error BOOLEAN)

    Retorna: (id_or_none, mensaje, is_error)
      - is_error=True  → el SP reportó un error de negocio; id_or_none=None
      - is_error=False → éxito; id_or_none=int con el ID creado/modificado

    BUG-FIX: agregado id_compra_result (faltaba → compras siempre fallaban).
    """
    if row is None:
        return None, "Sin respuesta del servidor.", True

    if isinstance(row, dict):
        # BUG-FIX: incluye id_compra_result que faltaba en la versión original
        id_val = (
            row.get("id_cliente_result")   or
            row.get("id_proveedor_result") or
            row.get("id_usuario_result")   or
            row.get("id_contacto_result")  or
            row.get("id_empleado_result")  or
            row.get("id_compra_result")
        )
        mensaje   = row.get("mensaje_result", "")
        # Si el SP devuelve is_error explícito, usarlo aunque id no sea None
        is_error_flag = row.get("is_error", None)
    else:
        # Fallback para tuplas (no debería ocurrir con ejecutar_funcion corregido)
        id_val        = row[0] if len(row) > 0 else None
        mensaje       = row[1] if len(row) > 1 else ""
        is_error_flag = row[2] if len(row) > 2 else None

    id_val = to_int(id_val)

    # Si el SP devuelve is_error=True explícitamente, confiar en él
    if is_error_flag is True:
        return None, mensaje, True

    if id_val is None or id_val < 0:
        return None, mensaje, True

    return id_val, mensaje, False


def ejecutar_funcion(nombre_funcion, *args):
    """
    Ejecuta una función PostgreSQL y retorna su resultado como dict.

    BUG-FIX: la versión original usaba db_connection() con cursor de TUPLAS.
    sp_result() intentaba hacer row.get('id_usuario_result') sobre una tupla
    → AttributeError → 500 en crear/actualizar usuario, empleado, cliente, etc.

    FIX: usa db_connection_dict() con RealDictCursor para que fetchone()
    devuelva un dict y sp_result() pueda leer por nombre de columna.
    """
    with db_connection_dict() as (conn, cursor):
        placeholders = ",".join(["%s"] * len(args))
        query = f"SELECT * FROM {nombre_funcion}({placeholders})"
        cursor.execute(query, list(args))
        if cursor.description:
            return cursor.fetchone()
        return None