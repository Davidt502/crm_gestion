-- ============================================================
-- CRM Ing Software - Script completo de Base de Datos
-- Motor: SQL Server
-- ============================================================

USE master;
GO

IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'crm_ing_software')
BEGIN
    CREATE DATABASE crm_ing_software;
    PRINT 'Base de datos creada exitosamente.';
END
ELSE
    PRINT 'La base de datos ya existe.';
GO

USE crm_ing_software;
GO

-- ============================================================
-- Tabla: usuarios
-- ============================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'usuarios')
BEGIN
    CREATE TABLE usuarios (
        id_usuario      INT IDENTITY(1,1) PRIMARY KEY,
        nombre          NVARCHAR(150)   NOT NULL,
        email           NVARCHAR(150)   NOT NULL UNIQUE,
        username        NVARCHAR(80)    NOT NULL UNIQUE,
        password_hash   NVARCHAR(255)   NOT NULL,
        rol             NVARCHAR(30)    NOT NULL DEFAULT 'usuario' CHECK (rol IN ('admin','usuario')),
        estado          NVARCHAR(20)    NOT NULL DEFAULT 'Activo' CHECK (estado IN ('Activo','Inactivo')),
        fecha_creacion  DATETIME        NOT NULL DEFAULT GETDATE(),
        ultimo_acceso   DATETIME        NULL
    );
    PRINT 'Tabla usuarios creada.';
END
GO

-- ============================================================
-- Tabla: clientes
-- ============================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'clientes')
BEGIN
    CREATE TABLE clientes (
        id_cliente               INT IDENTITY(1,1) PRIMARY KEY,
        nombre_razon_social      NVARCHAR(255)  NOT NULL,
        documento_identificacion NVARCHAR(50)   NOT NULL UNIQUE,
        tipo                     NVARCHAR(20)   NOT NULL CHECK (tipo IN ('Cliente','Prospecto')),
        estado                   NVARCHAR(20)   NOT NULL DEFAULT 'Activo' CHECK (estado IN ('Activo','Inactivo')),
        fecha_nacimiento         DATE           NULL,
        notificacion_email       BIT            NOT NULL DEFAULT 0,
        notificacion_sms         BIT            NOT NULL DEFAULT 0,
        fecha_creacion           DATETIME       NOT NULL DEFAULT GETDATE()
    );
    PRINT 'Tabla clientes creada.';
END
GO

-- ============================================================
-- Tabla: contactos_cliente
-- ============================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'contactos_cliente')
BEGIN
    CREATE TABLE contactos_cliente (
        id_contacto   INT IDENTITY(1,1) PRIMARY KEY,
        id_cliente    INT            NOT NULL FOREIGN KEY REFERENCES clientes(id_cliente),
        tipo_contacto NVARCHAR(50)   NOT NULL CHECK (tipo_contacto IN ('Teléfono','Dirección','Fax','Email','Celular')),
        descripcion   NVARCHAR(255)  NOT NULL,
        estado        NVARCHAR(20)   NOT NULL DEFAULT 'Activo' CHECK (estado IN ('Activo','Inactivo'))
    );
    PRINT 'Tabla contactos_cliente creada.';
END
GO

-- ============================================================
-- Tabla: proveedores
-- ============================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'proveedores')
BEGIN
    CREATE TABLE proveedores (
        id_proveedor        INT IDENTITY(1,1) PRIMARY KEY,
        nombre_empresa      NVARCHAR(255)  NOT NULL,
        nit                 NVARCHAR(50)   NOT NULL UNIQUE,
        contacto            NVARCHAR(150)  NULL,
        telefono            NVARCHAR(50)   NOT NULL,
        correo              NVARCHAR(150)  NULL,
        direccion           NVARCHAR(255)  NULL,
        categoria           NVARCHAR(50)   NOT NULL CHECK (categoria IN ('Tecnología','Papelería','Logística','Servicios','Alimentación','Otros')),
        notas               NVARCHAR(MAX)  NULL,
        estado              NVARCHAR(20)   NOT NULL DEFAULT 'Activo' CHECK (estado IN ('Activo','Inactivo')),
        motivo_inactivacion NVARCHAR(MAX)  NULL,
        fecha_creacion      DATETIME       NOT NULL DEFAULT GETDATE()
    );
    PRINT 'Tabla proveedores creada.';
