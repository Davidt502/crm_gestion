-- ============================================================
-- PostgreSQL: Funciones para Gestión de Usuarios
-- Convierte los SPs de SQL Server a funciones PostgreSQL
-- ============================================================

-- ─────────────────────────────────────────────────────────────
-- Función: sp_crear_usuario
-- Crea un nuevo usuario en el sistema
-- Retorna: id_usuario_result, mensaje_result, is_error
-- ─────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION sp_crear_usuario(
    p_nombre VARCHAR(150),
    p_email VARCHAR(150),
    p_username VARCHAR(80),
    p_password_hash VARCHAR(255),
    p_rol VARCHAR(30) DEFAULT 'usuario',
    p_usuario VARCHAR(80) DEFAULT 'sistema'
)
RETURNS TABLE (
    id_usuario_result INT,
    mensaje_result TEXT,
    is_error BOOLEAN
) AS $$
DECLARE
    v_new_id INT;
BEGIN
    -- Validaciones
    IF TRIM(COALESCE(p_nombre, '')) = '' THEN
        RETURN QUERY SELECT NULL::INT, 'El nombre es obligatorio.'::TEXT, TRUE;
        RETURN;
    END IF;

    IF TRIM(COALESCE(p_username, '')) = '' THEN
        RETURN QUERY SELECT NULL::INT, 'El nombre de usuario es obligatorio.'::TEXT, TRUE;
        RETURN;
    END IF;

    IF TRIM(COALESCE(p_password_hash, '')) = '' THEN
        RETURN QUERY SELECT NULL::INT, 'La contraseña es obligatoria.'::TEXT, TRUE;
        RETURN;
    END IF;

    IF p_rol NOT IN ('admin', 'usuario') THEN
        RETURN QUERY SELECT NULL::INT, 'El rol debe ser admin o usuario.'::TEXT, TRUE;
        RETURN;
    END IF;

    -- Verificar username duplicado
    IF EXISTS (SELECT 1 FROM usuarios WHERE username = TRIM(p_username)) THEN
        RETURN QUERY SELECT NULL::INT, 'Ya existe un usuario con ese nombre de usuario.'::TEXT, TRUE;
        RETURN;
    END IF;

    -- Verificar email duplicado (si se proporciona)
    IF p_email IS NOT NULL AND TRIM(p_email) != '' THEN
        IF EXISTS (SELECT 1 FROM usuarios WHERE email = TRIM(p_email)) THEN
            RETURN QUERY SELECT NULL::INT, 'Ya existe un usuario con ese correo electrónico.'::TEXT, TRUE;
            RETURN;
        END IF;
    END IF;

    -- Insertar nuevo usuario
    INSERT INTO usuarios (
        nombre,
        email,
        username,
        password_hash,
        rol,
        estado,
        usuario_creacion,
        fecha_creacion
    ) VALUES (
        TRIM(p_nombre),
        NULLIF(TRIM(COALESCE(p_email, '')), ''),
        TRIM(p_username),
        p_password_hash,
        p_rol,
        'Activo',
        p_usuario,
        CURRENT_TIMESTAMP
    ) RETURNING id_usuario INTO v_new_id;

    RETURN QUERY SELECT v_new_id, 'Usuario creado correctamente.'::TEXT, FALSE;

EXCEPTION WHEN OTHERS THEN
    RETURN QUERY SELECT NULL::INT, 'Error al crear el usuario: ' || SQLERRM, TRUE;
END;
$$ LANGUAGE plpgsql;


-- ─────────────────────────────────────────────────────────────
-- Función: sp_actualizar_usuario
-- Actualiza los datos de un usuario (sin cambiar contraseña)
-- ─────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION sp_actualizar_usuario(
    p_id_usuario INT,
    p_nombre VARCHAR(150),
    p_email VARCHAR(150) DEFAULT NULL,
    p_rol VARCHAR(30) DEFAULT NULL,
    p_usuario VARCHAR(80) DEFAULT 'sistema'
)
RETURNS TABLE (
    id_usuario_result INT,
    mensaje_result TEXT,
    is_error BOOLEAN
) AS $$
BEGIN
    -- Verificar que el usuario existe
    IF NOT EXISTS (SELECT 1 FROM usuarios WHERE id_usuario = p_id_usuario) THEN
        RETURN QUERY SELECT NULL::INT, 'El usuario no existe.'::TEXT, TRUE;
        RETURN;
    END IF;

    -- Validaciones
    IF TRIM(COALESCE(p_nombre, '')) = '' THEN
        RETURN QUERY SELECT NULL::INT, 'El nombre es obligatorio.'::TEXT, TRUE;
        RETURN;
    END IF;

    IF p_rol IS NOT NULL AND p_rol NOT IN ('admin', 'usuario') THEN
        RETURN QUERY SELECT NULL::INT, 'El rol debe ser admin o usuario.'::TEXT, TRUE;
        RETURN;
    END IF;

    -- Verificar email duplicado (si se proporciona)
    IF p_email IS NOT NULL AND TRIM(p_email) != '' THEN
        IF EXISTS (SELECT 1 FROM usuarios WHERE email = TRIM(p_email) AND id_usuario != p_id_usuario) THEN
            RETURN QUERY SELECT NULL::INT, 'Ya existe un usuario con ese correo electrónico.'::TEXT, TRUE;
            RETURN;
        END IF;
    END IF;

    -- Actualizar usuario
    UPDATE usuarios SET
        nombre = TRIM(p_nombre),
        email = NULLIF(TRIM(COALESCE(p_email, '')), ''),
        rol = COALESCE(p_rol, rol),
        fecha_modificacion = CURRENT_TIMESTAMP,
        usuario_modificacion = p_usuario
    WHERE id_usuario = p_id_usuario;

    RETURN QUERY SELECT p_id_usuario, 'Usuario actualizado correctamente.'::TEXT, FALSE;

