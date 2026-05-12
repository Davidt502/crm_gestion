#!/usr/bin/env python3
"""
verificar_postgresql.py - Diagnóstico de la configuración PostgreSQL
Verifica que la tabla usuarios existe y que las funciones están configuradas correctamente.
"""

import os
import sys
from pathlib import Path

# Agregar el backend al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

try:
    from database import db_connection_dict
    from dotenv import load_dotenv
except ImportError as e:
    print(f"Error: No se pueden importar los módulos necesarios: {e}")
    sys.exit(1)


def verificar_conexion():
    """Verifica que se puede conectar a PostgreSQL."""
    print("\n1. Verificando conexión a PostgreSQL...")
    try:
        load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'))
        with db_connection_dict() as (conn, cursor):
            cursor.execute("SELECT version()")
            version = cursor.fetchone()
            print(f"   ✓ Conectado a: {version['version'][:60]}...")
            return True
    except Exception as e:
        print(f"   ✗ Error de conexión: {e}")
        return False


def verificar_tabla_usuarios():
    """Verifica que la tabla usuarios existe y tiene la estructura correcta."""
    print("\n2. Verificando tabla 'usuarios'...")
    try:
        with db_connection_dict() as (conn, cursor):
            # Verificar que la tabla existe
            cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name = 'usuarios' AND table_schema = 'public'
                )
            """)
            existe = cursor.fetchone()[0]
            
            if not existe:
                print("   ✗ La tabla 'usuarios' NO existe")
                print("   → Ejecuta: psql -f database/postgresql_usuarios_setup.sql")
                return False
            
            print("   ✓ Tabla 'usuarios' existe")
            
            # Verificar columnas
            cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'usuarios' AND table_schema = 'public'
                ORDER BY ordinal_position
            """)
            columnas = cursor.fetchall()
            
            esperadas = {
                'id_usuario': 'integer',
                'nombre': 'character varying',
                'email': 'character varying',
                'username': 'character varying',
                'password_hash': 'character varying',
                'rol': 'character varying',
                'estado': 'character varying'
            }
            
            encontradas = {col['column_name']: col['data_type'] for col in columnas}
            
            for col, tipo in esperadas.items():
                if col in encontradas:
                    print(f"   ✓ Columna '{col}' existe ({encontradas[col]})")
                else:
                    print(f"   ✗ Columna '{col}' falta")
            
            # Contar registros
            cursor.execute("SELECT COUNT(*) as cnt FROM usuarios")
            count = cursor.fetchone()['cnt']
            print(f"   ℹ Usuarios en la base de datos: {count}")
            
            return True
            
    except Exception as e:
        print(f"   ✗ Error al verificar tabla: {e}")
        return False


def verificar_funciones():
    """Verifica que las funciones PostgreSQL existen."""
    print("\n3. Verificando funciones PostgreSQL...")
    
    funciones_esperadas = [
        'sp_crear_usuario',
        'sp_actualizar_usuario',
        'sp_cambiar_password_usuario',
        'sp_desactivar_usuario',
        'sp_reactivar_usuario'
    ]
    
    try:
        with db_connection_dict() as (conn, cursor):
            for func in funciones_esperadas:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.routines
                        WHERE routine_name = %s AND routine_schema = 'public'
                    )
                """, (func,))
                existe = cursor.fetchone()[0]
                
                if existe:
                    print(f"   ✓ Función '{func}' existe")
                else:
                    print(f"   ✗ Función '{func}' NO existe")
                    print(f"     → Ejecuta: psql -f database/postgresql_usuarios_setup.sql")
        
        return True
            
    except Exception as e:
        print(f"   ✗ Error al verificar funciones: {e}")
        return False


def verificar_usuario_admin():
    """Verifica que existe un usuario administrador."""
    print("\n4. Verificando usuario administrador...")
    try:
        with db_connection_dict() as (conn, cursor):
            cursor.execute("""
                SELECT id_usuario, nombre, username, email, rol
                FROM usuarios
                WHERE rol = 'admin'
                LIMIT 1
            """)
            admin = cursor.fetchone()
            
            if admin:
                print(f"   ✓ Usuario administrador existe")
                print(f"     - ID: {admin['id_usuario']}")
                print(f"     - Username: {admin['username']}")
                print(f"     - Nombre: {admin['nombre']}")
            else:
                print("   ⚠ NO hay usuario administrador")
                print("   → Crea uno con: python3 helper_crear_usuarios.py")
                return False
        
        return True
            
    except Exception as e:
        print(f"   ✗ Error al verificar admin: {e}")
        return False


def test_crear_usuario():
    """Intenta crear un usuario de prueba."""
    print("\n5. Testeando función sp_crear_usuario...")
    try:
        with db_connection_dict() as (conn, cursor):
            # Intenta llamar la función
            cursor.execute("""
                SELECT * FROM sp_crear_usuario(
                    'Usuario Prueba',
                    'prueba@test.com',
                    'test_user_' || (SELECT EXTRACT(EPOCH FROM NOW())::BIGINT),
                    '$2b$12$dummyhashnotused',
                    'usuario',
                    'test'
                )
            """)
            resultado = cursor.fetchone()
            
            if resultado:
                id_usuario = resultado.get('id_usuario_result')
                mensaje = resultado.get('mensaje_result')
                is_error = resultado.get('is_error', False)
                
                if is_error:
                    print(f"   ✗ Función reportó error: {mensaje}")
                    return False
                else:
                    print(f"   ✓ Función funciona correctamente")
                    print(f"     - Usuario creado con ID: {id_usuario}")
                    print(f"     - Mensaje: {mensaje}")
                    
                    # Limpiar: eliminar el usuario de prueba
                    try:
                        cursor.execute("DELETE FROM usuarios WHERE id_usuario = %s", (id_usuario,))
                        print(f"     - Usuario de prueba eliminado")
                    except:
                        pass
                    
                    return True
            else:
                print("   ✗ La función no retornó resultados")
                return False
                
    except Exception as e:
        print(f"   ✗ Error al testear función: {e}")
        return False


def resumen_diagnostico():
    """Ejecuta todos los diagnósticos y muestra resumen."""
    print("="*70)
    print("DIAGNÓSTICO: CONFIGURACIÓN PostgreSQL - CRM Ing Software")
    print("="*70)
    
    resultados = {
        "Conexión PostgreSQL": verificar_conexion(),
        "Tabla 'usuarios'": verificar_tabla_usuarios(),
        "Funciones PostgreSQL": verificar_funciones(),
        "Usuario administrador": verificar_usuario_admin(),
        "Test de función": test_crear_usuario(),
    }
    
    print("\n" + "="*70)
    print("RESUMEN")
    print("="*70)
    
    todos_ok = True
    for test, resultado in resultados.items():
        estado = "✓" if resultado else "✗"
        print(f"{estado} {test}")
        if not resultado:
            todos_ok = False
    
    if todos_ok:
        print("\n✓ Todo está configurado correctamente")
        print("  Los usuarios creados en el módulo de usuarios deberían funcionar")
    else:
        print("\n✗ Hay problemas en la configuración")
        print("  Lee los mensajes arriba para saber qué falta ejecutar")
    
    print("="*70)
    
    return todos_ok


if __name__ == "__main__":
    success = resumen_diagnostico()
    sys.exit(0 if success else 1)
