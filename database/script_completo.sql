-- ============================================================
-- CRM ING SOFTWARE - Base de Datos Empresarial Completa
-- SQL Server | Arquitectura 3FN | Stored Procedures | Triggers
-- ============================================================

USE master;
GO

IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'crm_ing_software')
BEGIN
    CREATE DATABASE crm_ing_software;
    PRINT '>>> Base de datos crm_ing_software creada.';
END
GO

USE crm_ing_software;
GO

-- ============================================================
-- SECCIÓN 1: TABLAS BASE
-- ============================================================

-- ------------------------------------------------------------
-- Tabla: usuarios (sistema de login)
-- ------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'usuarios')
BEGIN
    CREATE TABLE usuarios (
        id_usuario       INT IDENTITY(1,1) PRIMARY KEY,
        nombre           NVARCHAR(150)  NOT NULL,
        email            NVARCHAR(150)  NOT NULL,
        username         NVARCHAR(80)   NOT NULL,
        password_hash    NVARCHAR(255)  NOT NULL,
        rol              NVARCHAR(30)   NOT NULL DEFAULT 'usuario'
                         CONSTRAINT chk_rol_usuario CHECK (rol IN ('admin','usuario')),
        estado           NVARCHAR(20)   NOT NULL DEFAULT 'Activo'
                         CONSTRAINT chk_estado_usuario CHECK (estado IN ('Activo','Inactivo')),
        ultimo_acceso    DATETIME       NULL,
        fecha_creacion   DATETIME       NOT NULL DEFAULT GETDATE(),
        fecha_modificacion DATETIME     NULL,
        usuario_creacion   NVARCHAR(80) NOT NULL DEFAULT 'sistema',
        usuario_modificacion NVARCHAR(80) NULL,
        CONSTRAINT uq_email_usuario    UNIQUE (email),
        CONSTRAINT uq_username_usuario UNIQUE (username)
    );
    PRINT '>>> Tabla usuarios creada.';
END
GO

-- ------------------------------------------------------------
-- Tabla: dependencias
-- ------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'dependencias')
BEGIN
    CREATE TABLE dependencias (
        id_dependencia     INT IDENTITY(1,1) PRIMARY KEY,
        nombre_dependencia NVARCHAR(150)  NOT NULL,
        estado             NVARCHAR(20)   NOT NULL DEFAULT 'Activo'
                           CONSTRAINT chk_estado_dep CHECK (estado IN ('Activo','Inactivo')),
        fecha_creacion     DATETIME       NOT NULL DEFAULT GETDATE(),
        fecha_modificacion DATETIME       NULL,
        usuario_creacion   NVARCHAR(80)   NOT NULL DEFAULT 'sistema',
        usuario_modificacion NVARCHAR(80) NULL
    );
    PRINT '>>> Tabla dependencias creada.';
END
GO

-- ------------------------------------------------------------
-- Tabla: empleados
-- ------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'empleados')
BEGIN
    CREATE TABLE empleados (
        id_empleado        INT IDENTITY(1,1) PRIMARY KEY,
        numero_empleado    NVARCHAR(30)   NOT NULL,
        dpi                NVARCHAR(20)   NOT NULL,
        nombre_completo    NVARCHAR(200)  NOT NULL,
        cargo              NVARCHAR(100)  NULL,
        id_dependencia     INT            NULL,
        estado             NVARCHAR(20)   NOT NULL DEFAULT 'Activo'
                           CONSTRAINT chk_estado_emp CHECK (estado IN ('Activo','Inactivo')),
        fecha_nacimiento   DATE           NULL,
        correo             NVARCHAR(150)  NULL,
        telefono           NVARCHAR(30)   NULL,
        direccion          NVARCHAR(255)  NULL,
        fecha_creacion     DATETIME       NOT NULL DEFAULT GETDATE(),
        fecha_modificacion DATETIME       NULL,
        usuario_creacion   NVARCHAR(80)   NOT NULL DEFAULT 'sistema',
        usuario_modificacion NVARCHAR(80) NULL,
        CONSTRAINT uq_numero_empleado UNIQUE (numero_empleado),
        CONSTRAINT uq_dpi_empleado    UNIQUE (dpi),
        CONSTRAINT fk_empleado_dep    FOREIGN KEY (id_dependencia) REFERENCES dependencias(id_dependencia)
    );
    PRINT '>>> Tabla empleados creada.';
END
GO

-- ------------------------------------------------------------
-- Tabla: historial_dependencia
-- ------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'historial_dependencia')
BEGIN
    CREATE TABLE historial_dependencia (
        id_historial        INT IDENTITY(1,1) PRIMARY KEY,
        id_empleado         INT           NOT NULL,
        id_dependencia_origen  INT        NULL,
        id_dependencia_destino INT        NOT NULL,
        motivo              NVARCHAR(500) NULL,
        usuario             NVARCHAR(80)  NOT NULL DEFAULT 'sistema',
        fecha_movimiento    DATETIME      NOT NULL DEFAULT GETDATE(),
        fecha_creacion      DATETIME      NOT NULL DEFAULT GETDATE(),
        fecha_modificacion  DATETIME      NULL,
        usuario_creacion    NVARCHAR(80)  NOT NULL DEFAULT 'sistema',
        usuario_modificacion NVARCHAR(80) NULL,
        CONSTRAINT fk_hist_empleado FOREIGN KEY (id_empleado)
            REFERENCES empleados(id_empleado),
        CONSTRAINT fk_hist_dep_origen FOREIGN KEY (id_dependencia_origen)
            REFERENCES dependencias(id_dependencia),
        CONSTRAINT fk_hist_dep_destino FOREIGN KEY (id_dependencia_destino)
            REFERENCES dependencias(id_dependencia)
    );
    PRINT '>>> Tabla historial_dependencia creada.';
END
GO

-- ------------------------------------------------------------
-- Tabla: clientes
-- ------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'clientes')
BEGIN
    CREATE TABLE clientes (
        id_cliente               INT IDENTITY(1,1) PRIMARY KEY,
        nombre_razon_social      NVARCHAR(255)  NOT NULL,
        documento_identificacion NVARCHAR(50)   NOT NULL,
        tipo                     NVARCHAR(20)   NOT NULL DEFAULT 'Cliente'
                                 CONSTRAINT chk_tipo_cliente CHECK (tipo IN ('Cliente','Prospecto')),
        estado                   NVARCHAR(20)   NOT NULL DEFAULT 'Activo'
                                 CONSTRAINT chk_estado_cliente CHECK (estado IN ('Activo','Inactivo')),
        fecha_nacimiento         DATE           NULL,
        correo                   NVARCHAR(150)  NULL,
        notificacion_email       BIT            NOT NULL DEFAULT 0,
        notificacion_sms         BIT            NOT NULL DEFAULT 0,
        fecha_creacion           DATETIME       NOT NULL DEFAULT GETDATE(),
        fecha_modificacion       DATETIME       NULL,
        usuario_creacion         NVARCHAR(80)   NOT NULL DEFAULT 'sistema',
        usuario_modificacion     NVARCHAR(80)   NULL,
        CONSTRAINT uq_doc_cliente UNIQUE (documento_identificacion)
    );
    PRINT '>>> Tabla clientes creada.';
END
GO

-- ------------------------------------------------------------
-- Tabla: contactos_cliente
-- ------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'contactos_cliente')
BEGIN
    CREATE TABLE contactos_cliente (
        id_contacto    INT IDENTITY(1,1) PRIMARY KEY,
        id_cliente     INT           NOT NULL,
        nombre_contacto NVARCHAR(150) NOT NULL,
        tipo_contacto  NVARCHAR(50)  NOT NULL
                       CONSTRAINT chk_tipo_contacto CHECK (tipo_contacto IN ('Teléfono','Dirección','Fax','Email','Celular')),
        descripcion    NVARCHAR(255) NOT NULL,
        correo         NVARCHAR(150) NULL,
        telefono       NVARCHAR(30)  NULL,
        estado         NVARCHAR(20)  NOT NULL DEFAULT 'Activo'
                       CONSTRAINT chk_estado_contacto CHECK (estado IN ('Activo','Inactivo')),
        fecha_creacion DATETIME      NOT NULL DEFAULT GETDATE(),
        fecha_modificacion DATETIME  NULL,
        usuario_creacion   NVARCHAR(80) NOT NULL DEFAULT 'sistema',
        usuario_modificacion NVARCHAR(80) NULL,
        CONSTRAINT fk_contacto_cliente FOREIGN KEY (id_cliente)
            REFERENCES clientes(id_cliente)
    );
    PRINT '>>> Tabla contactos_cliente creada.';
