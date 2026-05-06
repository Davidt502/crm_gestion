"""
routes/auditoria_routes.py - Endpoints del panel de auditoría
Solo accesible para administradores.
Convertido a PostgreSQL.
"""
import logging
from flask import Blueprint, request, jsonify
from database import db_connection_dict
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
        page = max(1, int(request.args.get("page", 1)))
        per_page = min(100, max(10, int(request.args.get("per_page", 50))))
    except (ValueError, TypeError):
        page, per_page = 1, 50

    offset = (page - 1) * per_page

    filtros = []
    params = []

    username = request.args.get("username", "").strip()
    if username:
        filtros.append("a.username ILIKE %s")
        params.append(f"%{username}%")

    ip = request.args.get("ip", "").strip()
    if ip:
        filtros.append("a.ip_publica ILIKE %s")
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
        filtros.append("a.fecha_hora::date >= %s")
        params.append(fecha_desde)

    fecha_hasta = request.args.get("fecha_hasta", "").strip()
    if fecha_hasta:
        filtros.append("a.fecha_hora::date <= %s")
        params.append(fecha_hasta)

    where = "WHERE " + " AND ".join(filtros) if filtros else ""

    try:
        with db_connection_dict() as (conn, cursor):
            # Total
            cursor.execute(f"""
                SELECT COUNT(*) as total FROM auditoria_accesos a
                {where}
            """, params)
            total = cursor.fetchone()['total']

            # Datos paginados
            cursor.execute(f"""
                SELECT 
                    a.id_auditoria,
                    TO_CHAR(a.fecha_hora, 'YYYY-MM-DD HH24:MI:SS') as fecha_hora,
                    a.nombre_usuario, a.username, a.grupo,
                    a.ip_publica, a.tipo_acceso,
                    a.metodo_http, a.endpoint, a.accion,
                    a.recurso, a.id_recurso, a.exitoso,
                    a.codigo_respuesta,
                    LEFT(COALESCE(a.user_agent,''), 100) as user_agent,
                    a.detalle
                FROM auditoria_accesos a
                {where}
                ORDER BY a.fecha_hora DESC
                LIMIT %s OFFSET %s
            """, params + [per_page, offset])
            
            rows = cursor.fetchall()
            for r in rows:
                r["exitoso"] = bool(r["exitoso"])

        return jsonify({
            "registros": rows,
            "total": total,
            "page": page,
            "per_page": per_page,
            "paginas": (total + per_page - 1) // per_page,
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
        with db_connection_dict() as (conn, cursor):
            cursor.execute("""
                SELECT
                    COUNT(*) AS total_accesos,
                    SUM(CASE WHEN tipo_acceso = 'web' THEN 1 ELSE 0 END) AS accesos_web,
                    SUM(CASE WHEN tipo_acceso = 'api_publica' THEN 1 ELSE 0 END) AS accesos_api,
                    SUM(CASE WHEN exitoso = false THEN 1 ELSE 0 END) AS accesos_fallidos,
                    COUNT(DISTINCT ip_publica) AS ips_unicas,
                    COUNT(DISTINCT username) AS usuarios_activos
                FROM auditoria_accesos
                WHERE fecha_hora >= CURRENT_DATE - INTERVAL '30 days'
            """)
            stats = cursor.fetchone()

            # Top usuarios por actividad (últimos 30 días)
            cursor.execute("""
                SELECT 
                    username, nombre_usuario, grupo,
                    COUNT(*) AS total,
                    TO_CHAR(MAX(fecha_hora), 'YYYY-MM-DD HH24:MI:SS') AS ultimo_acceso
                FROM auditoria_accesos
                WHERE fecha_hora >= CURRENT_DATE - INTERVAL '30 days'
                  AND username IS NOT NULL
                GROUP BY username, nombre_usuario, grupo
                ORDER BY total DESC
                LIMIT 10
            """)
            top_usuarios = cursor.fetchall()

            # Top IPs
            cursor.execute("""
                SELECT 
                    ip_publica,
                    COUNT(*) AS total,
                    TO_CHAR(MAX(fecha_hora), 'YYYY-MM-DD HH24:MI:SS') AS ultimo_acceso
                FROM auditoria_accesos
                WHERE fecha_hora >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY ip_publica
                ORDER BY total DESC
                LIMIT 10
            """)
            top_ips = cursor.fetchall()

            # Accesos por recurso
            cursor.execute("""
                SELECT 
                    recurso, accion, COUNT(*) AS total
                FROM auditoria_accesos
                WHERE fecha_hora >= CURRENT_DATE - INTERVAL '30 days'
                  AND recurso IS NOT NULL AND recurso != ''
                GROUP BY recurso, accion
                ORDER BY total DESC
                LIMIT 10
            """)
            por_recurso = cursor.fetchall()

        stats["top_usuarios"] = top_usuarios
        stats["top_ips"] = top_ips
        stats["por_recurso"] = por_recurso
        return jsonify(stats)

    except Exception as exc:
        logger.error("Error en resumen_auditoria: %s", exc, exc_info=True)
        return jsonify({"error": "Error al obtener resumen."}), 500
