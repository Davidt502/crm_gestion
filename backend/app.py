"""
app.py - API REST Backend - CRM Ing Software
Correcciones:
  - Rate limiting en login para mitigar ataques de fuerza bruta
  - Cabeceras de seguridad HTTP (Content-Security-Policy, X-Frame-Options, etc.)
  - Manejo global de errores (404, 405, 500)
  - Logging configurado
  - Validación de Content-Type en endpoints POST/PUT/PATCH
"""
import sys
import os
import logging
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, request, jsonify, g
from flask_cors import CORS
import jwt

from config import SECRET_KEY, DEBUG, CORS_ORIGINS, JWT_EXPIRY_HOURS, ENFORCE_HTTPS, RATE_LIMIT_WINDOW, RATE_LIMIT_LOGIN_ATTEMPTS, RATE_LIMIT_API_ATTEMPTS
from middleware.auth_middleware import token_required, get_usuario

import auth as auth_mod
import empleados as empleados_mod
import compras as compras_mod
from auditoria import registrar_auditoria, get_ip_publica

from services import cliente_service
from routes.proveedor_routes import proveedor_bp
from routes.cliente_routes   import cliente_bp
from routes.usuario_routes   import usuario_bp
from routes.auditoria_routes import auditoria_bp
from api_publica import api_publica_bp

# ── Logging ───────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ── Flask App ─────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = SECRET_KEY

# CORS — configuración mejorada
CORS(
    app,
    origins=CORS_ORIGINS,
    supports_credentials=True,
    allow_headers=['Content-Type', 'Authorization'],
    methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'],
    expose_headers=['Content-Type'],
    max_age=3600
)

# Blueprints
app.register_blueprint(proveedor_bp)
app.register_blueprint(cliente_bp)
app.register_blueprint(usuario_bp)
app.register_blueprint(auditoria_bp)
app.register_blueprint(api_publica_bp)


# ── Cabeceras de seguridad HTTP ───────────────────────────────
@app.before_request
def handle_preflight():
    """Maneja solicitudes OPTIONS preflight para CORS."""
    if request.method == "OPTIONS":
        return "", 200


@app.before_request
def enforce_https():
    """Forzar HTTPS en producción (excepto para preflight)."""
    if ENFORCE_HTTPS and request.scheme != "https" and request.method != "OPTIONS":
        return jsonify({"error": "Se requiere conexión HTTPS"}), 403


@app.after_request
def set_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'self'"
    if not DEBUG:
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
    return response


# ── Rate limit simple en memoria ────
import threading
from time import monotonic as current_time
_login_attempts: dict[str, list[float]] = {}
_api_attempts: dict[str, list[float]] = {}
_rate_lock = threading.Lock()


def _is_rate_limited(ip: str, limit_type: str = "login") -> bool:
    """Verifica si una IP ha excedido el límite de intentos.
    
    Parámetros:
      - limit_type: 'login' o 'api'
    """
    if limit_type == "login":
        attempts_dict = _login_attempts
        window = RATE_LIMIT_WINDOW
        max_attempts = RATE_LIMIT_LOGIN_ATTEMPTS
    else:
        attempts_dict = _api_attempts
        window = RATE_LIMIT_WINDOW
        max_attempts = RATE_LIMIT_API_ATTEMPTS

    now = current_time()
    with _rate_lock:
        attempts = attempts_dict.get(ip, [])
        # Purgar intentos fuera de la ventana
        attempts = [t for t in attempts if now - t < window]
        if len(attempts) >= max_attempts:
            attempts_dict[ip] = attempts
            return True
        attempts.append(now)
        attempts_dict[ip] = attempts
    return False