END
GO

-- ------------------------------------------------------------
-- Tabla: categorias_proveedor
-- ------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'categorias_proveedor')
BEGIN
    CREATE TABLE categorias_proveedor (
        id_categoria       INT IDENTITY(1,1) PRIMARY KEY,
        nombre_categoria   NVARCHAR(100)  NOT NULL,
        descripcion        NVARCHAR(255)  NULL,
        estado             NVARCHAR(20)   NOT NULL DEFAULT 'Activo'
                           CONSTRAINT chk_estado_cat CHECK (estado IN ('Activo','Inactivo')),
        fecha_creacion     DATETIME       NOT NULL DEFAULT GETDATE(),
        fecha_modificacion DATETIME       NULL,
        usuario_creacion   NVARCHAR(80)   NOT NULL DEFAULT 'sistema',
        usuario_modificacion NVARCHAR(80) NULL,
        CONSTRAINT uq_nombre_categoria UNIQUE (nombre_categoria)
    );
    PRINT '>>> Tabla categorias_proveedor creada.';
END
GO

-- ------------------------------------------------------------
-- Tabla: proveedores
-- ------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'proveedores')
BEGIN
    CREATE TABLE proveedores (
        id_proveedor        INT IDENTITY(1,1) PRIMARY KEY,
        nombre_empresa      NVARCHAR(255)  NOT NULL,
        nit                 NVARCHAR(50)   NOT NULL,
        id_categoria        INT            NOT NULL,
        contacto            NVARCHAR(150)  NULL,
        telefono            NVARCHAR(50)   NOT NULL,
        correo              NVARCHAR(150)  NULL,
        direccion           NVARCHAR(255)  NULL,
        notas               NVARCHAR(MAX)  NULL,
        estado              NVARCHAR(20)   NOT NULL DEFAULT 'Activo'
                            CONSTRAINT chk_estado_prov CHECK (estado IN ('Activo','Inactivo')),
        motivo_inactivacion NVARCHAR(MAX)  NULL,
        fecha_creacion      DATETIME       NOT NULL DEFAULT GETDATE(),
        fecha_modificacion  DATETIME       NULL,
        usuario_creacion    NVARCHAR(80)   NOT NULL DEFAULT 'sistema',
        usuario_modificacion NVARCHAR(80)  NULL,
        CONSTRAINT uq_nit_proveedor   UNIQUE (nit),
        CONSTRAINT fk_prov_categoria  FOREIGN KEY (id_categoria)
            REFERENCES categorias_proveedor(id_categoria)
    );
    PRINT '>>> Tabla proveedores creada.';
END
GO

-- ------------------------------------------------------------
-- Tabla: compras_proveedor
-- ------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'compras_proveedor')
BEGIN
    CREATE TABLE compras_proveedor (
        id_compra          INT IDENTITY(1,1) PRIMARY KEY,
        id_proveedor       INT            NOT NULL,
        fecha_compra       DATE           NOT NULL DEFAULT CAST(GETDATE() AS DATE),
        productos          NVARCHAR(MAX)  NOT NULL,
        monto_total        DECIMAL(18,2)  NOT NULL
                           CONSTRAINT chk_monto_positivo CHECK (monto_total > 0),
        estado_pago        NVARCHAR(20)   NOT NULL DEFAULT 'Pendiente'
                           CONSTRAINT chk_estado_pago CHECK (estado_pago IN ('Pagado','Pendiente')),
        notas              NVARCHAR(500)  NULL,
        fecha_creacion     DATETIME       NOT NULL DEFAULT GETDATE(),
        fecha_modificacion DATETIME       NULL,
        usuario_creacion   NVARCHAR(80)   NOT NULL DEFAULT 'sistema',
        usuario_modificacion NVARCHAR(80) NULL,
        CONSTRAINT fk_compra_proveedor FOREIGN KEY (id_proveedor)
            REFERENCES proveedores(id_proveedor)
    );
    PRINT '>>> Tabla compras_proveedor creada.';
END
GO

-- ------------------------------------------------------------
-- Tabla: registro_felicitaciones
-- ------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'registro_felicitaciones')
BEGIN
    CREATE TABLE registro_felicitaciones (
        id_felicitacion    INT IDENTITY(1,1) PRIMARY KEY,
        id_cliente         INT           NULL,
        id_empleado        INT           NULL,
        tipo_felicitacion  NVARCHAR(30)  NOT NULL
                           CONSTRAINT chk_tipo_felic CHECK (tipo_felicitacion IN ('Cumpleaños','Aniversario')),
        fecha_envio        DATE          NOT NULL DEFAULT CAST(GETDATE() AS DATE),
        estado             NVARCHAR(20)  NOT NULL DEFAULT 'Enviado'
                           CONSTRAINT chk_estado_felic CHECK (estado IN ('Enviado','Pendiente','Error')),
        mensaje            NVARCHAR(500) NULL,
        fecha_creacion     DATETIME      NOT NULL DEFAULT GETDATE(),
        fecha_modificacion DATETIME      NULL,
        usuario_creacion   NVARCHAR(80)  NOT NULL DEFAULT 'sistema',
        usuario_modificacion NVARCHAR(80) NULL,
        CONSTRAINT fk_felic_cliente  FOREIGN KEY (id_cliente)
            REFERENCES clientes(id_cliente),
        CONSTRAINT fk_felic_empleado FOREIGN KEY (id_empleado)
            REFERENCES empleados(id_empleado)
    );
    PRINT '>>> Tabla registro_felicitaciones creada.';
END
GO

-- ============================================================
-- SECCIÓN 2: ÍNDICES DE RENDIMIENTO
-- ============================================================

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_clientes_documento')
    CREATE UNIQUE INDEX IX_clientes_documento ON clientes(documento_identificacion);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_clientes_nombre')
    CREATE INDEX IX_clientes_nombre ON clientes(nombre_razon_social);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_clientes_tipo_estado')
    CREATE INDEX IX_clientes_tipo_estado ON clientes(tipo, estado);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_clientes_nacimiento')
    CREATE INDEX IX_clientes_nacimiento ON clientes(fecha_nacimiento)
    WHERE fecha_nacimiento IS NOT NULL;

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_proveedores_nit')
    CREATE UNIQUE INDEX IX_proveedores_nit ON proveedores(nit);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_proveedores_categoria')
    CREATE INDEX IX_proveedores_categoria ON proveedores(id_categoria);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_empleados_numero')
    CREATE UNIQUE INDEX IX_empleados_numero ON empleados(numero_empleado);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_empleados_nacimiento')
    CREATE INDEX IX_empleados_nacimiento ON empleados(fecha_nacimiento)
    WHERE fecha_nacimiento IS NOT NULL;

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_contactos_cliente')
    CREATE INDEX IX_contactos_cliente ON contactos_cliente(id_cliente);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_historial_empleado')
    CREATE INDEX IX_historial_empleado ON historial_dependencia(id_empleado);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_felicitaciones_fecha')
    CREATE INDEX IX_felicitaciones_fecha ON registro_felicitaciones(fecha_envio);

PRINT '>>> Índices creados.';
GO

-- ============================================================
-- SECCIÓN 3: FUNCIONES DE VALIDACIÓN
-- ============================================================

-- Función: validar formato de correo
IF OBJECT_ID('dbo.fn_validar_correo', 'FN') IS NOT NULL
    DROP FUNCTION dbo.fn_validar_correo;
GO

