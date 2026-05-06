"""
cliente_repository.py - Capa de acceso a datos para Clientes
Correcciones:
  - Context manager en todas las funciones (no fugas de conexión)
  - OFFSET/FETCH parametrizados
  - Manejo de excepciones con logging
"""
import logging
from database import db_connection, to_int, sp_result

logger = logging.getLogger(__name__)


def _row_to_dict(row) -> dict:
    return {
        "id_cliente":               row[0],
        "nombre_razon_social":      row[1],
        "documento_identificacion": row[2],
        "tipo":                     row[3],
        "estado":                   row[4],
        "fecha_nacimiento":         row[5].strftime("%Y-%m-%d") if row[5] else None,
        "correo":                   row[6],
        "notificacion_email":       bool(row[7]),
        "notificacion_sms":         bool(row[8]),
        "fecha_creacion":           row[9].strftime("%Y-%m-%d %H:%M:%S") if row[9] else None,
    }


def find_all(where_clauses, params, offset, per_page):
    where_str = " AND ".join(where_clauses) if where_clauses else "1=1"
    try:
        with db_connection() as (conn, cursor):
            cursor.execute(
                f"SELECT COUNT(*) FROM clientes WHERE {where_str}",
                params,
            )
            total = cursor.fetchone()[0]

            cursor.execute(
                f"""
                SELECT id_cliente, nombre_razon_social, documento_identificacion,
                       tipo, estado, fecha_nacimiento, correo,
                       notificacion_email, notificacion_sms, fecha_creacion
                FROM clientes WHERE {where_str}
                ORDER BY fecha_creacion DESC
                OFFSET %s ROWS FETCH NEXT %s ROWS ONLY
                """,
                params + [offset, per_page],
            )
            rows = cursor.fetchall()

        return [_row_to_dict(r) for r in rows], total
    except Exception as exc:
        logger.error("find_all clientes: %s", exc, exc_info=True)
        return [], 0


def find_by_id(id_cliente):
    try:
        with db_connection() as (conn, cursor):
            cursor.execute(
                """
                SELECT id_cliente, nombre_razon_social, documento_identificacion,
                       tipo, estado, fecha_nacimiento, correo,
                       notificacion_email, notificacion_sms, fecha_creacion
                FROM clientes WHERE id_cliente = %s
                """,
                [id_cliente],
            )
            row = cursor.fetchone()
            if not row:
                return None

            cliente = _row_to_dict(row)

            cursor.execute(
                """
                SELECT id_contacto, nombre_contacto, tipo_contacto, descripcion,
                       correo, telefono, estado
                FROM contactos_cliente WHERE id_cliente = %s
                """,
                [id_cliente],
            )
            cliente["contactos"] = [
                {
                    "id_contacto":    c[0],
                    "nombre_contacto": c[1],
                    "tipo_contacto":  c[2],
                    "descripcion":    c[3],
                    "correo":         c[4],
                    "telefono":       c[5],
                    "estado":         c[6],
                }
                for c in cursor.fetchall()
            ]

        return cliente
    except Exception as exc:
        logger.error("find_by_id cliente: %s", exc, exc_info=True)
        return None


def insert(data):
    try:
        with db_connection() as (conn, cursor):
            cursor.callproc("sp_registrar_cliente", [
                data.get("nombre_razon_social", ""),
                data.get("documento_identificacion", ""),
                data.get("tipo", "Cliente"),
                data.get("estado", "Activo"),
                data.get("fecha_nacimiento") or None,
                data.get("correo") or None,
                1 if data.get("notificacion_email") else 0,
                1 if data.get("notificacion_sms") else 0,
                data.get("usuario", "sistema"),
            ])
            row = cursor.fetchone()
            id_cliente, mensaje, is_error = sp_result(row)

        if is_error:
            return None, mensaje
        return id_cliente, mensaje
    except Exception as exc:
        logger.error("insert cliente: %s", exc, exc_info=True)
        return None, "Error al registrar el cliente."


def insert_contacto(id_cliente, contacto, usuario):
    try:
        with db_connection() as (conn, cursor):
            cursor.callproc("sp_agregar_contacto", [
                id_cliente,
                contacto.get("nombre_contacto", "Contacto"),
                contacto.get("tipo_contacto", "Teléfono"),
                contacto.get("descripcion", ""),
                contacto.get("correo") or None,
                contacto.get("telefono") or None,
                usuario,
            ])
            cursor.fetchall()
    except Exception as exc:
        logger.error("insert_contacto: %s", exc, exc_info=True)


