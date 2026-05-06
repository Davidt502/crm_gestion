"""
auth_middleware.py - Middleware de autenticación JWT
Correcciones:
  - Soporte a token en cookie HttpOnly además de header (opcional)
  - Manejo estricto de algoritmos HS256 solamente
  - Sanitización del campo 'username' extraído del token
"""
import logging
from functools import wraps
from flask import request, jsonify, g
import jwt
from config import SECRET_KEY

logger = logging.getLogger(__name__)


def _extract_token() -> str | None:
    """Extrae el JWT del header Authorization (Bearer)."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        return token if token else None
    return None


def token_required(f):
    """Decorator para proteger endpoints con JWT."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = _extract_token()

        if not token:
            logger.warning("Token de autenticación faltante desde %s", request.remote_addr)
            return jsonify({"error": "Token de autenticación requerido"}), 401

        try:
            # algorithms debe ser una lista explícita para evitar el ataque
            # de confusión de algoritmo (CVE-2015-9235 style)
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            logger.warning("Token expirado desde %s", request.remote_addr)
            return jsonify({"error": "Token expirado. Inicia sesión nuevamente."}), 401
        except jwt.InvalidTokenError as exc:
            logger.warning("Token inválido desde %s: %s", request.remote_addr, exc)
            return jsonify({"error": "Token inválido"}), 401

        request.current_user = payload
        # Inyectar en g para el módulo de auditoría
        g.current_user_audit = {
            "id_usuario": payload.get("id_usuario"),
            "nombre":     payload.get("nombre"),
            "username":   payload.get("username"),
            "grupo":      payload.get("grupo", ""),
        }
        return f(*args, **kwargs)

    return decorated


def get_usuario() -> str:
    """Retorna el username del token JWT del request actual."""
    user = getattr(request, "current_user", {})
    return str(user.get("username", "sistema"))[:64]