EXCEPTION WHEN OTHERS THEN
    RETURN QUERY SELECT NULL::INT, 'Error al actualizar el usuario: ' || SQLERRM, TRUE;
END;
$$ LANGUAGE plpgsql;


-- ─────────────────────────────────────────────────────────────
-- Función: sp_cambiar_password_usuario
-- Cambia la contraseña de un usuario
-- ─────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION sp_cambiar_password_usuario(
    p_id_usuario INT,
    p_password_hash VARCHAR(255),
    p_usuario VARCHAR(80) DEFAULT 'sistema'
)
RETURNS TABLE (
    id_usuario_result INT,
    mensaje_result TEXT,
    is_error BOOLEAN
) AS $$
BEGIN
    -- Verificar que el usuario existe
    IF NOT EXISTS (SELECT 1 FROM usuarios WHERE id_usuario = p_id_usuario) THEN
        RETURN QUERY SELECT NULL::INT, 'El usuario no existe.'::TEXT, TRUE;
        RETURN;
    END IF;

    -- Validación
    IF TRIM(COALESCE(p_password_hash, '')) = '' THEN
        RETURN QUERY SELECT NULL::INT, 'La nueva contraseña es obligatoria.'::TEXT, TRUE;
        RETURN;
    END IF;

    -- Actualizar contraseña
    UPDATE usuarios SET
        password_hash = p_password_hash,
        fecha_modificacion = CURRENT_TIMESTAMP,
        usuario_modificacion = p_usuario
    WHERE id_usuario = p_id_usuario;

    RETURN QUERY SELECT p_id_usuario, 'Contraseña actualizada correctamente.'::TEXT, FALSE;

EXCEPTION WHEN OTHERS THEN
    RETURN QUERY SELECT NULL::INT, 'Error al cambiar la contraseña: ' || SQLERRM, TRUE;
END;
$$ LANGUAGE plpgsql;


-- ─────────────────────────────────────────────────────────────
-- Función: sp_desactivar_usuario
-- Desactiva un usuario (soft delete)
-- ─────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION sp_desactivar_usuario(
    p_id_usuario INT,
    p_usuario VARCHAR(80) DEFAULT 'sistema'
)
RETURNS TABLE (
    id_usuario_result INT,
    mensaje_result TEXT,
    is_error BOOLEAN
) AS $$
BEGIN
    -- Verificar que el usuario existe
    IF NOT EXISTS (SELECT 1 FROM usuarios WHERE id_usuario = p_id_usuario) THEN
        RETURN QUERY SELECT NULL::INT, 'El usuario no existe.'::TEXT, TRUE;
        RETURN;
    END IF;

    -- Desactivar usuario
    UPDATE usuarios SET
        estado = 'Inactivo',
        fecha_modificacion = CURRENT_TIMESTAMP,
        usuario_modificacion = p_usuario
    WHERE id_usuario = p_id_usuario;

    RETURN QUERY SELECT p_id_usuario, 'Usuario desactivado correctamente.'::TEXT, FALSE;

EXCEPTION WHEN OTHERS THEN
    RETURN QUERY SELECT NULL::INT, 'Error al desactivar el usuario: ' || SQLERRM, TRUE;
END;
$$ LANGUAGE plpgsql;


-- ─────────────────────────────────────────────────────────────
-- Función: sp_reactivar_usuario
-- Reactiva un usuario desactivado
-- ─────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION sp_reactivar_usuario(
    p_id_usuario INT,
    p_usuario VARCHAR(80) DEFAULT 'sistema'
)
RETURNS TABLE (
    id_usuario_result INT,
    mensaje_result TEXT,
    is_error BOOLEAN
) AS $$
BEGIN
    -- Verificar que el usuario existe
    IF NOT EXISTS (SELECT 1 FROM usuarios WHERE id_usuario = p_id_usuario) THEN
        RETURN QUERY SELECT NULL::INT, 'El usuario no existe.'::TEXT, TRUE;
        RETURN;
    END IF;

    -- Reactivar usuario
    UPDATE usuarios SET
        estado = 'Activo',
        fecha_modificacion = CURRENT_TIMESTAMP,
        usuario_modificacion = p_usuario
    WHERE id_usuario = p_id_usuario;

    RETURN QUERY SELECT p_id_usuario, 'Usuario reactivado correctamente.'::TEXT, FALSE;

EXCEPTION WHEN OTHERS THEN
    RETURN QUERY SELECT NULL::INT, 'Error al reactivar el usuario: ' || SQLERRM, TRUE;
END;
$$ LANGUAGE plpgsql;
