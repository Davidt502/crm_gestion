"""
google_auth.py - Autenticación con Google OAuth 2.0
Flujo: el frontend obtiene el id_token de Google → lo envía al backend →
       backend lo verifica con la API de Google → crea/actualiza usuario en BD.
"""
import logging
import requests
from database import db_connection

logger = logging.getLogger(__name__)

GOOGLE_TOKEN_INFO_URL = "https://oauth2.googleapis.com/tokeninfo"


def verificar_google_token(id_token: str) -> tuple:
    """
    Verifica un id_token de Google y retorna la info del usuario.
    Retorna (dict_google_user, None) o (None, str_error).
    """
    if not id_token:
        return None, "Token de Google no proporcionado."

    try:
        resp = requests.get(
            GOOGLE_TOKEN_INFO_URL,
            params={"id_token": id_token},
            timeout=10,
        )
        if resp.status_code != 200:
            return None, "Token de Google inválido o expirado."

        data = resp.json()

        # Validaciones básicas
        if data.get("email_verified") != "true":
            return None, "El email de Google no está verificado."

        return {
            "google_id":   data.get("sub"),
            "email":       data.get("email"),
            "nombre":      data.get("name", data.get("email", "").split("@")[0]),
            "picture":     data.get("picture", ""),
        }, None

    except requests.RequestException as exc:
        logger.error("Error contactando API de Google: %s", exc)
        return None, "Error al verificar con Google. Intenta nuevamente."


def login_o_crear_usuario_google(google_user: dict) -> tuple:
    """
    Busca el usuario en BD por google_id o email.
    Si no existe, lo crea automáticamente con rol='usuario'.
    Retorna (dict_usuario, None) o (None, str_error).
    """
    google_id = google_user["google_id"]
    email     = google_user["email"]
    nombre    = google_user["nombre"]
    picture   = google_user.get("picture", "")

    try:
        with db_connection() as (conn, cursor):
            # 1. Buscar por google_id
            cursor.execute(
                """
                SELECT u.id_usuario, u.nombre, u.username, u.rol, u.estado,
                       COALESCE(g.nombre_grupo, '') AS grupo
                FROM usuarios u
                LEFT JOIN grupos g ON u.id_grupo = g.id_grupo
                WHERE u.google_id = %s
                """,
                [google_id],
            )
            row = cursor.fetchone()

            if not row:
                # 2. Buscar por email (usuario existente que aún no usó Google)
                cursor.execute(
                    """
                    SELECT u.id_usuario, u.nombre, u.username, u.rol, u.estado,
                           COALESCE(g.nombre_grupo, '') AS grupo
                    FROM usuarios u
                    LEFT JOIN grupos g ON u.id_grupo = g.id_grupo
                    WHERE u.email = %s OR u.google_email = %s
                    """,
                    [email, email],
                )
                row = cursor.fetchone()

                if row:
                    # Vincular cuenta existente con Google
                    cursor.execute(
                        """
                        UPDATE usuarios SET
                            google_id      = %s,
                            google_email   = %s,
                            google_picture = %s,
                            auth_provider  = 'google',
                            ultimo_acceso  = GETDATE()
                        WHERE id_usuario = %s
                        """,
                        [google_id, email, picture, row[0]],
                    )

            if row:
                id_usuario, nombre_bd, username, rol, estado, grupo = row
                if estado != "Activo":
                    return None, "Tu cuenta está inactiva. Contacta al administrador."
                # Actualizar último acceso
                cursor.execute(
                    "UPDATE usuarios SET ultimo_acceso = GETDATE() WHERE id_usuario = %s",
                    [id_usuario],
                )
                return {
                    "id_usuario": id_usuario,
                    "nombre":     nombre_bd,
                    "username":   username,
                    "rol":        rol,
                    "grupo":      grupo,
                }, None

            # 3. Crear usuario nuevo con cuenta Google
            # Generar username único a partir del email
            base_username = email.split("@")[0][:60]
            username = base_username
            sufijo = 1
            while True:
                cursor.execute(
                    "SELECT 1 FROM usuarios WHERE username = %s", [username]
                )
                if not cursor.fetchone():
                    break
                username = f"{base_username}{sufijo}"
                sufijo += 1

            cursor.execute(
                """
                INSERT INTO usuarios
                    (nombre, email, username, password_hash, rol, estado,
                     google_id, google_email, google_picture, auth_provider,
                     ultimo_acceso, usuario_creacion)
                VALUES (%s, %s, %s, NULL, 'usuario', 'Activo',
                        %s, %s, %s, 'google',
                        GETDATE(), 'google_oauth')
                """,
                [nombre, email, username, google_id, email, picture],
            )
            cursor.execute("SELECT SCOPE_IDENTITY()")
            new_id = cursor.fetchone()[0]

            return {
                "id_usuario": int(new_id),
                "nombre":     nombre,
                "username":   username,
                "rol":        "usuario",
                "grupo":      "",
            }, None

    except Exception as exc:
        logger.error("Error en login_o_crear_usuario_google: %s", exc, exc_info=True)
        return None, "Error interno al autenticar con Google."
