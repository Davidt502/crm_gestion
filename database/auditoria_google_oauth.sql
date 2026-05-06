-- ============================================================
-- CRM ING SOFTWARE - Módulo: Auditoría + Google OAuth + APIs Públicas
-- Ejecutar DESPUÉS de script_completo.sql
-- ============================================================

USE crm_ing_software;
GO

-- ─────────────────────────────────────────────────────────────
-- EXTENSIÓN tabla usuarios: soporte Google OAuth
-- ─────────────────────────────────────────────────────────────
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('usuarios') AND name = 'google_id')
BEGIN
    ALTER TABLE usuarios ADD google_id      NVARCHAR(255) NULL;
    ALTER TABLE usuarios ADD google_email   NVARCHAR(150) NULL;
    ALTER TABLE usuarios ADD google_picture NVARCHAR(500) NULL;
    ALTER TABLE usuarios ADD auth_provider  NVARCHAR(20)  NOT NULL DEFAULT 'local'
        CONSTRAINT chk_auth_provider CHECK (auth_provider IN ('local','google'));
    -- Para usuarios Google la password_hash puede quedar vacía
    ALTER TABLE usuarios ALTER COLUMN password_hash NVARCHAR(255) NULL;
    PRINT '>>> Columnas Google OAuth agregadas a usuarios.';
END
GO

-- ─────────────────────────────────────────────────────────────
-- TABLA: grupos (para clasificar compañeros de trabajo)
-- ─────────────────────────────────────────────────────────────
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'grupos')
BEGIN
    CREATE TABLE grupos (
        id_grupo         INT IDENTITY(1,1) PRIMARY KEY,
        nombre_grupo     NVARCHAR(100) NOT NULL,
        descripcion      NVARCHAR(500) NULL,
        estado           NVARCHAR(20)  NOT NULL DEFAULT 'Activo'
                         CONSTRAINT chk_estado_grupo CHECK (estado IN ('Activo','Inactivo')),
        fecha_creacion   DATETIME      NOT NULL DEFAULT GETDATE(),
        usuario_creacion NVARCHAR(80)  NOT NULL DEFAULT 'sistema',
        CONSTRAINT uq_nombre_grupo UNIQUE (nombre_grupo)
    );
    PRINT '>>> Tabla grupos creada.';
END
GO

-- ─────────────────────────────────────────────────────────────
-- EXTENSIÓN tabla usuarios: campo grupo
-- ─────────────────────────────────────────────────────────────
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('usuarios') AND name = 'id_grupo')
BEGIN
    ALTER TABLE usuarios ADD id_grupo INT NULL
        CONSTRAINT fk_usuario_grupo FOREIGN KEY REFERENCES grupos(id_grupo);
    PRINT '>>> Campo id_grupo agregado a usuarios.';
END
GO

-- ─────────────────────────────────────────────────────────────
-- TABLA: api_tokens (tokens públicos para compartir APIs)
-- ─────────────────────────────────────────────────────────────
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'api_tokens')
BEGIN
    CREATE TABLE api_tokens (
        id_token         INT IDENTITY(1,1) PRIMARY KEY,
        nombre_token     NVARCHAR(100) NOT NULL,
        token            NVARCHAR(128) NOT NULL,
        descripcion      NVARCHAR(500) NULL,
        id_usuario       INT           NOT NULL,
        -- Endpoints permitidos: JSON array, ej: ["/api/clientes","/api/empleados"]
        endpoints_permitidos NVARCHAR(MAX) NOT NULL DEFAULT '[]',
        solo_lectura     BIT           NOT NULL DEFAULT 1,
        activo           BIT           NOT NULL DEFAULT 1,
        expira_en        DATETIME      NULL,  -- NULL = sin expiración
        total_usos       INT           NOT NULL DEFAULT 0,
        ultimo_uso       DATETIME      NULL,
        fecha_creacion   DATETIME      NOT NULL DEFAULT GETDATE(),
        usuario_creacion NVARCHAR(80)  NOT NULL DEFAULT 'sistema',
        CONSTRAINT uq_api_token UNIQUE (token),
        CONSTRAINT fk_apitoken_usuario FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario)
    );
    PRINT '>>> Tabla api_tokens creada.';
END
GO

