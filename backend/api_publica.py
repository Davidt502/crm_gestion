"""
api_publica.py - Portal de API pública con control total de admin
VERSIÓN COMPLETA Y CORREGIDA - Incluye creación de usuarios con contraseña
"""
import secrets
import json
import logging
import smtplib
import os
import time
import jwt
from functools import wraps
from datetime import datetime, timezone, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Blueprint, request, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash
from database import db_connection
from middleware.auth_middleware import token_required

logger = logging.getLogger(__name__)
api_publica_bp = Blueprint("api_publica", __name__)

# ── Configuración ──────────────────────────────────────────────
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "")
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://crm-frontend-reg9.onrender.com")
BACKEND_URL = os.getenv("BACKEND_URL", "https://crm-gestion.onrender.com")
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'tu-secret-key-cambia-esto')

# ── CORS ────────────────────────────────────────────────────────
@api_publica_bp.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-API-Token'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, PATCH, OPTIONS'
    return response

@api_publica_bp.route('/api/admin/<path:path>', methods=['OPTIONS'])
@api_publica_bp.route('/api/admin', methods=['OPTIONS'])
@api_publica_bp.route('/api/portal/<path:path>', methods=['OPTIONS'])
def handle_options(path=None):
    return '', 200

# ── Helpers ───────────────────────────────────────────────────
def _get_ip():
    xff = request.headers.get("X-Forwarded-For", "")
    return (xff.split(",")[0].strip() if xff else request.remote_addr or "desconocida")[:50]

def _get_ua():
    return request.headers.get("User-Agent", "")[:500]

def _enviar_correo(destinatario, asunto, cuerpo_html):
    if not SMTP_USER or not SMTP_PASS:
        logger.warning("SMTP no configurado, correo omitido.")
        return
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = asunto
        msg["From"] = SMTP_USER
        msg["To"] = destinatario
        msg.attach(MIMEText(cuerpo_html, "html"))
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as s:
            s.starttls()
            s.login(SMTP_USER, SMTP_PASS)
            s.sendmail(SMTP_USER, destinatario, msg.as_string())
        logger.info("Correo enviado a %s", destinatario)
    except Exception as e:
        logger.error("Error enviando correo: %s", e)

def _ip_bloqueada(ip):
    try:
        with db_connection() as (conn, cursor):
            cursor.execute("SELECT 1 FROM api_ips_bloqueadas WHERE ip=%s AND activo=TRUE", [ip])
            return cursor.fetchone() is not None
    except:
        return False

def _solo_admin():
    """Verifica si el usuario actual es administrador"""
    user = getattr(g, "current_user", None)
    
    if not user:
        return False, ""
    
    if isinstance(user, dict):
        username = user.get("username", "")
        rol = user.get("rol", "")
        if rol == "admin":
            return True, username
        
        try:
            with db_connection() as (conn, cursor):
                cursor.execute("SELECT rol, username FROM usuarios WHERE username = %s", [username])
                row = cursor.fetchone()
                if row:
                    return row[0] == "admin", row[1]
        except Exception as exc:
            logger.error("_solo_admin DB lookup: %s", exc)
        return False, username
    
    username = getattr(user, "username", "")
    try:
        with db_connection() as (conn, cursor):
            cursor.execute("SELECT rol FROM usuarios WHERE username = %s", [username])
            row = cursor.fetchone()
            if row:
                return row[0] == "admin", username
    except Exception as exc:
        logger.error("_solo_admin DB lookup: %s", exc)
    
    return False, username

# ══════════════════════════════════════════════════════════════
# RUTAS: Autenticación para usuarios portal
# ══════════════════════════════════════════════════════════════

@api_publica_bp.route("/api/portal/auth/login", methods=["POST"])
def portal_login():
    """Login para usuarios creados por admin (acceso solo al portal)"""
    if not request.is_json:
        return jsonify({"error": "Content-Type debe ser application/json"}), 400
    
    data = request.get_json(silent=True) or {}
    username = str(data.get("username", "")).strip()
    password = str(data.get("password", "")).strip()
    
    if not username or not password:
        return jsonify({"error": "Usuario y contraseña requeridos"}), 400
    
    try:
        with db_connection() as (conn, cursor):
            cursor.execute("""
                SELECT u.id_usuario, u.username, u.password_hash, u.nombre, u.rol,
                       up.endpoints_permitidos, up.max_requests_dia
                FROM usuarios u
                LEFT JOIN portal_usuarios up ON u.id_usuario = up.id_usuario
                WHERE u.username = %s
            """, [username])
            row = cursor.fetchone()
            
            if not row or not check_password_hash(row[2], password):
                return jsonify({"error": "Credenciales inválidas"}), 401
            
            id_usuario, username_db, password_hash, nombre, rol, endpoints, max_req = row
            
            # Generar token JWT para el portal
            token = jwt.encode({
                'id_usuario': id_usuario,
                'username': username,
                'rol': 'portal',
                'exp': datetime.utcnow() + timedelta(days=7)
            }, JWT_SECRET_KEY, algorithm='HS256')
            
            # Actualizar último acceso
            cursor.execute("UPDATE portal_usuarios SET ultimo_acceso = NOW() WHERE id_usuario = %s", [id_usuario])
            
            # Parsear endpoints permitidos
            try:
                endpoints_list = json.loads(endpoints) if endpoints else []
            except:
                endpoints_list = []
            
            return jsonify({
                "success": True,
                "token": token,
                "user": {
                    "id": id_usuario,
                    "username": username,
                    "nombre": nombre,
                    "rol": "portal",
                    "endpoints_permitidos": endpoints_list,
                    "max_requests_dia": max_req or 500
                }
            })
    except Exception as exc:
        logger.error("portal_login: %s", exc, exc_info=True)
        return jsonify({"error": "Error interno"}), 500


