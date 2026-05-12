#!/usr/bin/env python3
"""
helper_crear_usuarios.py - Script para crear usuarios en PostgreSQL
Uso: python3 helper_crear_usuarios.py
"""

import os
import sys
import bcrypt
from pathlib import Path

# Agregar el backend al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

try:
    from database import db_connection_dict
    from dotenv import load_dotenv
except ImportError as e:
    print(f"Error: No se pueden importar los módulos necesarios: {e}")
    print("Asegúrate de ejecutar esto desde la carpeta /database o el /backend")
    sys.exit(1)


def hash_password(password: str) -> str:
    """Genera un bcrypt hash seguro para una contraseña."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')


def crear_usuario_interactivo():
    """Crea un usuario interactivamente."""
    print("\n" + "="*60)
    print("CREAR USUARIO EN PostgreSQL")
    print("="*60 + "\n")
    
    # Obtener datos del usuario
    nombre = input("Nombre completo: ").strip()
    if not nombre:
        print("❌ El nombre no puede estar vacío")
        return False
    
    email = input("Email: ").strip()
    if not email or '@' not in email:
        print("❌ Email inválido")
        return False
    
    username = input("Username: ").strip()
    if not username or len(username) < 3:
        print("❌ Username debe tener al menos 3 caracteres")
        return False
    
    password = input("Contraseña: ").strip()
    if not password or len(password) < 8:
        print("❌ La contraseña debe tener al menos 8 caracteres")
        return False
    
    password_confirm = input("Confirmar contraseña: ").strip()
    if password != password_confirm:
        print("❌ Las contraseñas no coinciden")
        return False
    
    rol = input("Rol (admin/usuario) [usuario]: ").strip().lower() or "usuario"
    if rol not in ("admin", "usuario"):
        print("❌ Rol inválido. Debe ser 'admin' o 'usuario'")
        return False
    
    # Generar hash
    print("\nGenerando hash bcrypt...")
    password_hash = hash_password(password)
    
    # Intentar crear el usuario
    try:
        load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'))
        
        with db_connection_dict() as (conn, cursor):
            # Verificar que no exista el usuario
            cursor.execute("SELECT id_usuario FROM usuarios WHERE username = %s", (username,))
            if cursor.fetchone():
                print(f"❌ El usuario '{username}' ya existe")
                return False
            
            cursor.execute("SELECT id_usuario FROM usuarios WHERE email = %s", (email,))
            if cursor.fetchone():
                print(f"❌ El email '{email}' ya está registrado")
                return False
            
            # Llamar a la función PostgreSQL
            cursor.execute(
                "SELECT * FROM sp_crear_usuario(%s, %s, %s, %s, %s, %s)",
                (nombre, email, username, password_hash, rol, 'admin')
            )
            result = cursor.fetchone()
            
            if result:
                id_usuario = result.get('id_usuario_result')
                mensaje = result.get('mensaje_result')
                is_error = result.get('is_error', False)
                
                if is_error or id_usuario is None:
                    print(f"❌ Error: {mensaje}")
                    return False
                else:
                    print(f"\n✓ Usuario creado correctamente")
                    print(f"  ID: {id_usuario}")
                    print(f"  Username: {username}")
                    print(f"  Email: {email}")
                    print(f"  Rol: {rol}")
                    return True
            else:
                print("❌ No se pudo crear el usuario (respuesta vacía de la base de datos)")
                return False
                
    except Exception as e:
        print(f"❌ Error al crear el usuario: {e}")
        import traceback
        traceback.print_exc()
        return False


def generar_hash():
    """Genera un bcrypt hash para una contraseña manualmente."""
    print("\n" + "="*60)
    print("GENERAR BCRYPT HASH")
    print("="*60 + "\n")
    
    password = input("Contraseña a hashear: ").strip()
    if not password:
        print("❌ La contraseña no puede estar vacía")
        return
    
    hash_result = hash_password(password)
    print(f"\nHash generado:\n{hash_result}\n")
    print("Puedes usar este hash para crear usuarios directamente en la base de datos")


def listar_usuarios():
    """Lista todos los usuarios de la base de datos."""
    print("\n" + "="*60)
    print("LISTAR USUARIOS")
    print("="*60 + "\n")
    
    try:
        load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'))
        
        with db_connection_dict() as (conn, cursor):
            cursor.execute("""
                SELECT id_usuario, nombre, email, username, rol, estado, fecha_creacion
                FROM usuarios
                ORDER BY fecha_creacion DESC
                LIMIT 20
            """)
            usuarios = cursor.fetchall()
            
            if not usuarios:
                print("No hay usuarios en la base de datos")
                return
            
            print(f"{'ID':<4} {'Username':<15} {'Nombre':<25} {'Email':<30} {'Rol':<8} {'Estado':<10}")
            print("-" * 92)
            
            for u in usuarios:
                print(f"{u['id_usuario']:<4} {u['username']:<15} {u['nombre']:<25} {u['email']:<30} {u['rol']:<8} {u['estado']:<10}")
                
    except Exception as e:
        print(f"❌ Error al listar usuarios: {e}")


def menu_principal():
    """Muestra el menú principal."""
    while True:
        print("\n" + "="*60)
        print("HERRAMIENTAS DE USUARIOS - CRM Ing Software")
        print("="*60)
        print("1. Crear usuario nuevo")
        print("2. Generar bcrypt hash")
        print("3. Listar usuarios existentes")
        print("4. Salir")
        print("="*60)
        
        opcion = input("Selecciona una opción (1-4): ").strip()
        
        if opcion == "1":
            crear_usuario_interactivo()
        elif opcion == "2":
            generar_hash()
        elif opcion == "3":
            listar_usuarios()
        elif opcion == "4":
            print("\n¡Hasta luego!")
            break
        else:
            print("❌ Opción inválida")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Modo no-interactivo (si se pasan argumentos)
        if sys.argv[1] == "crear":
            crear_usuario_interactivo()
        elif sys.argv[1] == "hash":
            generar_hash()
        elif sys.argv[1] == "listar":
            listar_usuarios()
        else:
            print("Uso: python3 helper_crear_usuarios.py [crear|hash|listar]")
            print("O simplemente: python3 helper_crear_usuarios.py")
    else:
        # Modo interactivo
        menu_principal()