# ── JWT ───────────────────────────────────────────────────────
def generate_token(user_data: dict) -> str:
    payload = {
        "id_usuario": user_data.get("id_usuario"),
        "username": user_data["username"],
        "nombre":   user_data["nombre"],
        "rol":      user_data["rol"],
        "grupo":    user_data.get("grupo", ""),
        "exp":      datetime.now(tz=timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS),
        "iat":      datetime.now(tz=timezone.utc),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


# ── Manejo global de errores ──────────────────────────────────
@app.errorhandler(400)
def bad_request(e):
    logger.warning("Bad request: %s", request.path)
    return jsonify({"error": "Solicitud inválida"}), 400


@app.errorhandler(403)
def forbidden(e):
    return jsonify({"error": "Acceso denegado"}), 403


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Recurso no encontrado"}), 404


@app.errorhandler(405)
def method_not_allowed(e):
    logger.warning("Method not allowed: %s %s", request.method, request.path)
    return jsonify({"error": "Método no permitido"}), 405


@app.errorhandler(429)
def rate_limit_exceeded(e):
    return jsonify({"error": "Demasiadas solicitudes. Intenta más tarde."}), 429


@app.errorhandler(500)
def internal_error(e):
    logger.error("Error interno no capturado: %s", e, exc_info=True)
    return jsonify({"error": "Error interno del servidor"}), 500


# ── Health Check ──────────────────────────────────────────────
@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "message": "API Backend funcionando correctamente"})


# ── Auth ──────────────────────────────────────────────────────
@app.route("/api/auth/login", methods=["POST"])
def api_login():
    ip = request.remote_addr or "unknown"

    if _is_rate_limited(ip, "login"):
        logger.warning("Rate limit excedido para IP: %s", ip)
        return jsonify({"error": "Demasiados intentos. Espera un momento."}), 429

    if not request.is_json:
        return jsonify({"error": "Content-Type debe ser application/json"}), 400

    data = request.get_json(silent=True) or {}
    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))

    if not username or not password:
        return jsonify({"error": "Usuario y contraseña son requeridos"}), 400

    usuario, error = auth_mod.verificar_login(username, password)

    if usuario:
        token = generate_token(usuario)
        logger.info("Login exitoso: %s desde %s", username, ip)
        registrar_auditoria(
            accion="login",
            recurso="auth",
            exitoso=True,
            codigo_respuesta=200,
            detalle={"username": username},
        )
        return jsonify({
            "success": True,
            "token": token,
            "user": {
                "username": usuario["username"],
                "nombre":   usuario["nombre"],
                "rol":      usuario["rol"],
                "grupo":    usuario.get("grupo", ""),
            },
        })

    logger.warning("Login fallido: usuario='%s' desde %s — %s", username, ip, error)
    registrar_auditoria(
        accion="login",
        recurso="auth",
        exitoso=False,
        codigo_respuesta=401,
        detalle={"username": username, "error": error},
    )
    return jsonify({"error": error or "Credenciales incorrectas"}), 401


# ── Rutas de Cliente ──────────────────────────────────────────


@app.route("/api/auth/verify", methods=["GET"])
@token_required
def api_verify_token():
    return jsonify({"valid": True, "user": request.current_user})


# ── Dashboard ─────────────────────────────────────────────────
@app.route("/api/dashboard/stats", methods=["GET"])
@token_required
def api_stats():
    stats = cliente_service.get_stats()
    stats.update(empleados_mod.get_stats_empleados())
    stats.update(compras_mod.get_stats_compras())
    return jsonify(stats)


@app.route("/api/dashboard/cumpleaneros", methods=["GET"])
@token_required
def api_cumpleaneros():
    cumpleaneros = cliente_service.get_cumpleaneros_mes()
    return jsonify({"cumpleaneros": cumpleaneros})


# ── Endpoint de diagnóstico para debugging de cumpleaños ───────
@app.route("/api/debug/cumpleaneros-info", methods=["GET"])
@token_required
def debug_cumpleaneros():
    try:
        from database import db_connection
        with db_connection() as (conn, cursor):
            cursor.execute("SELECT COUNT(*) FROM clientes")
            total = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM clientes WHERE estado = 'Activo'")
            activos = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM clientes WHERE fecha_nacimiento IS NOT NULL")
            con_fecha = cursor.fetchone()[0]
            
            cursor.execute(
                "SELECT COUNT(*) FROM clientes WHERE EXTRACT(MONTH FROM fecha_nacimiento) = EXTRACT(MONTH FROM NOW()) AND estado = 'Activo' AND fecha_nacimiento IS NOT NULL"
            )
            cumpleaneros_mes = cursor.fetchone()[0]
        
        return jsonify({
            "info": {
                "total_clientes": total,
                "activos": activos,
                "con_fecha_nacimiento": con_fecha,
                "cumpleaneros_mes_actual": cumpleaneros_mes
            }
        }), 200
    except Exception as exc:
        logger.error("Debug error: %s", exc, exc_info=True)
        return jsonify({"error": str(exc)}), 500


