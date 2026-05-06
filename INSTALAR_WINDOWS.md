# Instalación en Windows — CRM Ing Software v3

## Requisitos previos

| Herramienta | Versión mínima | Descarga |
|---|---|---|
| Python | 3.9+ | https://www.python.org/downloads/ |
| SQL Server | 2017+ (o Express) | https://www.microsoft.com/sql-server/sql-server-downloads |
| SQL Server Management Studio | Cualquiera | https://aka.ms/ssmsfullsetup |
| Git Bash / PowerShell | — | Incluido en Windows |

> **Nota:** SQL Server Express es gratuito y suficiente para este sistema.

---

## Instalación paso a paso

### 1 — Abrir terminal

Abre **PowerShell** o **Git Bash** como administrador en la carpeta del proyecto.

---

### 2 — Crear entorno virtual

```powershell
cd backend
python -m venv venv
venv\Scripts\activate
```

Verás `(venv)` al inicio de la línea — eso indica que el entorno está activo.

---

### 3 — Instalar dependencias Python

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

> **Si falla la instalación de `pymssql`** en Windows, instala primero:
> - [Microsoft Visual C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
> - O instala la versión precompilada: `pip install pymssql --only-binary :all:`

---

### 4 — Configurar la base de datos

**4a.** Abre SQL Server Management Studio y conéctate a tu servidor.

**4b.** Abre el archivo `database/script_completo.sql` y ejecútalo completo.

Esto creará:
- Base de datos `crm_ing_software`
- Todas las tablas, índices y stored procedures
- Usuario administrador: `admin` / `admin123`

---

### 5 — Configurar el archivo `.env`

Copia el archivo de ejemplo:

```powershell
copy .env.example .env
```

Edita `backend/.env` con el Bloc de Notas o VS Code:

```env
DB_SERVER=localhost\SQLEXPRESS    # o solo "localhost" si usas SQL Server estándar
DB_PORT=1433
DB_NAME=crm_ing_software
DB_USER=sa                        # o tu usuario de Windows Auth
DB_PASSWORD=TuContraseñaAqui

SECRET_KEY=cambia-esto-por-una-clave-larga-y-aleatoria
FLASK_DEBUG=false
JWT_EXPIRY_HOURS=8
CORS_ORIGINS=http://localhost:3000
```

> **Autenticación Windows:** Si usas autenticación de Windows en lugar de usuario/contraseña SQL, 
> configura en `backend/database.py` el parámetro `trusted=True` en la conexión pymssql.

---

### 6 — Iniciar el backend

Abre una **primera ventana** de PowerShell:

```powershell
cd backend
venv\Scripts\activate
python app.py
```

Verifica que funciona abriendo: http://localhost:5000/api/health  
Debe responder: `{"status": "ok"}`

---

### 7 — Iniciar el frontend

Abre una **segunda ventana** de PowerShell:

```powershell
cd frontend
python server.py
```

Abre el navegador en: **http://localhost:3000**

---

### 8 — Iniciar sesión

```
Usuario:    admin
Contraseña: admin123
```

> ⚠️ Cambia la contraseña del admin desde **Usuarios → Editar** después del primer acceso.

---

## Solución de problemas comunes en Windows

| Error | Causa | Solución |
|---|---|---|
| `pymssql no encontrado` | Build tools faltantes | Instalar Visual C++ Build Tools |
| `Error de conexión DB` | SQL Server no acepta conexiones TCP | Habilitar TCP/IP en SQL Server Configuration Manager |
| `Puerto 1433 bloqueado` | Firewall de Windows | Agregar regla de entrada para puerto 1433 |
| `Login timeout` | Instancia SQL Server Express | Usar `localhost\SQLEXPRESS` como DB_SERVER |
| `Import error: jwt` | Conflicto con librería `jwt` antigua | `pip uninstall jwt PyJWT && pip install PyJWT==2.8.0` |
| `CORS error` en consola | Frontend en puerto diferente | Agregar el puerto a `CORS_ORIGINS` en `.env` |

---

## Estructura del proyecto

```
crm_v3/
├── backend/
│   ├── app.py              ← Servidor Flask (API REST)
│   ├── auth.py             ← Lógica de login/JWT
│   ├── requirements.txt    ← Dependencias Python
│   ├── .env                ← Configuración (NO subir a Git)
│   ├── routes/
│   │   ├── proveedor_routes.py
│   │   ├── cliente_routes.py
│   │   └── usuario_routes.py   ← NUEVO en v3
│   └── services/
│       └── proveedor_service.py
├── frontend/
│   ├── login.html
│   ├── dashboard.html
│   ├── proveedores.html
│   ├── compras.html
│   ├── usuarios.html           ← NUEVO en v3
│   ├── form_usuario.html       ← NUEVO en v3
│   └── js/
│       ├── compras.js          ← Corregido en v3
│       ├── proveedores.js      ← Corregido en v3
│       ├── sidebar.js          ← Actualizado en v3
│       └── usuarios.js         ← NUEVO en v3
└── database/
    ├── script_completo.sql     ← Script principal (ejecutar primero)
    └── usuarios_modulo.sql     ← SPs de usuarios (incluido en script_completo)
```