def portal_token_required(f):
    """Decorator para verificar token de portal"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        token = auth_header.replace('Bearer ', '') if auth_header.startswith('Bearer ') else None
        
        if not token:
            return jsonify({"error": "Token requerido"}), 401
        
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
            if payload.get('rol') != 'portal':
                return jsonify({"error": "Acceso no autorizado"}), 403
            
            g.portal_user = payload
            return f(*args, **kwargs)
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expirado"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Token inválido"}), 401
    return decorated


# ══════════════════════════════════════════════════════════════
# RUTAS: Gestión de usuarios portal (Admin)
# ══════════════════════════════════════════════════════════════

@api_publica_bp.route("/api/admin/portal/usuarios", methods=["GET"])
@token_required
def listar_usuarios_portal():
    """Listar todos los usuarios del portal (solo admin)"""
    es_admin, _ = _solo_admin()
    if not es_admin:
        return jsonify({"error": "Solo administradores"}), 403
    
    try:
        with db_connection() as (conn, cursor):
            cursor.execute("""
                SELECT 
                    u.id_usuario, 
                    u.username, 
                    u.nombre, 
                    u.email, 
                    u.fecha_creacion,
                    COALESCE(up.endpoints_permitidos, '[]') as endpoints_permitidos,
                    COALESCE(up.max_requests_dia, 500) as max_requests_dia,
                    COALESCE(up.ultimo_acceso, NULL) as ultimo_acceso,
                    COALESCE(up.total_requests, 0) as total_requests
                FROM usuarios u
                LEFT JOIN portal_usuarios up ON u.id_usuario = up.id_usuario
                WHERE u.rol = 'portal'
                ORDER BY u.fecha_creacion DESC
            """)
            
            columns = [desc[0] for desc in cursor.description]
            rows = []
            for row in cursor.fetchall():
                user_dict = dict(zip(columns, row))
                if user_dict.get('endpoints_permitidos'):
                    try:
                        user_dict['endpoints_permitidos'] = json.loads(user_dict['endpoints_permitidos'])
                    except:
                        user_dict['endpoints_permitidos'] = []
                for field in ['fecha_creacion', 'ultimo_acceso']:
                    if user_dict.get(field):
                        user_dict[field] = str(user_dict[field])
                rows.append(user_dict)
            
            return jsonify({"usuarios": rows, "total": len(rows)})
    except Exception as exc:
        logger.error("listar_usuarios_portal: %s", exc, exc_info=True)
        return jsonify({"error": str(exc)}), 500


@api_publica_bp.route("/api/admin/portal/usuarios", methods=["POST"])
@token_required
def crear_usuario_portal():
    """Crear nuevo usuario para el portal con contraseña (solo admin)"""
    es_admin, admin_user = _solo_admin()
    if not es_admin:
        return jsonify({"error": "Solo administradores"}), 403
    
    data = request.get_json(silent=True) or {}
    
    username = str(data.get("username", "")).strip()
    password = str(data.get("password", "")).strip()
    nombre = str(data.get("nombre", "")).strip()
    email = str(data.get("email", "")).strip()
    endpoints = data.get("endpoints_permitidos", ["/api/pub/clientes", "/api/pub/proveedores", "/api/pub/empleados"])
    max_requests = int(data.get("max_requests_dia", 500))
    
    # Validaciones
    if not username or len(username) < 3:
        return jsonify({"error": "Usuario debe tener al menos 3 caracteres"}), 400
    if not password or len(password) < 6:
        return jsonify({"error": "Contraseña debe tener al menos 6 caracteres"}), 400
    if not nombre:
        return jsonify({"error": "Nombre es requerido"}), 400
    if not email:
        return jsonify({"error": "Email es requerido"}), 400
    
    try:
        with db_connection() as (conn, cursor):
            # Verificar si usuario ya existe
            cursor.execute("SELECT id_usuario FROM usuarios WHERE username = %s", [username])
            if cursor.fetchone():
                return jsonify({"error": "El nombre de usuario ya existe"}), 400
            
            # Crear usuario con password hasheado
            password_hash = generate_password_hash(password)
            cursor.execute("""
                INSERT INTO usuarios (username, password_hash, nombre, email, rol)
                VALUES (%s, %s, %s, %s, 'portal')
                RETURNING id_usuario
            """, [username, password_hash, nombre, email])
            id_usuario = cursor.fetchone()[0]
            
            # Crear entrada en portal_usuarios
            cursor.execute("""
                INSERT INTO portal_usuarios (id_usuario, endpoints_permitidos, max_requests_dia, creado_por)
                VALUES (%s, %s, %s, %s)
            """, [id_usuario, json.dumps(endpoints), max_requests, admin_user])
            
            # Enviar correo con credenciales
            if email:
                login_url = f"{FRONTEND_URL}/portal_api.html"
                html = f"""
                <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto">
                    <h2 style="color:#2563eb">🎉 Acceso al Portal API - CRM</h2>
                    <p>Hola <strong>{nombre}</strong>,</p>
                    <p>Se ha creado tu cuenta de acceso al Portal de API del CRM.</p>
                    <div style="background:#f1f5f9;padding:16px;border-radius:8px;margin:16px 0">
                        <p><strong>🔑 Tus credenciales:</strong></p>
                        <p>Usuario: <code>{username}</code></p>
                        <p>Contraseña: <code>{password}</code></p>
                    </div>
                    <p>Puedes acceder al portal desde:</p>
                    <p><a href="{login_url}" style="background:#2563eb;color:white;padding:10px 20px;text-decoration:none;border-radius:6px">Acceder al Portal</a></p>
                    <p style="color:#6b7280;font-size:12px;margin-top:16px">
                        Por seguridad, cambia tu contraseña después del primer inicio de sesión.
                    </p>
                </div>"""
                _enviar_correo(email, "🎉 Tu cuenta de acceso al Portal API", html)
            
            return jsonify({
                "success": True,
                "usuario": {
                    "id": id_usuario,
                    "username": username,
                    "nombre": nombre,
                    "email": email,
                    "endpoints_permitidos": endpoints,
                    "max_requests_dia": max_requests
                },
                "mensaje": f"Usuario {username} creado exitosamente"
            })
    except Exception as exc:
        logger.error("crear_usuario_portal: %s", exc, exc_info=True)
        return jsonify({"error": str(exc)}), 500


@api_publica_bp.route("/api/admin/portal/usuarios/<int:id_usuario>", methods=["PUT"])
@token_required
def actualizar_usuario_portal(id_usuario):
    """Actualizar usuario portal (solo admin)"""
    es_admin, _ = _solo_admin()
    if not es_admin:
        return jsonify({"error": "Solo administradores"}), 403
    
    data = request.get_json(silent=True) or {}
    
    try:
        with db_connection() as (conn, cursor):
            if "max_requests_dia" in data:
                cursor.execute("UPDATE portal_usuarios SET max_requests_dia = %s WHERE id_usuario = %s", 
                              [data["max_requests_dia"], id_usuario])
            if "endpoints_permitidos" in data:
                cursor.execute("UPDATE portal_usuarios SET endpoints_permitidos = %s WHERE id_usuario = %s",
                              [json.dumps(data["endpoints_permitidos"]), id_usuario])
            if "activo" in data:
                cursor.execute("UPDATE usuarios SET activo = %s WHERE id_usuario = %s",
                              [data["activo"], id_usuario])
        
        return jsonify({"success": True, "mensaje": "Usuario actualizado"})
    except Exception as exc:
        logger.error("actualizar_usuario_portal: %s", exc, exc_info=True)
        return jsonify({"error": str(exc)}), 500


@api_publica_bp.route("/api/admin/portal/usuarios/<int:id_usuario>", methods=["DELETE"])
@token_required
def eliminar_usuario_portal(id_usuario):
    """Eliminar usuario portal (solo admin)"""
    es_admin, _ = _solo_admin()
    if not es_admin:
        return jsonify({"error": "Solo administradores"}), 403
    
    try:
        with db_connection() as (conn, cursor):
            cursor.execute("DELETE FROM portal_usuarios WHERE id_usuario = %s", [id_usuario])
            cursor.execute("DELETE FROM usuarios WHERE id_usuario = %s", [id_usuario])
        return jsonify({"success": True, "mensaje": "Usuario eliminado"})
    except Exception as exc:
        logger.error("eliminar_usuario_portal: %s", exc, exc_info=True)
        return jsonify({"error": str(exc)}), 500


# ══════════════════════════════════════════════════════════════
# ENDPOINTS PÚBLICOS (sin auth interna)
# ══════════════════════════════════════════════════════════════

@api_publica_bp.route("/api/portal/solicitar", methods=["POST"])
def solicitar_acceso():
    """Solicitud pública de acceso a API"""
    if not request.is_json:
        return jsonify({"error": "Content-Type debe ser application/json"}), 400

    data = request.get_json(silent=True) or {}
    nombre = str(data.get("nombre", "")).strip()
    carnet = str(data.get("carnet", "")).strip()
    tel = str(data.get("telefono", "")).strip()
    correo = str(data.get("correo_estudiante", "")).strip()
    numero_grupo = str(data.get("numero_grupo", "")).strip()
    apis_raw = data.get("apis_solicitadas", [])
    if isinstance(apis_raw, list):
        apis_solicitadas = ", ".join(str(a) for a in apis_raw)
    else:
        apis_solicitadas = str(apis_raw).strip()
    ip = _get_ip()
    ua = _get_ua()

    if not nombre:
        return jsonify({"error": "Nombre completo requerido."}), 400
    if not carnet:
        return jsonify({"error": "Número de carnet requerido."}), 400
    if not correo:
        return jsonify({"error": "Correo estudiantil requerido."}), 400
    if not numero_grupo:
        return jsonify({"error": "Número de grupo requerido."}), 400
    if not apis_solicitadas:
        return jsonify({"error": "Debes indicar qué API(s) deseas habilitar."}), 400

    if _ip_bloqueada(ip):
        return jsonify({"error": "Acceso denegado."}), 403

    token_ver = secrets.token_urlsafe(32)

    try:
        with db_connection() as (conn, cursor):
            cursor.execute("""
                SELECT id_solicitud FROM api_solicitudes
                WHERE correo=%s AND estado='Pendiente'
            """, [correo])
            if cursor.fetchone():
                return jsonify({"error": "Ya tienes una solicitud pendiente con ese correo."}), 400

            cursor.execute("""
                INSERT INTO api_solicitudes
                    (nombre, correo, telefono, empresa, cargo, motivo, ip_solicitud, user_agent, token_verificacion)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id_solicitud
            """, [nombre, correo, tel or None, carnet, numero_grupo, apis_solicitadas, ip, ua, token_ver])
            id_sol = cursor.fetchone()[0]

        # Enviar correo al admin
        if ADMIN_EMAIL:
            aprobar_url = f"{BACKEND_URL}/api/portal/aprobar-link/{token_ver}"
            rechazar_url = f"{BACKEND_URL}/api/portal/rechazar-link/{token_ver}"
            html = f"""
            <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto">
            <h2 style="color:#2563eb">🔔 Nueva solicitud de acceso a API</h2>
            <table style="width:100%;border-collapse:collapse">
              <tr><td style="padding:8px;font-weight:bold">Nombre:</td><td>{nombre}</td></tr>
              <tr><td style="padding:8px;font-weight:bold">Carnet:</td><td>{carnet}</td></tr>
              <tr><td style="padding:8px;font-weight:bold">Teléfono:</td><td>{tel or 'N/A'}</td></tr>
              <tr><td style="padding:8px;font-weight:bold">Correo:</td><td>{correo}</td></tr>
              <tr><td style="padding:8px;font-weight:bold">Grupo:</td><td>{numero_grupo}</td></tr>
              <tr><td style="padding:8px;font-weight:bold">APIs:</td><td>{apis_solicitadas}</td></tr>
              <tr><td style="padding:8px;font-weight:bold">IP:</td><td>{ip}</td></tr>
            20table
            <div style="margin-top:24px">
              <a href="{aprobar_url}" style="background:#16a34a;color:white;padding:12px 24px;text-decoration:none;border-radius:6px">✅ Aprobar</a>
              <a href="{rechazar_url}" style="background:#dc2626;color:white;padding:12px 24px;text-decoration:none;border-radius:6px">❌ Rechazar</a>
            </div>
            </div>"""
            _enviar_correo(ADMIN_EMAIL, f"[CRM API] Nueva solicitud de {nombre}", html)

        return jsonify({
            "success": True,
            "id_solicitud": id_sol,
            "mensaje": "Solicitud enviada. Recibirás respuesta por correo."
        }), 201
    except Exception as exc:
        logger.error("solicitar_acceso: %s", exc, exc_info=True)
        return jsonify({"error": str(exc)}), 500


@api_publica_bp.route("/api/portal/aprobar-link/<token_ver>", methods=["GET"])
def aprobar_via_link(token_ver):
    """Aprobar solicitud desde enlace del correo"""
    return _resolver_via_link(token_ver, "Aprobado")


@api_publica_bp.route("/api/portal/rechazar-link/<token_ver>", methods=["GET"])
def rechazar_via_link(token_ver):
    """Rechazar solicitud desde enlace del correo"""
    return _resolver_via_link(token_ver, "Rechazado")


def _resolver_via_link(token_ver, accion):
    try:
        with db_connection() as (conn, cursor):
            cursor.execute("""
                SELECT id_solicitud, nombre, correo, estado
                FROM api_solicitudes WHERE token_verificacion=%s
            """, [token_ver])
            row = cursor.fetchone()
            if not row:
                return jsonify({"error": "Enlace inválido o expirado."}), 404
            id_sol, nombre, correo, estado = row
            if estado != "Pendiente":
                return jsonify({"mensaje": f"Solicitud ya fue {estado}."}), 200

            if accion == "Aprobado":
                nuevo_token = secrets.token_urlsafe(48)
                cursor.execute("SELECT id_usuario FROM usuarios WHERE rol='admin' LIMIT 1")
                id_admin = cursor.fetchone()[0]
                cursor.execute("""
                    INSERT INTO api_tokens
                        (nombre_token, token, id_usuario, solo_lectura,
                         activo, usuario_creacion, max_requests_dia)
                    VALUES (%s, %s, %s, TRUE, TRUE, 'admin_link', 1000)
                    RETURNING id_token
                """, [f"Token - {nombre}", nuevo_token, id_admin])
                id_token = cursor.fetchone()[0]
                cursor.execute("""
                    UPDATE api_solicitudes SET estado='Aprobado',
                        aprobado_por='admin_link', fecha_resolucion=NOW()
                    WHERE id_solicitud=%s
                """, [id_sol])
                
                if correo:
                    html = f"""
                    <div style="font-family:Arial,sans-serif;max-width:600px">
                    <h2 style="color:#16a34a">✅ Tu acceso a la API ha sido aprobado</h2>
                    <p>Hola <strong>{nombre}</strong>, tu solicitud fue aprobada.</p>
                    <p><strong>Tu API Token:</strong></p>
                    <div style="background:#f1f5f9;padding:16px;border-radius:8px;font-family:monospace;word-break:break-all">
                      {nuevo_token}
                    </div>
                    <p><strong>Guárdalo bien, no se mostrará de nuevo.</strong></p>
                    <h3>¿Cómo usarlo?</h3>
                    <pre style="background:#1e293b;color:#e2e8f0;padding:16px;border-radius:8px">
