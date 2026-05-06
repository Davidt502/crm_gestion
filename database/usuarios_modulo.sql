-- ============================================================
-- MÓDULO: Gestión de Usuarios
-- CRM Ing Software v3
-- ============================================================

USE crm_ing_software;
GO

-- ─────────────────────────────────────────────────────────────
-- SP: Crear usuario
-- ─────────────────────────────────────────────────────────────
IF OBJECT_ID('dbo.sp_crear_usuario', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_crear_usuario;
GO

CREATE PROCEDURE dbo.sp_crear_usuario
    @nombre    NVARCHAR(150),
    @email     NVARCHAR(150),
    @username  NVARCHAR(80),
    @password_hash NVARCHAR(255),
    @rol       NVARCHAR(30) = 'usuario',
    @usuario   NVARCHAR(80) = 'sistema'
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;

        IF NULLIF(LTRIM(RTRIM(@nombre)), '') IS NULL
            THROW 50070, 'El nombre es obligatorio.', 1;

        IF NULLIF(LTRIM(RTRIM(@username)), '') IS NULL
            THROW 50071, 'El nombre de usuario es obligatorio.', 1;

        IF NULLIF(LTRIM(RTRIM(@password_hash)), '') IS NULL
            THROW 50072, 'La contraseña es obligatoria.', 1;

        IF @rol NOT IN ('admin', 'usuario')
            THROW 50073, 'El rol debe ser admin o usuario.', 1;

        IF EXISTS (SELECT 1 FROM usuarios WHERE username = @username)
            THROW 50074, 'Ya existe un usuario con ese nombre de usuario.', 1;

        IF @email IS NOT NULL AND @email != '' AND EXISTS (SELECT 1 FROM usuarios WHERE email = @email)
            THROW 50075, 'Ya existe un usuario con ese correo electrónico.', 1;

        INSERT INTO usuarios (nombre, email, username, password_hash, rol, estado, usuario_creacion)
        VALUES (
            LTRIM(RTRIM(@nombre)),
            NULLIF(LTRIM(RTRIM(@email)), ''),
            LTRIM(RTRIM(@username)),
            @password_hash,
            @rol,
            'Activo',
            @usuario
        );

        COMMIT TRANSACTION;
        SELECT SCOPE_IDENTITY() AS id_usuario, 'Usuario creado correctamente.' AS mensaje;

    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        SELECT ERROR_NUMBER() AS codigo_error, ERROR_MESSAGE() AS mensaje;
    END CATCH
END
GO

-- ─────────────────────────────────────────────────────────────
-- SP: Actualizar usuario
-- ─────────────────────────────────────────────────────────────
IF OBJECT_ID('dbo.sp_actualizar_usuario', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_actualizar_usuario;
GO

CREATE PROCEDURE dbo.sp_actualizar_usuario
    @id_usuario INT,
    @nombre     NVARCHAR(150),
    @email      NVARCHAR(150) = NULL,
    @rol        NVARCHAR(30)  = NULL,
    @usuario    NVARCHAR(80)  = 'sistema'
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;

        IF NOT EXISTS (SELECT 1 FROM usuarios WHERE id_usuario = @id_usuario)
            THROW 50076, 'El usuario no existe.', 1;

        IF NULLIF(LTRIM(RTRIM(@nombre)), '') IS NULL
            THROW 50070, 'El nombre es obligatorio.', 1;

        IF @rol IS NOT NULL AND @rol NOT IN ('admin', 'usuario')
            THROW 50073, 'El rol debe ser admin o usuario.', 1;

        IF @email IS NOT NULL AND @email != '' AND EXISTS (
            SELECT 1 FROM usuarios WHERE email = @email AND id_usuario <> @id_usuario
        )
            THROW 50075, 'Ya existe un usuario con ese correo electrónico.', 1;

        UPDATE usuarios SET
            nombre               = LTRIM(RTRIM(@nombre)),
            email                = NULLIF(LTRIM(RTRIM(ISNULL(@email, ''))), ''),
            rol                  = ISNULL(@rol, rol),
            fecha_modificacion   = GETDATE(),
            usuario_modificacion = @usuario
        WHERE id_usuario = @id_usuario;

        COMMIT TRANSACTION;
        SELECT @id_usuario AS id_usuario, 'Usuario actualizado correctamente.' AS mensaje;

    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        SELECT ERROR_NUMBER() AS codigo_error, ERROR_MESSAGE() AS mensaje;
    END CATCH
END
GO

-- ─────────────────────────────────────────────────────────────
-- SP: Cambiar contraseña
-- ─────────────────────────────────────────────────────────────
IF OBJECT_ID('dbo.sp_cambiar_password_usuario', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_cambiar_password_usuario;
GO

CREATE PROCEDURE dbo.sp_cambiar_password_usuario
    @id_usuario    INT,
    @password_hash NVARCHAR(255),
    @usuario       NVARCHAR(80) = 'sistema'
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;

        IF NOT EXISTS (SELECT 1 FROM usuarios WHERE id_usuario = @id_usuario)
            THROW 50076, 'El usuario no existe.', 1;

        IF NULLIF(LTRIM(RTRIM(@password_hash)), '') IS NULL
            THROW 50072, 'La nueva contraseña es obligatoria.', 1;

        UPDATE usuarios SET
            password_hash        = @password_hash,
            fecha_modificacion   = GETDATE(),
            usuario_modificacion = @usuario
        WHERE id_usuario = @id_usuario;

        COMMIT TRANSACTION;
        SELECT @id_usuario AS id_usuario, 'Contraseña actualizada correctamente.' AS mensaje;

    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        SELECT ERROR_NUMBER() AS codigo_error, ERROR_MESSAGE() AS mensaje;
    END CATCH
END
GO

-- ─────────────────────────────────────────────────────────────
-- SP: Desactivar usuario (soft delete)
-- ─────────────────────────────────────────────────────────────
IF OBJECT_ID('dbo.sp_desactivar_usuario', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_desactivar_usuario;
GO

CREATE PROCEDURE dbo.sp_desactivar_usuario
    @id_usuario INT,
    @usuario    NVARCHAR(80) = 'sistema'
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;

        IF NOT EXISTS (SELECT 1 FROM usuarios WHERE id_usuario = @id_usuario)
            THROW 50076, 'El usuario no existe.', 1;

        -- No permitir desactivar el único admin activo
        IF (SELECT COUNT(*) FROM usuarios WHERE rol = 'admin' AND estado = 'Activo') = 1
            AND EXISTS (SELECT 1 FROM usuarios WHERE id_usuario = @id_usuario AND rol = 'admin')
            THROW 50077, 'No se puede desactivar el único administrador activo del sistema.', 1;

        -- No permitir autodesactivarse
        IF (SELECT username FROM usuarios WHERE id_usuario = @id_usuario) = @usuario
            THROW 50078, 'No puedes desactivar tu propia cuenta.', 1;

        UPDATE usuarios SET
            estado               = 'Inactivo',
            fecha_modificacion   = GETDATE(),
            usuario_modificacion = @usuario
        WHERE id_usuario = @id_usuario;

        COMMIT TRANSACTION;
        SELECT @id_usuario AS id_usuario, 'Usuario desactivado correctamente.' AS mensaje;

    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        SELECT ERROR_NUMBER() AS codigo_error, ERROR_MESSAGE() AS mensaje;
    END CATCH
END
GO

-- ─────────────────────────────────────────────────────────────
-- SP: Reactivar usuario
-- ─────────────────────────────────────────────────────────────
IF OBJECT_ID('dbo.sp_reactivar_usuario', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_reactivar_usuario;
GO

CREATE PROCEDURE dbo.sp_reactivar_usuario
    @id_usuario INT,
    @usuario    NVARCHAR(80) = 'sistema'
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;

        IF NOT EXISTS (SELECT 1 FROM usuarios WHERE id_usuario = @id_usuario)
            THROW 50076, 'El usuario no existe.', 1;

        UPDATE usuarios SET
            estado               = 'Activo',
            fecha_modificacion   = GETDATE(),
            usuario_modificacion = @usuario
        WHERE id_usuario = @id_usuario;

        COMMIT TRANSACTION;
        SELECT @id_usuario AS id_usuario, 'Usuario reactivado correctamente.' AS mensaje;

    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        SELECT ERROR_NUMBER() AS codigo_error, ERROR_MESSAGE() AS mensaje;
    END CATCH
END
GO

PRINT '>>> SPs de gestión de usuarios creados correctamente.';
GO
