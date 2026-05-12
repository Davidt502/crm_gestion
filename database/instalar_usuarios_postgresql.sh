#!/bin/bash
# ============================================================
# instalar_usuarios_postgresql.sh
# Automatiza la instalación de funciones PostgreSQL para usuarios
# ============================================================

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funciones auxiliares
print_titulo() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════${NC}\n"
}

print_ok() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Verificar que estamos en el directorio correcto
if [ ! -f "postgresql_usuarios_setup.sql" ]; then
    print_error "Este script debe ejecutarse desde el directorio /database"
    echo "Usa: cd database && bash instalar_usuarios_postgresql.sh"
    exit 1
fi

# ============================================================
# MENÚ PRINCIPAL
# ============================================================

mostrar_menu() {
    print_titulo "INSTALACIÓN DE USUARIOS PostgreSQL"
    echo "1) Verificar diagnóstico"
    echo "2) Ejecutar script SQL (si tienes credenciales correctas)"
    echo "3) Crear usuario nuevo"
    echo "4) Listar usuarios existentes"
    echo "5) Generar bcrypt hash"
    echo "6) Abrir documentación"
    echo "7) Salir"
    echo ""
}

# ============================================================
# OPCIÓN 1: DIAGNÓSTICO
# ============================================================

verificar_diagnostico() {
    print_titulo "EJECUTANDO DIAGNÓSTICO"
    
    if command -v python3 &> /dev/null; then
        print_ok "Python3 encontrado"
        python3 verificar_postgresql.py
    else
        print_error "Python3 no está instalado"
        exit 1
    fi
}

# ============================================================
# OPCIÓN 2: EJECUTAR SCRIPT SQL
# ============================================================

ejecutar_script_sql() {
    print_titulo "EJECUTAR SCRIPT SQL"
    
    print_info "Este script instalará las funciones PostgreSQL necesarias"
    print_warning "Necesitas credenciales correctas de Supabase"
    echo ""
    
    # Leer credenciales
    read -p "Host (ej: aws-1-us-east-1.pooler.supabase.com): " DB_HOST
    read -p "Puerto [5432]: " DB_PORT
    DB_PORT=${DB_PORT:-5432}
    read -p "Database [postgres]: " DB_NAME
    DB_NAME=${DB_NAME:-postgres}
    read -p "Usuario (ej: postgres.cvjyecaehndryqzfkvgp): " DB_USER
    read -sp "Contraseña: " DB_PASSWORD
    echo ""
    
    # Construir connection string
    CONNECTION_STRING="postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}?sslmode=require"
    
    print_info "Conectando a: ${DB_HOST}:${DB_PORT}/${DB_NAME}"
    
    # Intentar conectar y ejecutar
    if command -v psql &> /dev/null; then
        print_info "Ejecutando script SQL..."
        psql "$CONNECTION_STRING" -f postgresql_usuarios_setup.sql
        if [ $? -eq 0 ]; then
            print_ok "Script SQL ejecutado correctamente"
        else
            print_error "Error al ejecutar script SQL"
            exit 1
        fi
    else
        print_error "psql no está instalado"
        echo ""
        print_info "Opciones:"
        echo "1. Instala PostgreSQL: sudo apt install postgresql-client"
        echo "2. O copia el contenido de postgresql_usuarios_setup.sql"
        echo "3. Y pégalo en https://app.supabase.com → SQL Editor"
        exit 1
    fi
}

# ============================================================
# OPCIÓN 3: CREAR USUARIO
# ============================================================

crear_usuario() {
    print_titulo "CREAR USUARIO NUEVO"
    
    if command -v python3 &> /dev/null; then
        python3 helper_crear_usuarios.py
    else
        print_error "Python3 no está instalado"
        exit 1
    fi
}

# ============================================================
# OPCIÓN 4: LISTAR USUARIOS
# ============================================================

listar_usuarios() {
    print_titulo "LISTAR USUARIOS"
    
    if command -v python3 &> /dev/null; then
        python3 helper_crear_usuarios.py listar
    else
        print_error "Python3 no está instalado"
        exit 1
    fi
}

# ============================================================
# OPCIÓN 5: GENERAR HASH
# ============================================================

generar_hash() {
    print_titulo "GENERAR BCRYPT HASH"
    
    if command -v python3 &> /dev/null; then
        python3 helper_crear_usuarios.py hash
    else
        print_error "Python3 no está instalado"
        exit 1
    fi
}

# ============================================================
# OPCIÓN 6: ABRIR DOCUMENTACIÓN
# ============================================================

abrir_documentacion() {
    print_titulo "DOCUMENTACIÓN"
    
    if [ -f "README_USUARIOS_POSTGRESQL.md" ]; then
        if command -v less &> /dev/null; then
            less README_USUARIOS_POSTGRESQL.md
        else
            cat README_USUARIOS_POSTGRESQL.md
        fi
    else
        print_error "Archivo README_USUARIOS_POSTGRESQL.md no encontrado"
    fi
}

# ============================================================
# LOOP PRINCIPAL
# ============================================================

while true; do
    mostrar_menu
    read -p "Selecciona una opción (1-7): " opcion
    
    case $opcion in
        1)
            verificar_diagnostico
            ;;
        2)
            ejecutar_script_sql
            ;;
        3)
            crear_usuario
            ;;
        4)
            listar_usuarios
            ;;
        5)
            generar_hash
            ;;
        6)
            abrir_documentacion
            ;;
        7)
            print_ok "¡Hasta luego!"
            exit 0
            ;;
        *)
            print_error "Opción inválida"
            ;;
    esac
    
    read -p "Presiona Enter para continuar..."
done