curl -H "X-API-Token: {nuevo_token[:20]}..." \\
     {BACKEND_URL}/api/pub/clientes</pre>
                    </div>"""
                    _enviar_correo(correo, "✅ Tu acceso a la API ha sido aprobado", html)
                return jsonify({"mensaje": f"Solicitud aprobada."}), 200
            else:
                cursor.execute("""
                    UPDATE api_solicitudes SET estado='Rechazado',
                        aprobado_por='admin_link', fecha_resolucion=NOW()
                    WHERE id_solicitud=%s
                """, [id_sol])
                return jsonify({"mensaje": "Solicitud rechazada."}), 200
    except Exception as exc:
        logger.error("resolver_via_link: %s", exc, exc_info=True)
        return jsonify({"error": "Error procesando enlace."}), 500


# ══════════════════════════════════════════════════════════════
# GESTIÓN ADMIN - SOLICITUDES
# ══════════════════════════════════════════════════════════════

@api_publica_bp.route("/api/admin/solicitudes", methods=["GET"])
@token_required
def listar_solicitudes():
    es_admin, _ = _solo_admin()
    if not es_admin:
        return jsonify({"error": "Solo administradores."}), 403
    
    estado = request.args.get("estado")
    try:
        with db_connection() as (conn, cursor):
            if estado:
                cursor.execute("""
                    SELECT id_solicitud, nombre, correo, telefono, empresa, cargo, motivo,
                           estado, ip_solicitud, user_agent, fecha_solicitud, 
                           aprobado_por, fecha_resolucion, notas_admin
                    FROM api_solicitudes 
                    WHERE estado = %s
                    ORDER BY fecha_solicitud DESC
                """, [estado])
            else:
                cursor.execute("""
                    SELECT id_solicitud, nombre, correo, telefono, empresa, cargo, motivo,
                           estado, ip_solicitud, user_agent, fecha_solicitud, 
                           aprobado_por, fecha_resolucion, notas_admin
                    FROM api_solicitudes 
                    ORDER BY fecha_solicitud DESC
                """)
            
            cols = [d[0] for d in cursor.description]
            rows = [dict(zip(cols, r)) for r in cursor.fetchall()]
            for r in rows:
                for f in ("fecha_solicitud", "fecha_resolucion"):
                    if r.get(f):
                        r[f] = str(r[f])
        return jsonify({"solicitudes": rows, "total": len(rows)})
    except Exception as exc:
        logger.error("listar_solicitudes: %s", exc, exc_info=True)
        return jsonify({"error": str(exc)}), 500


@api_publica_bp.route("/api/admin/solicitudes/<int:id_sol>/aprobar", methods=["POST"])
@token_required
def aprobar_solicitud(id_sol):
    es_admin, admin_user = _solo_admin()
    if not es_admin:
        return jsonify({"error": "Solo administradores."}), 403

    data = request.get_json(silent=True) or {}
    puede_escribir = bool(data.get("puede_escribir", False))
    max_req = data.get("max_requests_dia", 1000)
    endpoints = data.get("endpoints_permitidos", [])

    try:
        with db_connection() as (conn, cursor):
            cursor.execute("""
                SELECT nombre, correo, empresa, cargo
                FROM api_solicitudes WHERE id_solicitud=%s AND estado='Pendiente'
            """, [id_sol])
            row = cursor.fetchone()
            if not row:
                return jsonify({"error": "Solicitud no encontrada o ya procesada."}), 404
            nombre, correo, carnet, grupo = row

            nuevo_token = secrets.token_urlsafe(48)
            
            cursor.execute("SELECT id_usuario FROM usuarios WHERE username=%s", [admin_user])
            r = cursor.fetchone()
            id_admin = r[0] if r else 1

            cursor.execute("""
                INSERT INTO api_tokens
                    (nombre_token, token, id_usuario, endpoints_permitidos,
                     solo_lectura, activo, max_requests_dia, usuario_creacion)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id_token
            """, [
                f"Token - {nombre}", nuevo_token, id_admin, json.dumps(endpoints),
                not puede_escribir, True, max_req, admin_user
            ])
            id_token = cursor.fetchone()[0]

            cursor.execute("""
                UPDATE api_solicitudes 
                SET estado='Aprobado', aprobado_por=%s, fecha_resolucion=NOW()
                WHERE id_solicitud=%s
            """, [admin_user, id_sol])

        # Enviar correo al solicitante
        if correo:
            permisos = "Lectura y Escritura" if puede_escribir else "Solo Lectura"
            html = f"""
            <div style="font-family:Arial,sans-serif;max-width:600px">
            <h2 style="color:#16a34a">✅ Acceso a API Aprobado</h2>
            <p>Hola <strong>{nombre}</strong>, tu solicitud fue aprobada.</p>
            <p><strong>Permisos:</strong> {permisos}</p>
            <p><strong>Límite diario:</strong> {max_req} requests</p>
            <p><strong>Tu API Token:</strong></p>
            <div style="background:#f1f5f9;padding:16px;border-radius:8px;font-family:monospace;word-break:break-all">
              {nuevo_token}
            </div>
            <p><strong>Guárdalo bien, no se mostrará de nuevo.</strong></p>
            <h3>Ejemplo de uso:</h3>
            <pre style="background:#1e293b;color:#e2e8f0;padding:16px;border-radius:8px">
