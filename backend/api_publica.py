"""
api_publica.py - Portal de API pública con control total de admin
"""
import secrets, json, logging, smtplib, os, time
from functools import wraps
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Blueprint, request, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash
from database import db_connection
from middleware.auth_middleware import token_required

logger = logging.getLogger(__name__)
api_publica_bp = Blueprint("api_publica", __name__)

# ── Config correo ──────────────────────────────────────────────
SMTP_HOST     = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT     = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER     = os.getenv("SMTP_USER", "")
SMTP_PASS     = os.getenv("SMTP_PASS", "")
ADMIN_EMAIL   = os.getenv("ADMIN_EMAIL", "")
FRONTEND_URL  = os.getenv("FRONTEND_URL", "https://crm-frontend-reg9.onrender.com")
BACKEND_URL   = os.getenv("BACKEND_URL", "https://crm-gestion.onrender.com")


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
        msg["From"]    = SMTP_USER
        msg["To"]      = destinatario
        msg.attach(MIMEText(cuerpo_html, "html"))
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as s:
            s.starttls()
            s.login(SMTP_USER, SMTP_PASS)
            s.sendmail(SMTP_USER, destinatario, msg.as_string())
        logger.info("Correo enviado a %s", destinatario)
    except Exception as e:
        logger.error("Error enviando correo: %s", e)