CREATE FUNCTION dbo.fn_validar_correo (@correo NVARCHAR(150))
RETURNS BIT
AS
BEGIN
    IF @correo IS NULL OR @correo = '' RETURN 1; -- null es válido (campo opcional)
    IF @correo LIKE '%_@_%.__%'
        AND @correo NOT LIKE '% %'
        RETURN 1;
    RETURN 0;
END
GO

-- Función: obtener nombre de dependencia
IF OBJECT_ID('dbo.fn_nombre_dependencia', 'FN') IS NOT NULL
    DROP FUNCTION dbo.fn_nombre_dependencia;
GO

CREATE FUNCTION dbo.fn_nombre_dependencia (@id INT)
RETURNS NVARCHAR(150)
AS
BEGIN
    DECLARE @nombre NVARCHAR(150);
    SELECT @nombre = nombre_dependencia FROM dependencias WHERE id_dependencia = @id;
    RETURN ISNULL(@nombre, 'Sin dependencia');
END
GO

PRINT '>>> Funciones creadas.';
GO

-- ============================================================
-- SECCIÓN 4: STORED PROCEDURES - CLIENTES
-- ============================================================

-- ------------------------------------------------------------
-- sp_registrar_cliente
-- ------------------------------------------------------------
IF OBJECT_ID('dbo.sp_registrar_cliente', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_registrar_cliente;
GO

CREATE PROCEDURE dbo.sp_registrar_cliente
    @nombre_razon_social      NVARCHAR(255),
    @documento_identificacion NVARCHAR(50),
    @tipo                     NVARCHAR(20) = 'Cliente',
    @estado                   NVARCHAR(20) = 'Activo',
    @fecha_nacimiento         DATE         = NULL,
    @correo                   NVARCHAR(150)= NULL,
    @notificacion_email       BIT          = 0,
    @notificacion_sms         BIT          = 0,
    @usuario                  NVARCHAR(80) = 'sistema'
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;

        -- Validar campos obligatorios
        IF NULLIF(LTRIM(RTRIM(@nombre_razon_social)), '') IS NULL
            THROW 50001, 'El nombre o razón social es obligatorio.', 1;

        IF NULLIF(LTRIM(RTRIM(@documento_identificacion)), '') IS NULL
            THROW 50002, 'El documento de identificación es obligatorio.', 1;

        -- Validar tipo
        IF @tipo NOT IN ('Cliente','Prospecto')
            THROW 50003, 'El tipo debe ser Cliente o Prospecto.', 1;

        -- Validar documento duplicado
        IF EXISTS (SELECT 1 FROM clientes WHERE documento_identificacion = @documento_identificacion)
            THROW 50004, 'Ya existe un cliente registrado con este documento.', 1;

        -- Validar formato correo
        IF @correo IS NOT NULL AND dbo.fn_validar_correo(@correo) = 0
            THROW 50005, 'El formato del correo electrónico no es válido.', 1;

        -- Insertar
        INSERT INTO clientes (
            nombre_razon_social, documento_identificacion, tipo, estado,
            fecha_nacimiento, correo, notificacion_email, notificacion_sms,
            usuario_creacion
        )
        VALUES (
            LTRIM(RTRIM(@nombre_razon_social)),
            LTRIM(RTRIM(@documento_identificacion)),
            @tipo, @estado, @fecha_nacimiento, @correo,
            @notificacion_email, @notificacion_sms, @usuario
        );

        DECLARE @nuevo_id INT = SCOPE_IDENTITY();

        COMMIT TRANSACTION;
        SELECT @nuevo_id AS id_cliente, 'Cliente registrado exitosamente.' AS mensaje;

    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        SELECT
            ERROR_NUMBER()  AS codigo_error,
            ERROR_MESSAGE() AS mensaje;
    END CATCH
END
GO

-- ------------------------------------------------------------
-- sp_actualizar_cliente
-- ------------------------------------------------------------
IF OBJECT_ID('dbo.sp_actualizar_cliente', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_actualizar_cliente;
GO

CREATE PROCEDURE dbo.sp_actualizar_cliente
    @id_cliente               INT,
    @nombre_razon_social      NVARCHAR(255),
    @documento_identificacion NVARCHAR(50),
    @tipo                     NVARCHAR(20),
    @estado                   NVARCHAR(20),
    @fecha_nacimiento         DATE         = NULL,
    @correo                   NVARCHAR(150)= NULL,
    @notificacion_email       BIT          = 0,
    @notificacion_sms         BIT          = 0,
    @usuario                  NVARCHAR(80) = 'sistema'
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;

        IF NOT EXISTS (SELECT 1 FROM clientes WHERE id_cliente = @id_cliente)
            THROW 50010, 'El cliente no existe.', 1;

        IF NULLIF(LTRIM(RTRIM(@nombre_razon_social)), '') IS NULL
            THROW 50001, 'El nombre o razón social es obligatorio.', 1;

        IF NULLIF(LTRIM(RTRIM(@documento_identificacion)), '') IS NULL
            THROW 50002, 'El documento de identificación es obligatorio.', 1;

        IF @tipo NOT IN ('Cliente','Prospecto')
            THROW 50003, 'El tipo debe ser Cliente o Prospecto.', 1;

        -- Verificar duplicado excluyendo el mismo registro
        IF EXISTS (
            SELECT 1 FROM clientes
            WHERE documento_identificacion = @documento_identificacion
              AND id_cliente <> @id_cliente
        )
            THROW 50004, 'Ya existe otro cliente con este documento.', 1;

        IF @correo IS NOT NULL AND dbo.fn_validar_correo(@correo) = 0
            THROW 50005, 'El formato del correo no es válido.', 1;

        UPDATE clientes SET
            nombre_razon_social      = LTRIM(RTRIM(@nombre_razon_social)),
            documento_identificacion = LTRIM(RTRIM(@documento_identificacion)),
            tipo                     = @tipo,
            estado                   = @estado,
            fecha_nacimiento         = @fecha_nacimiento,
            correo                   = @correo,
            notificacion_email       = @notificacion_email,
            notificacion_sms         = @notificacion_sms,
            fecha_modificacion       = GETDATE(),
            usuario_modificacion     = @usuario
        WHERE id_cliente = @id_cliente;

        COMMIT TRANSACTION;
        SELECT @id_cliente AS id_cliente, 'Cliente actualizado exitosamente.' AS mensaje;

    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        SELECT ERROR_NUMBER() AS codigo_error, ERROR_MESSAGE() AS mensaje;
    END CATCH
END
GO

-- ------------------------------------------------------------
-- sp_inactivar_cliente
-- ------------------------------------------------------------
IF OBJECT_ID('dbo.sp_inactivar_cliente', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_inactivar_cliente;
GO

CREATE PROCEDURE dbo.sp_inactivar_cliente
    @id_cliente INT,
    @usuario    NVARCHAR(80) = 'sistema'
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;

        IF NOT EXISTS (SELECT 1 FROM clientes WHERE id_cliente = @id_cliente)
            THROW 50010, 'El cliente no existe.', 1;

        IF NOT EXISTS (SELECT 1 FROM clientes WHERE id_cliente = @id_cliente AND estado = 'Activo')
            THROW 50011, 'El cliente ya se encuentra inactivo.', 1;

        UPDATE clientes SET
            estado               = 'Inactivo',
            fecha_modificacion   = GETDATE(),
            usuario_modificacion = @usuario
        WHERE id_cliente = @id_cliente;

        COMMIT TRANSACTION;
        SELECT @id_cliente AS id_cliente, 'Cliente inactivado correctamente.' AS mensaje;

    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        SELECT ERROR_NUMBER() AS codigo_error, ERROR_MESSAGE() AS mensaje;
    END CATCH
END
GO

-- ============================================================
-- SECCIÓN 5: STORED PROCEDURES - CONTACTOS
-- ============================================================

IF OBJECT_ID('dbo.sp_agregar_contacto', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_agregar_contacto;
GO

CREATE PROCEDURE dbo.sp_agregar_contacto
    @id_cliente      INT,
    @nombre_contacto NVARCHAR(150),
    @tipo_contacto   NVARCHAR(50),
    @descripcion     NVARCHAR(255),
    @correo          NVARCHAR(150) = NULL,
    @telefono        NVARCHAR(30)  = NULL,
    @usuario         NVARCHAR(80)  = 'sistema'
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;

        IF NOT EXISTS (SELECT 1 FROM clientes WHERE id_cliente = @id_cliente)
            THROW 50020, 'El cliente no existe.', 1;

        IF NULLIF(LTRIM(RTRIM(@nombre_contacto)), '') IS NULL
            THROW 50021, 'El nombre del contacto es obligatorio.', 1;

        IF NULLIF(LTRIM(RTRIM(@descripcion)), '') IS NULL
            THROW 50022, 'La descripción es obligatoria.', 1;

        IF @tipo_contacto NOT IN ('Teléfono','Dirección','Fax','Email','Celular')
            THROW 50023, 'Tipo de contacto no válido.', 1;

        IF @correo IS NOT NULL AND dbo.fn_validar_correo(@correo) = 0
            THROW 50005, 'El formato del correo no es válido.', 1;

        INSERT INTO contactos_cliente (
            id_cliente, nombre_contacto, tipo_contacto,
            descripcion, correo, telefono, usuario_creacion
        )
        VALUES (
            @id_cliente, LTRIM(RTRIM(@nombre_contacto)),
            @tipo_contacto, LTRIM(RTRIM(@descripcion)),
            @correo, @telefono, @usuario
        );

        COMMIT TRANSACTION;
        SELECT SCOPE_IDENTITY() AS id_contacto, 'Contacto agregado exitosamente.' AS mensaje;

    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        SELECT ERROR_NUMBER() AS codigo_error, ERROR_MESSAGE() AS mensaje;
    END CATCH
END
GO

IF OBJECT_ID('dbo.sp_actualizar_contacto', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_actualizar_contacto;
GO

CREATE PROCEDURE dbo.sp_actualizar_contacto
    @id_contacto     INT,
    @nombre_contacto NVARCHAR(150),
    @tipo_contacto   NVARCHAR(50),
    @descripcion     NVARCHAR(255),
    @correo          NVARCHAR(150) = NULL,
    @telefono        NVARCHAR(30)  = NULL,
    @estado          NVARCHAR(20)  = 'Activo',
    @usuario         NVARCHAR(80)  = 'sistema'
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;

        IF NOT EXISTS (SELECT 1 FROM contactos_cliente WHERE id_contacto = @id_contacto)
            THROW 50030, 'El contacto no existe.', 1;

        IF @correo IS NOT NULL AND dbo.fn_validar_correo(@correo) = 0
            THROW 50005, 'El formato del correo no es válido.', 1;

        UPDATE contactos_cliente SET
            nombre_contacto    = LTRIM(RTRIM(@nombre_contacto)),
            tipo_contacto      = @tipo_contacto,
            descripcion        = LTRIM(RTRIM(@descripcion)),
            correo             = @correo,
            telefono           = @telefono,
            estado             = @estado,
            fecha_modificacion = GETDATE(),
            usuario_modificacion = @usuario
        WHERE id_contacto = @id_contacto;

        COMMIT TRANSACTION;
        SELECT @id_contacto AS id_contacto, 'Contacto actualizado exitosamente.' AS mensaje;

    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        SELECT ERROR_NUMBER() AS codigo_error, ERROR_MESSAGE() AS mensaje;
    END CATCH
END
GO

IF OBJECT_ID('dbo.sp_eliminar_contacto', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_eliminar_contacto;
GO

CREATE PROCEDURE dbo.sp_eliminar_contacto
    @id_contacto INT,
    @usuario     NVARCHAR(80) = 'sistema'
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;

        IF NOT EXISTS (SELECT 1 FROM contactos_cliente WHERE id_contacto = @id_contacto)
            THROW 50030, 'El contacto no existe.', 1;

        -- Inactivar en lugar de eliminar físicamente
        UPDATE contactos_cliente SET
            estado               = 'Inactivo',
            fecha_modificacion   = GETDATE(),
            usuario_modificacion = @usuario
        WHERE id_contacto = @id_contacto;

        COMMIT TRANSACTION;
        SELECT @id_contacto AS id_contacto, 'Contacto inactivado correctamente.' AS mensaje;

    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        SELECT ERROR_NUMBER() AS codigo_error, ERROR_MESSAGE() AS mensaje;
    END CATCH
END
GO

-- ============================================================
-- SECCIÓN 6: STORED PROCEDURES - PROVEEDORES
-- ============================================================

IF OBJECT_ID('dbo.sp_registrar_proveedor', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_registrar_proveedor;
GO

CREATE PROCEDURE dbo.sp_registrar_proveedor
    @nombre_empresa NVARCHAR(255),
    @nit            NVARCHAR(50),
    @id_categoria   INT,
    @telefono       NVARCHAR(50),
    @contacto       NVARCHAR(150) = NULL,
    @correo         NVARCHAR(150) = NULL,
    @direccion      NVARCHAR(255) = NULL,
    @notas          NVARCHAR(MAX) = NULL,
    @usuario        NVARCHAR(80)  = 'sistema'
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;

        IF NULLIF(LTRIM(RTRIM(@nombre_empresa)), '') IS NULL
            THROW 50040, 'El nombre de empresa es obligatorio.', 1;

        IF NULLIF(LTRIM(RTRIM(@nit)), '') IS NULL
            THROW 50041, 'El NIT es obligatorio.', 1;

        IF NULLIF(LTRIM(RTRIM(@telefono)), '') IS NULL
            THROW 50042, 'El teléfono es obligatorio.', 1;

        IF NOT EXISTS (SELECT 1 FROM categorias_proveedor WHERE id_categoria = @id_categoria AND estado = 'Activo')
            THROW 50043, 'La categoría no existe o está inactiva.', 1;

        IF EXISTS (SELECT 1 FROM proveedores WHERE nit = @nit)
            THROW 50044, 'Ya existe un proveedor con este NIT.', 1;

        IF @correo IS NOT NULL AND dbo.fn_validar_correo(@correo) = 0
            THROW 50005, 'El formato del correo no es válido.', 1;

        INSERT INTO proveedores (
            nombre_empresa, nit, id_categoria, telefono,
            contacto, correo, direccion, notas, usuario_creacion
        )
        VALUES (
            LTRIM(RTRIM(@nombre_empresa)), LTRIM(RTRIM(@nit)),
            @id_categoria, @telefono, @contacto, @correo,
            @direccion, @notas, @usuario
        );

        COMMIT TRANSACTION;
        SELECT SCOPE_IDENTITY() AS id_proveedor, 'Proveedor registrado exitosamente.' AS mensaje;

    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        SELECT ERROR_NUMBER() AS codigo_error, ERROR_MESSAGE() AS mensaje;
    END CATCH
END
GO

IF OBJECT_ID('dbo.sp_actualizar_proveedor', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_actualizar_proveedor;
GO

CREATE PROCEDURE dbo.sp_actualizar_proveedor
    @id_proveedor   INT,
    @nombre_empresa NVARCHAR(255),
    @nit            NVARCHAR(50),
    @id_categoria   INT,
    @telefono       NVARCHAR(50),
    @contacto       NVARCHAR(150) = NULL,
    @correo         NVARCHAR(150) = NULL,
    @direccion      NVARCHAR(255) = NULL,
    @notas          NVARCHAR(MAX) = NULL,
    @usuario        NVARCHAR(80)  = 'sistema'
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;

        IF NOT EXISTS (SELECT 1 FROM proveedores WHERE id_proveedor = @id_proveedor)
            THROW 50050, 'El proveedor no existe.', 1;

        IF EXISTS (
            SELECT 1 FROM proveedores
            WHERE nit = @nit AND id_proveedor <> @id_proveedor
        )
            THROW 50044, 'Ya existe otro proveedor con este NIT.', 1;

        IF @correo IS NOT NULL AND dbo.fn_validar_correo(@correo) = 0
            THROW 50005, 'El formato del correo no es válido.', 1;

        UPDATE proveedores SET
            nombre_empresa       = LTRIM(RTRIM(@nombre_empresa)),
            nit                  = LTRIM(RTRIM(@nit)),
            id_categoria         = @id_categoria,
            telefono             = @telefono,
            contacto             = @contacto,
            correo               = @correo,
            direccion            = @direccion,
            notas                = @notas,
            fecha_modificacion   = GETDATE(),
            usuario_modificacion = @usuario
        WHERE id_proveedor = @id_proveedor;

        COMMIT TRANSACTION;
        SELECT @id_proveedor AS id_proveedor, 'Proveedor actualizado exitosamente.' AS mensaje;

    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        SELECT ERROR_NUMBER() AS codigo_error, ERROR_MESSAGE() AS mensaje;
    END CATCH
END
GO

IF OBJECT_ID('dbo.sp_inactivar_proveedor', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_inactivar_proveedor;
GO

CREATE PROCEDURE dbo.sp_inactivar_proveedor
    @id_proveedor       INT,
    @motivo_inactivacion NVARCHAR(MAX),
    @usuario            NVARCHAR(80) = 'sistema'
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;

        IF NOT EXISTS (SELECT 1 FROM proveedores WHERE id_proveedor = @id_proveedor)
            THROW 50050, 'El proveedor no existe.', 1;

        IF NULLIF(LTRIM(RTRIM(@motivo_inactivacion)), '') IS NULL
            THROW 50051, 'El motivo de inactivación es obligatorio.', 1;

        IF NOT EXISTS (SELECT 1 FROM proveedores WHERE id_proveedor = @id_proveedor AND estado = 'Activo')
            THROW 50052, 'El proveedor ya se encuentra inactivo.', 1;

        UPDATE proveedores SET
            estado               = 'Inactivo',
            motivo_inactivacion  = LTRIM(RTRIM(@motivo_inactivacion)),
            fecha_modificacion   = GETDATE(),
            usuario_modificacion = @usuario
        WHERE id_proveedor = @id_proveedor;

        COMMIT TRANSACTION;
        SELECT @id_proveedor AS id_proveedor, 'Proveedor inactivado correctamente.' AS mensaje;

    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        SELECT ERROR_NUMBER() AS codigo_error, ERROR_MESSAGE() AS mensaje;
    END CATCH
END
GO

IF OBJECT_ID('dbo.sp_activar_proveedor', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_activar_proveedor;
GO

CREATE PROCEDURE dbo.sp_activar_proveedor
    @id_proveedor INT,
    @usuario      NVARCHAR(80) = 'sistema'
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;

        IF NOT EXISTS (SELECT 1 FROM proveedores WHERE id_proveedor = @id_proveedor)
            THROW 50050, 'El proveedor no existe.', 1;

        UPDATE proveedores SET
            estado               = 'Activo',
            motivo_inactivacion  = NULL,
            fecha_modificacion   = GETDATE(),
            usuario_modificacion = @usuario
        WHERE id_proveedor = @id_proveedor;

        COMMIT TRANSACTION;
        SELECT @id_proveedor AS id_proveedor, 'Proveedor activado correctamente.' AS mensaje;

    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        SELECT ERROR_NUMBER() AS codigo_error, ERROR_MESSAGE() AS mensaje;
    END CATCH
END
GO

IF OBJECT_ID('dbo.sp_eliminar_proveedor', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_eliminar_proveedor;
GO

CREATE PROCEDURE dbo.sp_eliminar_proveedor
    @id_proveedor INT,
    @usuario      NVARCHAR(80) = 'sistema'
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;

        IF NOT EXISTS (SELECT 1 FROM proveedores WHERE id_proveedor = @id_proveedor)
            THROW 50050, 'El proveedor no existe.', 1;

        IF EXISTS (SELECT 1 FROM compras_proveedor WHERE id_proveedor = @id_proveedor)
            THROW 50053, 'No se puede eliminar el proveedor porque tiene compras registradas.', 1;

        DELETE FROM proveedores WHERE id_proveedor = @id_proveedor;

        COMMIT TRANSACTION;
        SELECT @id_proveedor AS id_proveedor, 'Proveedor eliminado correctamente.' AS mensaje;

    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        SELECT ERROR_NUMBER() AS codigo_error, ERROR_MESSAGE() AS mensaje;
    END CATCH
END
GO

-- ============================================================
-- SECCIÓN 7: STORED PROCEDURES - COMPRAS
-- ============================================================

IF OBJECT_ID('dbo.sp_registrar_compra_proveedor', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_registrar_compra_proveedor;
GO

CREATE PROCEDURE dbo.sp_registrar_compra_proveedor
    @id_proveedor INT,
    @fecha_compra DATE         = NULL,
    @productos    NVARCHAR(MAX),
    @monto_total  DECIMAL(18,2),
    @estado_pago  NVARCHAR(20) = 'Pendiente',
    @notas        NVARCHAR(500)= NULL,
    @usuario      NVARCHAR(80) = 'sistema'
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;

        IF NOT EXISTS (SELECT 1 FROM proveedores WHERE id_proveedor = @id_proveedor AND estado = 'Activo')
            THROW 50060, 'El proveedor no existe o está inactivo.', 1;

        IF NULLIF(LTRIM(RTRIM(@productos)), '') IS NULL
            THROW 50061, 'El campo productos es obligatorio.', 1;

        IF @monto_total <= 0
            THROW 50062, 'El monto total debe ser mayor a cero.', 1;

        IF @estado_pago NOT IN ('Pagado','Pendiente')
            THROW 50063, 'Estado de pago inválido.', 1;

        INSERT INTO compras_proveedor (
            id_proveedor, fecha_compra, productos,
            monto_total, estado_pago, notas, usuario_creacion
        )
        VALUES (
            @id_proveedor,
            ISNULL(@fecha_compra, CAST(GETDATE() AS DATE)),
            LTRIM(RTRIM(@productos)),
            @monto_total, @estado_pago, @notas, @usuario
        );

        COMMIT TRANSACTION;
        SELECT SCOPE_IDENTITY() AS id_compra, 'Compra registrada exitosamente.' AS mensaje;

    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        SELECT ERROR_NUMBER() AS codigo_error, ERROR_MESSAGE() AS mensaje;
    END CATCH
END
GO

-- ============================================================
-- SECCIÓN 8: STORED PROCEDURES - EMPLEADOS
-- ============================================================

IF OBJECT_ID('dbo.sp_registrar_empleado', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_registrar_empleado;
GO

CREATE PROCEDURE dbo.sp_registrar_empleado
    @numero_empleado  NVARCHAR(30),
    @dpi              NVARCHAR(20),
    @nombre_completo  NVARCHAR(200),
    @cargo            NVARCHAR(100) = NULL,
    @id_dependencia   INT           = NULL,
    @fecha_nacimiento DATE          = NULL,
    @correo           NVARCHAR(150) = NULL,
    @telefono         NVARCHAR(30)  = NULL,
    @direccion        NVARCHAR(255) = NULL,
    @usuario          NVARCHAR(80)  = 'sistema'
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;

        IF NULLIF(LTRIM(RTRIM(@numero_empleado)), '') IS NULL
            THROW 50070, 'El número de empleado es obligatorio.', 1;

        IF NULLIF(LTRIM(RTRIM(@dpi)), '') IS NULL
            THROW 50071, 'El DPI es obligatorio.', 1;

        IF NULLIF(LTRIM(RTRIM(@nombre_completo)), '') IS NULL
            THROW 50072, 'El nombre completo es obligatorio.', 1;

        IF EXISTS (SELECT 1 FROM empleados WHERE numero_empleado = @numero_empleado)
            THROW 50073, 'Ya existe un empleado con este número.', 1;

        IF EXISTS (SELECT 1 FROM empleados WHERE dpi = @dpi)
            THROW 50074, 'Ya existe un empleado con este DPI.', 1;

        IF @id_dependencia IS NOT NULL
            AND NOT EXISTS (SELECT 1 FROM dependencias WHERE id_dependencia = @id_dependencia AND estado = 'Activo')
            THROW 50075, 'La dependencia no existe o está inactiva.', 1;

        IF @correo IS NOT NULL AND dbo.fn_validar_correo(@correo) = 0
            THROW 50005, 'El formato del correo no es válido.', 1;

        INSERT INTO empleados (
            numero_empleado, dpi, nombre_completo, cargo,
            id_dependencia, fecha_nacimiento, correo,
            telefono, direccion, usuario_creacion
        )
        VALUES (
            LTRIM(RTRIM(@numero_empleado)), LTRIM(RTRIM(@dpi)),
            LTRIM(RTRIM(@nombre_completo)), @cargo,
            @id_dependencia, @fecha_nacimiento, @correo,
            @telefono, @direccion, @usuario
        );

        DECLARE @nuevo_id INT = SCOPE_IDENTITY();

        -- Registrar en historial si tiene dependencia inicial
        IF @id_dependencia IS NOT NULL
            INSERT INTO historial_dependencia (
                id_empleado, id_dependencia_origen, id_dependencia_destino,
                motivo, usuario, usuario_creacion
            )
            VALUES (@nuevo_id, NULL, @id_dependencia, 'Asignación inicial', @usuario, @usuario);

        COMMIT TRANSACTION;
        SELECT @nuevo_id AS id_empleado, 'Empleado registrado exitosamente.' AS mensaje;

    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        SELECT ERROR_NUMBER() AS codigo_error, ERROR_MESSAGE() AS mensaje;
    END CATCH
END
GO

IF OBJECT_ID('dbo.sp_actualizar_empleado', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_actualizar_empleado;
GO

CREATE PROCEDURE dbo.sp_actualizar_empleado
    @id_empleado      INT,
    @nombre_completo  NVARCHAR(200),
    @cargo            NVARCHAR(100) = NULL,
    @fecha_nacimiento DATE          = NULL,
    @correo           NVARCHAR(150) = NULL,
    @telefono         NVARCHAR(30)  = NULL,
    @direccion        NVARCHAR(255) = NULL,
    @estado           NVARCHAR(20)  = 'Activo',
    @usuario          NVARCHAR(80)  = 'sistema'
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;

        IF NOT EXISTS (SELECT 1 FROM empleados WHERE id_empleado = @id_empleado)
            THROW 50080, 'El empleado no existe.', 1;

        IF @correo IS NOT NULL AND dbo.fn_validar_correo(@correo) = 0
            THROW 50005, 'El formato del correo no es válido.', 1;

        UPDATE empleados SET
            nombre_completo      = LTRIM(RTRIM(@nombre_completo)),
            cargo                = @cargo,
            fecha_nacimiento     = @fecha_nacimiento,
            correo               = @correo,
            telefono             = @telefono,
            direccion            = @direccion,
            estado               = @estado,
            fecha_modificacion   = GETDATE(),
            usuario_modificacion = @usuario
        WHERE id_empleado = @id_empleado;

        COMMIT TRANSACTION;
        SELECT @id_empleado AS id_empleado, 'Empleado actualizado exitosamente.' AS mensaje;

    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        SELECT ERROR_NUMBER() AS codigo_error, ERROR_MESSAGE() AS mensaje;
    END CATCH
END
GO

-- ------------------------------------------------------------
-- sp_reasignar_dependencia
-- ------------------------------------------------------------
IF OBJECT_ID('dbo.sp_reasignar_dependencia', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_reasignar_dependencia;
GO

CREATE PROCEDURE dbo.sp_reasignar_dependencia
    @id_empleado          INT,
    @id_dependencia_nueva INT,
    @motivo               NVARCHAR(500),
    @usuario              NVARCHAR(80) = 'sistema'
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;

        DECLARE @dep_actual INT;
        SELECT @dep_actual = id_dependencia
        FROM empleados WHERE id_empleado = @id_empleado;

        IF @dep_actual IS NULL AND NOT EXISTS (SELECT 1 FROM empleados WHERE id_empleado = @id_empleado)
            THROW 50080, 'El empleado no existe.', 1;

        IF @dep_actual = @id_dependencia_nueva
            THROW 50090, 'El empleado ya pertenece a esta dependencia.', 1;

        IF NOT EXISTS (SELECT 1 FROM dependencias WHERE id_dependencia = @id_dependencia_nueva AND estado = 'Activo')
            THROW 50091, 'La dependencia destino no existe o está inactiva.', 1;

        IF NULLIF(LTRIM(RTRIM(@motivo)), '') IS NULL
            THROW 50092, 'El motivo de reasignación es obligatorio.', 1;

        -- Actualizar empleado
        UPDATE empleados SET
            id_dependencia       = @id_dependencia_nueva,
            fecha_modificacion   = GETDATE(),
            usuario_modificacion = @usuario
        WHERE id_empleado = @id_empleado;

        -- Registrar en historial
        INSERT INTO historial_dependencia (
            id_empleado, id_dependencia_origen, id_dependencia_destino,
            motivo, usuario, usuario_creacion
        )
        VALUES (
            @id_empleado, @dep_actual, @id_dependencia_nueva,
            LTRIM(RTRIM(@motivo)), @usuario, @usuario
        );

        COMMIT TRANSACTION;
        SELECT @id_empleado AS id_empleado, 'Reasignación de dependencia registrada.' AS mensaje;

    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        SELECT ERROR_NUMBER() AS codigo_error, ERROR_MESSAGE() AS mensaje;
    END CATCH
END
GO

-- ============================================================
-- SECCIÓN 9: STORED PROCEDURE - FELICITACIONES
-- ============================================================

IF OBJECT_ID('dbo.sp_verificar_felicitaciones_diarias', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_verificar_felicitaciones_diarias;
GO

CREATE PROCEDURE dbo.sp_verificar_felicitaciones_diarias
    @usuario NVARCHAR(80) = 'sistema'
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;

        DECLARE @hoy DATE = CAST(GETDATE() AS DATE);
        DECLARE @mes INT  = MONTH(@hoy);
        DECLARE @dia INT  = DAY(@hoy);
        DECLARE @contador INT = 0;

        -- Cumpleaños clientes
        INSERT INTO registro_felicitaciones (
            id_cliente, tipo_felicitacion, fecha_envio,
            estado, mensaje, usuario_creacion
        )
        SELECT
            c.id_cliente,
            'Cumpleaños',
            @hoy,
            'Enviado',
            '¡Feliz cumpleaños, ' + c.nombre_razon_social + '!',
            @usuario
        FROM clientes c
        WHERE
            c.estado = 'Activo'
            AND c.fecha_nacimiento IS NOT NULL
            AND MONTH(c.fecha_nacimiento) = @mes
            AND DAY(c.fecha_nacimiento)   = @dia
            AND NOT EXISTS (
                SELECT 1 FROM registro_felicitaciones rf
                WHERE rf.id_cliente         = c.id_cliente
                  AND rf.tipo_felicitacion  = 'Cumpleaños'
                  AND rf.fecha_envio        = @hoy
            );

        SET @contador = @contador + @@ROWCOUNT;

        -- Cumpleaños empleados
        INSERT INTO registro_felicitaciones (
            id_empleado, tipo_felicitacion, fecha_envio,
            estado, mensaje, usuario_creacion
        )
        SELECT
            e.id_empleado,
            'Cumpleaños',
            @hoy,
            'Enviado',
            '¡Feliz cumpleaños, ' + e.nombre_completo + '!',
            @usuario
        FROM empleados e
        WHERE
            e.estado = 'Activo'
            AND e.fecha_nacimiento IS NOT NULL
            AND MONTH(e.fecha_nacimiento) = @mes
            AND DAY(e.fecha_nacimiento)   = @dia
            AND NOT EXISTS (
                SELECT 1 FROM registro_felicitaciones rf
                WHERE rf.id_empleado         = e.id_empleado
                  AND rf.tipo_felicitacion   = 'Cumpleaños'
                  AND rf.fecha_envio         = @hoy
            );

        SET @contador = @contador + @@ROWCOUNT;

        COMMIT TRANSACTION;
        SELECT @contador AS felicitaciones_enviadas,
               'Proceso de felicitaciones completado.' AS mensaje;

    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        SELECT ERROR_NUMBER() AS codigo_error, ERROR_MESSAGE() AS mensaje;
    END CATCH
END
GO

-- ============================================================
-- SECCIÓN 10: TRIGGERS
-- ============================================================

-- Trigger: actualizar fecha_modificacion en clientes
IF OBJECT_ID('dbo.trg_clientes_update', 'TR') IS NOT NULL
    DROP TRIGGER dbo.trg_clientes_update;
GO

CREATE TRIGGER dbo.trg_clientes_update
ON clientes
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE clientes
    SET fecha_modificacion = GETDATE()
    WHERE id_cliente IN (SELECT id_cliente FROM inserted);
END
GO

-- Trigger: actualizar fecha_modificacion en proveedores
IF OBJECT_ID('dbo.trg_proveedores_update', 'TR') IS NOT NULL
    DROP TRIGGER dbo.trg_proveedores_update;
GO

CREATE TRIGGER dbo.trg_proveedores_update
ON proveedores
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE proveedores
    SET fecha_modificacion = GETDATE()
    WHERE id_proveedor IN (SELECT id_proveedor FROM inserted);
END
GO

-- Trigger: actualizar fecha_modificacion en empleados
IF OBJECT_ID('dbo.trg_empleados_update', 'TR') IS NOT NULL
    DROP TRIGGER dbo.trg_empleados_update;
GO

CREATE TRIGGER dbo.trg_empleados_update
ON empleados
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE empleados
    SET fecha_modificacion = GETDATE()
    WHERE id_empleado IN (SELECT id_empleado FROM inserted);
END
GO

-- ============================================================
-- SECCIÓN 11: DATOS INICIALES
-- ============================================================

-- Categorías de proveedor
IF NOT EXISTS (SELECT TOP 1 * FROM categorias_proveedor)
BEGIN
    INSERT INTO categorias_proveedor (nombre_categoria, descripcion, usuario_creacion)
    VALUES
        ('Tecnología',   'Equipos, software y servicios tecnológicos', 'sistema'),
        ('Papelería',    'Útiles de oficina y papelería',               'sistema'),
        ('Logística',    'Transporte y distribución',                   'sistema'),
        ('Servicios',    'Servicios profesionales y consultoría',       'sistema'),
        ('Alimentación', 'Productos alimenticios',                      'sistema'),
        ('Otros',        'Categoría general',                           'sistema');
    PRINT '>>> Categorías de proveedor insertadas.';
END
GO

-- Dependencias
IF NOT EXISTS (SELECT TOP 1 * FROM dependencias)
BEGIN
    INSERT INTO dependencias (nombre_dependencia, usuario_creacion)
    VALUES
        ('Gerencia General',    'sistema'),
        ('Recursos Humanos',    'sistema'),
        ('Tecnología',          'sistema'),
        ('Contabilidad',        'sistema'),
        ('Ventas',              'sistema'),
        ('Logística',           'sistema');
    PRINT '>>> Dependencias insertadas.';
END
GO

-- Usuario administrador
IF NOT EXISTS (SELECT * FROM usuarios WHERE username = 'admin')
BEGIN
    INSERT INTO usuarios (nombre, email, username, password_hash, rol, usuario_creacion)
    VALUES (
        'Administrador',
        'admin@crm.com',
        'admin',
        '$2b$12$rIo8uK9cgE/P5hgJ.20BEO7I0WmLVr7z.D3.TQ33YiwjA5GlrkGcm',
        'admin',
        'sistema'
    );
    PRINT '>>> Usuario admin creado (password: admin123).';
END
GO

-- Datos de ejemplo - Clientes
IF NOT EXISTS (SELECT TOP 1 * FROM clientes)
BEGIN
    EXEC sp_registrar_cliente
        @nombre_razon_social = 'Juan Carlos Pérez',
        @documento_identificacion = '1234567890',
        @tipo = 'Cliente',
        @fecha_nacimiento = NULL,
        @correo = 'juan.perez@email.com',
        @notificacion_email = 1;

    EXEC sp_registrar_cliente
        @nombre_razon_social = 'Empresa ABC S.A.S',
        @documento_identificacion = '900123456',
        @tipo = 'Cliente',
        @correo = 'info@abc.com',
        @notificacion_email = 1,
        @notificacion_sms = 1;

    EXEC sp_registrar_cliente
        @nombre_razon_social = 'María López Torres',
        @documento_identificacion = '0987654321',
        @tipo = 'Prospecto',
        @correo = 'maria.lopez@gmail.com';

    PRINT '>>> Clientes de ejemplo insertados.';
END
GO

-- Datos de ejemplo - Proveedores
IF NOT EXISTS (SELECT TOP 1 * FROM proveedores)
BEGIN
    EXEC sp_registrar_proveedor
        @nombre_empresa = 'TechCorp Colombia',
        @nit = '900111222-1',
        @id_categoria = 1,
        @telefono = '6015551234',
        @correo = 'ventas@techcorp.co',
        @direccion = 'Av. El Dorado 92-32, Bogotá',
        @notas = 'Proveedor principal de equipos';

    EXEC sp_registrar_proveedor
        @nombre_empresa = 'Papelería Central',
        @nit = '800333444-5',
        @id_categoria = 2,
        @telefono = '6015555678',
        @correo = 'info@papelcentral.com';

    PRINT '>>> Proveedores de ejemplo insertados.';
END
GO

-- ============================================================
-- SECCIÓN 12: EJEMPLOS DE EJECUCIÓN
-- ============================================================

/*
-- Registrar cliente
EXEC sp_registrar_cliente
    @nombre_razon_social = 'Pedro Ramírez',
    @documento_identificacion = '5566778899',
    @tipo = 'Cliente',
    @correo = 'pedro@email.com',
    @usuario = 'admin';

-- Actualizar cliente
EXEC sp_actualizar_cliente
    @id_cliente = 1,
    @nombre_razon_social = 'Juan Carlos Pérez Gómez',
    @documento_identificacion = '1234567890',
    @tipo = 'Cliente',
    @estado = 'Activo',
    @usuario = 'admin';

-- Inactivar cliente
EXEC sp_inactivar_cliente @id_cliente = 1, @usuario = 'admin';

-- Agregar contacto
EXEC sp_agregar_contacto
    @id_cliente = 1,
    @nombre_contacto = 'Asistente',
    @tipo_contacto = 'Teléfono',
    @descripcion = '3001234567',
    @usuario = 'admin';

-- Registrar proveedor
EXEC sp_registrar_proveedor
    @nombre_empresa = 'Logística Express',
    @nit = '700999888-3',
    @id_categoria = 3,
    @telefono = '3105559999',
    @usuario = 'admin';

-- Registrar compra
EXEC sp_registrar_compra_proveedor
    @id_proveedor = 1,
    @productos = 'Laptops x5, Mouse x10',
    @monto_total = 15000000,
    @estado_pago = 'Pendiente',
    @usuario = 'admin';

-- Registrar empleado
EXEC sp_registrar_empleado
    @numero_empleado = 'EMP-001',
    @dpi = '1234567890101',
    @nombre_completo = 'Ana Sofía García',
    @cargo = 'Desarrolladora',
    @id_dependencia = 3,
    @fecha_nacimiento = '1995-06-15',
    @correo = 'ana.garcia@empresa.com',
    @usuario = 'admin';

-- Reasignar dependencia
EXEC sp_reasignar_dependencia
    @id_empleado = 1,
    @id_dependencia_nueva = 2,
    @motivo = 'Ascenso al área de RRHH',
    @usuario = 'admin';

-- Verificar felicitaciones del día
EXEC sp_verificar_felicitaciones_diarias @usuario = 'sistema';
*/

PRINT '============================================================';
PRINT 'CRM Ing Software - Base de datos completada exitosamente.';
PRINT 'Tablas: 10 | SPs: 17 | Triggers: 3 | Funciones: 2';
PRINT '============================================================';
GO

-- ============================================================
-- SECCIÓN 13: STORED PROCEDURES - GESTIÓN DE USUARIOS (v3)
-- ============================================================

-- SP: Crear usuario
IF OBJECT_ID('dbo.sp_crear_usuario', 'P') IS NOT NULL DROP PROCEDURE dbo.sp_crear_usuario;
GO
CREATE PROCEDURE dbo.sp_crear_usuario
    @nombre    NVARCHAR(150), @email NVARCHAR(150), @username NVARCHAR(80),
    @password_hash NVARCHAR(255), @rol NVARCHAR(30) = 'usuario', @usuario NVARCHAR(80) = 'sistema'
AS BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;
        IF NULLIF(LTRIM(RTRIM(@nombre)),'')    IS NULL THROW 50070,'El nombre es obligatorio.',1;
        IF NULLIF(LTRIM(RTRIM(@username)),'')  IS NULL THROW 50071,'El nombre de usuario es obligatorio.',1;
        IF NULLIF(LTRIM(RTRIM(@password_hash)),'') IS NULL THROW 50072,'La contraseña es obligatoria.',1;
        IF @rol NOT IN ('admin','usuario')          THROW 50073,'El rol debe ser admin o usuario.',1;
        IF EXISTS (SELECT 1 FROM usuarios WHERE username = @username)
            THROW 50074,'Ya existe un usuario con ese nombre de usuario.',1;
        IF @email IS NOT NULL AND @email!='' AND EXISTS (SELECT 1 FROM usuarios WHERE email=@email)
            THROW 50075,'Ya existe un usuario con ese correo electrónico.',1;
        INSERT INTO usuarios (nombre,email,username,password_hash,rol,estado,usuario_creacion)
        VALUES (LTRIM(RTRIM(@nombre)),NULLIF(LTRIM(RTRIM(@email)),''),LTRIM(RTRIM(@username)),
                @password_hash,@rol,'Activo',@usuario);
        COMMIT TRANSACTION;
        SELECT SCOPE_IDENTITY() AS id_usuario,'Usuario creado correctamente.' AS mensaje;
    END TRY BEGIN CATCH
        IF @@TRANCOUNT>0 ROLLBACK TRANSACTION;
        SELECT ERROR_NUMBER() AS codigo_error, ERROR_MESSAGE() AS mensaje;
    END CATCH
END
GO

-- SP: Actualizar usuario
IF OBJECT_ID('dbo.sp_actualizar_usuario','P') IS NOT NULL DROP PROCEDURE dbo.sp_actualizar_usuario;
GO
CREATE PROCEDURE dbo.sp_actualizar_usuario
    @id_usuario INT, @nombre NVARCHAR(150), @email NVARCHAR(150)=NULL,
    @rol NVARCHAR(30)=NULL, @usuario NVARCHAR(80)='sistema'
AS BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;
        IF NOT EXISTS (SELECT 1 FROM usuarios WHERE id_usuario=@id_usuario) THROW 50076,'El usuario no existe.',1;
        IF NULLIF(LTRIM(RTRIM(@nombre)),'') IS NULL THROW 50070,'El nombre es obligatorio.',1;
        IF @rol IS NOT NULL AND @rol NOT IN ('admin','usuario') THROW 50073,'El rol debe ser admin o usuario.',1;
        IF @email IS NOT NULL AND @email!='' AND EXISTS (SELECT 1 FROM usuarios WHERE email=@email AND id_usuario<>@id_usuario)
            THROW 50075,'Ya existe un usuario con ese correo electrónico.',1;
        UPDATE usuarios SET nombre=LTRIM(RTRIM(@nombre)),email=NULLIF(LTRIM(RTRIM(ISNULL(@email,''))),''),
            rol=ISNULL(@rol,rol),fecha_modificacion=GETDATE(),usuario_modificacion=@usuario
        WHERE id_usuario=@id_usuario;
        COMMIT TRANSACTION;
        SELECT @id_usuario AS id_usuario,'Usuario actualizado correctamente.' AS mensaje;
    END TRY BEGIN CATCH
        IF @@TRANCOUNT>0 ROLLBACK TRANSACTION;
        SELECT ERROR_NUMBER() AS codigo_error, ERROR_MESSAGE() AS mensaje;
    END CATCH
END
GO

-- SP: Cambiar contraseña
IF OBJECT_ID('dbo.sp_cambiar_password_usuario','P') IS NOT NULL DROP PROCEDURE dbo.sp_cambiar_password_usuario;
GO
CREATE PROCEDURE dbo.sp_cambiar_password_usuario
    @id_usuario INT, @password_hash NVARCHAR(255), @usuario NVARCHAR(80)='sistema'
AS BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;
        IF NOT EXISTS (SELECT 1 FROM usuarios WHERE id_usuario=@id_usuario) THROW 50076,'El usuario no existe.',1;
        IF NULLIF(LTRIM(RTRIM(@password_hash)),'') IS NULL THROW 50072,'La nueva contraseña es obligatoria.',1;
        UPDATE usuarios SET password_hash=@password_hash,fecha_modificacion=GETDATE(),
            usuario_modificacion=@usuario WHERE id_usuario=@id_usuario;
        COMMIT TRANSACTION;
        SELECT @id_usuario AS id_usuario,'Contraseña actualizada correctamente.' AS mensaje;
    END TRY BEGIN CATCH
        IF @@TRANCOUNT>0 ROLLBACK TRANSACTION;
        SELECT ERROR_NUMBER() AS codigo_error, ERROR_MESSAGE() AS mensaje;
    END CATCH
END
GO

-- SP: Desactivar usuario (soft delete)
IF OBJECT_ID('dbo.sp_desactivar_usuario','P') IS NOT NULL DROP PROCEDURE dbo.sp_desactivar_usuario;
GO
CREATE PROCEDURE dbo.sp_desactivar_usuario
    @id_usuario INT, @usuario NVARCHAR(80)='sistema'
AS BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;
        IF NOT EXISTS (SELECT 1 FROM usuarios WHERE id_usuario=@id_usuario) THROW 50076,'El usuario no existe.',1;
        IF (SELECT COUNT(*) FROM usuarios WHERE rol='admin' AND estado='Activo')=1
           AND EXISTS (SELECT 1 FROM usuarios WHERE id_usuario=@id_usuario AND rol='admin')
            THROW 50077,'No se puede desactivar el único administrador activo del sistema.',1;
        IF (SELECT username FROM usuarios WHERE id_usuario=@id_usuario)=@usuario
            THROW 50078,'No puedes desactivar tu propia cuenta.',1;
        UPDATE usuarios SET estado='Inactivo',fecha_modificacion=GETDATE(),
            usuario_modificacion=@usuario WHERE id_usuario=@id_usuario;
        COMMIT TRANSACTION;
        SELECT @id_usuario AS id_usuario,'Usuario desactivado correctamente.' AS mensaje;
    END TRY BEGIN CATCH
        IF @@TRANCOUNT>0 ROLLBACK TRANSACTION;
        SELECT ERROR_NUMBER() AS codigo_error, ERROR_MESSAGE() AS mensaje;
    END CATCH
END
GO

-- SP: Reactivar usuario
IF OBJECT_ID('dbo.sp_reactivar_usuario','P') IS NOT NULL DROP PROCEDURE dbo.sp_reactivar_usuario;
GO
CREATE PROCEDURE dbo.sp_reactivar_usuario
    @id_usuario INT, @usuario NVARCHAR(80)='sistema'
AS BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;
        IF NOT EXISTS (SELECT 1 FROM usuarios WHERE id_usuario=@id_usuario) THROW 50076,'El usuario no existe.',1;
        UPDATE usuarios SET estado='Activo',fecha_modificacion=GETDATE(),
            usuario_modificacion=@usuario WHERE id_usuario=@id_usuario;
        COMMIT TRANSACTION;
        SELECT @id_usuario AS id_usuario,'Reactivado correctamente.' AS mensaje;
    END TRY BEGIN CATCH
        IF @@TRANCOUNT>0 ROLLBACK TRANSACTION;
        SELECT ERROR_NUMBER() AS codigo_error, ERROR_MESSAGE() AS mensaje;
    END CATCH
END
GO
PRINT '>>> SPs de Gestión de Usuarios (v3) creados correctamente.';
GO
