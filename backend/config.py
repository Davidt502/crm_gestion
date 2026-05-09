"""
config.py - Configuración del Backend API
IMPORTANTE: Las credenciales sensibles se leen de variables de entorno.
Crea un archivo .env en /backend/ con las variables requeridas.
"""
import os
import secrets

# Intentar cargar python-dotenv si está disponible
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ============================================================
# CONFIGURACIÓN POSTGRESQL (SUPABASE)
# ============================================================
DB_CONFIG = {
    "host": os.getenv("DB_HOST", os.getenv("DB_SERVER", "localhost")),
    "server": os.getenv("DB_HOST", os.getenv("DB_SERVER", "localhost")),
    "port": int(os.getenv("DB_PORT", "5432")),
    "database": os.getenv("DB_NAME", "postgres"),
    "username": os.getenv("DB_USER", "postgres"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
    "sslmode": os.getenv("DB_SSLMODE", "require"),
}

DATABASE_URL = os.getenv("DATABASE_URL", f"postgresql://{DB_CONFIG['username']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}?sslmode={DB_CONFIG['sslmode']}")

# ============================================================
# SEGURIDAD
# ============================================================
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY or SECRET_KEY == "CAMBIA_ESTO_EN_PRODUCCION_CON_UNA_CLAVE_SEGURA_32CHARS":
    SECRET_KEY = secrets.token_hex(32)
    print(f"⚠️ SECRET_KEY generada automáticamente: {SECRET_KEY[:20]}...")

JWT_SECRET = os.getenv("JWT_SECRET", SECRET_KEY)
JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "8"))

DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"
ENFORCE_HTTPS = os.getenv("ENFORCE_HTTPS", "true").lower() == "true" and not DEBUG

API_VERSION = "v1"
API_BASE_PATH = f"/api/{API_VERSION}"

# ============================================================
# CORS
# ============================================================
_origins_raw = os.getenv(
    "CORS_ORIGINS",
    "https://crm-frontend-reg9.onrender.com,http://localhost:3000,http://127.0.0.1:3000,http://localhost:8080,http://127.0.0.1:8080,http://localhost:8001,http://127.0.0.1:8001,http://localhost:5500,http://127.0.0.1:5500"
)
CORS_ORIGINS = [o.strip() for o in _origins_raw.split(",") if o.strip()]

# ============================================================
# RATE LIMITING
# ============================================================
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
RATE_LIMIT_LOGIN_ATTEMPTS = int(os.getenv("RATE_LIMIT_LOGIN_ATTEMPTS", "5"))
RATE_LIMIT_API_ATTEMPTS = int(os.getenv("RATE_LIMIT_API_ATTEMPTS", "100"))

# ============================================================
# PASSWORD POLICY
# ============================================================
PASSWORD_MIN_LENGTH = int(os.getenv("PASSWORD_MIN_LENGTH", "8"))
PASSWORD_REQUIRE_UPPER = os.getenv("PASSWORD_REQUIRE_UPPER", "true").lower() == "true"
PASSWORD_REQUIRE_LOWER = os.getenv("PASSWORD_REQUIRE_LOWER", "true").lower() == "true"
PASSWORD_REQUIRE_DIGIT = os.getenv("PASSWORD_REQUIRE_DIGIT", "true").lower() == "true"
PASSWORD_REQUIRE_SPECIAL = os.getenv("PASSWORD_REQUIRE_SPECIAL", "true").lower() == "true"
BCRYPT_ROUNDS = int(os.getenv("BCRYPT_ROUNDS", "12"))

# ============================================================
# TIPO DE BASE DE DATOS
# ============================================================
DB_TYPE = os.getenv("DB_TYPE", "postgresql")

# ============================================================
# VALIDACIÓN
# ============================================================
def validate_config():
    errors = []
    if not DB_CONFIG["password"]:
        errors.append("DB_PASSWORD no está configurada")
    if errors:
        import warnings
        for error in errors:
            warnings.warn(f"⚠️ {error}")
        return False
    return True

if DEBUG:
    validate_config()