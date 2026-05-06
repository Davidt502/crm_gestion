"""
auditoria.py - Registro de auditoría completo
Captura: quién entró, IP pública, qué vio, qué copió/exportó, qué acciones realizó.
"""
import json
import logging
from datetime import datetime
from functools import wraps
from flask import request, g
from database import db_connection

logger = logging.getLogger(__name__)


# ── Obtener IP real del cliente ───────────────────────────────
def get_ip_publica() -> str:
    """
    Obtiene la IP pública del cliente.
    Considera proxies reversos (X-Forwarded-For, X-Real-IP).
    """
    # X-Forwarded-For puede tener múltiples IPs: "client, proxy1, proxy2"
    xff = request.headers.get("X-Forwarded-For", "")
    if xff:
        ip = xff.split(",")[0].strip()
        if ip:
            return ip[:50]
    x_real = request.headers.get("X-Real-IP", "")
    if x_real:
        return x_real.strip()[:50]
    return (request.remote_addr or "desconocida")[:50]


def get_user_agent() -> str:
    return (request.headers.get("User-Agent", ""))[:500]


# ── Clasificar acción según método + endpoint ─────────────────
def clasificar_accion(method: str, endpoint: str) -> str:
    method = method.upper()
    ep = endpoint.lower()

    if "login"    in ep: return "login"
    if "logout"   in ep: return "logout"
    if "export"   in ep or "descargar" in ep: return "exportar"
    if "copiar"   in ep or "copy"      in ep: return "copiar"

    if method == "GET":
        # Si hay parámetros de búsqueda
        if request.args:
            return "buscar"
        return "ver"
    if method == "POST":   return "crear"
    if method in ("PUT", "PATCH"): return "editar"
    if method == "DELETE": return "eliminar"
    return "acceder"


def extraer_recurso(endpoint: str) -> str:
    """Extrae el nombre del recurso del endpoint. /api/clientes/5 → clientes"""
    partes = [p for p in endpoint.split("/") if p and p != "api"]
    if partes:
        return partes[0][:100]
    return ""


def extraer_id_recurso(endpoint: str) -> str:
    """Extrae el ID del recurso si existe en la URL."""
    partes = [p for p in endpoint.split("/") if p and p != "api"]
    if len(partes) >= 2:
        id_parte = partes[1]
        if id_parte.isdigit() or (len(id_parte) < 50):
            return id_parte[:50]
    return ""


# ── Función principal de registro ─────────────────────────────
def registrar_auditoria(
    accion: str = None,
    recurso: str = None,
    id_recurso: str = None,
    detalle: dict = None,
    exitoso: bool = True,
    codigo_respuesta: int = None,
    tipo_acceso: str = "web",
    id_token_publico: int = None,
):
    """
    Registra un evento de auditoría en la base de datos.
    Usa los datos del request actual y del usuario autenticado (g.current_user).
    """
    try:
        ip          = get_ip_publica()
        user_agent  = get_user_agent()
        endpoint    = request.path
        method      = request.method

        accion_final   = accion   or clasificar_accion(method, endpoint)
        recurso_final  = recurso  or extraer_recurso(endpoint)
        id_rec_final   = id_recurso or extraer_id_recurso(endpoint)

        # Datos del usuario autenticado (si existe)
        user        = getattr(g, "current_user_audit", {}) or {}
        id_usuario  = user.get("id_usuario")
        nombre      = user.get("nombre")
        username    = user.get("username")
        grupo       = user.get("grupo", "")

        detalle_json = json.dumps(detalle, ensure_ascii=False) if detalle else None

        with db_connection() as (conn, cursor):
            cursor.execute(
                """
                EXEC sp_registrar_auditoria
                    @id_usuario       = %s,
                    @nombre_usuario   = %s,
                    @username         = %s,
                    @grupo            = %s,
                    @ip_publica       = %s,
                    @user_agent       = %s,
                    @tipo_acceso      = %s,
                    @id_token         = %s,
                    @endpoint         = %s,
                    @metodo_http      = %s,
                    @accion           = %s,
                    @recurso          = %s,
                    @id_recurso       = %s,
                    @detalle          = %s,
                    @exitoso          = %s,
                    @codigo_respuesta = %s
                """,
                [
                    id_usuario, nombre, username, grupo,
                    ip, user_agent, tipo_acceso, id_token_publico,
                    endpoint[:255], method[:10],
                    accion_final[:50], recurso_final[:100], id_rec_final[:50],
                    detalle_json, 1 if exitoso else 0, codigo_respuesta,
                ],
            )
    except Exception as exc:
        # La auditoría no debe interrumpir el flujo principal
        logger.error("Error al registrar auditoría: %s", exc, exc_info=True)


# ── Decorator para auditar endpoints automáticamente ──────────
def auditar(accion: str = None, recurso: str = None):
    """
    Decorator que registra automáticamente el acceso a un endpoint.

    Uso:
        @app.route("/api/clientes")
        @token_required
        @auditar()
        def get_clientes(): ...

        @app.route("/api/clientes/<id>")
        @token_required
        @auditar(accion="ver", recurso="clientes")
        def get_cliente(id): ...
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            response = f(*args, **kwargs)

            # Extraer código de respuesta
            if hasattr(response, "status_code"):
                codigo = response.status_code
            elif isinstance(response, tuple) and len(response) >= 2:
                codigo = response[1]
            else:
                codigo = 200

            exitoso = codigo < 400
            registrar_auditoria(
                accion=accion,
                recurso=recurso,
                exitoso=exitoso,
                codigo_respuesta=codigo,
            )
            return response
        return decorated
    return decorator
