#!/bin/bash
# ──────────────────────────────────────────────
#  CRM Ing Software v3 — Arrancar Backend
# ──────────────────────────────────────────────
cd "$(dirname "$0")/backend"

if [ ! -d "venv" ]; then
    echo "❌  Entorno virtual no encontrado."
    echo "    Ejecuta primero: bash instalar.sh"
    exit 1
fi

if [ ! -f ".env" ]; then
    echo "❌  Archivo .env no encontrado."
    echo "    Ejecuta primero: bash instalar.sh"
    exit 1
fi

source venv/bin/activate

echo ""
echo "  ╔══════════════════════════════════════╗"
echo "  ║   CRM Ing Software — Backend v3     ║"
echo "  ╚══════════════════════════════════════╝"
echo ""
echo "  API disponible en: http://localhost:5000"
echo "  Health check:      http://localhost:5000/api/health"
echo "  Detener:           Ctrl + C"
echo ""

python3 app.py
