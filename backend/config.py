"""
config.py - Configuración del Backend API
IMPORTANTE: Las credenciales sensibles se leen de variables de entorno.
Crea un archivo .env en /backend/ con las variables requeridas.
"""
import os

# Intentar cargar python-dotenv si está disponible
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

DB_CONFIG = {
    "server":   os.getenv("DB_SERVER", "localhost"),
    "database": os.getenv("DB_NAME", "crm_ing_software"),
    "username": os.getenv("DB_USER", "sa"),
    "password": os.getenv("DB_PASSWORD", ""),   # NUNCA hardcodear
    "port":     int(os.getenv("DB_PORT", "1433")),
}

# Genera una clave segura: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY = os.getenv("SECRET_KEY", "CAMBIA_ESTO_EN_PRODUCCION_CON_UNA_CLAVE_SEGURA_32CHARS")

# DEBUG solo en desarrollo — en producción establecer FLASK_DEBUG=false
DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"

# URLs permitidas para CORS (frontend)
_origins_raw = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8080,http://127.0.0.1:8080,http://localhost:8001,http://127.0.0.1:8001,http://localhost:5500,http://127.0.0.1:5500,http://192.168.56.101:3000,http://192.168.56.101:8080,http://192.168.56.101:8001,http://192.168.56.101:5500"
)
CORS_ORIGINS = [o.strip() for o in _origins_raw.split(",") if o.strip()]

# Expiración del JWT (horas)
JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "8"))

# Paginación
DEFAULT_PER_PAGE = 20
MAX_PER_PAGE = 100
