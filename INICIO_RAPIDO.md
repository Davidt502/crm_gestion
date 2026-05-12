# ⚡ INICIO RÁPIDO: Corregir Usuarios en 5 Minutos

## 🎯 El Problema
Los administradores crean usuarios, pero estos **no pueden iniciar sesión** con la contraseña asignada.

## ✅ La Solución (en 3 pasos)

### **PASO 1: Obtener Credenciales Correctas de Supabase**

1. Ve a: https://app.supabase.com
2. Selecciona tu proyecto CRM
3. **Settings** → **Database**
4. En "Connection pooler" busca:
   - **Host**: `aws-1-us-east-1.pooler.supabase.com` (copia el tuyo)
   - **Port**: `5432`
   - **Database**: `postgres`
   - **User**: `postgres.XXXXXX` (copia el tuyo)
   - **Password**: Tu contraseña de Supabase

5. Abre `/backend/.env` y actualiza:
```
DB_HOST=tu_host_aqui
DB_USER=postgres.tu_id_aqui
DB_PASSWORD=tu_contraseña_aqui
```

### **PASO 2: Ejecutar el Script SQL**

**Opción A: Desde Terminal (si tienes `psql`)**
```bash
cd database
psql postgresql://postgres.XXXXX:CONTRASEÑA@HOST:5432/postgres -f postgresql_usuarios_setup.sql
```

**Opción B: Desde Supabase Web (más fácil)**
1. Ve a: https://app.supabase.com → tu proyecto
2. Abre **SQL Editor** en la barra lateral
3. Haz clic en **New Query**
4. Abre: `/database/postgresql_usuarios_setup.sql`
5. **Copia TODO** el contenido
6. **Pega** en el editor
7. Haz clic en **Run** ▶

### **PASO 3: Verificar que Funcionó**

```bash
cd database
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

---

## 🎮 Para Crear Usuarios Después

```bash
cd database
python3 helper_crear_usuarios.py
```

O usa el menú interactivo:
```bash
bash instalar_usuarios_postgresql.sh
```

---

## 📋 Checklist

- [ ] Obtuve credenciales de Supabase
- [ ] Actualicé `/backend/.env`
- [ ] Ejecuté `postgresql_usuarios_setup.sql`
- [ ] Verifiqué con `verificar_postgresql.py`
- [ ] Creé un usuario de prueba
- [ ] ✅ **Listo para usar**

---

## 🚨 Si No Funciona

### "password authentication failed"
→ La contraseña en `.env` es incorrecta

**Solución:**
1. Ve a Supabase → Settings → Database → Reset Password
2. Actualiza `.env` con la nueva contraseña

### "La tabla usuarios no existe"
→ No ejecutaste el script SQL

**Solución:**
1. Sigue el PASO 2 de arriba

### "Las funciones no existen"
→ El script SQL no se ejecutó completamente

**Solución:**
1. Abre el SQL Editor de Supabase
2. Ejecuta el script de nuevo

---

## 💡 Alternativa: Menú Interactivo (Recomendado)

```bash
cd /home/david/Descargas/crm_gestion/database
bash instalar_usuarios_postgresql.sh
```

Esto te abre un menú donde puedes:
- Verificar diagnóstico
- Crear usuarios nuevos
- Listar usuarios existentes
- Generar contraseñas

---

## ✨ ¿Qué Cambia Para el Usuario Final?

**ANTES:**
```
Admin crea usuario → Sistema falla silenciosamente → Usuario NO puede ingresar ❌
```

**DESPUÉS:**
```
Admin crea usuario → Contraseña guardada con bcrypt → Usuario PUEDE ingresar ✅
```

---

## 📚 Documentación Completa

- `SOLUCION_USUARIOS_POSTGRESQL.md` - Guía detallada paso a paso
- `README_USUARIOS_POSTGRESQL.md` - Referencia técnica
- `RESUMEN_SOLUCION.md` - Vista general de cambios

---

## 🆘 Ayuda

Si necesitas ayuda:
1. Lee `SOLUCION_USUARIOS_POSTGRESQL.md`
2. Ejecuta `python3 verificar_postgresql.py` para diagnóstico
3. Revisa la sección "Problemas Comunes" en `SOLUCION_USUARIOS_POSTGRESQL.md`