-- ─────────────────────────────────────────────────────────────
-- TABLA: auditoria_accesos (log completo de quién entró y qué vio)
-- ─────────────────────────────────────────────────────────────
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'auditoria_accesos')
BEGIN
    CREATE TABLE auditoria_accesos (
        id_auditoria     INT IDENTITY(1,1) PRIMARY KEY,
        id_usuario       INT           NULL,  -- NULL = acceso por token público
        nombre_usuario   NVARCHAR(150) NULL,
        username         NVARCHAR(80)  NULL,
        grupo            NVARCHAR(100) NULL,
        ip_publica       NVARCHAR(50)  NOT NULL,
        user_agent       NVARCHAR(500) NULL,
        tipo_acceso      NVARCHAR(20)  NOT NULL DEFAULT 'web'
                         CONSTRAINT chk_tipo_acceso CHECK (tipo_acceso IN ('web','api_publica','api_interna')),
        id_token         INT           NULL,  -- referencia al token si es api_publica
        endpoint         NVARCHAR(255) NOT NULL,
        metodo_http      NVARCHAR(10)  NOT NULL,
        accion           NVARCHAR(50)  NOT NULL,  -- 'ver','buscar','crear','editar','eliminar','copiar','exportar','login','logout'
        recurso          NVARCHAR(100) NULL,       -- ej: 'clientes', 'empleados', 'proveedores'
        id_recurso       NVARCHAR(50)  NULL,       -- ID específico si aplica
        detalle          NVARCHAR(MAX) NULL,       -- JSON con parámetros / datos adicionales
        exitoso          BIT           NOT NULL DEFAULT 1,
        codigo_respuesta INT           NULL,
        fecha_hora       DATETIME      NOT NULL DEFAULT GETDATE(),
        CONSTRAINT fk_auditoria_usuario FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario),
        CONSTRAINT fk_auditoria_token   FOREIGN KEY (id_token)   REFERENCES api_tokens(id_token)
    );

    -- Índices para consultas rápidas de auditoría
    CREATE INDEX ix_audit_usuario    ON auditoria_accesos(id_usuario, fecha_hora DESC);
    CREATE INDEX ix_audit_ip         ON auditoria_accesos(ip_publica, fecha_hora DESC);
    CREATE INDEX ix_audit_fecha      ON auditoria_accesos(fecha_hora DESC);
    CREATE INDEX ix_audit_recurso    ON auditoria_accesos(recurso, fecha_hora DESC);
    CREATE INDEX ix_audit_token      ON auditoria_accesos(id_token, fecha_hora DESC);
    PRINT '>>> Tabla auditoria_accesos creada con índices.';
END
GO

-- ─────────────────────────────────────────────────────────────
-- DATOS: Grupos iniciales de ejemplo
-- ─────────────────────────────────────────────────────────────
IF NOT EXISTS (SELECT 1 FROM grupos)
BEGIN
    INSERT INTO grupos (nombre_grupo, descripcion, usuario_creacion) VALUES
        ('Administración',  'Personal administrativo y gerencia',        'sistema'),
        ('Tecnología',      'Equipo de sistemas y desarrollo',           'sistema'),
        ('Ventas',          'Equipo comercial y atención al cliente',    'sistema'),
        ('Contabilidad',    'Departamento financiero y contable',        'sistema'),
        ('Recursos Humanos','Gestión de personal y reclutamiento',       'sistema');
    PRINT '>>> Grupos iniciales insertados.';
END
GO

-- ─────────────────────────────────────────────────────────────
-- SP: Registrar evento de auditoría
-- ─────────────────────────────────────────────────────────────
IF OBJECT_ID('dbo.sp_registrar_auditoria', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_registrar_auditoria;
GO

CREATE PROCEDURE dbo.sp_registrar_auditoria
    @id_usuario    INT           = NULL,
    @nombre_usuario NVARCHAR(150) = NULL,
    @username      NVARCHAR(80)  = NULL,
    @grupo         NVARCHAR(100) = NULL,
    @ip_publica    NVARCHAR(50),
    @user_agent    NVARCHAR(500) = NULL,
    @tipo_acceso   NVARCHAR(20)  = 'web',
    @id_token      INT           = NULL,
    @endpoint      NVARCHAR(255),
    @metodo_http   NVARCHAR(10),
    @accion        NVARCHAR(50),
    @recurso       NVARCHAR(100) = NULL,
    @id_recurso    NVARCHAR(50)  = NULL,
    @detalle       NVARCHAR(MAX) = NULL,
    @exitoso       BIT           = 1,
    @codigo_respuesta INT        = NULL
AS
BEGIN
    SET NOCOUNT ON;
    INSERT INTO auditoria_accesos (
        id_usuario, nombre_usuario, username, grupo,
        ip_publica, user_agent, tipo_acceso, id_token,
        endpoint, metodo_http, accion, recurso, id_recurso,
        detalle, exitoso, codigo_respuesta
    ) VALUES (
        @id_usuario, @nombre_usuario, @username, @grupo,
        @ip_publica, @user_agent, @tipo_acceso, @id_token,
        @endpoint, @metodo_http, @accion, @recurso, @id_recurso,
        @detalle, @exitoso, @codigo_respuesta
    );
END
GO

PRINT '=== Módulo Auditoría + Google OAuth + APIs Públicas instalado correctamente ===';
GO
