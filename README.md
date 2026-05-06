# CRM Ing Software - Arquitectura de 3 Capas

## Descripción General

Sistema CRM (Customer Relationship Management) implementado con una **arquitectura de 3 capas** que separa las responsabilidades en:

1. **Capa de Presentación (Frontend)**
2. **Capa de Lógica de Negocio (Backend/API)**
3. **Capa de Datos (Base de Datos)**

---

## Arquitectura de 3 Capas

### Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              ARQUITECTURA DE 3 CAPAS                            │
└─────────────────────────────────────────────────────────────────────────────────┘

     ┌─────────────────────┐                                                      
     │      USUARIO        │                                                      
     │    (Navegador)      │                                                      
     └──────────┬──────────┘                                                      
                │                                                                 
                │ HTTP Request                                                    
                ▼                                                                 
┌───────────────────────────────────────┐                                         
│                                       │                                         
│   CAPA 1: PRESENTACIÓN (FRONTEND)     │                                         
│   ─────────────────────────────────   │                                         
│                                       │                                         
│   • HTML/CSS/JavaScript               │                                         
│   • Puerto: 3000                      │                                         
│   • Servidor: Python HTTP Server      │                                         
│                                       │                                         
│   Archivos:                           │                                         
│   ├── login.html                      │                                         
│   ├── dashboard.html                  │                                         
│   ├── clientes.html                   │                                         
│   ├── css/styles.css                  │                                         
│   └── js/                             │                                         
│       ├── config.js                   │                                         
│       ├── sidebar.js                  │                                         
│       ├── dashboard.js                │                                         
│       └── clientes.js                 │                                         
│                                       │                                         
└───────────────────┬───────────────────┘                                         
                    │                                                             
                    │ HTTP/REST + JSON                                            
                    │ Authorization: Bearer <JWT>                                 
                    ▼                                                             
┌───────────────────────────────────────┐                                         
│                                       │                                         
│   CAPA 2: LÓGICA DE NEGOCIO (API)     │                                         
│   ─────────────────────────────────   │                                         
│                                       │                                         
│   • Flask + Flask-CORS                │                                         
│   • Puerto: 5000                      │                                         
│   • Autenticación: JWT                │                                         
│                                       │                                         
│   Archivos:                           │                                         
│   ├── app.py (endpoints REST)         │                                         
│   ├── config.py (configuración)       │                                         
│   ├── auth.py (autenticación)         │                                         
│   ├── clientes.py                     │                                         
│   ├── proveedores.py                  │                                         
│   ├── empleados.py                    │                                         
│   └── compras.py                      │                                         
│                                       │                                         
└───────────────────┬───────────────────┘                                         
                    │                                                             
                    │ SQL Queries / Stored Procedures                             
                    │ pymssql                                                     
                    ▼                                                             
