# ⚠️ Guía de Seguridad y Configuración — CRM Ing Software

## 🚀 Configuración inicial (obligatoria antes de correr)

### 1. Variables de entorno

```bash
cd backend/
cp .env.example .env
# Edita .env con tus credenciales reales
```

Contenido mínimo del `.env`:
```
DB_SERVER=tu-servidor
DB_PORT=1433
DB_NAME=crm_ing_software
DB_USER=tu_usuario
DB_PASSWORD=tu_password_seguro
SECRET_KEY=genera_con_python_-c_"import secrets; print(secrets.token_hex(32))"
FLASK_DEBUG=false
JWT_EXPIRY_HOURS=8
CORS_ORIGINS=http://tu-frontend.com
```

### 2. Instalar dependencias

```bash
cd backend/
pip install -r requirements.txt
```

### 3. Ejecutar

```bash
# Backend
python app.py

# Frontend (solo desarrollo)
cd frontend/
python server.py
```

---

## 🔐 Vulnerabilidades corregidas

| # | Severidad | Vulnerabilidad | Archivo | Corrección |
|---|-----------|----------------|---------|------------|
| 1 | 🔴 CRÍTICO | Credenciales de BD hardcodeadas en código fuente | `config.py` | Variables de entorno |
| 2 | 🔴 CRÍTICO | Secret JWT débil y hardcodeado | `config.py` | Variable de entorno + instrucciones |
| 3 | 🔴 CRÍTICO | Credenciales por defecto visibles en login | `login.html` | Eliminadas |
| 4 | 🟠 ALTO | Sin rate limiting en `/api/auth/login` (fuerza bruta) | `app.py` | 10 intentos/60s por IP |
| 5 | 🟠 ALTO | XSS en sidebar con datos de usuario | `sidebar.js` | `escapeHtml()` + `textContent` |
| 6 | 🟠 ALTO | XSS en tablas de datos (clientes, proveedores, etc.) | `*.js` | `escapeHtml()` en todos los campos |
| 7 | 🟠 ALTO | Sin cabeceras HTTP de seguridad | `app.py`, `server.py` | `X-Frame-Options`, `CSP`, `NOSNIFF`, `HSTS` |
| 8 | 🟠 ALTO | Enumeración de usuarios en login (mensajes diferentes) | `auth.py` | Mensaje único genérico |
| 9 | 🟡 MEDIO | Confusión de algoritmo JWT | `auth_middleware.py` | `algorithms=["HS256"]` explícito |
| 10 | 🟡 MEDIO | `DEBUG=True` expone stack traces en producción | `config.py` | `FLASK_DEBUG=false` por defecto |
| 11 | 🟡 MEDIO | Sin validación `Content-Type` en endpoints POST/PUT | `app.py`, routes | Validación `request.is_json` |
| 12 | 🟡 MEDIO | URL param `parseInt()` sin validación (podía ser NaN) | `form_*.html` | Validación con `Number.isInteger()` |
| 13 | 🟡 MEDIO | `.env` no estaba en `.gitignore` | `.gitignore` | Añadido `*.env`, `!.env.example` |

## 🐛 Bugs lógicos corregidos

| # | Archivo | Bug | Corrección |
|---|---------|-----|------------|
| 1 | `empleados.py` | Doble ejecución de la misma query SQL en `create_dependencia` | Eliminado el `cursor.execute` duplicado |
| 2 | `app.py` | `datetime.utcnow()` deprecado en Python 3.12+ | `datetime.now(tz=timezone.utc)` |
| 3 | Todos los módulos | Fugas de conexión garantizadas si ocurría excepción | `@contextmanager db_connection()` |
| 4 | `compras.py` | Estado "Anulado" no incluido en validación | Añadido a `ESTADOS_PAGO_VALIDOS` |
| 5 | `clientes.js` | `showToast` definida 4 veces (duplicada en cada módulo) | Centralizada en `config.js` |
| 6 | `app.py` | Sin manejo global de errores 404/405/500 | Handlers registrados |

## ⚡ Mejoras de arquitectura

- **`database.py`**: Context manager `db_connection()` — cierre y rollback automáticos
- **`config.js`**: Nueva `apiJSON()` — parsea JSON y lanza errores descriptivos
- **`config.js`**: `escapeHtml()` global para sanitizar datos antes de HTML
- **`sidebar.js`**: Soporte responsive (botón hamburger + overlay para móvil)
- **`requirements.txt`**: Versiones mínimas + `python-dotenv`
- **`server.py`**: Cabeceras de seguridad también en el servidor de desarrollo

## 📋 Checklist para producción

- [ ] `.env` configurado con credenciales reales y `SECRET_KEY` generada de forma segura
- [ ] `FLASK_DEBUG=false` en producción
- [ ] Certificado TLS/SSL instalado (para activar HSTS)
- [ ] `CORS_ORIGINS` con solo los dominios reales del frontend
- [ ] Reemplazar `server.py` por Nginx + Gunicorn en producción
- [ ] Revisar y ajustar el rate limiting según el tráfico esperado
- [ ] Configurar logging a archivo en producción
