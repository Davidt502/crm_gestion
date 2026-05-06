"""
routes/auditoria_routes.py - Endpoints del panel de auditoría
Solo accesible para administradores.
"""
import logging
from flask import Blueprint, request, jsonify, g
from database import db_connection
from middleware.auth_middleware import token_required

logger = logging.getLogger(__name__)

auditoria_bp = Blueprint("auditoria", __name__)


def _solo_admin():
    user = getattr(request, "current_user", {})
    if user.get("rol") != "admin":
        return jsonify({"error": "Acceso restringido a administradores."}), 403
    return None


@auditoria_bp.route("/api/auditoria", methods=["GET"])
@token_required
def listar_auditoria():
    """
    Lista registros de auditoría con filtros.
    Parámetros opcionales:
      - username, ip, recurso, accion, tipo_acceso
      - fecha_desde (YYYY-MM-DD), fecha_hasta (YYYY-MM-DD)
      - page (default 1), per_page (default 50)
    """
    deny = _solo_admin()
    if deny:
        return deny

    try:
        page     = max(1, int(request.args.get("page", 1)))
        per_page = min(100, max(10, int(request.args.get("per_page", 50))))
    except (ValueError, TypeError):
        page, per_page = 1, 50

    offset = (page - 1) * per_page

    filtros = []
    params  = []

    username = request.args.get("username", "").strip()
    if username:
        filtros.append("a.username LIKE %s")
        params.append(f"%{username}%")

    ip = request.args.get("ip", "").strip()
    if ip:
        filtros.append("a.ip_publica LIKE %s")
        params.append(f"%{ip}%")

    recurso = request.args.get("recurso", "").strip()
    if recurso:
        filtros.append("a.recurso = %s")
        params.append(recurso)

    accion = request.args.get("accion", "").strip()
    if accion:
        filtros.append("a.accion = %s")
        params.append(accion)

    tipo = request.args.get("tipo_acceso", "").strip()
    if tipo:
        filtros.append("a.tipo_acceso = %s")
        params.append(tipo)

    fecha_desde = request.args.get("fecha_desde", "").strip()
    if fecha_desde:
        filtros.append("CAST(a.fecha_hora AS DATE) >= %s")
        params.append(fecha_desde)

    fecha_hasta = request.args.get("fecha_hasta", "").strip()
    if fecha_hasta:
        filtros.append("CAST(a.fecha_hora AS DATE) <= %s")
        params.append(fecha_hasta)

    where = ("WHERE " + " AND ".join(filtros)) if filtros else ""

    try:
        with db_connection() as (conn, cursor):
            # Total
            cursor.execute(
                f"""
                SELECT COUNT(*) FROM auditoria_accesos a
                {where}
                """,
                params,
            )
            total = cursor.fetchone()[0]

            # Datos paginados
            cursor.execute(
                f"""
                SELECT TOP {per_page}
                    a.id_auditoria,
                    CONVERT(VARCHAR(19), a.fecha_hora, 120) AS fecha_hora,
                    a.nombre_usuario, a.username, a.grupo,
                    a.ip_publica, a.tipo_acceso,
                    a.metodo_http, a.endpoint, a.accion,
                    a.recurso, a.id_recurso, a.exitoso,
                    a.codigo_respuesta,
                    LEFT(ISNULL(a.user_agent,''), 100) AS user_agent,
                    a.detalle
                FROM auditoria_accesos a
                {where}
                ORDER BY a.fecha_hora DESC
                OFFSET {offset} ROWS
                FETCH NEXT {per_page} ROWS ONLY
                """,
                params,
            )
            cols = [d[0] for d in cursor.description]
            rows = [dict(zip(cols, r)) for r in cursor.fetchall()]
            for r in rows:
                r["exitoso"] = bool(r["exitoso"])

        return jsonify({
            "registros": rows,
            "total":     total,
            "page":      page,
            "per_page":  per_page,
            "paginas":   -(-total // per_page),
        })

    except Exception as exc:
        logger.error("Error en listar_auditoria: %s", exc, exc_info=True)
        return jsonify({"error": "Error al obtener registros de auditoría."}), 500


@auditoria_bp.route("/api/auditoria/resumen", methods=["GET"])
@token_required
def resumen_auditoria():
    """Resumen estadístico para el panel de administración."""
    deny = _solo_admin()
    if deny:
        return deny

    try:
        with db_connection() as (conn, cursor):
            cursor.execute(
                """
                SELECT
                    COUNT(*) AS total_accesos,
                    SUM(CASE WHEN tipo_acceso = 'web' THEN 1 ELSE 0 END) AS accesos_web,
                    SUM(CASE WHEN tipo_acceso = 'api_publica' THEN 1 ELSE 0 END) AS accesos_api,
                    SUM(CASE WHEN exitoso = 0 THEN 1 ELSE 0 END) AS accesos_fallidos,
                    COUNT(DISTINCT ip_publica) AS ips_unicas,
                    COUNT(DISTINCT username) AS usuarios_activos
                FROM auditoria_accesos
                WHERE fecha_hora >= DATEADD(DAY, -30, GETDATE())
                """
            )
            row = cursor.fetchone()
            cols = [d[0] for d in cursor.description]
            stats = dict(zip(cols, row))

            # Top usuarios por actividad (últimos 30 días)
            cursor.execute(
                """
                SELECT TOP 10
                    username, nombre_usuario, grupo,
                    COUNT(*) AS total,
                    MAX(CONVERT(VARCHAR(19), fecha_hora, 120)) AS ultimo_acceso
                FROM auditoria_accesos
                WHERE fecha_hora >= DATEADD(DAY, -30, GETDATE())
                  AND username IS NOT NULL
                GROUP BY username, nombre_usuario, grupo
                ORDER BY total DESC
                """
            )
            cols2 = [d[0] for d in cursor.description]
            top_usuarios = [dict(zip(cols2, r)) for r in cursor.fetchall()]

            # Top IPs
            cursor.execute(
                """
                SELECT TOP 10
                    ip_publica,
                    COUNT(*) AS total,
                    MAX(CONVERT(VARCHAR(19), fecha_hora, 120)) AS ultimo_acceso
                FROM auditoria_accesos
                WHERE fecha_hora >= DATEADD(DAY, -30, GETDATE())
                GROUP BY ip_publica
                ORDER BY total DESC
                """
            )
            cols3 = [d[0] for d in cursor.description]
            top_ips = [dict(zip(cols3, r)) for r in cursor.fetchall()]

            # Accesos por recurso
            cursor.execute(
                """
                SELECT TOP 10
                    recurso, accion, COUNT(*) AS total
                FROM auditoria_accesos
                WHERE fecha_hora >= DATEADD(DAY, -30, GETDATE())
                  AND recurso IS NOT NULL AND recurso != ''
                GROUP BY recurso, accion
                ORDER BY total DESC
                """
            )
            cols4 = [d[0] for d in cursor.description]
            por_recurso = [dict(zip(cols4, r)) for r in cursor.fetchall()]

        stats["top_usuarios"] = top_usuarios
        stats["top_ips"]      = top_ips
        stats["por_recurso"]  = por_recurso
        return jsonify(stats)

    except Exception as exc:
        logger.error("Error en resumen_auditoria: %s", exc, exc_info=True)
        return jsonify({"error": "Error al obtener resumen."}), 500


@auditoria_bp.route("/api/auditoria/grupos", methods=["GET"])
@token_required
def listar_grupos():
    """Lista los grupos disponibles."""
    try:
        with db_connection() as (conn, cursor):
            cursor.execute(
                "SELECT id_grupo, nombre_grupo, descripcion, estado FROM grupos ORDER BY nombre_grupo"
            )
            cols = [d[0] for d in cursor.description]
            grupos = [dict(zip(cols, r)) for r in cursor.fetchall()]
        return jsonify({"grupos": grupos})
    except Exception as exc:
        logger.error("Error listando grupos: %s", exc, exc_info=True)
        return jsonify({"error": "Error al obtener grupos."}), 500