┌───────────────────────────────────────┐                                         
│                                       │                                         
│   CAPA 3: DATOS (DATABASE)            │                                         
│   ─────────────────────────────────   │                                         
│                                       │                                         
│   • SQL Server                        │                                         
│   • Puerto: 1433                      │                                         
│   • Base de datos: crm_ing_software   │                                         
│                                       │                                         
│   Tablas:                             │                                         
│   ├── usuarios                        │                                         
│   ├── clientes                        │                                         
│   ├── contactos_cliente               │                                         
│   ├── proveedores                     │                                         
│   ├── categorias_proveedor            │                                         
│   ├── empleados                       │                                         
│   ├── dependencias                    │                                         
│   ├── compras_proveedor               │                                         
│   ├── TipoCliente                     │                                         
│   └── TipoContacto                    │                                         
│                                       │                                         
└───────────────────────────────────────┘                                         
```

---

## Descripción de Cada Capa

### Capa 1: Presentación (Frontend)

**Responsabilidad:** Interacción con el usuario, visualización de datos y captura de información.

| Aspecto | Detalle |
|---------|---------|
| **Tecnología** | HTML5, CSS3, JavaScript (Vanilla) |
| **Servidor** | Python HTTP Server |
| **Puerto** | 3000 |
| **Ubicación** | `frontend/` |

**Características:**
- Interfaz de usuario moderna y responsive
- No tiene acceso directo a la base de datos
- Se comunica exclusivamente con el Backend via API REST
- Almacena el token JWT en localStorage para autenticación
- Incluye validaciones del lado del cliente

**Archivos principales:**
```
frontend/
├── index.html          # Redirección inicial
├── login.html          # Página de inicio de sesión
├── dashboard.html      # Panel principal con estadísticas
├── clientes.html       # Gestión de clientes
├── css/
│   └── styles.css      # Estilos globales
├── js/
│   ├── config.js       # Configuración API y funciones de auth
│   ├── sidebar.js      # Menú lateral dinámico
│   ├── dashboard.js    # Lógica del dashboard
│   └── clientes.js     # Lógica de gestión de clientes
└── server.py           # Servidor HTTP simple
```

---

### Capa 2: Lógica de Negocio (Backend/API)

**Responsabilidad:** Procesar solicitudes, aplicar reglas de negocio, validaciones y coordinar el acceso a datos.

| Aspecto | Detalle |
|---------|---------|
| **Tecnología** | Python, Flask, Flask-CORS |
| **Autenticación** | JWT (JSON Web Tokens) |
| **Puerto** | 5000 |
| **Ubicación** | `backend/` |

**Características:**
- API RESTful con endpoints bien definidos
- Autenticación mediante JWT con expiración de 8 horas
- CORS configurado para permitir peticiones del frontend
- Validación de datos y manejo de errores
- Uso de Stored Procedures para operaciones complejas

**Archivos principales:**
```
backend/
├── app.py              # Aplicación Flask con todos los endpoints
├── config.py           # Configuración (DB, CORS, Secret Key)
├── database.py         # Conexión a SQL Server
├── auth.py             # Verificación de credenciales
├── clientes.py         # Módulo de clientes
├── proveedores.py      # Módulo de proveedores
├── empleados.py        # Módulo de empleados
├── compras.py          # Módulo de compras
└── requirements.txt    # Dependencias Python
```

**Endpoints disponibles:**

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/auth/login` | Iniciar sesión |
| GET | `/api/auth/verify` | Verificar token |
| GET | `/api/dashboard/stats` | Estadísticas generales |
| GET | `/api/dashboard/cumpleaneros` | Cumpleañeros del mes |
| GET | `/api/clientes` | Listar clientes |
| GET | `/api/clientes/:id` | Obtener cliente |
| POST | `/api/clientes` | Crear cliente |
| PUT | `/api/clientes/:id` | Actualizar cliente |
| PATCH | `/api/clientes/:id/inactivar` | Inactivar cliente |
| GET | `/api/clientes/tipos-cliente` | Tipos de cliente |
| GET | `/api/clientes/tipos-contacto` | Tipos de contacto |
| GET | `/api/proveedores` | Listar proveedores |
| POST | `/api/proveedores` | Crear proveedor |
| GET | `/api/empleados` | Listar empleados |
| POST | `/api/empleados` | Crear empleado |
| GET | `/api/compras` | Listar compras |
| POST | `/api/compras` | Crear compra |

---

### Capa 3: Datos (Database)

**Responsabilidad:** Almacenamiento persistente, integridad de datos y consultas.

| Aspecto | Detalle |
|---------|---------|
| **Tecnología** | Microsoft SQL Server |
| **Conexión** | pymssql |
| **Puerto** | 1433 |
| **Base de datos** | crm_ing_software |

**Características:**
- Solo el Backend tiene acceso a la base de datos
- Uso de Stored Procedures para operaciones CRUD
- Constraints para integridad referencial
- Índices para optimización de consultas

