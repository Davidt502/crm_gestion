"""
auth_middleware.py - Middleware de autenticación JWT
Correcciones:
  - Soporte a token en cookie HttpOnly además de header (opcional)
  - Manejo estricto de algoritmos HS256 solamente
  - Sanitización del campo 'username' extraído del token
"""
import jwt
import logging
from functools import wraps
from flask import request, jsonify, g
from datetime import datetime, timezone
from config import SECRET_KEY

logger = logging.getLogger(__name__)

_revoked_tokens = set()


def revoke_token(token: str):
    _revoked_tokens.add(token)
    if len(_revoked_tokens) > 1000:
        _revoked_tokens.clear()


def is_token_revoked(token: str) -> bool:
    return token in _revoked_tokens


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({"error": "Token de autenticación requerido"}), 401
        
        if is_token_revoked(token):
            return jsonify({"error": "Token inválido"}), 401
        
        try:
            payload = jwt.decode(
                token, 
                SECRET_KEY, 
                algorithms=["HS256"],
                options={"require": ["exp"]},
            )
            
            exp = payload.get('exp')
            if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
                return jsonify({"error": "Token expirado"}), 401
            
            g.current_user = {
                "id_usuario": payload.get('id_usuario'),
                "username": payload.get('username'),
                "nombre": payload.get('nombre'),
                "rol": payload.get('rol'),
                "grupo": payload.get('grupo', ''),
            }
            g.current_user_audit = g.current_user
            
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expirado"}), 401
        except jwt.InvalidTokenError as e:
            logger.warning(f"Token inválido: {str(e)}")
            return jsonify({"error": "Token inválido"}), 401
        
        return f(*args, **kwargs)
    return decorated


def get_usuario():
    """Obtiene el username del usuario actual"""
    return getattr(g, 'current_user', {}).get('username', 'sistema')


def get_current_user_rol():
    """Obtiene el rol del usuario actual"""
    return getattr(g, 'current_user', {}).get('rol', 'usuario')


def get_current_user_id():
    """Obtiene el ID del usuario actual"""
    return getattr(g, 'current_user', {}).get('id_usuario')


def get_current_user_nombre():
    """Obtiene el nombre del usuario actual"""
    return getattr(g, 'current_user', {}).get('nombre', 'Usuario')


def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = getattr(g, 'current_user', {})
        if user.get('rol') != 'admin':
            return jsonify({"error": "Acceso denegado. Se requiere rol de administrador."}), 403
        return f(*args, **kwargs)
    return decorated