curl -H "X-API-Token: TU_TOKEN" \\
     {BACKEND_URL}/api/pub/clientes</pre>
            <p>Documentación: {FRONTEND_URL}/portal_api.html</p>
            </div>"""
            _enviar_correo(correo, "✅ Tu acceso a la API ha sido aprobado", html)

        return jsonify({
            "success": True,
            "id_token": id_token,
            "token": nuevo_token,
            "mensaje": f"Solicitud aprobada."
        })
    except Exception as exc:
        logger.error("aprobar_solicitud: %s", exc, exc_info=True)
        return jsonify({"error": str(exc)}), 500


@api_publica_bp.route("/api/admin/solicitudes/<int:id_sol>/rechazar", methods=["POST"])
@token_required
def rechazar_solicitud(id_sol):
    es_admin, admin_user = _solo_admin()
    if not es_admin:
        return jsonify({"error": "Solo administradores."}), 403
    
    data = request.get_json(silent=True) or {}
    notas = str(data.get("notas", "")).strip()
    
    try:
        with db_connection() as (conn, cursor):
            cursor.execute("SELECT nombre, correo FROM api_solicitudes WHERE id_solicitud=%s", [id_sol])
            row = cursor.fetchone()
            if not row:
                return jsonify({"error": "Solicitud no encontrada."}), 404
            nombre, correo = row
            
            cursor.execute("""
                UPDATE api_solicitudes 
                SET estado='Rechazado', aprobado_por=%s, fecha_resolucion=NOW(), notas_admin=%s
                WHERE id_solicitud=%s AND estado='Pendiente'
            """, [admin_user, notas or None, id_sol])
            
            if cursor.rowcount == 0:
                return jsonify({"error": "Solicitud ya procesada."}), 400
        
        if correo:
            html = f"""
            <div style="font-family:Arial,sans-serif">
            <h2 style="color:#dc2626">Solicitud no aprobada</h2>
            <p>Hola {nombre}, tu solicitud de acceso a la API no fue aprobada.</p>
            {f"<p><strong>Motivo:</strong> {notas}</p>" if notas else ""}
            <p>Si crees que es un error, contáctanos.</p>
            </div>"""
            _enviar_correo(correo, "Actualización sobre tu solicitud de API", html)
        
        return jsonify({"success": True, "mensaje": "Solicitud rechazada."})
    except Exception as exc:
        logger.error("rechazar_solicitud: %s", exc, exc_info=True)
        return jsonify({"error": str(exc)}), 500


# ══════════════════════════════════════════════════════════════
# GESTIÓN ADMIN - TOKENS
# ══════════════════════════════════════════════════════════════

@api_publica_bp.route("/api/admin/tokens", methods=["GET"])
@token_required
def listar_tokens():
    es_admin, _ = _solo_admin()
    if not es_admin:
        return jsonify({"error": "Solo administradores."}), 403
    
    try:
        with db_connection() as (conn, cursor):
            cursor.execute("""
                SELECT 
                    id_token, 
                    nombre_token, 
                    token,
                    solo_lectura, 
                    activo, 
                    max_requests_dia,
                    total_usos,
                    fecha_creacion
                FROM api_tokens
                ORDER BY fecha_creacion DESC
            """)
            
            rows = []
            for row in cursor.fetchall():
                token_dict = {
                    "id_token": row[0],
                    "nombre_token": row[1],
                    "token_preview": row[2][:8] + "..." if row[2] else "",
                    "solo_lectura": row[3],
                    "activo": row[4],
                    "max_requests_dia": row[5] or 1000,
                    "total_usos": row[6] or 0,
                    "fecha_creacion": str(row[7]) if row[7] else ""
                }
                rows.append(token_dict)
            
            return jsonify({"tokens": rows, "total": len(rows)})
    except Exception as exc:
        logger.error("listar_tokens: %s", exc, exc_info=True)
        return jsonify({"error": str(exc)}), 500


@api_publica_bp.route("/api/admin/tokens/<int:id_token>/toggle", methods=["PATCH"])
@token_required
def toggle_token(id_token):
    es_admin, _ = _solo_admin()
    if not es_admin:
        return jsonify({"error": "Solo administradores."}), 403
    try:
        with db_connection() as (conn, cursor):
            cursor.execute("UPDATE api_tokens SET activo = NOT activo WHERE id_token = %s RETURNING activo", [id_token])
            row = cursor.fetchone()
            if not row:
                return jsonify({"error": "Token no encontrado."}), 404
        return jsonify({"success": True, "activo": row[0], "mensaje": "Token actualizado"})
    except Exception as exc:
        logger.error("toggle_token: %s", exc, exc_info=True)
        return jsonify({"error": str(exc)}), 500


# ══════════════════════════════════════════════════════════════
# GESTIÓN ADMIN - LOGS
# ══════════════════════════════════════════════════════════════

@api_publica_bp.route("/api/admin/logs", methods=["GET"])
@token_required
def listar_logs():
    es_admin, _ = _solo_admin()
    if not es_admin:
        return jsonify({"error": "Solo administradores."}), 403
    try:
        page = max(1, int(request.args.get("page", 1)))
        per_page = 50
        offset = (page - 1) * per_page
        
        with db_connection() as (conn, cursor):
            cursor.execute("SELECT COUNT(*) FROM api_logs")
            total = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT id_log, endpoint, metodo, ip_publica, codigo_respuesta, 
                       fecha_uso, exitoso, detalle
                FROM api_logs 
                ORDER BY fecha_uso DESC 
                LIMIT %s OFFSET %s
            """, [per_page, offset])
            
            rows = []
            for row in cursor.fetchall():
                rows.append({
                    "id_log": row[0],
                    "endpoint": row[1],
                    "metodo": row[2],
                    "ip_publica": row[3],
                    "codigo_respuesta": row[4],
                    "fecha_uso": str(row[5]) if row[5] else "",
                    "exitoso": row[6],
                    "detalle": row[7] or "",
                    "nombre_usuario": "",
                    "correo_usuario": ""
                })
        
        total_pages = max(1, (total + per_page - 1) // per_page)
        return jsonify({
            "logs": rows, 
            "total": total, 
            "page": page,
            "total_pages": total_pages
        })
    except Exception as exc:
        logger.error("listar_logs: %s", exc, exc_info=True)
        return jsonify({"error": str(exc)}), 500


# ══════════════════════════════════════════════════════════════
# GESTIÓN ADMIN - STATS
# ══════════════════════════════════════════════════════════════

@api_publica_bp.route("/api/admin/stats", methods=["GET"])
@token_required
def stats_portal():
    es_admin, _ = _solo_admin()
    if not es_admin:
        return jsonify({"error": "Solo administradores."}), 403
    try:
        with db_connection() as (conn, cursor):
            cursor.execute("SELECT COUNT(*) FROM api_solicitudes")
            total_sol = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM api_solicitudes WHERE estado='Pendiente'")
            pendientes = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM api_tokens WHERE activo=TRUE")
            tokens_activos = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM api_logs WHERE fecha_uso >= NOW() - INTERVAL '24 hours'")
            calls_24h = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM api_ips_bloqueadas WHERE activo=TRUE")
            ips_bloqueadas = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM portal_usuarios")
            usuarios_portal = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT endpoint, COUNT(*) as total
                FROM api_logs 
                WHERE fecha_uso >= NOW() - INTERVAL '7 days'
                GROUP BY endpoint 
                ORDER BY total DESC 
                LIMIT 5
            """)
            top_endpoints = [{"endpoint": r[0], "total": r[1]} for r in cursor.fetchall()]
        
        return jsonify({
            "total_solicitudes": total_sol,
            "pendientes": pendientes,
            "tokens_activos": tokens_activos,
            "llamadas_24h": calls_24h,
            "ips_bloqueadas": ips_bloqueadas,
            "usuarios_portal": usuarios_portal,
            "top_endpoints": top_endpoints
        })
    except Exception as exc:
        logger.error("stats_portal: %s", exc, exc_info=True)
        return jsonify({"error": str(exc)}), 500


# ══════════════════════════════════════════════════════════════
# GESTIÓN ADMIN - IPS BLOQUEADAS
# ══════════════════════════════════════════════════════════════

@api_publica_bp.route("/api/admin/ips-bloqueadas", methods=["GET"])
@token_required
def listar_ips_bloqueadas():
    es_admin, _ = _solo_admin()
    if not es_admin:
        return jsonify({"error": "Solo administradores."}), 403
    try:
        with db_connection() as (conn, cursor):
            cursor.execute("""
                SELECT id_bloqueo, ip, motivo, activo, fecha_bloqueo
                FROM api_ips_bloqueadas 
                WHERE activo = TRUE
                ORDER BY fecha_bloqueo DESC
            """)
            rows = []
            for row in cursor.fetchall():
                rows.append({
                    "id_bloqueo": row[0],
                    "ip": row[1],
                    "motivo": row[2] or "Sin motivo",
                    "activo": row[3],
                    "fecha_bloqueo": str(row[4]) if row[4] else ""
                })
        return jsonify({"ips": rows, "total": len(rows)})
    except Exception as exc:
        logger.error("listar_ips_bloqueadas: %s", exc, exc_info=True)
        return jsonify({"error": str(exc)}), 500


@api_publica_bp.route("/api/admin/ips-bloqueadas/<int:id_bloqueo>", methods=["DELETE"])
@token_required
def desbloquear_ip(id_bloqueo):
    es_admin, _ = _solo_admin()
    if not es_admin:
        return jsonify({"error": "Solo administradores."}), 403
    try:
        with db_connection() as (conn, cursor):
            cursor.execute("UPDATE api_ips_bloqueadas SET activo = FALSE WHERE id_bloqueo = %s", [id_bloqueo])
        return jsonify({"success": True, "mensaje": "IP desbloqueada"})
    except Exception as exc:
        logger.error("desbloquear_ip: %s", exc, exc_info=True)
        return jsonify({"error": str(exc)}), 500


# ══════════════════════════════════════════════════════════════
# GESTIÓN ADMIN - ALERTAS
# ══════════════════════════════════════════════════════════════

@api_publica_bp.route("/api/admin/alertas", methods=["GET"])
@token_required
def listar_alertas():
    es_admin, _ = _solo_admin()
    if not es_admin:
        return jsonify({"error": "Solo administradores."}), 403
    try:
        with db_connection() as (conn, cursor):
            cursor.execute("""
                SELECT id_alerta, tipo, descripcion, ip, fecha_alerta
                FROM api_alertas 
                ORDER BY fecha_alerta DESC
                LIMIT 100
            """)
            rows = []
            for row in cursor.fetchall():
                rows.append({
                    "id_alerta": row[0],
                    "tipo": row[1] or "info",
                    "descripcion": row[2] or "",
                    "ip": row[3] or "",
                    "fecha_alerta": str(row[4]) if row[4] else ""
                })
        return jsonify({"alertas": rows, "total": len(rows)})
    except Exception as exc:
        logger.error("listar_alertas: %s", exc, exc_info=True)
        return jsonify({"alertas": [], "total": 0})


# ══════════════════════════════════════════════════════════════
# ENDPOINTS PÚBLICOS CON TOKEN (datos del CRM)
# ══════════════════════════════════════════════════════════════

def token_publico_required(f):
    """Decorator para validar token público en endpoints de datos"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token_str = request.headers.get("X-API-Token", "").strip()
        if not token_str:
            return jsonify({"error": "Token requerido. Usa el header X-API-Token"}), 401
        
        try:
            with db_connection() as (conn, cursor):
                cursor.execute("""
                    SELECT t.id_token, t.activo, t.max_requests_dia, 
                           t.endpoints_permitidos, u.nombre
                    FROM api_tokens t
                    JOIN usuarios u ON t.id_usuario = u.id_usuario
                    WHERE t.token = %s
                """, [token_str])
                row = cursor.fetchone()
                if not row:
                    return jsonify({"error": "Token inválido"}), 401
                
                id_token, activo, max_req, endpoints_json, nombre = row
                if not activo:
                    return jsonify({"error": "Token inactivo"}), 401
                
                # Verificar si el token tiene acceso al endpoint actual
                try:
                    endpoints = json.loads(endpoints_json) if endpoints_json else []
                except:
                    endpoints = []
                
                current_endpoint = request.path
                if endpoints and not any(current_endpoint.startswith(e.rstrip("*")) for e in endpoints):
                    return jsonify({"error": "Este token no tiene acceso a este endpoint"}), 403
                
                g.token_info = {"id_token": id_token, "nombre": nombre}
                return f(*args, **kwargs)
        except Exception as e:
            logger.error("token_publico_required: %s", e)
            return jsonify({"error": "Error validando token"}), 500
    return decorated


@api_publica_bp.route("/api/pub/clientes", methods=["GET"])
@token_publico_required
def pub_clientes():
    try:
        with db_connection() as (conn, cursor):
            cursor.execute("""
                SELECT id_cliente, nombre, correo, telefono, estado
                FROM clientes 
                WHERE estado = 'Activo' 
                LIMIT 100
            """)
            cols = [d[0] for d in cursor.description]
            rows = [dict(zip(cols, r)) for r in cursor.fetchall()]
        return jsonify({"clientes": rows, "total": len(rows)})
    except Exception as exc:
        logger.error("pub_clientes: %s", exc)
        return jsonify({"error": str(exc)}), 500


@api_publica_bp.route("/api/pub/proveedores", methods=["GET"])
@token_publico_required
def pub_proveedores():
    try:
        with db_connection() as (conn, cursor):
            cursor.execute("""
                SELECT id_proveedor, nombre_empresa, nit, telefono, correo, estado
                FROM proveedores 
                WHERE estado = 'Activo' 
                LIMIT 100
            """)
            cols = [d[0] for d in cursor.description]
            rows = [dict(zip(cols, r)) for r in cursor.fetchall()]
        return jsonify({"proveedores": rows, "total": len(rows)})
    except Exception as exc:
        logger.error("pub_proveedores: %s", exc)
        return jsonify({"error": str(exc)}), 500


@api_publica_bp.route("/api/pub/empleados", methods=["GET"])
@token_publico_required
def pub_empleados():
    try:
        with db_connection() as (conn, cursor):
            cursor.execute("""
                SELECT id_empleado, nombre, cargo, correo, estado
                FROM empleados 
                WHERE estado = 'Activo' 
                LIMIT 100
            """)
            cols = [d[0] for d in cursor.description]
            rows = [dict(zip(cols, r)) for r in cursor.fetchall()]
        return jsonify({"empleados": rows, "total": len(rows)})
    except Exception as exc:
        logger.error("pub_empleados: %s", exc)
        return jsonify({"error": str(exc)}), 500