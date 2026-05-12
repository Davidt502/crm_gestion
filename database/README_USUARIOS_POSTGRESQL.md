# Corrección: Crear Usuarios en PostgreSQL

## Problema
Los administradores crean usuarios mediante el módulo de usuarios, pero esos usuarios no pueden ingresar con las contraseñas asignadas.

## Causa
El backend está configurado para usar PostgreSQL (Supabase), pero los scripts SQL están en SQL Server (T-SQL). Las funciones PostgreSQL `sp_crear_usuario`, `sp_actualizar_usuario`, y `sp_cambiar_password_usuario` no existían en la base de datos.

## Solución

### Paso 1: Ejecutar el Script de Configuración

Para ejecutar el script PostgreSQL que crea la tabla `usuarios` y las funciones necesarias:

#### Opción A: Via CLI psql (recomendado)

```bash
# Conectarse a la base de datos PostgreSQL
psql postgresql://usuario:contraseña@host:5432/crm_ing_software -f database/postgresql_usuarios_setup.sql

# O si usas Supabase:
psql "postgresql://postgres.[ID].supabase.co:5432/postgres" -f database/postgresql_usuarios_setup.sql
```

#### Opción B: Via pgAdmin o herramienta SQL
1. Abre pgAdmin o tu herramienta SQL preferida
2. Conectate a tu base de datos PostgreSQL
3. Abre el archivo `database/postgresql_usuarios_setup.sql`
4. Ejecuta todo el script

### Paso 2: Verificar que las Funciones fueron Creadas

```sql
-- Listar funciones creadas
SELECT routine_name 
FROM information_schema.routines 
WHERE routine_name LIKE 'sp_%usuario%' 
  AND routine_schema = 'public';
```

Deberías ver:
- `sp_crear_usuario`
- `sp_actualizar_usuario`
- `sp_cambiar_password_usuario`
- `sp_desactivar_usuario`
- `sp_reactivar_usuario`

### Paso 3: Crear Usuario Admin Inicial (si no existe)

```bash
# Conectarse a PostgreSQL y ejecutar:
psql postgresql://usuario:contraseña@host:5432/crm_ing_software
```

Luego en el prompt SQL:

```sql
-- Insertar un usuario admin (requiere bcrypt hash de contraseña)
-- Primero, genera el hash en Python:
-- python3 -c "import bcrypt; print(bcrypt.hashpw(b'TuContraseña123', bcrypt.gensalt(rounds=12)).decode())"

INSERT INTO usuarios (nombre, email, username, password_hash, rol, estado, usuario_creacion) 
VALUES (
    'Administrador',
    'admin@example.com',
    'admin',
    '$2b$12$...(tu_hash_bcrypt_aqui)...', -- Reemplaza con el hash generado
    'admin',
    'Activo',
    'sistema'
);
```

### Paso 4: Probar el Login

```bash
# Llamar al endpoint de login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"TuContraseña123"}'
```

## Archivos Incluidos

- `postgresql_usuarios_setup.sql` - Script completo que crea tabla y funciones
- `postgresql_usuarios_funciones.sql` - Solo las funciones (si la tabla ya existe)
- `README_USUARIOS_POSTGRESQL.md` - Este archivo

## Notas Importantes

1. **Bcrypt Hashing**: Las contraseñas se guardan como bcrypt hashes (con rounds=12)
2. **Backend**: El backend está configurado en `/backend/database.py` para usar PostgreSQL
3. **Validaciones**: Las funciones incluyen validaciones en la base de datos (nombres únicos, campos obligatorios, etc.)

## Si Aún Tienes Problemas

1. Verifica que el backend pueda conectarse a PostgreSQL:
   ```bash
   cd backend
   python3 -c "from database import db_connection_dict; conn, cursor = db_connection_dict().__enter__(); print('✓ Conexión exitosa')"
   ```

2. Verifica que la tabla `usuarios` existe:
   ```sql
   \dt usuarios
   ```

3. Verifica que las funciones existen y son accesibles:
   ```sql
   SELECT 1 FROM sp_crear_usuario('test', 'test@test.com', 'testuser', 'hash', 'usuario');
   ```
