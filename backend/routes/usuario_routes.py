"""
usuario_routes.py - Módulo de Gestión de Usuarios
CRM Ing Software v3 - PostgreSQL version

Endpoints:
  GET    /api/usuarios              - Listar usuarios
  POST   /api/usuarios              - Crear usuario
  PUT    /api/usuarios/<id>         - Editar datos (sin contraseña)
  PATCH  /api/usuarios/<id>/password - Cambiar contraseña
  PATCH  /api/usuarios/<id>/desactivar - Desactivar (soft delete)
  PATCH  /api/usuarios/<id>/reactivar  - Reactivar
"""
import logging
import bcrypt
from flask import Blueprint, request, jsonify
from middleware.auth_middleware import token_required, get_usuario
from database import db_connection_dict, to_int, ejecutar_funcion

logger = logging.getLogger(__name__)

usuario_bp = Blueprint("usuarios", __name__, url_prefix="/api/usuarios")

_MAX_FIELD = 256
_MIN_PASSWORD_LEN = 6


def _sanitize(value, max_len=500) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()[:max_len]


def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def _row_to_dict(row: dict) -> dict:
    """Nunca incluye password_hash."""
    return {
        "id_usuario":    row.get('id_usuario'),
        "nombre":        row.get('nombre'),
        "email":         row.get('email'),
        "username":      row.get('username'),
        "rol":           row.get('rol'),
        "estado":        row.get('estado'),
        "ultimo_acceso": row.get('ultimo_acceso').strftime("%Y-%m-%d %H:%M:%S") if row.get('ultimo_acceso') else None,
        "fecha_creacion": row.get('fecha_creacion').strftime("%Y-%m-%d %H:%M:%S") if row.get('fecha_creacion') else None,
    }


