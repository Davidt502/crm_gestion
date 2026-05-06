"""
database.py - Conexión a PostgreSQL (Supabase) con psycopg2
Usa context manager para evitar fugas de conexión.
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()

# Configuración desde variables de entorno
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '5432')),
    'database': os.getenv('DB_NAME', 'postgres'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD'),
    'sslmode': os.getenv('DB_SSLMODE', 'require')
}


def get_connection():
    """Abre y retorna una conexión a PostgreSQL."""
    return psycopg2.connect(**DB_CONFIG)


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


@contextmanager
def db_connection_dict():
    """
    Context manager que retorna cursor con resultados como diccionarios.
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
    Interpreta la fila de retorno estándar de los Stored Procedures/Funciones del CRM.
    
    Todas las funciones de este proyecto devuelven (id, mensaje) donde:
      - id != None y > 0 → éxito real (es el ID del registro creado/actualizado)
      - id == None → error del SP
    
    Retorna una tupla (id_or_none, mensaje, is_error):
      - is_error=True  → la función reportó un error, id_or_none=None
      - is_error=False → operación exitosa, id_or_none=int con el ID real
    """
    if row is None:
        return None, "Sin respuesta del servidor.", True
    
    # row puede ser un dict o una tupla
    if isinstance(row, dict):
        id_val = row.get('id_cliente_result') or row.get('id_proveedor_result') or row.get('id_usuario_result') or row.get('id_contacto_result') or row.get('id_empleado_result')
        mensaje = row.get('mensaje_result', '')
    else:
        id_val = row[0] if len(row) > 0 else None
        mensaje = row[1] if len(row) > 1 else ""
    
    id_val = to_int(id_val)
    
    if id_val is None or id_val < 0:
        return None, mensaje, True
    
    return id_val, mensaje, False


def ejecutar_funcion(nombre_funcion, *args):
    """
    Ejecuta una función de PostgreSQL y retorna su resultado.
    """
    with db_connection() as (conn, cursor):
        # Construir la llamada con placeholders
        placeholders = ','.join(['%s'] * len(args))
        query = f"SELECT * FROM {nombre_funcion}({placeholders})"
        cursor.execute(query, args)
        
        # Obtener resultados
        if cursor.description:
            row = cursor.fetchone()
            return row
        return None
