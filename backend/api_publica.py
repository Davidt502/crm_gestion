"""
api_publica.py - Gestión de tokens públicos para compartir APIs
Permite crear tokens con acceso limitado a endpoints específicos,
con registro de auditoría de cada uso.
"""
import secrets
import json
import logging
from functools import wraps
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, g
from database import db_connection
from middleware.auth_middleware import token_required, get_usuario
from auditoria import registrar_auditoria, get_ip_publica

logger = logging.getLogger(__name__)

api_publica_bp = Blueprint("api_publica", __name__)


# ── Validar token público ──────────────────────────────────────
def validar_token_publico(token_str: str) -> tuple:
    """
    Verifica que el token público sea válido y no esté expirado.
    Retorna (dict_token, None) o (None, str_error).
    """
    if not token_str:
        return None, "Token requerido."

    try:
        with db_connection() as (conn, cursor):
            cursor.execute(
                """
                SELECT t.id_token, t.nombre_token, t.endpoints_permitidos,
                       t.solo_lectura, t.activo, t.expira_en,
                       u.nombre, u.username,
                       ISNULL(g.nombre_grupo,'') AS grupo
                FROM api_tokens t
                JOIN usuarios u ON t.id_usuario = u.id_usuario
                LEFT JOIN grupos g ON u.id_grupo = g.id_grupo
                WHERE t.token = %s
                """,
                [token_str],
            )
            row = cursor.fetchone()

            if not row:
                return None, "Token inválido."

            (id_token, nombre_token, endpoints_json, solo_lectura,
             activo, expira_en, nombre_dueño, username_dueño, grupo) = row

            if not activo:
                return None, "Token inactivo."

            if expira_en:
                # expira_en viene como datetime naive (SQL Server)
                if datetime.utcnow() > expira_en:
                    return None, "Token expirado."

            # Actualizar estadísticas de uso
            cursor.execute(
                """
                UPDATE api_tokens SET
                    total_usos = total_usos + 1,
                    ultimo_uso = GETDATE()
                WHERE id_token = %s
                """,
                [id_token],
            )

            try:
                endpoints = json.loads(endpoints_json) if endpoints_json else []
            except Exception:
                endpoints = []

            return {
                "id_token":    id_token,
                "nombre":      nombre_token,
                "endpoints":   endpoints,
                "solo_lectura": bool(solo_lectura),
                "propietario": nombre_dueño,
                "username":    username_dueño,
                "grupo":       grupo,
            }, None

    except Exception as exc:
        logger.error("Error validando token público: %s", exc, exc_info=True)
        return None, "Error interno al validar token."


