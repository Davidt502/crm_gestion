"""
empleados.py - Módulo empleados y dependencias
Correcciones:
  - Context manager (no fugas de conexión)
  - Eliminada doble ejecución en create_dependencia (bug lógico)
  - OFFSET/FETCH pasan como parámetros, no por f-string (SQL injection)
  - Manejo de excepciones con logging
"""
import logging
from database import db_connection, to_int, sp_result

logger = logging.getLogger(__name__)

_MAX_STR = 500  # Longitud máxima para campos string


def _sanitize_str(value, max_len=_MAX_STR) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()[:max_len]


def _to_int_safe(value):
    """Convierte a int sin lanzar excepción si el valor no es numérico."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


# ── Dependencias ──────────────────────────────────────────────

def get_all_dependencias():
    try:
        with db_connection() as (conn, cursor):
            cursor.execute(
                "SELECT id_dependencia, nombre_dependencia, estado "
                "FROM dependencias ORDER BY nombre_dependencia"
            )
            rows = cursor.fetchall()
        return [{"id_dependencia": r[0], "nombre_dependencia": r[1], "estado": r[2]} for r in rows]
    except Exception as exc:
        logger.error("get_all_dependencias: %s", exc, exc_info=True)
        return []


def create_dependencia(data):
    nombre = _sanitize_str(data.get("nombre_dependencia", ""))
    if not nombre:
        return {"error": "El nombre de la dependencia es obligatorio."}

    try:
        with db_connection() as (conn, cursor):
            # Verificar duplicado
            cursor.execute(
                "SELECT COUNT(*) FROM dependencias WHERE nombre_dependencia = %s",
                [nombre],
            )
            if cursor.fetchone()[0] > 0:
                return {"error": "Ya existe una dependencia con ese nombre."}

            cursor.execute(
                "INSERT INTO dependencias (nombre_dependencia, usuario_creacion) VALUES (%s, %s)",
                [nombre, _sanitize_str(data.get("usuario", "sistema"))],
            )
            cursor.execute("SELECT SCOPE_IDENTITY()")
            new_id = int(cursor.fetchone()[0])

        return {"id_dependencia": new_id, "mensaje": "Dependencia creada exitosamente."}
    except Exception as exc:
        logger.error("create_dependencia: %s", exc, exc_info=True)
        return {"error": "Error al crear la dependencia."}


# ── Empleados ─────────────────────────────────────────────────

def _row_emp(r):
    return {
        "id_empleado":      r[0],
        "numero_empleado":  r[1],
        "dpi":              r[2],
        "nombre_completo":  r[3],
        "cargo":            r[4],
        "id_dependencia":   r[5],
        "dependencia":      r[6],
        "estado":           r[7],
        "fecha_nacimiento": r[8].strftime("%Y-%m-%d") if r[8] else None,
        "correo":           r[9],
        "telefono":         r[10],
        "direccion":        r[11],
        "fecha_creacion":   r[12].strftime("%Y-%m-%d %H:%M:%S") if r[12] else None,
    }


def get_all_empleados(nombre=None, dependencia=None, estado=None, page=1, per_page=20):
    page = max(1, int(page))
    per_page = min(max(1, int(per_page)), 100)
    offset = (page - 1) * per_page

    where = ["1=1"]
    params = []

    if nombre:
        where.append("e.nombre_completo LIKE %s")
        params.append(f"%{_sanitize_str(nombre)}%")
    if dependencia:
        dep_int = _to_int_safe(dependencia)
        if dep_int is not None:
            where.append("e.id_dependencia = %s")
            params.append(dep_int)
    if estado:
        where.append("e.estado = %s")
        params.append(_sanitize_str(estado, 20))

    where_str = " AND ".join(where)

    try:
        with db_connection() as (conn, cursor):
            # COUNT — where_str solo contiene literales de columna o %s parametrizado
            cursor.execute(
                f"SELECT COUNT(*) FROM empleados e WHERE {where_str}",
                params,
            )
            total = cursor.fetchone()[0]

            # OFFSET y FETCH también se parametrizan
            cursor.execute(
                f"""
                SELECT e.id_empleado, e.numero_empleado, e.dpi, e.nombre_completo,
                       e.cargo, e.id_dependencia,
                       ISNULL(d.nombre_dependencia, 'Sin asignar') AS dependencia,
                       e.estado, e.fecha_nacimiento, e.correo, e.telefono,
                       e.direccion, e.fecha_creacion
                FROM empleados e
                LEFT JOIN dependencias d ON e.id_dependencia = d.id_dependencia
                WHERE {where_str}
                ORDER BY e.fecha_creacion DESC
                OFFSET %s ROWS FETCH NEXT %s ROWS ONLY
                """,
                params + [offset, per_page],
            )
            rows = cursor.fetchall()

        return {"empleados": [_row_emp(r) for r in rows], "total": total, "page": page, "per_page": per_page}
    except Exception as exc:
        logger.error("get_all_empleados: %s", exc, exc_info=True)
        return {"empleados": [], "total": 0, "page": page, "per_page": per_page}


def get_empleado_by_id(id_empleado):
    try:
        with db_connection() as (conn, cursor):
            cursor.execute(
                """
                SELECT e.id_empleado, e.numero_empleado, e.dpi, e.nombre_completo,
                       e.cargo, e.id_dependencia,
                       ISNULL(d.nombre_dependencia,'Sin asignar'),
                       e.estado, e.fecha_nacimiento, e.correo, e.telefono,
                       e.direccion, e.fecha_creacion
                FROM empleados e
                LEFT JOIN dependencias d ON e.id_dependencia = d.id_dependencia
                WHERE e.id_empleado = %s
                """,
                [id_empleado],
            )
            r = cursor.fetchone()
            if not r:
                return None

            emp = _row_emp(r)

            cursor.execute(
                """
                SELECT h.fecha_movimiento,
                       ISNULL(do.nombre_dependencia,'Inicio') AS origen,
                       dd.nombre_dependencia AS destino,
                       h.motivo, h.usuario
                FROM historial_dependencia h
                LEFT JOIN dependencias do ON h.id_dependencia_origen  = do.id_dependencia
                JOIN  dependencias dd ON h.id_dependencia_destino = dd.id_dependencia
                WHERE h.id_empleado = %s
                ORDER BY h.fecha_movimiento DESC
                """,
                [id_empleado],
            )
            emp["historial"] = [
                {
                    "fecha":   h[0].strftime("%Y-%m-%d %H:%M") if h[0] else None,
                    "origen":  h[1],
                    "destino": h[2],
                    "motivo":  h[3],
                    "usuario": h[4],
                }
                for h in cursor.fetchall()
            ]

        return emp
    except Exception as exc:
        logger.error("get_empleado_by_id: %s", exc, exc_info=True)
        return None


def create_empleado(data):
    try:
        with db_connection() as (conn, cursor):
            cursor.callproc("sp_registrar_empleado", [
                _sanitize_str(data.get("numero_empleado", "")),
                _sanitize_str(data.get("dpi", "")),
                _sanitize_str(data.get("nombre_completo", "")),
                _sanitize_str(data.get("cargo", "")) or None,
                int(data["id_dependencia"]) if data.get("id_dependencia") else None,
                data.get("fecha_nacimiento") or None,
                _sanitize_str(data.get("correo", "")) or None,
                _sanitize_str(data.get("telefono", "")) or None,
                _sanitize_str(data.get("direccion", "")) or None,
                _sanitize_str(data.get("usuario", "sistema")),
            ])
            row = cursor.fetchone()

        id_emp, mensaje, is_error = sp_result(row)
        if is_error:
            return {"error": mensaje or "Error al crear el empleado."}
        return {"id_empleado": id_emp, "mensaje": mensaje}
    except Exception as exc:
        logger.error("create_empleado: %s", exc, exc_info=True)
        return {"error": "Error al crear el empleado."}


def update_empleado(id_empleado, data):
    try:
        with db_connection() as (conn, cursor):
            cursor.callproc("sp_actualizar_empleado", [
                id_empleado,
                _sanitize_str(data.get("nombre_completo", "")),
                _sanitize_str(data.get("cargo", "")) or None,
                data.get("fecha_nacimiento") or None,
                _sanitize_str(data.get("correo", "")) or None,
                _sanitize_str(data.get("telefono", "")) or None,
                _sanitize_str(data.get("direccion", "")) or None,
                _sanitize_str(data.get("estado", "Activo"), 20),
                _sanitize_str(data.get("usuario", "sistema")),
            ])
            row = cursor.fetchone()

        id_emp, mensaje, is_error = sp_result(row)
        if is_error:
            return {"error": mensaje or "Error al actualizar el empleado."}
        return {"id_empleado": id_emp, "mensaje": mensaje}
    except Exception as exc:
        logger.error("update_empleado: %s", exc, exc_info=True)
        return {"error": "Error al actualizar el empleado."}


def reasignar_dependencia(id_empleado, data):
    id_dep_nueva = _to_int_safe(data.get("id_dependencia_nueva"))
    if not id_dep_nueva:
        return {"error": "El campo id_dependencia_nueva es obligatorio y debe ser un número válido."}

    motivo = _sanitize_str(data.get("motivo", ""))
    if not motivo:
        return {"error": "El motivo de reasignación es obligatorio."}

    try:
        with db_connection() as (conn, cursor):
            cursor.callproc("sp_reasignar_dependencia", [
                id_empleado,
                id_dep_nueva,
                motivo,
                _sanitize_str(data.get("usuario", "sistema")),
            ])
            row = cursor.fetchone()

        id_res, mensaje, is_error = sp_result(row)
        if is_error:
            return {"error": mensaje or "Error al reasignar dependencia."}
        return {"mensaje": mensaje}
    except Exception as exc:
        logger.error("reasignar_dependencia: %s", exc, exc_info=True)
        return {"error": "Error al reasignar dependencia."}


def get_stats_empleados():
    try:
        with db_connection() as (conn, cursor):
            cursor.execute("SELECT COUNT(*) FROM empleados WHERE estado='Activo'")
            activos = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM empleados WHERE estado='Inactivo'")
            inactivos = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM dependencias WHERE estado='Activo'")
            deps = cursor.fetchone()[0]
        return {"activos": activos, "inactivos": inactivos, "dependencias": deps}
    except Exception as exc:
        logger.error("get_stats_empleados: %s", exc, exc_info=True)
        return {"activos": 0, "inactivos": 0, "dependencias": 0}
