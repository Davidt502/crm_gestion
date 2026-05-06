"""
auth.py - Autenticación con bcrypt + PostgreSQL
Correcciones:
  - Uso de context manager (no fugas de conexión)
  - Validación de entrada antes de consultar
  - Mensajes de error genéricos para evitar enumeración de usuarios
"""
import bcrypt
import logging
from database import db_connection_dict, to_int, ejecutar_funcion

logger = logging.getLogger(__name__)

# Longitud máxima aceptable para evitar ataques de DoS con passwords enormes
_MAX_FIELD_LEN = 256


def verificar_login(username: str, password: str):
    """
    Verifica credenciales de usuario.
    Retorna (dict_usuario, None) si son correctas, o (None, str_error) si no.
    """
    # Validación básica de entrada con límites estrictos
    if not username or not password:
        return None, "Usuario o contraseña incorrectos."

    username = str(username).strip()[:_MAX_FIELD_LEN]
    password = str(password)
    
    # Evitar intentos de ataque con contraseñas gigantes
    if len(password) > _MAX_FIELD_LEN:
        logger.warning("Intento de login con contraseña muy larga desde: %s", username)
        return None, "Usuario o contraseña incorrectos."
    
    # Validar que username no sea vacío tras sanitizar
    if not username or len(username) < 3:
        return None, "Usuario o contraseña incorrectos."

    try:
        with db_connection_dict() as (conn, cursor):
            cursor.execute(
                """
                SELECT id_usuario, nombre, username, password_hash, rol, estado
                FROM usuarios
                WHERE username = %s
                """,
                (username,)
            )
            row = cursor.fetchone()

            # Mensaje genérico para no revelar si el usuario existe
            if not row:
                return None, "Usuario o contraseña incorrectos."

            id_usuario = row['id_usuario']
            nombre = row['nombre']
            uname = row['username']
            pw_hash = row['password_hash']
            rol = row['rol']
            estado = row['estado']

            if estado != "Activo":
                return None, "Usuario o contraseña incorrectos."

            # Normalizar pw_hash a bytes
            if isinstance(pw_hash, str):
                pw_hash_bytes = pw_hash.encode("utf-8")
            else:
                pw_hash_bytes = pw_hash

            try:
                pw_ok = bcrypt.checkpw(password.encode("utf-8"), pw_hash_bytes)
            except Exception:
                return None, "Error al verificar credenciales."

            if not pw_ok:
                return None, "Usuario o contraseña incorrectos."

            # Actualizar último acceso
            cursor.execute(
                "UPDATE usuarios SET ultimo_acceso = CURRENT_TIMESTAMP WHERE id_usuario = %s",
                (id_usuario,)
            )

            return {
                "id_usuario": id_usuario,
                "nombre": nombre,
                "username": uname,
                "rol": rol,
            }, None

    except Exception as exc:
        logger.error("Error en verificar_login: %s", exc, exc_info=True)
        return None, "Error interno al autenticar."


def verificar_login_sin_update(username: str, password: str):
    """Verifica credenciales sin actualizar último acceso (útil para API pública)."""
    if not username or not password:
        return None, "Usuario o contraseña incorrectos."

    username = username.strip()[:_MAX_FIELD_LEN]

    try:
        with db_connection_dict() as (conn, cursor):
            cursor.execute(
                """
                SELECT id_usuario, nombre, username, password_hash, rol, estado
                FROM usuarios
                WHERE username = %s
                """,
                (username,)
            )
            row = cursor.fetchone()

            if not row:
                return None, "Usuario o contraseña incorrectos."

            if row['estado'] != "Activo":
                return None, "Usuario o contraseña incorrectos."

            pw_hash = row['password_hash']
            if isinstance(pw_hash, str):
                pw_hash_bytes = pw_hash.encode("utf-8")
            else:
                pw_hash_bytes = pw_hash

            if not bcrypt.checkpw(password.encode("utf-8"), pw_hash_bytes):
                return None, "Usuario o contraseña incorrectos."

            return {
                "id_usuario": row['id_usuario'],
                "nombre": row['nombre'],
                "username": row['username'],
                "rol": row['rol'],
            }, None

    except Exception as exc:
        logger.error("Error en verificar_login_sin_update: %s", exc, exc_info=True)
        return None, "Error interno al autenticar."