**Tablas principales:**
```sql
-- Usuarios y Autenticación
usuarios (id_usuario, nombre, username, password_hash, rol, estado)

-- Clientes
clientes (id_cliente, nombre_razon_social, documento_identificacion, tipo, estado, ...)
contactos_cliente (id_contacto, id_cliente, tipo_contacto, descripcion, ...)
TipoCliente (id_tipo_cliente, descripcion)
TipoContacto (id_tipo_contacto, descripcion)

-- Proveedores
proveedores (id_proveedor, nombre_empresa, nit, id_categoria, estado, ...)
categorias_proveedor (id_categoria, nombre_categoria, estado)

-- Empleados
empleados (id_empleado, numero_empleado, nombre_completo, id_dependencia, ...)
dependencias (id_dependencia, nombre_dependencia, estado)

-- Compras
compras_proveedor (id_compra, id_proveedor, fecha_compra, monto_total, estado_pago, ...)
```

---

## Flujo de Datos

### Ejemplo: Inicio de Sesión

```
┌──────────┐    1. Usuario ingresa     ┌──────────┐
│ Usuario  │ ─────credenciales──────► │ Frontend │
└──────────┘                           └────┬─────┘
                                            │
                    2. POST /api/auth/login │
                       {username, password} │
                                            ▼
                                      ┌──────────┐
                                      │ Backend  │
                                      │  (API)   │
                                      └────┬─────┘
                                           │
                    3. SELECT * FROM       │
                       usuarios WHERE ...  │
                                           ▼
                                      ┌──────────┐
                                      │ Database │
                                      └────┬─────┘
                                           │
                    4. Retorna datos       │
                       del usuario         │
                                           ▼
                                      ┌──────────┐
                                      │ Backend  │
                    5. Valida password│  (API)   │
                       Genera JWT     └────┬─────┘
                                           │
                    6. {success, token,    │
                        user}              │
                                           ▼
                                      ┌──────────┐
                    7. Guarda token   │ Frontend │
                       en localStorage└────┬─────┘
                                           │
                    8. Redirige a          │
                       dashboard           │
                                           ▼
                                      ┌──────────┐
                                      │ Usuario  │
                                      └──────────┘
```

### Ejemplo: Consultar Clientes

```
┌──────────┐    1. Navega a            ┌──────────┐
│ Usuario  │ ─────/clientes.html────► │ Frontend │
└──────────┘                           └────┬─────┘
                                            │
                    2. GET /api/clientes    │
                       Header: Bearer JWT   │
                                            ▼
                                      ┌──────────┐
                                      │ Backend  │
                    3. Valida JWT     │  (API)   │
                                      └────┬─────┘
                                           │
                    4. SELECT * FROM       │
                       clientes ...        │
                                           ▼
                                      ┌──────────┐
                                      │ Database │
                                      └────┬─────┘
                                           │
                    5. Retorna lista       │
                       de clientes         │
                                           ▼
                                      ┌──────────┐
                    6. Formatea JSON  │ Backend  │
                                      └────┬─────┘
                                           │
                    7. {clientes: [...],   │
                        total, page}       │
                                           ▼
                                      ┌──────────┐
                    8. Renderiza      │ Frontend │
                       tabla HTML     └────┬─────┘
                                           │
                    9. Muestra datos       │
                                           ▼
                                      ┌──────────┐
                                      │ Usuario  │
                                      └──────────┘
```

---

## Ventajas de la Arquitectura de 3 Capas

| Ventaja | Descripción |
|---------|-------------|
| **Separación de responsabilidades** | Cada capa tiene una función específica y bien definida |
| **Mantenibilidad** | Los cambios en una capa no afectan directamente a las otras |
| **Escalabilidad** | Cada capa puede escalar independientemente según la demanda |
| **Seguridad** | El frontend no tiene acceso directo a la base de datos |
| **Reutilización** | La API puede ser consumida por múltiples clientes (web, móvil, etc.) |
| **Testing** | Cada capa puede ser probada de forma independiente |
| **Despliegue independiente** | Frontend y Backend pueden desplegarse en servidores diferentes |

