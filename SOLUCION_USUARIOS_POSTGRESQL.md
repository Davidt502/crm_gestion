# GUÍA COMPLETA: Corregir la Creación de Usuarios en PostgreSQL

## 🔴 Problema Diagnosticado

Las credenciales de Supabase en `.env` son **incorrectas** o la contraseña fue cambiada.

```
Error: FATAL: password authentication failed for user "postgres"
```

## ✅ Solución Paso a Paso

### Paso 1: Obtener Credenciales Correctas de Supabase

1. Ve a https://app.supabase.com
2. Selecciona tu proyecto CRM
3. Haz clic en **"Settings" → "Database"**
4. Busca la sección **"Connection String"**
5. Selecciona el modo **"URI"**
6. Copia la cadena de conexión que se ve así:

```
postgresql://postgres.[ID].supabase.co:5432/postgres?password=[YOUR_PASSWORD]
```

O en la sección **"Connection Info"** encontrarás:
- **Host**: `aws-1-us-east-1.pooler.supabase.com` (o similar)
- **Port**: `5432`
- **Database**: `postgres`
- **User**: `postgres.[ID_DEL_PROYECTO]`
- **Password**: (la contraseña que estableciste)

### Paso 2: Actualizar el archivo `.env`

Edita `/backend/.env` con las credenciales correctas:

```bash
# ─── Configuración PostgreSQL (Supabase) ───
DB_HOST=aws-1-us-east-1.pooler.supabase.com
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres.cvjyecaehndryqzfkvgp    # ← VERIFICA ESTO
DB_PASSWORD=TU_CONTRASEÑA_CORRECTA        # ← ACTUALIZA ESTO
DB_SSLMODE=require

DATABASE_URL=postgresql://postgres.cvjyecaehndryqzfkvgp:TU_CONTRASEÑA@aws-1-us-east-1.pooler.supabase.com:5432/postgres?sslmode=require
```

### Paso 3: Ejecutar el Script de Configuración

Una vez que las credenciales sean correctas, ejecuta:

```bash
cd /home/david/Descargas/crm_gestion/database

# Opción A: Usando psql directamente
psql postgresql://postgres.cvjyecaehndryqzfkvgp:TU_CONTRASEÑA@aws-1-us-east-1.pooler.supabase.com:5432/postgres?sslmode=require -f postgresql_usuarios_setup.sql

# Opción B: Copiar y pegar en la consola SQL de Supabase
# 1. Ve a https://app.supabase.com → tu proyecto → SQL Editor
# 2. Crea una nueva consulta
# 3. Copia todo el contenido de: database/postgresql_usuarios_setup.sql
# 4. Pégalo en el editor
# 5. Haz clic en "Run"
```

### Paso 4: Verificar que Todo Está Correcto

```bash
cd /home/david/Descargas/crm_gestion/database
python3 verificar_postgresql.py
```

Deberías ver:
```
✓ Conexión PostgreSQL
✓ Tabla 'usuarios'
✓ Funciones PostgreSQL
✓ Usuario administrador
✓ Test de función
```

### Paso 5: Crear Usuarios

Una vez que las funciones estén en la base de datos:

```bash
cd /home/david/Descargas/crm_gestion/database
python3 helper_crear_usuarios.py
```

Selecciona la opción **1** para crear un usuario interactivo.

---

## 🔧 Solución Alternativa: Supabase SQL Editor

Si prefieres hacer todo desde Supabase:

1. **Ve a tu proyecto Supabase**
   - URL: https://app.supabase.com

2. **Abre SQL Editor**
   - Haz clic en **"SQL Editor"** en la barra lateral izquierda
   - Haz clic en **"New Query"**

3. **Copia el Script de Configuración**
   - Abre este archivo: `/database/postgresql_usuarios_setup.sql`
   - Copia TODO el contenido
   - Pégalo en el editor SQL de Supabase

4. **Ejecuta el Script**
   - Haz clic en **"Run"** (esquina superior derecha)
   - Debería ver mensajes de éxito

5. **Verifica las Funciones**
   - En el SQL Editor, escribe:
   ```sql
   SELECT routine_name FROM information_schema.routines 
   WHERE routine_name LIKE 'sp_%usuario%' AND routine_schema = 'public';
   ```
   - Deberías ver 5 funciones listadas

6. **Crea un Usuario Admin**
   ```sql
   -- Primero, genera el hash bcrypt en terminal:
   -- python3 -c "import bcrypt; print(bcrypt.hashpw(b'MiContraseña123', bcrypt.gensalt(rounds=12)).decode())"
   
   INSERT INTO usuarios (nombre, email, username, password_hash, rol, estado, usuario_creacion) 
   VALUES (
       'Administrador',
       'admin@example.com',
       'admin',
       '$2b$12$PEGA_EL_HASH_AQUI',  -- Reemplaza con el hash generado
       'admin',
       'Activo',
       'sistema'
   );
   ```

---

## 📋 Resumen de Archivos Creados

| Archivo | Propósito |
|---------|-----------|
| `database/postgresql_usuarios_setup.sql` | **Script principal** - Crea tabla + 5 funciones |
| `database/postgresql_usuarios_funciones.sql` | Solo las funciones (si la tabla ya existe) |
| `database/helper_crear_usuarios.py` | **Helper interactivo** - Crea usuarios fácilmente |
| `database/verificar_postgresql.py` | **Script de diagnóstico** - Verifica la configuración |
| `database/README_USUARIOS_POSTGRESQL.md` | Documentación de referencia |

---

## 🚀 Verificación Final

Una vez que todo esté configurado, los administradores pueden:

1. **Crear usuarios** en el módulo de usuarios del CRM
2. **Asignar contraseña** desde el módulo
3. **Los usuarios** pueden **iniciar sesión** con esa contraseña

El flujo debería ser:
- Admin crea usuario → Contraseña hasheada con bcrypt → Almacenada en BD → Usuario puede login

---

## ❓ Problemas Comunes

### "password authentication failed"
- Verifica que la contraseña en `.env` sea correcta
- Va a Supabase → Settings → Database → Busca el usuario postgres
- Haz clic en "Reset password" si es necesario

### "No se pueden importar los módulos necesarios"
- Asegúrate de tener `psycopg2` y `bcrypt` instalados:
```bash
pip install psycopg2-binary bcrypt python-dotenv
```

### "La tabla usuarios no existe"
- Ejecuta: `database/postgresql_usuarios_setup.sql`
- O usa el SQL Editor de Supabase

### "Las funciones no existen"
- Ejecuta: `database/postgresql_usuarios_setup.sql`
- Debería crear las 5 funciones automáticamente

---

## 📞 Soporte

Si necesitas ayuda:
1. Ejecuta: `python3 database/verificar_postgresql.py`
2. Copia el output del diagnóstico
3. Verifica todos los pasos de este documento
4. Si aún hay problemas, contacta al equipo de soporte técnico
