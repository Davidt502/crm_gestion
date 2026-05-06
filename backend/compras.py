"""
compras.py - Módulo compras a proveedores
Correcciones:
  - Context manager (no fugas de conexión)
  - OFFSET/FETCH parametrizados (no f-string con enteros calculados sin validar)
  - Validación de estado_pago con lista blanca
  - Sanitización de entradas
  - Manejo de excepciones con logging
"""
import logging
from database import db_connection, to_int, sp_result

logger = logging.getLogger(__name__)

ESTADOS_PAGO_VALIDOS = {"Pagado", "Pendiente", "Anulado"}


def _sanitize_str(value, max_len=500) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()[:max_len]


def _row_compra(r):
    return {
        "id_compra":      r[0],
        "id_proveedor":   r[1],
        "proveedor":      r[2],
        "fecha_compra":   r[3].strftime("%Y-%m-%d") if r[3] else None,
        "productos":      r[4],
        "monto_total":    float(r[5]) if r[5] is not None else 0.0,
        "estado_pago":    r[6],
        "notas":          r[7],
        "fecha_creacion": r[8].strftime("%Y-%m-%d %H:%M:%S") if r[8] else None,
    }


def get_all_compras(proveedor=None, estado_pago=None, page=1, per_page=20):
    page = max(1, int(page))
    per_page = min(max(1, int(per_page)), 100)
    offset = (page - 1) * per_page

    where = ["1=1"]
    params = []

    if proveedor:
        where.append("p.nombre_empresa LIKE %s")
        params.append(f"%{_sanitize_str(proveedor)}%")
    if estado_pago and estado_pago in ESTADOS_PAGO_VALIDOS:
        where.append("c.estado_pago = %s")
        params.append(estado_pago)

    where_str = " AND ".join(where)

    try:
        with db_connection() as (conn, cursor):
            cursor.execute(
                f"""
                SELECT COUNT(*) FROM compras_proveedor c
                JOIN proveedores p ON c.id_proveedor = p.id_proveedor
                WHERE {where_str}
                """,
                params,
            )
            total = cursor.fetchone()[0]

            cursor.execute(
                f"""
                SELECT c.id_compra, c.id_proveedor, p.nombre_empresa,
                       c.fecha_compra, c.productos, c.monto_total,
                       c.estado_pago, c.notas, c.fecha_creacion
                FROM compras_proveedor c
                JOIN proveedores p ON c.id_proveedor = p.id_proveedor
                WHERE {where_str}
                ORDER BY c.fecha_creacion DESC
                OFFSET %s ROWS FETCH NEXT %s ROWS ONLY
                """,
                params + [offset, per_page],
            )
            rows = cursor.fetchall()

        return {"compras": [_row_compra(r) for r in rows], "total": total, "page": page, "per_page": per_page}
    except Exception as exc:
        logger.error("get_all_compras: %s", exc, exc_info=True)
        return {"compras": [], "total": 0, "page": page, "per_page": per_page}


def get_compra_by_id(id_compra):
    try:
        with db_connection() as (conn, cursor):
            cursor.execute(
                """
                SELECT c.id_compra, c.id_proveedor, p.nombre_empresa,
                       c.fecha_compra, c.productos, c.monto_total,
                       c.estado_pago, c.notas, c.fecha_creacion
                FROM compras_proveedor c
                JOIN proveedores p ON c.id_proveedor = p.id_proveedor
                WHERE c.id_compra = %s
                """,
                [id_compra],
            )
            r = cursor.fetchone()
        return _row_compra(r) if r else None
    except Exception as exc:
        logger.error("get_compra_by_id: %s", exc, exc_info=True)
        return None


def create_compra(data):
    try:
        monto = float(data.get("monto_total", 0))
        if monto <= 0:
            return {"error": "El monto debe ser mayor a 0."}

        estado = _sanitize_str(data.get("estado_pago", "Pendiente"), 20)
        if estado not in ESTADOS_PAGO_VALIDOS:
            estado = "Pendiente"

        with db_connection() as (conn, cursor):
            cursor.callproc("sp_registrar_compra_proveedor", [
                int(data.get("id_proveedor", 0)),
                data.get("fecha_compra") or None,
                _sanitize_str(data.get("productos", "")),
                monto,
                estado,
                _sanitize_str(data.get("notas", "")) or None,
                _sanitize_str(data.get("usuario", "sistema")),
            ])
            row = cursor.fetchone()

        id_compra, mensaje, is_error = sp_result(row)
        if is_error:
            return {"error": mensaje or "Error al registrar la compra."}
        return {"id_compra": id_compra, "mensaje": mensaje}
    except Exception as exc:
        logger.error("create_compra: %s", exc, exc_info=True)
        return {"error": "Error al registrar la compra."}


def update_estado_pago(id_compra, estado_pago, usuario="sistema"):
    if estado_pago not in ESTADOS_PAGO_VALIDOS:
        return {"error": f"Estado de pago inválido. Valores permitidos: {', '.join(ESTADOS_PAGO_VALIDOS)}"}

    try:
        with db_connection() as (conn, cursor):
            # Verificar que la compra existe antes de actualizar
            cursor.execute(
                "SELECT COUNT(*) FROM compras_proveedor WHERE id_compra = %s",
                [id_compra],
            )
            if cursor.fetchone()[0] == 0:
                return {"not_found": True}

            cursor.execute(
                """
                UPDATE compras_proveedor
                SET estado_pago = %s,
                    fecha_modificacion = GETDATE(),
                    usuario_modificacion = %s
                WHERE id_compra = %s
                """,
                [estado_pago, _sanitize_str(usuario), id_compra],
            )
        return {"mensaje": f"Compra marcada como {estado_pago}."}
    except Exception as exc:
        logger.error("update_estado_pago: %s", exc, exc_info=True)
        return {"error": "Error al actualizar el estado de pago."}


def get_stats_compras():
    try:
        with db_connection() as (conn, cursor):
            cursor.execute("SELECT COUNT(*), ISNULL(SUM(monto_total),0) FROM compras_proveedor")
            r1 = cursor.fetchone()
            cursor.execute("SELECT COUNT(*) FROM compras_proveedor WHERE estado_pago='Pendiente'")
            pendientes = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM compras_proveedor WHERE estado_pago='Pagado'")
            pagadas = cursor.fetchone()[0]

        return {
            "total_compras": r1[0],
            "monto_total":   float(r1[1]),
            "pendientes":    pendientes,
            "pagadas":       pagadas,
        }
    except Exception as exc:
        logger.error("get_stats_compras: %s", exc, exc_info=True)
        return {"total_compras": 0, "monto_total": 0.0, "pendientes": 0, "pagadas": 0}