# ── Decorator para endpoints públicos ─────────────────────────
def token_publico_required(f):
    """
    Decorator para endpoints que aceptan acceso mediante token público.
    El token se pasa como header: X-API-Token: <token>
    o como query param: ?api_token=<token>
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Buscar token en header o query param
        token_str = (
            request.headers.get("X-API-Token") or
            request.args.get("api_token") or
            ""
        ).strip()

        token_info, error = validar_token_publico(token_str)

        if error:
            registrar_auditoria(
                accion="acceso_denegado",
                exitoso=False,
                codigo_respuesta=401,
                tipo_acceso="api_publica",
                detalle={"error": error},
            )
            return jsonify({"error": error}), 401

        # Verificar que el endpoint esté permitido
        endpoint_actual = request.path
        endpoints_permitidos = token_info.get("endpoints", [])

        if endpoints_permitidos:  # Lista vacía = acceso a todo
            permitido = any(
                endpoint_actual.startswith(ep.rstrip("*"))
                for ep in endpoints_permitidos
            )
            if not permitido:
                registrar_auditoria(
                    accion="acceso_denegado",
                    exitoso=False,
                    codigo_respuesta=403,
                    tipo_acceso="api_publica",
                    id_token_publico=token_info["id_token"],
                    detalle={"endpoint": endpoint_actual, "error": "Endpoint no permitido"},
                )
                return jsonify({"error": "Este token no tiene acceso a este endpoint."}), 403

        # Solo lectura: bloquear métodos de escritura
        if token_info["solo_lectura"] and request.method not in ("GET", "HEAD", "OPTIONS"):
            return jsonify({"error": "Este token es de solo lectura."}), 403

        # Inyectar info del token en g para auditoría
        g.token_publico = token_info
        g.current_user_audit = {
            "id_usuario": None,
            "nombre": f"[Token] {token_info['propietario']}",
            "username": token_info["username"],
            "grupo": token_info["grupo"],
        }

        # Registrar acceso
        registrar_auditoria(
            tipo_acceso="api_publica",
            id_token_publico=token_info["id_token"],
            exitoso=True,
        )

        return f(*args, **kwargs)
    return decorated


# ── CRUD de tokens públicos (solo admins/usuarios autenticados) ──
@api_publica_bp.route("/api/tokens", methods=["GET"])
@token_required
def listar_tokens():
    """Lista los tokens del usuario autenticado (admins ven todos)."""
    user = getattr(request, "current_user", {})
    es_admin = user.get("rol") == "admin"

    try:
        with db_connection() as (conn, cursor):
            if es_admin:
                cursor.execute(
                    """
                    SELECT t.id_token, t.nombre_token, t.descripcion,
                           t.endpoints_permitidos, t.solo_lectura, t.activo,
                           t.expira_en, t.total_usos, t.ultimo_uso,
                           t.fecha_creacion, u.nombre AS propietario,
                           LEFT(t.token, 8) + '...' AS token_preview
                    FROM api_tokens t
                    JOIN usuarios u ON t.id_usuario = u.id_usuario
                    ORDER BY t.fecha_creacion DESC
                    """
                )
            else:
                cursor.execute(
                    """
                    SELECT t.id_token, t.nombre_token, t.descripcion,
                           t.endpoints_permitidos, t.solo_lectura, t.activo,
                           t.expira_en, t.total_usos, t.ultimo_uso,
                           t.fecha_creacion, u.nombre AS propietario,
                           LEFT(t.token, 8) + '...' AS token_preview
                    FROM api_tokens t
                    JOIN usuarios u ON t.id_usuario = u.id_usuario
                    WHERE t.id_usuario = (
                        SELECT id_usuario FROM usuarios WHERE username = %s
                    )
                    ORDER BY t.fecha_creacion DESC
                    """,
                    [user.get("username")],
                )

            cols = [d[0] for d in cursor.description]
            rows = cursor.fetchall()
            tokens = []
            for row in rows:
                t = dict(zip(cols, row))
                if t.get("endpoints_permitidos"):
                    try:
                        t["endpoints_permitidos"] = json.loads(t["endpoints_permitidos"])
                    except Exception:
                        t["endpoints_permitidos"] = []
                if t.get("expira_en"):
                    t["expira_en"] = str(t["expira_en"])
                if t.get("ultimo_uso"):
                    t["ultimo_uso"] = str(t["ultimo_uso"])
                if t.get("fecha_creacion"):
                    t["fecha_creacion"] = str(t["fecha_creacion"])
                tokens.append(t)

        return jsonify({"tokens": tokens, "total": len(tokens)})
    except Exception as exc:
        logger.error("Error listando tokens: %s", exc, exc_info=True)
        return jsonify({"error": "Error al obtener tokens."}), 500


@api_publica_bp.route("/api/tokens", methods=["POST"])
@token_required
def crear_token():
    """Crea un nuevo token público."""
    if not request.is_json:
        return jsonify({"error": "Content-Type debe ser application/json"}), 400

    data = request.get_json(silent=True) or {}
    nombre = str(data.get("nombre", "")).strip()
    if not nombre:
        return jsonify({"error": "El nombre del token es requerido."}), 400

    descripcion = str(data.get("descripcion", "")).strip()[:500]
    endpoints   = data.get("endpoints_permitidos", [])  # [] = acceso total
    solo_lectura = bool(data.get("solo_lectura", True))
    expira_en   = data.get("expira_en")  # ISO date string o None

    if not isinstance(endpoints, list):
        endpoints = []

    # Generar token seguro
    nuevo_token = secrets.token_urlsafe(48)
    endpoints_json = json.dumps(endpoints)

    user = getattr(request, "current_user", {})
    username = user.get("username")

    try:
        with db_connection() as (conn, cursor):
            cursor.execute(
                "SELECT id_usuario FROM usuarios WHERE username = %s", [username]
            )
            row = cursor.fetchone()
            if not row:
                return jsonify({"error": "Usuario no encontrado."}), 404
            id_usuario = row[0]

            cursor.execute(
                """
                INSERT INTO api_tokens
                    (nombre_token, token, descripcion, id_usuario,
                     endpoints_permitidos, solo_lectura, activo, expira_en, usuario_creacion)
                VALUES (%s, %s, %s, %s, %s, %s, 1, %s, %s)
                """,
                [nombre, nuevo_token, descripcion, id_usuario,
                 endpoints_json, 1 if solo_lectura else 0, expira_en, username],
            )
            cursor.execute("SELECT SCOPE_IDENTITY()")
            new_id = int(cursor.fetchone()[0])

        registrar_auditoria(accion="crear", recurso="api_tokens", id_recurso=str(new_id))
        return jsonify({
            "success": True,
            "id_token": new_id,
            "token": nuevo_token,
            "mensaje": "Token creado. Guárdalo, no se volverá a mostrar completo.",
        }), 201

    except Exception as exc:
        logger.error("Error creando token: %s", exc, exc_info=True)
        return jsonify({"error": "Error al crear el token."}), 500


@api_publica_bp.route("/api/tokens/<int:id_token>", methods=["DELETE"])
@token_required
def revocar_token(id_token: int):
    """Revoca (desactiva) un token."""
    user = getattr(request, "current_user", {})
    username = user.get("username")
    es_admin = user.get("rol") == "admin"

    try:
        with db_connection() as (conn, cursor):
            if es_admin:
                cursor.execute(
                    "UPDATE api_tokens SET activo = 0 WHERE id_token = %s", [id_token]
                )
            else:
                cursor.execute(
                    """
                    UPDATE api_tokens SET activo = 0
                    WHERE id_token = %s AND id_usuario = (
                        SELECT id_usuario FROM usuarios WHERE username = %s
                    )
                    """,
                    [id_token, username],
                )
            if cursor.rowcount == 0:
                return jsonify({"error": "Token no encontrado o sin permisos."}), 404

        registrar_auditoria(accion="eliminar", recurso="api_tokens", id_recurso=str(id_token))
        return jsonify({"success": True, "mensaje": "Token revocado correctamente."})

    except Exception as exc:
        logger.error("Error revocando token: %s", exc, exc_info=True)
        return jsonify({"error": "Error al revocar el token."}), 500