def update(id_cliente, data):
    try:
        with db_connection() as (conn, cursor):
            cursor.callproc("sp_actualizar_cliente", [
                id_cliente,
                data.get("nombre_razon_social", ""),
                data.get("documento_identificacion", ""),
                data.get("tipo", "Cliente"),
                data.get("estado", "Activo"),
                data.get("fecha_nacimiento") or None,
                data.get("correo") or None,
                1 if data.get("notificacion_email") else 0,
                1 if data.get("notificacion_sms") else 0,
                data.get("usuario", "sistema"),
            ])
            row = cursor.fetchone()
            id_result, mensaje, is_error = sp_result(row)

        if is_error:
            return None, mensaje
        return id_result, mensaje
    except Exception as exc:
        logger.error("update cliente: %s", exc, exc_info=True)
        return None, "Error al actualizar el cliente."


def update_contacto(contacto, usuario):
    try:
        with db_connection() as (conn, cursor):
            cursor.callproc("sp_actualizar_contacto", [
                contacto["id_contacto"],
                contacto.get("nombre_contacto", "Contacto"),
                contacto.get("tipo_contacto", "Teléfono"),
                contacto.get("descripcion", ""),
                contacto.get("correo") or None,
                contacto.get("telefono") or None,
                contacto.get("estado", "Activo"),
                usuario,
            ])
            cursor.fetchall()
    except Exception as exc:
        logger.error("update_contacto: %s", exc, exc_info=True)


def set_inactive(id_cliente, usuario):
    try:
        with db_connection() as (conn, cursor):
            cursor.callproc("sp_inactivar_cliente", [id_cliente, usuario])
            row = cursor.fetchone()
        id_result, mensaje, is_error = sp_result(row)
        if is_error:
            return None, mensaje
        return id_result, mensaje
    except Exception as exc:
        logger.error("set_inactive cliente: %s", exc, exc_info=True)
        return None, "Error al inactivar el cliente."


def find_cumpleaneros_mes():
    try:
        with db_connection() as (conn, cursor):
            cursor.execute(
                """
                SELECT nombre_razon_social,
                       DAY(fecha_nacimiento) AS dia,
                       YEAR(GETDATE()) - YEAR(fecha_nacimiento) AS edad
                FROM clientes
                WHERE MONTH(fecha_nacimiento) = MONTH(GETDATE())
                  AND fecha_nacimiento IS NOT NULL
                  AND estado = 'Activo'
                ORDER BY DAY(fecha_nacimiento)
                """
            )
            rows = cursor.fetchall()
        return [{"nombre": r[0], "dia": r[1], "edad": r[2]} for r in rows]
    except Exception as exc:
        logger.error("find_cumpleaneros_mes: %s", exc, exc_info=True)
        return []


def get_stats():
    try:
        with db_connection() as (conn, cursor):
            cursor.execute("SELECT COUNT(*) FROM clientes WHERE estado='Activo' AND tipo='Cliente'")
            activos = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM clientes WHERE estado='Inactivo'")
            inactivos = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM clientes WHERE tipo='Prospecto'")
            prospectos = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM proveedores WHERE estado='Activo'")
            prov_activos = cursor.fetchone()[0]

        return {
            "clientes_activos":   activos,
            "clientes_inactivos": inactivos,
            "prospectos":         prospectos,
            "proveedores_activos": prov_activos,
        }
    except Exception as exc:
        logger.error("get_stats: %s", exc, exc_info=True)
        return {"clientes_activos": 0, "clientes_inactivos": 0, "prospectos": 0, "proveedores_activos": 0}


def get_stats_clientes():
    try:
        with db_connection() as (conn, cursor):
            cursor.execute("SELECT COUNT(*) FROM clientes WHERE estado='Activo' AND tipo='Cliente'")
            total_activos = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM clientes WHERE estado='Inactivo' AND tipo='Cliente'")
            total_inactivos = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM clientes WHERE tipo='Prospecto'")
            total_prospectos = cursor.fetchone()[0]

        return {
            "total_activos":    total_activos,
            "total_inactivos":  total_inactivos,
            "total_prospectos": total_prospectos,
        }
    except Exception as exc:
        logger.error("get_stats_clientes: %s", exc, exc_info=True)
        return {"total_activos": 0, "total_inactivos": 0, "total_prospectos": 0}
