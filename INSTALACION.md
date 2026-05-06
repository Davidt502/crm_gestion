# Guía de Instalación — CRM Ing Software v3

## Requisitos previos

| Requisito | Versión mínima | Cómo verificar |
|-----------|---------------|----------------|
| Python | 3.9+ | `python3 --version` |
| SQL Server | 2017+ | — |
| Navegador moderno | Chrome, Edge, Firefox | — |
| Sistema operativo | Windows 10/11, Ubuntu 20.04+, macOS 12+ | — |

---

## Instalación en Linux / macOS / WSL2

### Paso 1 — Descomprimir el proyecto

```bash
unzip crm_v3_corregido.zip
cd crm_v3
```

### Paso 2 — Ejecutar el instalador automático

```bash
bash instalar.sh
```

El script instala automáticamente:
- Dependencias del sistema (freetds, unixodbc)
- Entorno virtual Python en `backend/venv`
- Todos los paquetes Python (`Flask`, `PyJWT`, `bcrypt`, `pymssql`, etc.)
- Crea el archivo `backend/.env` con una `SECRET_KEY` generada automáticamente

---

## Instalación en Windows (sin WSL)

### Paso 1 — Requisitos

1. Instala [Python 3.10+](https://python.org/downloads) — marca **"Add to PATH"**
2. Instala los drivers de SQL Server:  
   Descarga [Microsoft ODBC Driver 17/18](https://aka.ms/downloadmsodbcsql)

### Paso 2 — Abrir PowerShell en la carpeta del proyecto

```powershell
cd ruta\al\proyecto\crm_v3\backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Paso 3 — Crear el archivo .env

```powershell
copy .env.example .env
notepad .env
```

---

## Configurar la base de datos

### Paso 1 — Editar `backend/.env`

```env
DB_SERVER=localhost          # IP o nombre del servidor SQL
DB_PORT=1433                 # Puerto (1433 por defecto)
DB_NAME=crm_ing_software     # Nombre de la base de datos
DB_USER=tu_usuario           # Usuario SQL Server
DB_PASSWORD=tu_contraseña    # Contraseña SQL Server
SECRET_KEY=...               # Ya generado automáticamente
FLASK_DEBUG=false
JWT_EXPIRY_HOURS=8
CORS_ORIGINS=http://localhost:3000
```

### Paso 2 — Ejecutar el script SQL

Abre **SQL Server Management Studio** o **Azure Data Studio** y ejecuta:

```
database/script_completo.sql
```

> Este script crea la base de datos, todas las tablas, stored procedures,  
> triggers, funciones e inserta datos iniciales incluyendo el usuario admin.

**Usuario administrador creado:**
```
Usuario:    admin
Contraseña: admin123
```
> ⚠️ Cambia esta contraseña desde el módulo de Usuarios tras el primer login.

---

## Iniciar el sistema

### Terminal 1 — Backend API

**Linux/macOS:**
```bash
bash arrancar_backend.sh
```

**Windows:**
```powershell
cd backend
venv\Scripts\activate
python app.py
```

Verás:
```
✓ Backend iniciando en http://localhost:5000
```

### Terminal 2 — Frontend

**Linux/macOS:**
```bash
bash arrancar_frontend.sh
```

**Windows:**
```powershell
cd frontend
python server.py
```

Verás:
```
✓ Frontend iniciando en http://localhost:3000
```

### Abrir en el navegador

```
http://localhost:3000
```

---

## Estructura del proyecto

```
crm_v3/
├── backend/                  ← API REST (Flask + Python)
│   ├── app.py                ← Punto de entrada, rutas principales
│   ├── auth.py               ← Lógica de autenticación
│   ├── compras.py            ← Módulo de compras
│   ├── empleados.py          ← Módulo de empleados
│   ├── config.py             ← Configuración desde .env
│   ├── database.py           ← Conexión SQL Server
│   ├── routes/
│   │   ├── proveedor_routes.py
│   │   ├── cliente_routes.py
│   │   └── usuario_routes.py ← NUEVO v3
│   ├── services/
│   │   ├── proveedor_service.py
│   │   └── cliente_service.py
│   ├── repositories/
│   │   ├── proveedor_repository.py
│   │   └── cliente_repository.py
│   ├── middleware/
│   │   └── auth_middleware.py
│   ├── requirements.txt
│   ├── .env.example
│   └── .env                  ← Creado por instalar.sh (no subir a git)
│
├── frontend/                 ← Interfaz web (HTML + CSS + JS)
│   ├── login.html
│   ├── dashboard.html
│   ├── proveedores.html      ← Corregido v3
│   ├── compras.html          ← Corregido v3
│   ├── form_compra.html
│   ├── usuarios.html         ← NUEVO v3
│   ├── form_usuario.html     ← NUEVO v3
│   ├── css/styles.css
│   ├── js/
│   │   ├── config.js
│   │   ├── sidebar.js        ← Actualizado v3
│   │   ├── proveedores.js    ← Corregido v3
│   │   ├── compras.js        ← Corregido v3
│   │   └── usuarios.js       ← NUEVO v3
│   └── server.py             ← Servidor estático de desarrollo
│
└── database/
    ├── script_completo.sql   ← Script principal (incluye usuarios v3)
    ├── usuarios_modulo.sql   ← SPs de usuarios (separado)
    └── fix_admin_password.sql
```

---

## Solución de problemas frecuentes

### Error: `pymssql.OperationalError: (20009, ...)`
**Causa:** No se puede conectar al servidor SQL.  
**Solución:**
- Verifica que SQL Server esté iniciado
- Confirma `DB_SERVER`, `DB_PORT`, `DB_USER` y `DB_PASSWORD` en `.env`
- Verifica que el puerto 1433 esté habilitado en el firewall
- En SQL Server Configuration Manager activa `TCP/IP`

### Error: `ModuleNotFoundError: No module named 'flask'`
**Causa:** El entorno virtual no está activado.  
**Solución:**
```bash
source backend/venv/bin/activate   # Linux/macOS
backend\venv\Scripts\activate      # Windows
```

### Error al instalar `pymssql`: `freetds not found`
**Solución Linux:**
```bash
sudo apt-get install freetds-dev freetds-bin unixodbc-dev gcc
pip install pymssql
```

### La página carga pero el login falla con "Credenciales incorrectas"
**Causa:** El hash del admin puede estar corrupto.  
**Solución:** Ejecuta en SQL Server:
```sql
-- database/fix_admin_password.sql
```
Contraseña a recuperar: `admin123`

### El módulo "Usuarios" no aparece en el sidebar
**Causa:** Solo es visible para usuarios con rol `admin`.  
**Solución:** Asegúrate de iniciar sesión con el usuario `admin`.

---

## Credenciales por defecto

| Campo | Valor |
|-------|-------|
| URL sistema | `http://localhost:3000` |
| URL API | `http://localhost:5000` |
| Usuario admin | `admin` |
| Contraseña admin | `admin123` |

> **Importante:** Cambia la contraseña del admin desde **Usuarios → Editar** en el primer uso.
