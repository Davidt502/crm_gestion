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

# ============================================================
# CONFIGURACIÓN POSTGRESQL (SUPABASE)
# ============================================================
DB_CONFIG = {
    "host": os.getenv("DB_HOST", os.getenv("DB_SERVER", "localhost")),
    "server": os.getenv("DB_HOST", os.getenv("DB_SERVER", "localhost")),  # Compatibilidad
    "port": int(os.getenv("DB_PORT", "5432")),
    "database": os.getenv("DB_NAME", "postgres"),
    "username": os.getenv("DB_USER", "postgres"),
    "user": os.getenv("DB_USER", "postgres"),  # Compatibilidad
    "password": os.getenv("DB_PASSWORD", ""),
    "sslmode": os.getenv("DB_SSLMODE", "require"),
}

# Opcional: URL directa de conexión (si se prefiere)
DATABASE_URL = os.getenv("DATABASE_URL", f"postgresql://{DB_CONFIG['username']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}?sslmode={DB_CONFIG['sslmode']}")

# ============================================================
# SEGURIDAD
# ============================================================
# Genera una clave segura: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY = os.getenv("SECRET_KEY", "CAMBIA_ESTO_EN_PRODUCCION_CON_UNA_CLAVE_SEGURA_32CHARS")
JWT_SECRET = os.getenv("JWT_SECRET", SECRET_KEY)

# DEBUG solo en desarrollo — en producción establecer FLASK_DEBUG=false
DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"

# Enforcer HTTPS en producción
ENFORCE_HTTPS = os.getenv("ENFORCE_HTTPS", "true").lower() == "true" and not DEBUG

# Versionado de API
API_VERSION = "v1"
API_BASE_PATH = f"/api/{API_VERSION}"

# ============================================================
# CORS - URLs permitidas (frontend)
# ============================================================
_origins_raw = os.getenv(
    "CORS_ORIGINS",
    "https://crm-frontend-reg9.onrender.com,http://localhost:3000,http://127.0.0.1:3000,http://localhost:8080,http://127.0.0.1:8080,http://localhost:8001,http://127.0.0.1:8001,http://localhost:5500,http://127.0.0.1:5500,http://192.168.56.101:3000,http://192.168.56.101:8080,http://192.168.56.101:8001,http://192.168.56.101:5500"
)
CORS_ORIGINS = [o.strip() for o in _origins_raw.split(",") if o.strip()]

# ============================================================
# JWT Y PAGINACIÓN
# ============================================================
JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "8"))
DEFAULT_PER_PAGE = 20
MAX_PER_PAGE = 100

# ============================================================
# TIPO DE BASE DE DATOS (para compatibilidad)
# ============================================================
DB_TYPE = os.getenv("DB_TYPE", "postgresql")  # postgresql o sqlserver

# ============================================================
# FUNCIÓN DE VALIDACIÓN DE CONFIGURACIÓN
# ============================================================
def validate_config():
    """Verifica que la configuración sea válida antes de iniciar."""
    errors = []
    
    if not DB_CONFIG["password"]:
        errors.append("DB_PASSWORD no está configurada en variables de entorno")
    
    if SECRET_KEY == "CAMBIA_ESTO_EN_PRODUCCION_CON_UNA_CLAVE_SEGURA_32CHARS":
        errors.append("SECRET_KEY debe cambiarse por un valor seguro en producción")
    
    if errors:
        import warnings
        for error in errors:
            warnings.warn(f"⚠️ Configuración: {error}")
        return False
    return True

# Validar al importar (solo mostrar advertencias en desarrollo)
if DEBUG:
    validate_config()
