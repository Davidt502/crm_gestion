"""
proveedor_repository.py - Capa de acceso a datos para Proveedores
Correcciones:
  - Context manager en todas las funciones (no fugas de conexión)
  - OFFSET/FETCH parametrizados
  - Manejo de excepciones con logging
  - Conversión de filas a diccionarios con función auxiliar
"""
import logging
from database import db_connection

logger = logging.getLogger(__name__)


def _row_to_dict(row) -> dict:
    return {
        "id_proveedor":        row[0],
        "nombre_empresa":      row[1],
        "nit":                 row[2],
        "id_categoria":        row[3],
        "categoria":           row[4],
        "contacto":            row[5],
        "telefono":            row[6],
        "correo":              row[7],
        "direccion":           row[8],
        "notas":               row[9],
        "estado":              row[10],
        "motivo_inactivacion": row[11],
        "fecha_creacion":      row[12].strftime("%Y-%m-%d %H:%M:%S") if row[12] else None,
    }


def find_all(where_clauses, params, offset, per_page):
    where_str = " AND ".join(where_clauses) if where_clauses else "1=1"
    try:
        with db_connection() as (conn, cursor):
            cursor.execute(
                f"""
                SELECT COUNT(*) FROM proveedores p
                JOIN categorias_proveedor c ON p.id_categoria = c.id_categoria
                WHERE {where_str}
                """,
                params,
            )
            total = cursor.fetchone()[0]

            cursor.execute(
                f"""
                SELECT p.id_proveedor, p.nombre_empresa, p.nit, p.id_categoria,
                       c.nombre_categoria, p.contacto, p.telefono, p.correo,
                       p.direccion, p.notas, p.estado, p.motivo_inactivacion, p.fecha_creacion
                FROM proveedores p
                JOIN categorias_proveedor c ON p.id_categoria = c.id_categoria
                WHERE {where_str}
                ORDER BY p.fecha_creacion DESC
                OFFSET %s ROWS FETCH NEXT %s ROWS ONLY
                """,
                params + [offset, per_page],
            )
            rows = cursor.fetchall()

        return [_row_to_dict(r) for r in rows], total
    except Exception as exc:
        logger.error("find_all proveedores: %s", exc, exc_info=True)
        return [], 0


def find_by_id(id_proveedor):
    try:
        with db_connection() as (conn, cursor):
            cursor.execute(
                """
                SELECT p.id_proveedor, p.nombre_empresa, p.nit, p.id_categoria,
                       c.nombre_categoria, p.contacto, p.telefono, p.correo,
                       p.direccion, p.notas, p.estado, p.motivo_inactivacion, p.fecha_creacion
                FROM proveedores p
                JOIN categorias_proveedor c ON p.id_categoria = c.id_categoria
                WHERE p.id_proveedor = %s
                """,
                [id_proveedor],
            )
            row = cursor.fetchone()
        return _row_to_dict(row) if row else None
    except Exception as exc:
        logger.error("find_by_id proveedor: %s", exc, exc_info=True)
        return None


def find_all_categorias():
    try:
        with db_connection() as (conn, cursor):
            cursor.execute(
                """
                SELECT id_categoria, nombre_categoria
                FROM categorias_proveedor
                WHERE estado='Activo'
                ORDER BY nombre_categoria
                """
            )
            rows = cursor.fetchall()
        return [{"id": r[0], "nombre": r[1]} for r in rows]
    except Exception as exc:
        logger.error("find_all_categorias: %s", exc, exc_info=True)
        return []


def insert(data):
    try:
        with db_connection() as (conn, cursor):
            cursor.callproc("sp_registrar_proveedor", [
                data.get("nombre_empresa", ""),
                data.get("nit", ""),
                int(data.get("id_categoria", 0)),
                data.get("telefono", ""),
                data.get("contacto") or None,
                data.get("correo") or None,
                data.get("direccion") or None,
                data.get("notas") or None,
                data.get("usuario", "sistema"),
            ])
            row = cursor.fetchone()
        return row
    except Exception as exc:
        logger.error("insert proveedor: %s", exc, exc_info=True)
        return None


def update(id_proveedor, data):
    try:
        with db_connection() as (conn, cursor):
            cursor.callproc("sp_actualizar_proveedor", [
                id_proveedor,
                data.get("nombre_empresa", ""),
                data.get("nit", ""),
                int(data.get("id_categoria", 0)),
                data.get("telefono", ""),
                data.get("contacto") or None,
                data.get("correo") or None,
                data.get("direccion") or None,
                data.get("notas") or None,
                data.get("usuario", "sistema"),
            ])
            row = cursor.fetchone()
        return row
    except Exception as exc:
        logger.error("update proveedor: %s", exc, exc_info=True)
        return None


def set_inactive(id_proveedor, motivo, usuario):
    try:
        with db_connection() as (conn, cursor):
            cursor.callproc("sp_inactivar_proveedor", [id_proveedor, motivo, usuario])
            row = cursor.fetchone()
        return row
    except Exception as exc:
        logger.error("set_inactive proveedor: %s", exc, exc_info=True)
        return None


def set_active(id_proveedor, usuario):
    try:
        with db_connection() as (conn, cursor):
            cursor.callproc("sp_activar_proveedor", [id_proveedor, usuario])
            row = cursor.fetchone()
        return row
    except Exception as exc:
        logger.error("set_active proveedor: %s", exc, exc_info=True)
        return None


def delete(id_proveedor, usuario):
    try:
        with db_connection() as (conn, cursor):
            cursor.callproc("sp_eliminar_proveedor", [id_proveedor, usuario])
            row = cursor.fetchone()
        return row
    except Exception as exc:
        logger.error("delete proveedor: %s", exc, exc_info=True)
        return None
