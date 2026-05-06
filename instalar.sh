#!/bin/bash
# ══════════════════════════════════════════════════════════════════
#  CRM Ing Software v3 — Instalador automático
#  Compatible: Ubuntu 20.04+ · Debian 11+ · macOS 12+ · WSL2
#  Uso: bash instalar.sh
# ══════════════════════════════════════════════════════════════════

set -e

VERDE='\033[0;32m'
AMARILLO='\033[1;33m'
ROJO='\033[0;31m'
CYAN='\033[0;36m'
GRIS='\033[0;37m'
NC='\033[0m'

ok()     { echo -e "${VERDE}  ✓  $1${NC}"; }
warn()   { echo -e "${AMARILLO}  ⚠  $1${NC}"; }
err()    { echo -e "${ROJO}  ✗  $1${NC}"; exit 1; }
info()   { echo -e "${GRIS}     $1${NC}"; }
titulo() { echo -e "\n${CYAN}══  $1${NC}"; }

clear
echo ""
echo "  ╔══════════════════════════════════════════════════╗"
echo "  ║       CRM Ing Software  —  Instalador v3        ║"
echo "  ╚══════════════════════════════════════════════════╝"
echo ""

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

# ──────────────────────────────────────────────────────────────
titulo "PASO 1 — Verificando Python"
# ──────────────────────────────────────────────────────────────

if ! command -v python3 &>/dev/null; then
    err "Python 3 no encontrado.\n  Ubuntu/Debian : sudo apt install python3 python3-pip python3-venv\n  macOS         : brew install python3"
fi

PYVER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$(echo $PYVER | cut -d. -f1)
PY_MINOR=$(echo $PYVER | cut -d. -f2)

if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 9 ]; }; then
    err "Se requiere Python 3.9+. Versión actual: $PYVER"
fi
ok "Python $PYVER"

# ──────────────────────────────────────────────────────────────
titulo "PASO 2 — Instalando dependencias del sistema"
# ──────────────────────────────────────────────────────────────

if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    if command -v brew &>/dev/null; then
        brew install freetds unixodbc 2>/dev/null || warn "Homebrew: dependencias pueden ya estar instaladas"
        ok "Dependencias macOS (freetds, unixodbc)"
    else
        warn "Homebrew no encontrado. Instala manualmente: brew install freetds unixodbc"
    fi
else
    # Linux / WSL
    sudo apt-get update -qq 2>/dev/null || warn "apt-get update falló (continuando)"
    sudo apt-get install -y -qq \
        freetds-dev freetds-bin \
        unixodbc-dev \
        python3-venv python3-pip \
        gcc build-essential 2>/dev/null \
        || warn "Algunas dependencias pueden ya estar instaladas"
    ok "Dependencias Linux instaladas (freetds, unixodbc, gcc)"
fi

# ──────────────────────────────────────────────────────────────
titulo "PASO 3 — Creando entorno virtual Python"
# ──────────────────────────────────────────────────────────────

cd "$ROOT_DIR/backend"

if [ ! -d "venv" ]; then
    python3 -m venv venv
    ok "Entorno virtual creado en backend/venv/"
else
    ok "Entorno virtual ya existe — reutilizando"
fi

source venv/bin/activate

# ──────────────────────────────────────────────────────────────
titulo "PASO 4 — Instalando paquetes Python"
# ──────────────────────────────────────────────────────────────

pip install --upgrade pip setuptools wheel -q
pip install -r requirements.txt -q

ok "Paquetes instalados:"
pip list --format=columns 2>/dev/null \
  | grep -E "Flask|PyJWT|bcrypt|pymssql|dotenv|cors" \
  | while read line; do info "$line"; done

# ──────────────────────────────────────────────────────────────
titulo "PASO 5 — Configurando variables de entorno (.env)"
# ──────────────────────────────────────────────────────────────

if [ ! -f ".env" ]; then
    cp .env.example .env
    # Generar SECRET_KEY aleatoria
    SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    sed -i "s/REEMPLAZA_ESTO_CON_UNA_CLAVE_SECRETA_SEGURA_DE_64_CHARS/$SECRET/" .env
    ok "Archivo backend/.env creado con SECRET_KEY aleatoria"
else
    ok "Archivo backend/.env ya existe — conservando configuración"
fi

cd "$ROOT_DIR"

# ──────────────────────────────────────────────────────────────
titulo "PASO 6 — Asignando permisos de ejecución"
# ──────────────────────────────────────────────────────────────

chmod +x arrancar_backend.sh arrancar_frontend.sh instalar.sh
ok "Scripts ejecutables: arrancar_backend.sh, arrancar_frontend.sh"

deactivate 2>/dev/null || true

# ══════════════════════════════════════════════════════════════
echo ""
echo "  ╔══════════════════════════════════════════════════════════╗"
echo -e "  ║   ${VERDE}✓  Instalación completada correctamente${NC}               ║"
echo "  ╚══════════════════════════════════════════════════════════╝"
echo ""
echo -e "  ${CYAN}PRÓXIMOS PASOS OBLIGATORIOS:${NC}"
echo ""
echo -e "  ${AMARILLO}① CONFIGURAR LA BASE DE DATOS${NC}"
echo "     Edita el archivo de conexión:"
echo "     nano backend/.env"
echo ""
echo "     Configura estas variables con los datos de tu SQL Server:"
echo "     DB_SERVER=localhost        ← IP o nombre del servidor"
echo "     DB_PORT=1433               ← Puerto (1433 por defecto)"
echo "     DB_NAME=crm_ing_software   ← Nombre de la base de datos"
echo "     DB_USER=sa                 ← Usuario SQL Server"
echo "     DB_PASSWORD=TuPassword123  ← Contraseña"
echo ""
echo -e "  ${AMARILLO}② CREAR LA BASE DE DATOS (SQL Server)${NC}"
echo "     Abre SQL Server Management Studio o Azure Data Studio:"
echo "     → Ejecuta: database/script_completo.sql"
echo "     Esto crea tablas, índices, stored procedures y datos iniciales."
echo ""
echo -e "  ${AMARILLO}③ INICIAR EL BACKEND (Terminal 1)${NC}"
echo "     bash arrancar_backend.sh"
echo "     → API disponible en: http://localhost:5000/api/health"
echo ""
echo -e "  ${AMARILLO}④ INICIAR EL FRONTEND (Terminal 2)${NC}"
echo "     bash arrancar_frontend.sh"
echo "     → Aplicación en: http://localhost:3000"
echo ""
echo "  ─────────────────────────────────────────────────────────"
echo -e "  ${VERDE}LOGIN INICIAL:${NC}  usuario: admin   contraseña: admin123"
echo "  ─────────────────────────────────────────────────────────"
echo ""