def _solo_admin(f):
    """Decorator: solo admins pueden gestionar usuarios."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        user = getattr(request, "current_user", {})
        if user.get("rol") != "admin":
            return jsonify({"error": "Acceso denegado. Se requiere rol de administrador."}), 403
        return f(*args, **kwargs)
    return decorated


# ── GET /api/usuarios ─────────────────────────────────────────
@usuario_bp.route("", methods=["GET"])
@token_required
@_solo_admin
def listar_usuarios():
    try:
        page = max(1, int(request.args.get("page", 1)))
    except (ValueError, TypeError):
        page = 1

    per_page = 20
    offset = (page - 1) * per_page
    nombre = _sanitize(request.args.get("nombre", ""))
    estado = request.args.get("estado") or None

    where = ["1=1"]
    params = []
    if nombre:
        where.append("(nombre ILIKE %s OR username ILIKE %s)")
        params.extend([f"%{nombre}%", f"%{nombre}%"])
    if estado in ("Activo", "Inactivo"):
        where.append("estado = %s")
        params.append(estado)

    where_str = " AND ".join(where)

    try:
        with db_connection_dict() as (conn, cursor):
            cursor.execute(f"SELECT COUNT(*) as total FROM usuarios WHERE {where_str}", params)
            total = cursor.fetchone()['total']

            cursor.execute(f"""
                SELECT id_usuario, nombre, email, username, rol, estado,
                       ultimo_acceso, fecha_creacion
                FROM usuarios
                WHERE {where_str}
                ORDER BY fecha_creacion DESC
                LIMIT %s OFFSET %s
            """, params + [per_page, offset])
            
            rows = cursor.fetchall()

        return jsonify({
            "usuarios":    [_row_to_dict(r) for r in rows],
            "total":       total,
            "page":        page,
            "per_page":    per_page,
            "total_pages": max(1, (total + per_page - 1) // per_page),
        })
    except Exception as exc:
        logger.error("listar_usuarios: %s", exc, exc_info=True)
        return jsonify({"error": "Error al obtener la lista de usuarios."}), 500


# ── GET /api/usuarios/<id> ────────────────────────────────────
@usuario_bp.route("/<int:id>", methods=["GET"])
@token_required
@_solo_admin
def get_usuario_by_id(id):
    try:
        with db_connection_dict() as (conn, cursor):
            cursor.execute("""
                SELECT id_usuario, nombre, email, username, rol, estado,
                       ultimo_acceso, fecha_creacion
                FROM usuarios WHERE id_usuario = %s
            """, (id,))
            row = cursor.fetchone()
        
        if not row:
            return jsonify({"error": "Usuario no encontrado."}), 404
        return jsonify(_row_to_dict(row))
    except Exception as exc:
        logger.error("get_usuario_by_id: %s", exc, exc_info=True)
        return jsonify({"error": "Error al obtener el usuario."}), 500


# ── POST /api/usuarios ────────────────────────────────────────
@usuario_bp.route("", methods=["POST"])
@token_required
@_solo_admin
def crear_usuario():
    if not request.is_json:
        return jsonify({"error": "Content-Type debe ser application/json"}), 400
    data = request.get_json(silent=True) or {}

    nombre = _sanitize(data.get("nombre", ""))
    email = _sanitize(data.get("email", ""), 150)
    username = _sanitize(data.get("username", ""), 80)
    password = data.get("password", "")
    rol = _sanitize(data.get("rol", "usuario"), 30)

    # Validaciones
    errors = []
    if not nombre: errors.append("El nombre es obligatorio.")
    if not username: errors.append("El nombre de usuario es obligatorio.")
    if not password: errors.append("La contraseña es obligatoria.")
    elif len(password) < _MIN_PASSWORD_LEN:
        errors.append(f"La contraseña debe tener al menos {_MIN_PASSWORD_LEN} caracteres.")
    elif len(password) > _MAX_FIELD:
        errors.append("La contraseña es demasiado larga.")
    if rol not in ("admin", "usuario"):
        errors.append("El rol debe ser 'admin' o 'usuario'.")

    if errors:
        return jsonify({"error": errors[0], "errores": errors}), 400

    password_hash = _hash_password(password)

    try:
        row = ejecutar_funcion("sp_crear_usuario", nombre, email or None, username, password_hash, rol, get_usuario())
        
        if row:
            if isinstance(row, dict):
                id_usr = row.get('id_usuario_result')
                mensaje = row.get('mensaje_result')
            else:
                id_usr = row[0] if len(row) > 0 else None
                mensaje = row[1] if len(row) > 1 else "Usuario creado."
            
            if id_usr:
                return jsonify({"id_usuario": id_usr, "mensaje": mensaje}), 201
        
        return jsonify({"error": "Error al crear el usuario."}), 400

    except Exception as exc:
        logger.error("crear_usuario: %s", exc, exc_info=True)
        return jsonify({"error": "Error interno al crear el usuario."}), 500


# ── PUT /api/usuarios/<id> ────────────────────────────────────
@usuario_bp.route("/<int:id>", methods=["PUT"])
@token_required
@_solo_admin
def actualizar_usuario(id):
    if not request.is_json:
        return jsonify({"error": "Content-Type debe ser application/json"}), 400
    data = request.get_json(silent=True) or {}

    nombre = _sanitize(data.get("nombre", ""))
    email = _sanitize(data.get("email", ""), 150)
    rol = _sanitize(data.get("rol", ""), 30) or None

    if not nombre:
        return jsonify({"error": "El nombre es obligatorio."}), 400
    if rol and rol not in ("admin", "usuario"):
        return jsonify({"error": "El rol debe ser 'admin' o 'usuario'."}), 400

    try:
        row = ejecutar_funcion("sp_actualizar_usuario", id, nombre, email or None, rol, get_usuario())
        
        if row:
            if isinstance(row, dict):
                id_usr = row.get('id_usuario_result')
                mensaje = row.get('mensaje_result')
            else:
                id_usr = row[0] if len(row) > 0 else None
                mensaje = row[1] if len(row) > 1 else "Usuario actualizado."
            
            if id_usr:
                return jsonify({"id_usuario": id_usr, "mensaje": mensaje})
        
        return jsonify({"error": "Error al actualizar el usuario."}), 400

    except Exception as exc:
        logger.error("actualizar_usuario: %s", exc, exc_info=True)
        return jsonify({"error": "Error interno al actualizar el usuario."}), 500


# ── PATCH /api/usuarios/<id>/password ─────────────────────────
@usuario_bp.route("/<int:id>/password", methods=["PATCH"])
@token_required
@_solo_admin
def cambiar_password(id):
    if not request.is_json:
        return jsonify({"error": "Content-Type debe ser application/json"}), 400
    data = request.get_json(silent=True) or {}

    password = data.get("password", "")
    if not password:
        return jsonify({"error": "La nueva contraseña es obligatoria."}), 400
    if len(password) < _MIN_PASSWORD_LEN:
        return jsonify({"error": f"La contraseña debe tener al menos {_MIN_PASSWORD_LEN} caracteres."}), 400
    if len(password) > _MAX_FIELD:
        return jsonify({"error": "La contraseña es demasiado larga."}), 400

    password_hash = _hash_password(password)

    try:
        row = ejecutar_funcion("sp_cambiar_password_usuario", id, password_hash, get_usuario())
        
        if row:
            if isinstance(row, dict):
                id_usr = row.get('id_usuario_result')
                mensaje = row.get('mensaje_result')
            else:
                id_usr = row[0] if len(row) > 0 else None
                mensaje = row[1] if len(row) > 1 else "Contraseña actualizada."
            
            if id_usr:
                return jsonify({"mensaje": mensaje})
        
        return jsonify({"error": "Error al cambiar la contraseña."}), 400

    except Exception as exc:
        logger.error("cambiar_password: %s", exc, exc_info=True)
        return jsonify({"error": "Error interno al cambiar la contraseña."}), 500


# ── PATCH /api/usuarios/<id>/desactivar ───────────────────────
@usuario_bp.route("/<int:id>/desactivar", methods=["PATCH"])
@token_required
@_solo_admin
def desactivar_usuario(id):
    try:
        row = ejecutar_funcion("sp_desactivar_usuario", id, get_usuario())
        
        if row:
            if isinstance(row, dict):
                id_usr = row.get('id_usuario_result')
                mensaje = row.get('mensaje_result')
            else:
                id_usr = row[0] if len(row) > 0 else None
                mensaje = row[1] if len(row) > 1 else "Usuario desactivado."
            
            if id_usr:
                return jsonify({"mensaje": mensaje})
        
        return jsonify({"error": "Error al desactivar el usuario."}), 400

    except Exception as exc:
        logger.error("desactivar_usuario: %s", exc, exc_info=True)
        return jsonify({"error": "Error interno al desactivar el usuario."}), 500


# ── PATCH /api/usuarios/<id>/reactivar ────────────────────────
@usuario_bp.route("/<int:id>/reactivar", methods=["PATCH"])
@token_required
@_solo_admin
def reactivar_usuario(id):
    try:
        row = ejecutar_funcion("sp_reactivar_usuario", id, get_usuario())
        
        if row:
            if isinstance(row, dict):
                id_usr = row.get('id_usuario_result')
                mensaje = row.get('mensaje_result')
            else:
                id_usr = row[0] if len(row) > 0 else None
                mensaje = row[1] if len(row) > 1 else "Usuario reactivado."
            
            if id_usr:
                return jsonify({"mensaje": mensaje})
        
        return jsonify({"error": "Error al reactivar el usuario."}), 400

    except Exception as exc:
        logger.error("reactivar_usuario: %s", exc, exc_info=True)
        return jsonify({"error": "Error interno al reactivar el usuario."}), 500
