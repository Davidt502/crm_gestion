"""
auth.py - Autenticación con bcrypt + SQL Server
Correcciones:
  - Uso de context manager (no fugas de conexión)
  - Validación de entrada antes de consultar
  - Mensajes de error genéricos para evitar enumeración de usuarios
  - pw_hash puede venir como bytes o str según driver; se normaliza
"""
import bcrypt
from database import db_connection


# Longitud máxima aceptable para evitar ataques de DoS con passwords enormes
_MAX_FIELD_LEN = 256


def verificar_login(username: str, password: str):
    """
    Verifica credenciales de usuario.
    Retorna (dict_usuario, None) si son correctas, o (None, str_error) si no.
    """
    # Validación básica de entrada
    if not username or not password:
        return None, "Usuario o contraseña incorrectos."

    username = username.strip()[:_MAX_FIELD_LEN]
    if len(password) > _MAX_FIELD_LEN:
        return None, "Usuario o contraseña incorrectos."

    try:
        with db_connection() as (conn, cursor):
            cursor.execute(
                """
                SELECT id_usuario, nombre, username, password_hash, rol, estado
                FROM usuarios
                WHERE username = %s
                """,
                [username],
            )
            row = cursor.fetchone()

            # Mensaje genérico para no revelar si el usuario existe
            if not row:
                return None, "Usuario o contraseña incorrectos."

            id_usuario, nombre, uname, pw_hash, rol, estado = row

            if estado != "Activo":
                # Mensaje genérico para no revelar el motivo real
                return None, "Usuario o contraseña incorrectos."

            # Normalizar pw_hash a bytes (pymssql puede retornar str o bytes)
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
                "UPDATE usuarios SET ultimo_acceso = GETDATE() WHERE id_usuario = %s",
                [id_usuario],
            )

            return {
                "id_usuario": id_usuario,
                "nombre":     nombre,
                "username":   uname,
                "rol":        rol,
            }, None

    except Exception as exc:
        # No exponer detalles internos al cliente
        import logging
        logging.getLogger(__name__).error("Error en verificar_login: %s", exc, exc_info=True)
        return None, "Error interno al autenticar."