END
GO

-- ============================================================
-- Usuario administrador por defecto
-- password: admin123  (hash bcrypt)
-- ============================================================
IF NOT EXISTS (SELECT * FROM usuarios WHERE username = 'admin')
BEGIN
    INSERT INTO usuarios (nombre, email, username, password_hash, rol, estado)
    VALUES (
        'Administrador',
        'admin@crm.com',
        'admin',
        '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4oEqGEhZNa',
        'admin',
        'Activo'
    );
    PRINT 'Usuario admin creado (password: admin123).';
END
GO

-- ============================================================
-- Datos de ejemplo - Clientes
-- ============================================================
IF NOT EXISTS (SELECT TOP 1 * FROM clientes)
BEGIN
    INSERT INTO clientes (nombre_razon_social, documento_identificacion, tipo, estado, fecha_nacimiento, notificacion_email, notificacion_sms)
    VALUES
        ('Juan Carlos Pérez',    '1234567890', 'Cliente',   'Activo',   DATEFROMPARTS(YEAR(GETDATE()), MONTH(GETDATE()), 15), 1, 0),
        ('Empresa ABC S.A.S',    '900123456',  'Cliente',   'Activo',   NULL, 1, 1),
        ('María López Torres',   '0987654321', 'Prospecto', 'Activo',   DATEFROMPARTS(YEAR(GETDATE()), MONTH(GETDATE()), 22), 0, 1),
        ('Tech Solutions Ltda',  '800456789',  'Cliente',   'Inactivo', NULL, 0, 0),
        ('Roberto Díaz',         '1122334455', 'Prospecto', 'Activo',   DATEFROMPARTS(YEAR(GETDATE()), MONTH(GETDATE()), 5),  1, 0);

    INSERT INTO contactos_cliente (id_cliente, tipo_contacto, descripcion, estado)
    VALUES
        (1, 'Teléfono',  '3001234567',              'Activo'),
        (1, 'Email',     'juan.perez@email.com',     'Activo'),
        (2, 'Teléfono',  '6011234567',              'Activo'),
        (2, 'Dirección', 'Calle 100 # 15-20, Bogotá','Activo'),
        (3, 'Celular',   '3209876543',              'Activo');

    PRINT 'Datos de ejemplo clientes insertados.';
END
GO

-- ============================================================
-- Datos de ejemplo - Proveedores
-- ============================================================
IF NOT EXISTS (SELECT TOP 1 * FROM proveedores)
BEGIN
    INSERT INTO proveedores (nombre_empresa, nit, contacto, telefono, correo, direccion, categoria, notas, estado)
    VALUES
        ('TechCorp Colombia',  '900111222-1', 'Carlos Ruiz',  '6015551234', 'ventas@techcorp.co',    'Av. El Dorado 92-32', 'Tecnología',  'Proveedor principal de equipos', 'Activo'),
        ('Papelería Central',  '800333444-5', 'Ana Gómez',    '6015555678', 'info@papelcentral.com', 'Calle 72 # 10-15',    'Papelería',   NULL,                            'Activo'),
        ('LogisTrans S.A.S',   '900555666-3', 'Pedro Mora',   '3154449876', 'logistrans@mail.com',   'Zona Industrial',     'Logística',   'Transporte nacional',           'Inactivo'),
        ('Alimentos Frescos',  '700777888-0', 'Lucy Vargas',  '3178887654', 'frescos@ali.com',       'Mercado Central',     'Alimentación', NULL,                           'Activo');

    PRINT 'Datos de ejemplo proveedores insertados.';
END
GO

PRINT '============================================================';
PRINT 'Base de datos crm_ing_software lista correctamente.';
PRINT '============================================================';