---

## Requisitos del Sistema

### Software necesario:
- **Python 3.8+**
- **SQL Server** (local o remoto)
- **Navegador web moderno** (Chrome, Firefox, Edge)

### Dependencias Python (Backend):
```
flask>=3.0.0
flask-cors>=4.0.0
pymssql>=2.2.0
bcrypt>=4.1.0
PyJWT>=2.8.0
```

---

## Instalación y Configuración

### Paso 1: Configurar la Base de Datos

1. Instalar SQL Server
2. Crear la base de datos `crm_ing_software`
3. Ejecutar los scripts SQL para crear tablas y datos iniciales

### Paso 2: Configurar el Backend

```bash
cd backend

# Crear entorno virtual (recomendado)
python -m venv venv

# Activar entorno virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

Editar `backend/config.py` con los datos de conexión:

```python
DB_CONFIG = {
    "server":   "localhost",
    "database": "crm_ing_software",
    "username": "sa",
    "password": "TU_PASSWORD",
    "port":     1433,
}
```

### Paso 3: Ejecutar los Servidores

**Terminal 1 - Backend (API):**
```bash
cd backend
python app.py
```
```
============================================================
  CRM Ing Software - API Backend
  Servidor corriendo en: http://localhost:5000
  Endpoints disponibles en: /api/*
============================================================
```

**Terminal 2 - Frontend:**
```bash
cd frontend
python server.py
```
```
============================================================
  CRM Ing Software - Frontend Server
  Servidor corriendo en: http://localhost:3000
  Presiona Ctrl+C para detener
============================================================
```

### Paso 4: Acceder al Sistema

1. Abrir navegador en: `http://localhost:3000`
2. Iniciar sesión con las credenciales configuradas
3. Navegar por los módulos del sistema

---

## Seguridad Implementada

### Autenticación JWT

```
┌─────────────────────────────────────────────────────────────┐
│                    FLUJO DE AUTENTICACIÓN                   │
└─────────────────────────────────────────────────────────────┘

1. Login exitoso → Backend genera JWT con:
   {
     "username": "admin",
     "nombre": "Administrador",
     "rol": "admin",
     "exp": <timestamp + 8 horas>
   }

2. Frontend almacena token en localStorage

3. Cada petición incluye header:
   Authorization: Bearer eyJhbGciOiJIUzI1NiIs...

4. Backend valida:
   - Token no expirado
   - Firma válida
   - Usuario existe

5. Si falla → 401 Unauthorized → Redirige a login
```

### CORS (Cross-Origin Resource Sharing)

```python
# Configurado en backend/config.py
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
```

---

## Estructura Final del Proyecto

```
crm_separado/
│
├── README.md                    # Este archivo
│
├── backend/                     # CAPA 2: API REST
│   ├── app.py                  # Aplicación principal Flask
│   ├── config.py               # Configuración
│   ├── database.py             # Conexión a BD
│   ├── auth.py                 # Autenticación
│   ├── clientes.py             # Módulo clientes
│   ├── proveedores.py          # Módulo proveedores
│   ├── empleados.py            # Módulo empleados
│   ├── compras.py              # Módulo compras
│   └── requirements.txt        # Dependencias
│
└── frontend/                    # CAPA 1: Interfaz de Usuario
    ├── index.html              # Redirección inicial
    ├── login.html              # Inicio de sesión
    ├── dashboard.html          # Panel principal
    ├── clientes.html           # Gestión clientes
    ├── server.py               # Servidor HTTP
    ├── css/
    │   └── styles.css          # Estilos
    └── js/
        ├── config.js           # Config y auth
        ├── sidebar.js          # Menú lateral
        ├── dashboard.js        # Lógica dashboard
        └── clientes.js         # Lógica clientes
```

---

## Autores

- **Curso:** Ingeniería de Software
- **Universidad:** UMG
- **Año:** 2026