def _registrar_log(id_token, endpoint, metodo, ip, ua, codigo, exitoso,
                   detalle=None, nombre=None, correo=None, tel=None, empresa=None, ms=None):
    try:
        with db_connection() as (conn, cursor):
            cursor.execute("""
                INSERT INTO api_logs
                    (id_token,nombre_usuario,correo_usuario,telefono_usuario,empresa_usuario,
                     endpoint,metodo,ip_publica,user_agent,codigo_respuesta,
                     tiempo_respuesta_ms,exitoso,detalle)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, [id_token,nombre,correo,tel,empresa,endpoint,metodo,ip,ua,codigo,ms,exitoso,detalle])
    except Exception as exc:
        logger.error("Error log: %s", exc)

def _ip_bloqueada(ip):
    try:
        with db_connection() as (conn, cursor):
            cursor.execute("SELECT 1 FROM api_ips_bloqueadas WHERE ip=%s AND activo=TRUE", [ip])
            return cursor.fetchone() is not None
    except:
        return False

def _crear_alerta(tipo, descripcion, ip=None, id_token=None, correo=None):
    try:
        with db_connection() as (conn, cursor):
            cursor.execute("""
                INSERT INTO api_alertas (tipo,descripcion,ip,id_token,correo_usuario)
                VALUES (%s,%s,%s,%s,%s)
            """, [tipo, descripcion, ip, id_token, correo])
    except Exception as exc:
        logger.error("Error alerta: %s", exc)


# ── Validar token público ──────────────────────────────────────
def validar_token_publico(token_str):
    if not token_str:
        return None, "Token requerido."
    try:
        with db_connection() as (conn, cursor):
            cursor.execute("""
                SELECT t.id_token, t.nombre_token, t.endpoints_permitidos,
                       t.puede_leer, t.puede_escribir, t.activo, t.expira_en,
                       t.max_requests_dia, t.requests_hoy, t.fecha_reset_contador,
                       u.nombre, u.username,
                       s.nombre, s.correo, s.telefono, s.empresa
                FROM api_tokens t
                JOIN usuarios u ON t.id_usuario = u.id_usuario
                LEFT JOIN api_solicitudes s ON t.id_solicitud = s.id_solicitud
                WHERE t.token = %s
            """, [token_str])
            row = cursor.fetchone()
            if not row:
                return None, "Token inválido."

            (id_token, nombre_token, endpoints_json, puede_leer, puede_escribir,
             activo, expira_en, max_req, req_hoy, fecha_reset,
             prop_nombre, prop_user, sol_nombre, sol_correo, sol_tel, sol_empresa) = row

            if not activo:
                return None, "Token inactivo."
            if expira_en and datetime.now(timezone.utc) > expira_en.replace(tzinfo=timezone.utc):
                return None, "Token expirado."

            # Reset contador diario
            hoy = datetime.now().date()
            if fecha_reset != hoy:
                cursor.execute("""
                    UPDATE api_tokens SET requests_hoy=1, fecha_reset_contador=%s WHERE id_token=%s
                """, [hoy, id_token])
            else:
                # Verificar límite diario
                if max_req and req_hoy >= max_req:
                    _crear_alerta("limite_excedido",
                        f"Token {id_token} ({sol_nombre}) excedió límite diario de {max_req} requests",
                        id_token=id_token, correo=sol_correo)
                    return None, f"Límite diario de {max_req} requests excedido."
                cursor.execute("""
                    UPDATE api_tokens SET requests_hoy=requests_hoy+1, total_usos=total_usos+1, ultimo_uso=NOW()
                    WHERE id_token=%s
                """, [id_token])

            try:
                endpoints = json.loads(endpoints_json) if endpoints_json else []
            except:
                endpoints = []

            return {
                "id_token":      id_token,
                "nombre":        nombre_token,
                "endpoints":     endpoints,
                "puede_leer":    bool(puede_leer),
                "puede_escribir": bool(puede_escribir),
                "sol_nombre":    sol_nombre or prop_nombre,
                "sol_correo":    sol_correo,
                "sol_telefono":  sol_tel,
                "sol_empresa":   sol_empresa,
            }, None
    except Exception as exc:
        logger.error("validar_token: %s", exc, exc_info=True)
        return None, "Error interno."


# ── Decorator token público ────────────────────────────────────
def token_publico_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        ip  = _get_ip()
        ua  = _get_ua()
        ep  = request.path
        met = request.method
        t0  = time.monotonic()

        if _ip_bloqueada(ip):
            _registrar_log(None, ep, met, ip, ua, 403, False, "IP bloqueada")
            return jsonify({"error": "Acceso denegado."}), 403

        token_str = (request.headers.get("X-API-Token") or request.args.get("api_token") or "").strip()
        token_info, error = validar_token_publico(token_str)

        if error:
            _registrar_log(None, ep, met, ip, ua, 401, False, error)
            return jsonify({"error": error}), 401

        # Verificar endpoint
        eps = token_info.get("endpoints", [])
        if eps and not any(ep.startswith(e.rstrip("*")) for e in eps):
            _registrar_log(token_info["id_token"], ep, met, ip, ua, 403, False, "Endpoint no permitido",
                           token_info["sol_nombre"], token_info["sol_correo"])
            return jsonify({"error": "Este token no tiene acceso a este endpoint."}), 403

        # Verificar escritura
        if met not in ("GET","HEAD","OPTIONS") and not token_info["puede_escribir"]:
            _registrar_log(token_info["id_token"], ep, met, ip, ua, 403, False, "Solo lectura",
                           token_info["sol_nombre"], token_info["sol_correo"])
            return jsonify({"error": "Este token es de solo lectura."}), 403

        g.token_publico = token_info
        resp = f(*args, **kwargs)
        ms   = int((time.monotonic() - t0) * 1000)
        code = resp[1] if isinstance(resp, tuple) else 200
        _registrar_log(token_info["id_token"], ep, met, ip, ua, code, code < 400, None,
                       token_info["sol_nombre"], token_info["sol_correo"],
                       token_info["sol_telefono"], token_info["sol_empresa"], ms)
        return resp
    return decorated


# ══════════════════════════════════════════════════════════════
# NUEVAS RUTAS: Autenticación para usuarios portal
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
                SELECT u.id_usuario, u.username, u.password_hash, u.nombre, u.activo,
                       u.rol, up.id_portal_usuario, up.endpoints_permitidos, up.max_requests_dia
                FROM usuarios u
                JOIN portal_usuarios up ON u.id_usuario = up.id_usuario
                WHERE u.username = %s AND u.activo = TRUE
            """, [username])
            row = cursor.fetchone()
            
            if not row or not check_password_hash(row[2], password):
                return jsonify({"error": "Credenciales inválidas"}), 401
            
            id_usuario, username_db, password_hash, nombre, activo, rol, id_portal, endpoints, max_req = row
            
            # Generar token JWT específico para portal
            import jwt
            token = jwt.encode({
                'id_usuario': id_usuario,
                'username': username,
                'rol': 'portal',
                'id_portal': id_portal,
                'exp': datetime.utcnow() + datetime.timedelta(days=7)
            }, os.getenv('JWT_SECRET_KEY', 'tu-secret-key-cambia-esto'), algorithm='HS256')
            
            return jsonify({
                "success": True,
                "token": token,
                "user": {
                    "id": id_usuario,
                    "username": username,
                    "nombre": nombre,
                    "rol": "portal",
                    "endpoints_permitidos": json.loads(endpoints) if endpoints else [],
                    "max_requests_dia": max_req
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
            import jwt
            payload = jwt.decode(token, os.getenv('JWT_SECRET_KEY', 'tu-secret-key-cambia-esto'), algorithms=['HS256'])
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
# NUEVAS RUTAS: Gestión de usuarios portal (Admin)
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
                SELECT u.id_usuario, u.username, u.nombre, u.email, u.activo,
                       u.fecha_creacion, up.endpoints_permitidos, up.max_requests_dia,
                       up.ultimo_acceso, COALESCE(up.total_requests, 0) as total_requests
                FROM usuarios u
                JOIN portal_usuarios up ON u.id_usuario = up.id_usuario
                ORDER BY u.fecha_creacion DESC
            """)
            cols = [d[0] for d in cursor.description]
            rows = []
            for r in cursor.fetchall():
                row_dict = dict(zip(cols, r))
                if row_dict.get('endpoints_permitidos'):
                    try:
                        row_dict['endpoints_permitidos'] = json.loads(row_dict['endpoints_permitidos'])
                    except:
                        pass
                if row_dict.get('fecha_creacion'):
                    row_dict['fecha_creacion'] = str(row_dict['fecha_creacion'])
                if row_dict.get('ultimo_acceso'):
                    row_dict['ultimo_acceso'] = str(row_dict['ultimo_acceso'])
                rows.append(row_dict)
        return jsonify({"usuarios": rows})
    except Exception as exc:
        logger.error("listar_usuarios_portal: %s", exc, exc_info=True)
        return jsonify({"error": "Error al listar usuarios"}), 500

@api_publica_bp.route("/api/admin/portal/usuarios", methods=["POST"])
@token_required
def crear_usuario_portal():
    """Crear nuevo usuario para el portal (solo admin)"""
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
            
            # Crear usuario
            password_hash = generate_password_hash(password)
            cursor.execute("""
                INSERT INTO usuarios (username, password_hash, nombre, email, rol, activo)
                VALUES (%s, %s, %s, %s, 'portal', TRUE)
                RETURNING id_usuario
            """, [username, password_hash, nombre, email])
            id_usuario = cursor.fetchone()[0]
            
            # Crear entrada en portal_usuarios
            cursor.execute("""
                INSERT INTO portal_usuarios (id_usuario, endpoints_permitidos, max_requests_dia)
                VALUES (%s, %s, %s)
            """, [id_usuario, json.dumps(endpoints), max_requests])
            
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
        return jsonify({"error": "Error al crear usuario"}), 500

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
            updates = []
            params = []
            
            if "nombre" in data:
                updates.append("nombre = %s")
                params.append(data["nombre"])
            if "email" in data:
                updates.append("email = %s")
                params.append(data["email"])
            if "activo" in data:
                updates.append("activo = %s")
                params.append(data["activo"])
            if "max_requests_dia" in data:
                cursor.execute("UPDATE portal_usuarios SET max_requests_dia = %s WHERE id_usuario = %s", 
                              [data["max_requests_dia"], id_usuario])
            if "endpoints_permitidos" in data:
                cursor.execute("UPDATE portal_usuarios SET endpoints_permitidos = %s WHERE id_usuario = %s",
                              [json.dumps(data["endpoints_permitidos"]), id_usuario])
            if "password" in data and data["password"]:
                password_hash = generate_password_hash(data["password"])
                updates.append("password_hash = %s")
                params.append(password_hash)
            
            if updates:
                params.append(id_usuario)
                cursor.execute(f"UPDATE usuarios SET {', '.join(updates)} WHERE id_usuario = %s", params)
        
        return jsonify({"success": True, "mensaje": "Usuario actualizado"})
    except Exception as exc:
        logger.error("actualizar_usuario_portal: %s", exc, exc_info=True)
        return jsonify({"error": "Error al actualizar"}), 500

@api_publica_bp.route("/api/admin/portal/usuarios/<int:id_usuario>", methods=["DELETE"])
@token_required
def eliminar_usuario_portal(id_usuario):
    """Eliminar usuario portal (solo admin)"""
    es_admin, _ = _solo_admin()
    if not es_admin:
        return jsonify({"error": "Solo administradores"}), 403
    
    try:
        with db_connection() as (conn, cursor):
            # Desactivar en lugar de eliminar
            cursor.execute("UPDATE usuarios SET activo = FALSE WHERE id_usuario = %s", [id_usuario])
        return jsonify({"success": True, "mensaje": "Usuario desactivado"})
    except Exception as exc:
        logger.error("eliminar_usuario_portal: %s", exc, exc_info=True)
        return jsonify({"error": "Error al eliminar"}), 500


# ══════════════════════════════════════════════════════════════
# ENDPOINTS PÚBLICOS (sin auth interna)
# ══════════════════════════════════════════════════════════════

@api_publica_bp.route("/api/portal/solicitar", methods=["POST"])
def solicitar_acceso():
    if not request.is_json:
        return jsonify({"error": "Content-Type debe ser application/json"}), 400

    data             = request.get_json(silent=True) or {}
    nombre           = str(data.get("nombre",            "")).strip()
    carnet           = str(data.get("carnet",            "")).strip()
    tel              = str(data.get("telefono",          "")).strip()
    correo           = str(data.get("correo_estudiante", "")).strip()
    numero_grupo     = str(data.get("numero_grupo",      "")).strip()
    apis_raw         = data.get("apis_solicitadas", [])
    if isinstance(apis_raw, list):
        apis_solicitadas = ", ".join(str(a) for a in apis_raw)
    else:
        apis_solicitadas = str(apis_raw).strip()
    ip = _get_ip()
    ua = _get_ua()

    if not nombre:            return jsonify({"error": "Nombre completo requerido."}), 400
    if not carnet:            return jsonify({"error": "Número de carnet requerido."}), 400
    if not correo:            return jsonify({"error": "Correo estudiantil requerido."}), 400
    if not numero_grupo:      return jsonify({"error": "Número de grupo requerido."}), 400
    if not apis_solicitadas:  return jsonify({"error": "Debes indicar qué API(s) deseas habilitar."}), 400

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
                    (nombre,correo,telefono,empresa,cargo,motivo,ip_solicitud,user_agent,token_verificacion)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                RETURNING id_solicitud
            """, [nombre, correo, tel or None, carnet, numero_grupo, apis_solicitadas, ip, ua, token_ver])
            id_sol = cursor.fetchone()[0]

        if ADMIN_EMAIL:
            aprobar_url  = f"{BACKEND_URL}/api/portal/aprobar-link/{token_ver}"
            rechazar_url = f"{BACKEND_URL}/api/portal/rechazar-link/{token_ver}"
            html = f"""
            <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto">
            <h2 style="color:#2563eb">🔔 Nueva solicitud de acceso a API</h2>
            <table style="width:100%;border-collapse:collapse">
              <tr><td style="padding:8px;font-weight:bold">Nombre:</td><td>{nombre}</td></tr>
              <tr><td style="padding:8px;font-weight:bold">Carnet:</td><td>{carnet}</td></tr>
              <tr><td style="padding:8px;font-weight:bold">Teléfono:</td><td>{tel or 'N/A'}</td></tr>
              <tr><td style="padding:8px;font-weight:bold">Correo estudiantil:</td><td>{correo}</td></tr>
              <tr><td style="padding:8px;font-weight:bold">Número de grupo:</td><td>{numero_grupo}</td></tr>
              <tr><td style="padding:8px;font-weight:bold">APIs solicitadas:</td><td>{apis_solicitadas}</td></tr>
              <tr><td style="padding:8px;font-weight:bold">IP:</td><td>{ip}</td></tr>
            </table>
            <div style="margin-top:24px">
              <a href="{aprobar_url}" style="background:#16a34a;color:white;padding:12px 24px;text-decoration:none;border-radius:6px">✅ Aprobar</a>
              <a href="{rechazar_url}" style="background:#dc2626;color:white;padding:12px 24px;text-decoration:none;border-radius:6px">❌ Rechazar</a>
            </div>
            <p style="color:#6b7280;font-size:12px;margin-top:16px">
              Panel de administración: {FRONTEND_URL}/admin_api.html
            </p>
            </div>"""
            _enviar_correo(ADMIN_EMAIL, f"[CRM API] Nueva solicitud de {nombre} (Carnet: {carnet})", html)

        return jsonify({
            "success":     True,
            "id_solicitud": id_sol,
            "mensaje":     "Solicitud enviada. Te contactaremos a la brevedad."
        }), 201

    except Exception as exc:
        logger.error("solicitar_acceso: %s", exc, exc_info=True)
        return jsonify({"error": "Error al enviar solicitud."}), 500


@api_publica_bp.route("/api/portal/aprobar-link/<token_ver>", methods=["GET"])
def aprobar_via_link(token_ver):
    """Aprobar solicitud desde enlace del correo."""
    return _resolver_via_link(token_ver, "Aprobado")

@api_publica_bp.route("/api/portal/rechazar-link/<token_ver>", methods=["GET"])
def rechazar_via_link(token_ver):
    """Rechazar solicitud desde enlace del correo."""
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
                        (nombre_token,token,id_usuario,puede_leer,puede_escribir,
                         activo,usuario_creacion,id_solicitud)
                    VALUES (%s,%s,%s,TRUE,FALSE,TRUE,'admin_link',%s)
                    RETURNING id_token
                """, [f"Token - {nombre}", nuevo_token, id_admin, id_sol])
                id_token = cursor.fetchone()[0]
                cursor.execute("""
                    UPDATE api_solicitudes SET estado='Aprobado',id_token=%s,
                        aprobado_por='admin_link',fecha_resolucion=NOW()
                    WHERE id_solicitud=%s
                """, [id_token, id_sol])
                if correo:
                    html = f"""
                    <div style="font-family:Arial,sans-serif;max-width:600px">
                    <h2 style="color:#16a34a">✅ Tu acceso a la API ha sido aprobado</h2>
                    <p>Hola <strong>{nombre}</strong>, tu solicitud fue aprobada.</p>
                    <p>Tu API Token:</p>
                    <div style="background:#f1f5f9;padding:16px;border-radius:8px;font-family:monospace;word-break:break-all">
                      {nuevo_token}
                    </div>
                    <p style="color:#dc2626"><strong>Guárdalo bien, no se mostrará de nuevo.</strong></p>
                    <h3>¿Cómo usarlo?</h3>
                    <pre style="background:#1e293b;color:#e2e8f0;padding:16px;border-radius:8px">
curl -H "X-API-Token: {nuevo_token[:20]}..." \\
     {BACKEND_URL}/api/pub/clientes</pre>
                    </div>"""
                    _enviar_correo(correo, "✅ Tu acceso a la API ha sido aprobado", html)
                return jsonify({"mensaje": f"Solicitud aprobada. Token generado para {nombre}."}), 200
            else:
                cursor.execute("""
                    UPDATE api_solicitudes SET estado='Rechazado',
                        aprobado_por='admin_link',fecha_resolucion=NOW()
                    WHERE id_solicitud=%s
                """, [id_sol])
                return jsonify({"mensaje": "Solicitud rechazada."}), 200
    except Exception as exc:
        logger.error("resolver_via_link: %s", exc, exc_info=True)
        return jsonify({"error": "Error procesando enlace."}), 500


# ══════════════════════════════════════════════════════════════
# GESTIÓN ADMIN (requiere auth interna)
# ══════════════════════════════════════════════════════════════

def _solo_admin():
    user = getattr(g, "current_user", {}) or {}
    username = user.get("username", "")

    if not username:
        return False, ""

    if "rol" in user:
        return user["rol"] == "admin", username

    try:
        with db_connection() as (conn, cursor):
            cursor.execute(
                "SELECT rol FROM usuarios WHERE username = %s AND activo = TRUE",
                [username]
            )
            row = cursor.fetchone()
            if row:
                return row[0] == "admin", username
    except Exception as exc:
        logger.error("_solo_admin DB lookup: %s", exc)

    return False, username

@api_publica_bp.route("/api/admin/solicitudes", methods=["GET"])
@token_required
def listar_solicitudes():
    es_admin, _ = _solo_admin()
    if not es_admin: return jsonify({"error": "Solo administradores."}), 403
    estado = request.args.get("estado")
    try:
        with db_connection() as (conn, cursor):
            where  = "WHERE 1=1" + (" AND s.estado=%s" if estado else "")
            params = [estado] if estado else []
            cursor.execute(f"""
                SELECT s.id_solicitud, s.nombre, s.correo, s.telefono,
                       s.empresa  AS carnet,
                       s.cargo    AS numero_grupo,
                       s.motivo   AS apis_solicitadas,
                       s.estado, s.ip_solicitud, s.user_agent,
                       s.fecha_solicitud, s.aprobado_por, s.fecha_resolucion, s.notas_admin,
                       t.nombre_token, t.activo AS token_activo, t.puede_leer, t.puede_escribir,
                       t.total_usos, t.id_token
                FROM api_solicitudes s
                LEFT JOIN api_tokens t ON s.id_solicitud=t.id_solicitud
                {where} ORDER BY s.fecha_solicitud DESC
            """, params)
            cols = [d[0] for d in cursor.description]
            rows = [dict(zip(cols,r)) for r in cursor.fetchall()]
            for r in rows:
                for f in ("fecha_solicitud","fecha_resolucion"):
                    if r.get(f): r[f] = str(r[f])
        return jsonify({"solicitudes": rows, "total": len(rows)})
    except Exception as exc:
        logger.error("listar_solicitudes: %s", exc, exc_info=True)
        return jsonify({"error": "Error."}), 500


@api_publica_bp.route("/api/admin/solicitudes/<int:id_sol>/aprobar", methods=["POST"])
@token_required
def aprobar_solicitud(id_sol):
    es_admin, admin_user = _solo_admin()
    if not es_admin: return jsonify({"error": "Solo administradores."}), 403

    data          = request.get_json(silent=True) or {}
    puede_leer    = bool(data.get("puede_leer", True))
    puede_escribir = bool(data.get("puede_escribir", False))
    expira_en     = data.get("expira_en")
    max_req       = data.get("max_requests_dia", 1000)
    endpoints     = data.get("endpoints_permitidos", [])
    notas         = str(data.get("notas","")).strip()

    try:
        with db_connection() as (conn, cursor):
            cursor.execute("""
                SELECT nombre,correo,telefono,empresa,estado
                FROM api_solicitudes WHERE id_solicitud=%s
            """, [id_sol])
            row = cursor.fetchone()
            if not row: return jsonify({"error": "Solicitud no encontrada."}), 404
            nombre, correo, tel, empresa, estado = row
            if estado != "Pendiente":
                return jsonify({"error": "Solicitud ya procesada."}), 400

            nuevo_token = secrets.token_urlsafe(48)
            cursor.execute("SELECT id_usuario FROM usuarios WHERE username=%s", [admin_user])
            r = cursor.fetchone()
            id_admin = r[0] if r else 1

            cursor.execute("""
                INSERT INTO api_tokens
                    (nombre_token,token,descripcion,id_usuario,endpoints_permitidos,
                     solo_lectura,puede_leer,puede_escribir,activo,expira_en,
                     max_requests_dia,usuario_creacion,id_solicitud)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,TRUE,%s,%s,%s,%s)
                RETURNING id_token
            """, [
                f"Token - {nombre}", nuevo_token,
                f"Acceso para {nombre} ({empresa or correo})",
                id_admin, json.dumps(endpoints),
                not puede_escribir, puede_leer, puede_escribir,
                expira_en, max_req, admin_user, id_sol
            ])
            id_token = cursor.fetchone()[0]

            cursor.execute("""
                UPDATE api_solicitudes SET estado='Aprobado',id_token=%s,
                    aprobado_por=%s,fecha_resolucion=NOW(),notas_admin=%s
                WHERE id_solicitud=%s
            """, [id_token, admin_user, notas or None, id_sol])

        if correo:
            permisos = "Lectura y Escritura" if puede_escribir else "Solo Lectura"
            html = f"""
            <div style="font-family:Arial,sans-serif;max-width:600px">
            <h2 style="color:#16a34a">✅ Acceso a API Aprobado</h2>
            <p>Hola <strong>{nombre}</strong>, tu solicitud fue aprobada.</p>
            <p><strong>Permisos:</strong> {permisos}</p>
            <p><strong>Límite diario:</strong> {max_req} requests</p>
            <p><strong>Tu API Token (guárdalo, no se mostrará de nuevo):</strong></p>
            <div style="background:#f1f5f9;padding:16px;border-radius:8px;font-family:monospace;word-break:break-all;font-size:14px">
              {nuevo_token}
            </div>
            <h3>Uso básico:</h3>
            <pre style="background:#1e293b;color:#e2e8f0;padding:16px;border-radius:8px;font-size:13px">
curl -H "X-API-Token: TU_TOKEN" \\
     {BACKEND_URL}/api/pub/clientes</pre>
            <p style="color:#6b7280">Documentación: {FRONTEND_URL}/portal_api.html</p>
            </div>"""
            _enviar_correo(correo, "✅ Tu acceso a la API ha sido aprobado - CRM", html)

        return jsonify({
            "success": True, "id_token": id_token,
            "token": nuevo_token,
            "mensaje": f"Aprobado. Token generado para {nombre}."
        })
    except Exception as exc:
        logger.error("aprobar_solicitud: %s", exc, exc_info=True)
        return jsonify({"error": "Error al aprobar."}), 500


@api_publica_bp.route("/api/admin/solicitudes/<int:id_sol>/rechazar", methods=["POST"])
@token_required
def rechazar_solicitud(id_sol):
    es_admin, admin_user = _solo_admin()
    if not es_admin: return jsonify({"error": "Solo administradores."}), 403
    data  = request.get_json(silent=True) or {}
    notas = str(data.get("notas","")).strip()
    try:
        with db_connection() as (conn, cursor):
            cursor.execute("SELECT nombre,correo FROM api_solicitudes WHERE id_solicitud=%s",[id_sol])
            row = cursor.fetchone()
            if not row: return jsonify({"error": "No encontrada."}), 404
            nombre, correo = row
            cursor.execute("""
                UPDATE api_solicitudes SET estado='Rechazado',aprobado_por=%s,
                    fecha_resolucion=NOW(),notas_admin=%s
                WHERE id_solicitud=%s AND estado='Pendiente'
            """, [admin_user, notas or None, id_sol])
            if cursor.rowcount == 0:
                return jsonify({"error": "Solicitud ya procesada."}), 400
        if correo:
            html = f"""<div style="font-family:Arial,sans-serif">
            <h2 style="color:#dc2626">Solicitud no aprobada</h2>
            <p>Hola {nombre}, tu solicitud de acceso a la API no fue aprobada.</p>
            {"<p><strong>Motivo:</strong> " + notas + "</p>" if notas else ""}
            <p>Si crees que es un error, contáctanos.</p></div>"""
            _enviar_correo(correo, "Actualización sobre tu solicitud de API - CRM", html)
        return jsonify({"success": True, "mensaje": "Solicitud rechazada."})
    except Exception as exc:
        logger.error("rechazar_solicitud: %s", exc, exc_info=True)
        return jsonify({"error": "Error."}), 500


@api_publica_bp.route("/api/admin/tokens", methods=["GET"])
@token_required
def listar_tokens():
    es_admin, _ = _solo_admin()
    if not es_admin: return jsonify({"error": "Solo administradores."}), 403
    try:
        with db_connection() as (conn, cursor):
            cursor.execute("""
                SELECT t.id_token, t.nombre_token, t.puede_leer, t.puede_escribir,
                       t.activo, t.expira_en, t.total_usos, t.requests_hoy,
                       t.max_requests_dia, t.ultimo_uso, t.fecha_creacion,
                       LEFT(t.token,8)||'...' AS token_preview,
                       s.nombre, s.correo, s.telefono,
                       s.empresa AS carnet,
                       s.cargo   AS numero_grupo,
                       s.motivo  AS apis_solicitadas
                FROM api_tokens t
                LEFT JOIN api_solicitudes s ON t.id_solicitud=s.id_solicitud
                ORDER BY t.fecha_creacion DESC
            """)
            cols = [d[0] for d in cursor.description]
            rows = [dict(zip(cols,r)) for r in cursor.fetchall()]
            for r in rows:
                for f in ("expira_en","ultimo_uso","fecha_creacion"):
                    if r.get(f): r[f] = str(r[f])
        return jsonify({"tokens": rows, "total": len(rows)})
    except Exception as exc:
        logger.error("listar_tokens: %s", exc, exc_info=True)
        return jsonify({"error": "Error."}), 500


@api_publica_bp.route("/api/admin/tokens/<int:id_token>/toggle", methods=["PATCH"])
@token_required
def toggle_token(id_token):
    es_admin, _ = _solo_admin()
    if not es_admin: return jsonify({"error": "Solo administradores."}), 403
    try:
        with db_connection() as (conn, cursor):
            cursor.execute("""
                UPDATE api_tokens SET activo=NOT activo WHERE id_token=%s RETURNING activo
            """, [id_token])
            row = cursor.fetchone()
            if not row: return jsonify({"error": "No encontrado."}), 404
        return jsonify({"success": True, "activo": row[0],
                        "mensaje": "Token " + ("activado" if row[0] else "desactivado")})
    except Exception as exc:
        logger.error("toggle_token: %s", exc, exc_info=True)
        return jsonify({"error": "Error."}), 500


@api_publica_bp.route("/api/admin/logs", methods=["GET"])
@token_required
def listar_logs():
    es_admin, _ = _solo_admin()
    if not es_admin: return jsonify({"error": "Solo administradores."}), 403
    try:
        page     = max(1, int(request.args.get("page", 1)))
        per_page = 50
        offset   = (page - 1) * per_page
        id_tok   = request.args.get("id_token")
        where    = "WHERE 1=1" + (" AND l.id_token=%s" if id_tok else "")
        params   = [int(id_tok)] if id_tok else []
        with db_connection() as (conn, cursor):
            cursor.execute(f"SELECT COUNT(*) FROM api_logs l {where}", params)
            total = cursor.fetchone()[0]
            cursor.execute(f"""
                SELECT l.id_log,l.id_token,t.nombre_token,
                       l.nombre_usuario,l.correo_usuario,l.telefono_usuario,l.empresa_usuario,
                       l.endpoint,l.metodo,l.ip_publica,l.user_agent,
                       l.codigo_respuesta,l.tiempo_respuesta_ms,l.exitoso,l.detalle,l.fecha_uso
                FROM api_logs l
                LEFT JOIN api_tokens t ON l.id_token=t.id_token
                {where} ORDER BY l.fecha_uso DESC LIMIT %s OFFSET %s
            """, params + [per_page, offset])
            cols = [d[0] for d in cursor.description]
            rows = [dict(zip(cols,r)) for r in cursor.fetchall()]
            for r in rows:
                if r.get("fecha_uso"): r["fecha_uso"] = str(r["fecha_uso"])
        return jsonify({"logs": rows, "total": total, "page": page,
                        "total_pages": max(1,(total+per_page-1)//per_page)})
    except Exception as exc:
        logger.error("listar_logs: %s", exc, exc_info=True)
        return jsonify({"error": "Error."}), 500


@api_publica_bp.route("/api/admin/stats", methods=["GET"])
@token_required
def stats_portal():
    es_admin, _ = _solo_admin()
    if not es_admin: return jsonify({"error": "Solo administradores."}), 403
    try:
        with db_connection() as (conn, cursor):
            cursor.execute("SELECT COUNT(*) FROM api_solicitudes")
            total_sol = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM api_solicitudes WHERE estado='Pendiente'")
            pendientes = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM api_tokens WHERE activo=TRUE")
            tokens_activos = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM api_logs WHERE fecha_uso >= NOW()-INTERVAL '24 hours'")
            calls_24h = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM api_ips_bloqueadas WHERE activo=TRUE")
            ips_bloqueadas = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM portal_usuarios")
            usuarios_portal = cursor.fetchone()[0]
            cursor.execute("""
                SELECT endpoint, COUNT(*) as total
                FROM api_logs WHERE fecha_uso >= NOW()-INTERVAL '7 days'
                GROUP BY endpoint ORDER BY total DESC LIMIT 5
            """)
            top_endpoints = [{"endpoint": r[0], "total": r[1]} for r in cursor.fetchall()]
        return jsonify({
            "total_solicitudes":  total_sol,
            "pendientes":         pendientes,
            "tokens_activos":     tokens_activos,
            "llamadas_24h":       calls_24h,
            "ips_bloqueadas":     ips_bloqueadas,
            "usuarios_portal":    usuarios_portal,
            "top_endpoints":      top_endpoints,
        })
    except Exception as exc:
        logger.error("stats_portal: %s", exc, exc_info=True)
        return jsonify({"error": "Error."}), 500


# ══════════════════════════════════════════════════════════════
# ENDPOINTS PÚBLICOS CON TOKEN (datos del CRM)
# ══════════════════════════════════════════════════════════════

@api_publica_bp.route("/api/pub/clientes", methods=["GET"])
@token_publico_required
def pub_clientes():
    try:
        with db_connection() as (conn, cursor):
            cursor.execute("""
                SELECT id_cliente,nombre,correo,telefono,estado
                FROM clientes WHERE estado='Activo' LIMIT 100
            """)
            cols = [d[0] for d in cursor.description]
            rows = [dict(zip(cols,r)) for r in cursor.fetchall()]
        return jsonify({"clientes": rows, "total": len(rows)})
    except Exception as exc:
        return jsonify({"error": "Error."}), 500

@api_publica_bp.route("/api/pub/proveedores", methods=["GET"])
@token_publico_required
def pub_proveedores():
    try:
        with db_connection() as (conn, cursor):
            cursor.execute("""
                SELECT p.id_proveedor,p.nombre_empresa,p.nit,p.telefono,p.correo,
                       p.estado,c.nombre_categoria
                FROM proveedores p
                LEFT JOIN categorias_proveedor c ON p.id_categoria=c.id_categoria
                WHERE p.estado='Activo' LIMIT 100
            """)
            cols = [d[0] for d in cursor.description]
            rows = [dict(zip(cols,r)) for r in cursor.fetchall()]
        return jsonify({"proveedores": rows, "total": len(rows)})
    except Exception as exc:
        return jsonify({"error": "Error."}), 500

@api_publica_bp.route("/api/pub/empleados", methods=["GET"])
@token_publico_required
def pub_empleados():
    try:
        with db_connection() as (conn, cursor):
            cursor.execute("""
                SELECT e.id_empleado,e.nombre,e.cargo,e.correo,e.estado,
                       d.nombre_dependencia
                FROM empleados e
                LEFT JOIN dependencias d ON e.id_dependencia=d.id_dependencia
                WHERE e.estado='Activo' LIMIT 100
            """)
            cols = [d[0] for d in cursor.description]
            rows = [dict(zip(cols,r)) for r in cursor.fetchall()]
        return jsonify({"empleados": rows, "total": len(rows)})
    except Exception as exc:
        return jsonify({"error": "Error."}), 500