# ── Dependencias ──────────────────────────────────────────────
@app.route("/api/dependencias", methods=["GET"])
@token_required
def api_get_dependencias():
    return jsonify(empleados_mod.get_all_dependencias())


@app.route("/api/dependencias", methods=["POST"])
@token_required
def api_create_dependencia():
    if not request.is_json:
        return jsonify({"error": "Content-Type debe ser application/json"}), 400
    data = request.get_json(silent=True) or {}
    data["usuario"] = get_usuario()
    r = empleados_mod.create_dependencia(data)
    return (jsonify(r), 400) if "error" in r else (jsonify(r), 201)


# ── Empleados ─────────────────────────────────────────────────
@app.route("/api/empleados", methods=["GET"])
@token_required
def api_get_empleados():
    try:
        page = max(1, int(request.args.get("page", 1)))
    except (ValueError, TypeError):
        page = 1
    return jsonify(empleados_mod.get_all_empleados(
        nombre=request.args.get("nombre") or None,
        dependencia=request.args.get("dependencia") or None,
        estado=request.args.get("estado") or None,
        page=page,
    ))


@app.route("/api/empleados/<int:id>", methods=["GET"])
@token_required
def api_get_empleado(id):
    d = empleados_mod.get_empleado_by_id(id)
    return jsonify(d) if d else (jsonify({"error": "No encontrado"}), 404)


@app.route("/api/empleados", methods=["POST"])
@token_required
def api_create_empleado():
    if not request.is_json:
        return jsonify({"error": "Content-Type debe ser application/json"}), 400
    data = request.get_json(silent=True) or {}
    data["usuario"] = get_usuario()
    r = empleados_mod.create_empleado(data)
    return (jsonify(r), 400) if "error" in r else (jsonify(r), 201)


@app.route("/api/empleados/<int:id>", methods=["PUT"])
@token_required
def api_update_empleado(id):
    if not request.is_json:
        return jsonify({"error": "Content-Type debe ser application/json"}), 400
    data = request.get_json(silent=True) or {}
    data["usuario"] = get_usuario()
    r = empleados_mod.update_empleado(id, data)
    return (jsonify(r), 400) if "error" in r else jsonify(r)


@app.route("/api/empleados/<int:id>/reasignar", methods=["PATCH"])
@token_required
def api_reasignar(id):
    if not request.is_json:
        return jsonify({"error": "Content-Type debe ser application/json"}), 400
    data = request.get_json(silent=True) or {}
    data["usuario"] = get_usuario()
    r = empleados_mod.reasignar_dependencia(id, data)
    return (jsonify(r), 400) if "error" in r else jsonify(r)


# ── Compras ───────────────────────────────────────────────────
@app.route("/api/compras", methods=["GET"])
@token_required
def api_get_compras():
    try:
        page = max(1, int(request.args.get("page", 1)))
    except (ValueError, TypeError):
        page = 1
    return jsonify(compras_mod.get_all_compras(
        proveedor=request.args.get("proveedor") or None,
        estado_pago=request.args.get("estado_pago") or None,
        page=page,
    ))


@app.route("/api/compras/<int:id>", methods=["GET"])
@token_required
def api_get_compra(id):
    d = compras_mod.get_compra_by_id(id)
    return jsonify(d) if d else (jsonify({"error": "No encontrado"}), 404)


@app.route("/api/compras", methods=["POST"])
@token_required
def api_create_compra():
    if not request.is_json:
        return jsonify({"error": "Content-Type debe ser application/json"}), 400
    data = request.get_json(silent=True) or {}
    data["usuario"] = get_usuario()
    r = compras_mod.create_compra(data)
    return (jsonify(r), 400) if "error" in r else (jsonify(r), 201)


@app.route("/api/compras/<int:id>/estado", methods=["PATCH"])
@token_required
def api_estado_compra(id):
    if not request.is_json:
        return jsonify({"error": "Content-Type debe ser application/json"}), 400
    body = request.get_json(silent=True) or {}
    r = compras_mod.update_estado_pago(id, body.get("estado_pago", ""), get_usuario())
    return (jsonify(r), 400) if "error" in r else jsonify(r)


# ── Main ──────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  CRM Ing Software - API Backend")
    print("  Servidor corriendo en: http://localhost:5000")
    print("  DEBUG:", DEBUG)
    print("=" * 60)
    app.run(debug=DEBUG, host="0.0.0.0", port=5000)

