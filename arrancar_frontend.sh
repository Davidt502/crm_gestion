#!/bin/bash
# ──────────────────────────────────────────────
#  CRM Ing Software v3 — Arrancar Frontend
# ──────────────────────────────────────────────
cd "$(dirname "$0")/frontend"

echo ""
echo "  ╔══════════════════════════════════════╗"
echo "  ║   CRM Ing Software — Frontend v3    ║"
echo "  ╚══════════════════════════════════════╝"
echo ""
echo "  Aplicación en: http://localhost:3000"
echo "  Detener:       Ctrl + C"
echo ""

python3 server.py
