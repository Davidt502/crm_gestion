-- ============================================================
-- CRM ING SOFTWARE - Base de Datos Empresarial Completa
-- PostgreSQL | Arquitectura 3FN | Stored Procedures | Triggers
-- ============================================================

-- Crear base de datos (ejecutar como superusuario)
-- CREATE DATABASE crm_ing_software;
-- \c crm_ing_software

-- ============================================================
-- SECCIÓN 1: TABLAS BASE
-- ============================================================

-- Tabla: usuarios (sistema de login)
CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario SERIAL PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    username VARCHAR(80) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    rol VARCHAR(30) NOT NULL DEFAULT 'usuario'
        CHECK (rol IN ('admin','usuario')),
    estado VARCHAR(20) NOT NULL DEFAULT 'Activo'
        CHECK (estado IN ('Activo','Inactivo')),
    ultimo_acceso TIMESTAMP NULL,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP NULL,
    usuario_creacion VARCHAR(80) NOT NULL DEFAULT 'sistema',
    usuario_modificacion VARCHAR(80) NULL
);

-- Tabla: dependencias
CREATE TABLE IF NOT EXISTS dependencias (
    id_dependencia SERIAL PRIMARY KEY,
    nombre_dependencia VARCHAR(150) NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'Activo'
        CHECK (estado IN ('Activo','Inactivo')),
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP NULL,
    usuario_creacion VARCHAR(80) NOT NULL DEFAULT 'sistema',
    usuario_modificacion VARCHAR(80) NULL
);

-- Tabla: empleados
CREATE TABLE IF NOT EXISTS empleados (
    id_empleado SERIAL PRIMARY KEY,
    numero_empleado VARCHAR(30) NOT NULL UNIQUE,
    dpi VARCHAR(20) NOT NULL UNIQUE,
    nombre_completo VARCHAR(200) NOT NULL,
    cargo VARCHAR(100) NULL,
    id_dependencia INTEGER NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'Activo'
        CHECK (estado IN ('Activo','Inactivo')),
    fecha_nacimiento DATE NULL,
    correo VARCHAR(150) NULL,
    telefono VARCHAR(30) NULL,
    direccion VARCHAR(255) NULL,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP NULL,
    usuario_creacion VARCHAR(80) NOT NULL DEFAULT 'sistema',
    usuario_modificacion VARCHAR(80) NULL,
    CONSTRAINT fk_empleado_dep FOREIGN KEY (id_dependencia) 
        REFERENCES dependencias(id_dependencia)
);

-- Tabla: historial_dependencia
CREATE TABLE IF NOT EXISTS historial_dependencia (
    id_historial SERIAL PRIMARY KEY,
    id_empleado INTEGER NOT NULL,
    id_dependencia_origen INTEGER NULL,
    id_dependencia_destino INTEGER NOT NULL,
    motivo VARCHAR(500) NULL,
    usuario VARCHAR(80) NOT NULL DEFAULT 'sistema',
    fecha_movimiento TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP NULL,
    usuario_creacion VARCHAR(80) NOT NULL DEFAULT 'sistema',
    usuario_modificacion VARCHAR(80) NULL,
    CONSTRAINT fk_hist_empleado FOREIGN KEY (id_empleado)
        REFERENCES empleados(id_empleado),
    CONSTRAINT fk_hist_dep_origen FOREIGN KEY (id_dependencia_origen)
        REFERENCES dependencias(id_dependencia),
    CONSTRAINT fk_hist_dep_destino FOREIGN KEY (id_dependencia_destino)
        REFERENCES dependencias(id_dependencia)
);

-- Tabla: clientes
CREATE TABLE IF NOT EXISTS clientes (
    id_cliente SERIAL PRIMARY KEY,
    nombre_razon_social VARCHAR(255) NOT NULL,
    documento_identificacion VARCHAR(50) NOT NULL UNIQUE,
    tipo VARCHAR(20) NOT NULL DEFAULT 'Cliente'
        CHECK (tipo IN ('Cliente','Prospecto')),
    estado VARCHAR(20) NOT NULL DEFAULT 'Activo'
        CHECK (estado IN ('Activo','Inactivo')),
    fecha_nacimiento DATE NULL,
    correo VARCHAR(150) NULL,
    notificacion_email BOOLEAN NOT NULL DEFAULT FALSE,
    notificacion_sms BOOLEAN NOT NULL DEFAULT FALSE,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP NULL,
    usuario_creacion VARCHAR(80) NOT NULL DEFAULT 'sistema',
    usuario_modificacion VARCHAR(80) NULL
);

-- Tabla: contactos_cliente
CREATE TABLE IF NOT EXISTS contactos_cliente (
    id_contacto SERIAL PRIMARY KEY,
    id_cliente INTEGER NOT NULL,
    nombre_contacto VARCHAR(150) NOT NULL,
    tipo_contacto VARCHAR(50) NOT NULL
        CHECK (tipo_contacto IN ('Teléfono','Dirección','Fax','Email','Celular')),
    descripcion VARCHAR(255) NOT NULL,
    correo VARCHAR(150) NULL,
    telefono VARCHAR(30) NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'Activo'
        CHECK (estado IN ('Activo','Inactivo')),
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP NULL,
    usuario_creacion VARCHAR(80) NOT NULL DEFAULT 'sistema',
    usuario_modificacion VARCHAR(80) NULL,
    CONSTRAINT fk_contacto_cliente FOREIGN KEY (id_cliente)
        REFERENCES clientes(id_cliente)
);

-- Tabla: categorias_proveedor
CREATE TABLE IF NOT EXISTS categorias_proveedor (
    id_categoria SERIAL PRIMARY KEY,
    nombre_categoria VARCHAR(100) NOT NULL UNIQUE,
    descripcion VARCHAR(255) NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'Activo'
        CHECK (estado IN ('Activo','Inactivo')),
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP NULL,
    usuario_creacion VARCHAR(80) NOT NULL DEFAULT 'sistema',
    usuario_modificacion VARCHAR(80) NULL
);

-- Tabla: proveedores
CREATE TABLE IF NOT EXISTS proveedores (
    id_proveedor SERIAL PRIMARY KEY,
    nombre_empresa VARCHAR(255) NOT NULL,
    nit VARCHAR(50) NOT NULL UNIQUE,
    id_categoria INTEGER NOT NULL,
    contacto VARCHAR(150) NULL,
    telefono VARCHAR(50) NOT NULL,
    correo VARCHAR(150) NULL,
    direccion VARCHAR(255) NULL,
    notas TEXT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'Activo'
        CHECK (estado IN ('Activo','Inactivo')),
    motivo_inactivacion TEXT NULL,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP NULL,
    usuario_creacion VARCHAR(80) NOT NULL DEFAULT 'sistema',
    usuario_modificacion VARCHAR(80) NULL,
    CONSTRAINT fk_prov_categoria FOREIGN KEY (id_categoria)
        REFERENCES categorias_proveedor(id_categoria)
);

-- Tabla: compras_proveedor
CREATE TABLE IF NOT EXISTS compras_proveedor (
    id_compra SERIAL PRIMARY KEY,
    id_proveedor INTEGER NOT NULL,
    fecha_compra DATE NOT NULL DEFAULT CAST(CURRENT_DATE AS DATE),
    productos TEXT NOT NULL,
    monto_total NUMERIC(18,2) NOT NULL
        CHECK (monto_total > 0),
    estado_pago VARCHAR(20) NOT NULL DEFAULT 'Pendiente'
        CHECK (estado_pago IN ('Pagado','Pendiente')),
    notas VARCHAR(500) NULL,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP NULL,
    usuario_creacion VARCHAR(80) NOT NULL DEFAULT 'sistema',
    usuario_modificacion VARCHAR(80) NULL,
    CONSTRAINT fk_compra_proveedor FOREIGN KEY (id_proveedor)
        REFERENCES proveedores(id_proveedor)
);

-- Tabla: registro_felicitaciones
CREATE TABLE IF NOT EXISTS registro_felicitaciones (
    id_felicitacion SERIAL PRIMARY KEY,
    id_cliente INTEGER NULL,
    id_empleado INTEGER NULL,
    tipo_felicitacion VARCHAR(30) NOT NULL
        CHECK (tipo_felicitacion IN ('Cumpleaños','Aniversario')),
    fecha_envio DATE NOT NULL DEFAULT CAST(CURRENT_DATE AS DATE),
    estado VARCHAR(20) NOT NULL DEFAULT 'Enviado'
        CHECK (estado IN ('Enviado','Pendiente','Error')),
    mensaje VARCHAR(500) NULL,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP NULL,
    usuario_creacion VARCHAR(80) NOT NULL DEFAULT 'sistema',
    usuario_modificacion VARCHAR(80) NULL,
    CONSTRAINT fk_felic_cliente FOREIGN KEY (id_cliente)
        REFERENCES clientes(id_cliente),
    CONSTRAINT fk_felic_empleado FOREIGN KEY (id_empleado)
        REFERENCES empleados(id_empleado)
);

-- ============================================================
-- SECCIÓN 2: ÍNDICES DE RENDIMIENTO
-- ============================================================

CREATE INDEX IF NOT EXISTS ix_clientes_documento ON clientes(documento_identificacion);
CREATE INDEX IF NOT EXISTS ix_clientes_nombre ON clientes(nombre_razon_social);
CREATE INDEX IF NOT EXISTS ix_clientes_tipo_estado ON clientes(tipo, estado);
CREATE INDEX IF NOT EXISTS ix_clientes_nacimiento ON clientes(fecha_nacimiento) 
    WHERE fecha_nacimiento IS NOT NULL;

CREATE INDEX IF NOT EXISTS ix_proveedores_nit ON proveedores(nit);
CREATE INDEX IF NOT EXISTS ix_proveedores_categoria ON proveedores(id_categoria);

CREATE INDEX IF NOT EXISTS ix_empleados_numero ON empleados(numero_empleado);
CREATE INDEX IF NOT EXISTS ix_empleados_nacimiento ON empleados(fecha_nacimiento) 
    WHERE fecha_nacimiento IS NOT NULL;

CREATE INDEX IF NOT EXISTS ix_contactos_cliente ON contactos_cliente(id_cliente);
CREATE INDEX IF NOT EXISTS ix_historial_empleado ON historial_dependencia(id_empleado);
CREATE INDEX IF NOT EXISTS ix_felicitaciones_fecha ON registro_felicitaciones(fecha_envio);

-- ============================================================
-- SECCIÓN 3: FUNCIONES DE VALIDACIÓN
-- ============================================================

-- Función: validar formato de correo
CREATE OR REPLACE FUNCTION fn_validar_correo(correo VARCHAR)
RETURNS BOOLEAN AS $$
BEGIN
    IF correo IS NULL OR correo = '' THEN
        RETURN TRUE;
    END IF;
    IF correo ~ '^[^@]+@[^@]+\.[^@]+$' AND correo NOT LIKE '% %' THEN
        RETURN TRUE;
    END IF;
    RETURN FALSE;
END;
$$ LANGUAGE plpgsql;

-- Función: obtener nombre de dependencia
CREATE OR REPLACE FUNCTION fn_nombre_dependencia(id INTEGER)
RETURNS VARCHAR AS $$
DECLARE
    nombre VARCHAR(150);
BEGIN
    SELECT nombre_dependencia INTO nombre FROM dependencias WHERE id_dependencia = id;
    RETURN COALESCE(nombre, 'Sin dependencia');
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- SECCIÓN 4: STORED PROCEDURES - CLIENTES
-- ============================================================

-- sp_registrar_cliente
CREATE OR REPLACE FUNCTION sp_registrar_cliente(
    p_nombre_razon_social VARCHAR,
    p_documento_identificacion VARCHAR,
    p_tipo VARCHAR DEFAULT 'Cliente',
    p_estado VARCHAR DEFAULT 'Activo',
    p_fecha_nacimiento DATE DEFAULT NULL,
    p_correo VARCHAR DEFAULT NULL,
    p_notificacion_email BOOLEAN DEFAULT FALSE,
    p_notificacion_sms BOOLEAN DEFAULT FALSE,
    p_usuario VARCHAR DEFAULT 'sistema'
)
RETURNS TABLE(id_cliente INTEGER, mensaje VARCHAR) AS $$
DECLARE
    v_nuevo_id INTEGER;
BEGIN
    -- Validar campos obligatorios
    IF TRIM(COALESCE(p_nombre_razon_social, '')) = '' THEN
        RAISE EXCEPTION 'El nombre o razón social es obligatorio.';
    END IF;

    IF TRIM(COALESCE(p_documento_identificacion, '')) = '' THEN
        RAISE EXCEPTION 'El documento de identificación es obligatorio.';
    END IF;

    -- Validar tipo
    IF p_tipo NOT IN ('Cliente','Prospecto') THEN
        RAISE EXCEPTION 'El tipo debe ser Cliente o Prospecto.';
    END IF;

    -- Validar documento duplicado
    IF EXISTS (SELECT 1 FROM clientes WHERE documento_identificacion = p_documento_identificacion) THEN
        RAISE EXCEPTION 'Ya existe un cliente registrado con este documento.';
    END IF;

    -- Validar formato correo
    IF p_correo IS NOT NULL AND NOT fn_validar_correo(p_correo) THEN
        RAISE EXCEPTION 'El formato del correo electrónico no es válido.';
    END IF;

    -- Insertar
    INSERT INTO clientes (
        nombre_razon_social, documento_identificacion, tipo, estado,
        fecha_nacimiento, correo, notificacion_email, notificacion_sms,
        usuario_creacion
    )
    VALUES (
        TRIM(p_nombre_razon_social),
        TRIM(p_documento_identificacion),
        p_tipo, p_estado, p_fecha_nacimiento, p_correo,
        p_notificacion_email, p_notificacion_sms, p_usuario
    )
    RETURNING id_cliente INTO v_nuevo_id;

    RETURN QUERY SELECT v_nuevo_id AS id_cliente, 'Cliente registrado exitosamente.' AS mensaje;
END;
$$ LANGUAGE plpgsql;

-- sp_actualizar_cliente
CREATE OR REPLACE FUNCTION sp_actualizar_cliente(
    p_id_cliente INTEGER,
    p_nombre_razon_social VARCHAR,
    p_documento_identificacion VARCHAR,
    p_tipo VARCHAR,
    p_estado VARCHAR,
    p_fecha_nacimiento DATE DEFAULT NULL,
    p_correo VARCHAR DEFAULT NULL,
    p_notificacion_email BOOLEAN DEFAULT FALSE,
    p_notificacion_sms BOOLEAN DEFAULT FALSE,
    p_usuario VARCHAR DEFAULT 'sistema'
)
RETURNS TABLE(id_cliente INTEGER, mensaje VARCHAR) AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM clientes WHERE id_cliente = p_id_cliente) THEN
        RAISE EXCEPTION 'El cliente no existe.';
    END IF;

    IF TRIM(COALESCE(p_nombre_razon_social, '')) = '' THEN
        RAISE EXCEPTION 'El nombre o razón social es obligatorio.';
    END IF;

    IF TRIM(COALESCE(p_documento_identificacion, '')) = '' THEN
        RAISE EXCEPTION 'El documento de identificación es obligatorio.';
    END IF;

    IF p_tipo NOT IN ('Cliente','Prospecto') THEN
        RAISE EXCEPTION 'El tipo debe ser Cliente o Prospecto.';
    END IF;

    IF EXISTS (
        SELECT 1 FROM clientes
        WHERE documento_identificacion = p_documento_identificacion
          AND id_cliente <> p_id_cliente
    ) THEN
        RAISE EXCEPTION 'Ya existe otro cliente con este documento.';
    END IF;

    IF p_correo IS NOT NULL AND NOT fn_validar_correo(p_correo) THEN
        RAISE EXCEPTION 'El formato del correo no es válido.';
    END IF;

    UPDATE clientes SET
        nombre_razon_social = TRIM(p_nombre_razon_social),
        documento_identificacion = TRIM(p_documento_identificacion),
        tipo = p_tipo,
        estado = p_estado,
        fecha_nacimiento = p_fecha_nacimiento,
        correo = p_correo,
        notificacion_email = p_notificacion_email,
        notificacion_sms = p_notificacion_sms,
        fecha_modificacion = CURRENT_TIMESTAMP,
        usuario_modificacion = p_usuario
    WHERE id_cliente = p_id_cliente;

    RETURN QUERY SELECT p_id_cliente AS id_cliente, 'Cliente actualizado exitosamente.' AS mensaje;
END;
$$ LANGUAGE plpgsql;

-- sp_inactivar_cliente
CREATE OR REPLACE FUNCTION sp_inactivar_cliente(
    p_id_cliente INTEGER,
    p_usuario VARCHAR DEFAULT 'sistema'
)
RETURNS TABLE(id_cliente INTEGER, mensaje VARCHAR) AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM clientes WHERE id_cliente = p_id_cliente) THEN
        RAISE EXCEPTION 'El cliente no existe.';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM clientes WHERE id_cliente = p_id_cliente AND estado = 'Activo') THEN
        RAISE EXCEPTION 'El cliente ya se encuentra inactivo.';
    END IF;

    UPDATE clientes SET
        estado = 'Inactivo',
        fecha_modificacion = CURRENT_TIMESTAMP,
        usuario_modificacion = p_usuario
    WHERE id_cliente = p_id_cliente;

    RETURN QUERY SELECT p_id_cliente AS id_cliente, 'Cliente inactivado correctamente.' AS mensaje;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- SECCIÓN 5: STORED PROCEDURES - CONTACTOS
-- ============================================================

CREATE OR REPLACE FUNCTION sp_agregar_contacto(
    p_id_cliente INTEGER,
    p_nombre_contacto VARCHAR,
    p_tipo_contacto VARCHAR,
    p_descripcion VARCHAR,
    p_correo VARCHAR DEFAULT NULL,
    p_telefono VARCHAR DEFAULT NULL,
    p_usuario VARCHAR DEFAULT 'sistema'
)
RETURNS TABLE(id_contacto INTEGER, mensaje VARCHAR) AS $$
DECLARE
    v_id_contacto INTEGER;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM clientes WHERE id_cliente = p_id_cliente) THEN
        RAISE EXCEPTION 'El cliente no existe.';
    END IF;

    IF TRIM(COALESCE(p_nombre_contacto, '')) = '' THEN
        RAISE EXCEPTION 'El nombre del contacto es obligatorio.';
    END IF;

    IF TRIM(COALESCE(p_descripcion, '')) = '' THEN
        RAISE EXCEPTION 'La descripción es obligatoria.';
    END IF;

    IF p_tipo_contacto NOT IN ('Teléfono','Dirección','Fax','Email','Celular') THEN
        RAISE EXCEPTION 'Tipo de contacto no válido.';
    END IF;

    IF p_correo IS NOT NULL AND NOT fn_validar_correo(p_correo) THEN
        RAISE EXCEPTION 'El formato del correo no es válido.';
    END IF;

    INSERT INTO contactos_cliente (
        id_cliente, nombre_contacto, tipo_contacto,
        descripcion, correo, telefono, usuario_creacion
    )
    VALUES (
        p_id_cliente, TRIM(p_nombre_contacto),
        p_tipo_contacto, TRIM(p_descripcion),
        p_correo, p_telefono, p_usuario
    )
    RETURNING id_contacto INTO v_id_contacto;

    RETURN QUERY SELECT v_id_contacto AS id_contacto, 'Contacto agregado exitosamente.' AS mensaje;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION sp_actualizar_contacto(
    p_id_contacto INTEGER,
    p_nombre_contacto VARCHAR,
    p_tipo_contacto VARCHAR,
    p_descripcion VARCHAR,
    p_correo VARCHAR DEFAULT NULL,
    p_telefono VARCHAR DEFAULT NULL,
    p_estado VARCHAR DEFAULT 'Activo',
    p_usuario VARCHAR DEFAULT 'sistema'
)
RETURNS TABLE(id_contacto INTEGER, mensaje VARCHAR) AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM contactos_cliente WHERE id_contacto = p_id_contacto) THEN
        RAISE EXCEPTION 'El contacto no existe.';
    END IF;

    IF p_correo IS NOT NULL AND NOT fn_validar_correo(p_correo) THEN
        RAISE EXCEPTION 'El formato del correo no es válido.';
    END IF;

    UPDATE contactos_cliente SET
        nombre_contacto = TRIM(p_nombre_contacto),
        tipo_contacto = p_tipo_contacto,
        descripcion = TRIM(p_descripcion),
        correo = p_correo,
        telefono = p_telefono,
        estado = p_estado,
        fecha_modificacion = CURRENT_TIMESTAMP,
        usuario_modificacion = p_usuario
    WHERE id_contacto = p_id_contacto;

    RETURN QUERY SELECT p_id_contacto AS id_contacto, 'Contacto actualizado exitosamente.' AS mensaje;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION sp_eliminar_contacto(
    p_id_contacto INTEGER,
    p_usuario VARCHAR DEFAULT 'sistema'
)
RETURNS TABLE(id_contacto INTEGER, mensaje VARCHAR) AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM contactos_cliente WHERE id_contacto = p_id_contacto) THEN
        RAISE EXCEPTION 'El contacto no existe.';
    END IF;

    UPDATE contactos_cliente SET
        estado = 'Inactivo',
        fecha_modificacion = CURRENT_TIMESTAMP,
        usuario_modificacion = p_usuario
    WHERE id_contacto = p_id_contacto;

    RETURN QUERY SELECT p_id_contacto AS id_contacto, 'Contacto inactivado correctamente.' AS mensaje;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- SECCIÓN 6: STORED PROCEDURES - PROVEEDORES
-- ============================================================

CREATE OR REPLACE FUNCTION sp_registrar_proveedor(
    p_nombre_empresa VARCHAR,
    p_nit VARCHAR,
    p_id_categoria INTEGER,
    p_telefono VARCHAR,
    p_contacto VARCHAR DEFAULT NULL,
    p_correo VARCHAR DEFAULT NULL,
    p_direccion VARCHAR DEFAULT NULL,
    p_notas TEXT DEFAULT NULL,
    p_usuario VARCHAR DEFAULT 'sistema'
)
RETURNS TABLE(id_proveedor INTEGER, mensaje VARCHAR) AS $$
DECLARE
    v_id_proveedor INTEGER;
BEGIN
    IF TRIM(COALESCE(p_nombre_empresa, '')) = '' THEN
        RAISE EXCEPTION 'El nombre de empresa es obligatorio.';
    END IF;

    IF TRIM(COALESCE(p_nit, '')) = '' THEN
        RAISE EXCEPTION 'El NIT es obligatorio.';
    END IF;

    IF TRIM(COALESCE(p_telefono, '')) = '' THEN
        RAISE EXCEPTION 'El teléfono es obligatorio.';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM categorias_proveedor WHERE id_categoria = p_id_categoria AND estado = 'Activo') THEN
        RAISE EXCEPTION 'La categoría no existe o está inactiva.';
    END IF;

    IF EXISTS (SELECT 1 FROM proveedores WHERE nit = p_nit) THEN
        RAISE EXCEPTION 'Ya existe un proveedor con este NIT.';
    END IF;

    IF p_correo IS NOT NULL AND NOT fn_validar_correo(p_correo) THEN
        RAISE EXCEPTION 'El formato del correo no es válido.';
    END IF;

    INSERT INTO proveedores (
        nombre_empresa, nit, id_categoria, telefono,
        contacto, correo, direccion, notas, usuario_creacion
    )
    VALUES (
        TRIM(p_nombre_empresa), TRIM(p_nit),
        p_id_categoria, p_telefono, p_contacto, p_correo,
        p_direccion, p_notas, p_usuario
    )
    RETURNING id_proveedor INTO v_id_proveedor;

    RETURN QUERY SELECT v_id_proveedor AS id_proveedor, 'Proveedor registrado exitosamente.' AS mensaje;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION sp_actualizar_proveedor(
    p_id_proveedor INTEGER,
    p_nombre_empresa VARCHAR,
    p_nit VARCHAR,
    p_id_categoria INTEGER,
    p_telefono VARCHAR,
    p_contacto VARCHAR DEFAULT NULL,
    p_correo VARCHAR DEFAULT NULL,
    p_direccion VARCHAR DEFAULT NULL,
    p_notas TEXT DEFAULT NULL,
    p_usuario VARCHAR DEFAULT 'sistema'
)
RETURNS TABLE(id_proveedor INTEGER, mensaje VARCHAR) AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM proveedores WHERE id_proveedor = p_id_proveedor) THEN
        RAISE EXCEPTION 'El proveedor no existe.';
    END IF;

    IF EXISTS (
        SELECT 1 FROM proveedores
        WHERE nit = p_nit AND id_proveedor <> p_id_proveedor
    ) THEN
        RAISE EXCEPTION 'Ya existe otro proveedor con este NIT.';
    END IF;

    IF p_correo IS NOT NULL AND NOT fn_validar_correo(p_correo) THEN
        RAISE EXCEPTION 'El formato del correo no es válido.';
    END IF;

    UPDATE proveedores SET
        nombre_empresa = TRIM(p_nombre_empresa),
        nit = TRIM(p_nit),
        id_categoria = p_id_categoria,
        telefono = p_telefono,
        contacto = p_contacto,
        correo = p_correo,
        direccion = p_direccion,
        notas = p_notas,
        fecha_modificacion = CURRENT_TIMESTAMP,
        usuario_modificacion = p_usuario
    WHERE id_proveedor = p_id_proveedor;

    RETURN QUERY SELECT p_id_proveedor AS id_proveedor, 'Proveedor actualizado exitosamente.' AS mensaje;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION sp_inactivar_proveedor(
    p_id_proveedor INTEGER,
    p_motivo_inactivacion TEXT,
    p_usuario VARCHAR DEFAULT 'sistema'
)
RETURNS TABLE(id_proveedor INTEGER, mensaje VARCHAR) AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM proveedores WHERE id_proveedor = p_id_proveedor) THEN
        RAISE EXCEPTION 'El proveedor no existe.';
    END IF;

    IF TRIM(COALESCE(p_motivo_inactivacion, '')) = '' THEN
        RAISE EXCEPTION 'El motivo de inactivación es obligatorio.';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM proveedores WHERE id_proveedor = p_id_proveedor AND estado = 'Activo') THEN
        RAISE EXCEPTION 'El proveedor ya se encuentra inactivo.';
    END IF;

    UPDATE proveedores SET
        estado = 'Inactivo',
        motivo_inactivacion = TRIM(p_motivo_inactivacion),
        fecha_modificacion = CURRENT_TIMESTAMP,
        usuario_modificacion = p_usuario
    WHERE id_proveedor = p_id_proveedor;

    RETURN QUERY SELECT p_id_proveedor AS id_proveedor, 'Proveedor inactivado correctamente.' AS mensaje;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION sp_activar_proveedor(
    p_id_proveedor INTEGER,
    p_usuario VARCHAR DEFAULT 'sistema'
)
RETURNS TABLE(id_proveedor INTEGER, mensaje VARCHAR) AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM proveedores WHERE id_proveedor = p_id_proveedor) THEN
        RAISE EXCEPTION 'El proveedor no existe.';
    END IF;

    UPDATE proveedores SET
        estado = 'Activo',
        motivo_inactivacion = NULL,
        fecha_modificacion = CURRENT_TIMESTAMP,
        usuario_modificacion = p_usuario
    WHERE id_proveedor = p_id_proveedor;

    RETURN QUERY SELECT p_id_proveedor AS id_proveedor, 'Proveedor activado correctamente.' AS mensaje;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION sp_eliminar_proveedor(
    p_id_proveedor INTEGER,
    p_usuario VARCHAR DEFAULT 'sistema'
)
RETURNS TABLE(id_proveedor INTEGER, mensaje VARCHAR) AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM proveedores WHERE id_proveedor = p_id_proveedor) THEN
        RAISE EXCEPTION 'El proveedor no existe.';
    END IF;

    IF EXISTS (SELECT 1 FROM compras_proveedor WHERE id_proveedor = p_id_proveedor) THEN
        RAISE EXCEPTION 'No se puede eliminar el proveedor porque tiene compras registradas.';
    END IF;

    DELETE FROM proveedores WHERE id_proveedor = p_id_proveedor;

    RETURN QUERY SELECT p_id_proveedor AS id_proveedor, 'Proveedor eliminado correctamente.' AS mensaje;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- SECCIÓN 7: STORED PROCEDURES - COMPRAS
-- ============================================================

CREATE OR REPLACE FUNCTION sp_registrar_compra_proveedor(
    p_id_proveedor INTEGER,
    p_fecha_compra DATE DEFAULT NULL,
    p_productos TEXT DEFAULT '',
    p_monto_total NUMERIC DEFAULT 0,
    p_estado_pago VARCHAR DEFAULT 'Pendiente',
    p_notas VARCHAR DEFAULT NULL,
    p_usuario VARCHAR DEFAULT 'sistema'
)
RETURNS TABLE(id_compra INTEGER, mensaje VARCHAR) AS $$
DECLARE
    v_id_compra INTEGER;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM proveedores WHERE id_proveedor = p_id_proveedor AND estado = 'Activo') THEN
        RAISE EXCEPTION 'El proveedor no existe o está inactivo.';
    END IF;

    IF TRIM(COALESCE(p_productos, '')) = '' THEN
        RAISE EXCEPTION 'El campo productos es obligatorio.';
    END IF;

    IF p_monto_total <= 0 THEN
        RAISE EXCEPTION 'El monto total debe ser mayor a cero.';
    END IF;

    IF p_estado_pago NOT IN ('Pagado','Pendiente') THEN
        RAISE EXCEPTION 'Estado de pago inválido.';
    END IF;

    INSERT INTO compras_proveedor (
        id_proveedor, fecha_compra, productos,
        monto_total, estado_pago, notas, usuario_creacion
    )
    VALUES (
        p_id_proveedor,
        COALESCE(p_fecha_compra, CAST(CURRENT_DATE AS DATE)),
        TRIM(p_productos),
        p_monto_total, p_estado_pago, p_notas, p_usuario
    )
    RETURNING id_compra INTO v_id_compra;

    RETURN QUERY SELECT v_id_compra AS id_compra, 'Compra registrada exitosamente.' AS mensaje;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- SECCIÓN 8: STORED PROCEDURES - EMPLEADOS
-- ============================================================

CREATE OR REPLACE FUNCTION sp_registrar_empleado(
    p_numero_empleado VARCHAR,
    p_dpi VARCHAR,
    p_nombre_completo VARCHAR,
    p_cargo VARCHAR DEFAULT NULL,
    p_id_dependencia INTEGER DEFAULT NULL,
    p_fecha_nacimiento DATE DEFAULT NULL,
    p_correo VARCHAR DEFAULT NULL,
    p_telefono VARCHAR DEFAULT NULL,
    p_direccion VARCHAR DEFAULT NULL,
    p_usuario VARCHAR DEFAULT 'sistema'
)
RETURNS TABLE(id_empleado INTEGER, mensaje VARCHAR) AS $$
DECLARE
    v_nuevo_id INTEGER;
BEGIN
    IF TRIM(COALESCE(p_numero_empleado, '')) = '' THEN
        RAISE EXCEPTION 'El número de empleado es obligatorio.';
    END IF;

    IF TRIM(COALESCE(p_dpi, '')) = '' THEN
        RAISE EXCEPTION 'El DPI es obligatorio.';
    END IF;

    IF TRIM(COALESCE(p_nombre_completo, '')) = '' THEN
        RAISE EXCEPTION 'El nombre completo es obligatorio.';
    END IF;

    IF EXISTS (SELECT 1 FROM empleados WHERE numero_empleado = p_numero_empleado) THEN
        RAISE EXCEPTION 'Ya existe un empleado con este número.';
    END IF;

    IF EXISTS (SELECT 1 FROM empleados WHERE dpi = p_dpi) THEN
        RAISE EXCEPTION 'Ya existe un empleado con este DPI.';
    END IF;

    IF p_id_dependencia IS NOT NULL
        AND NOT EXISTS (SELECT 1 FROM dependencias WHERE id_dependencia = p_id_dependencia AND estado = 'Activo') THEN
        RAISE EXCEPTION 'La dependencia no existe o está inactiva.';
    END IF;

    IF p_correo IS NOT NULL AND NOT fn_validar_correo(p_correo) THEN
        RAISE EXCEPTION 'El formato del correo no es válido.';
    END IF;

    INSERT INTO empleados (
        numero_empleado, dpi, nombre_completo, cargo,
        id_dependencia, fecha_nacimiento, correo,
        telefono, direccion, usuario_creacion
    )
    VALUES (
        TRIM(p_numero_empleado), TRIM(p_dpi),
        TRIM(p_nombre_completo), p_cargo,
        p_id_dependencia, p_fecha_nacimiento, p_correo,
        p_telefono, p_direccion, p_usuario
    )
    RETURNING id_empleado INTO v_nuevo_id;

    -- Registrar en historial si tiene dependencia inicial
    IF p_id_dependencia IS NOT NULL THEN
        INSERT INTO historial_dependencia (
            id_empleado, id_dependencia_origen, id_dependencia_destino,
            motivo, usuario, usuario_creacion
        )
        VALUES (v_nuevo_id, NULL, p_id_dependencia, 'Asignación inicial', p_usuario, p_usuario);
    END IF;

    RETURN QUERY SELECT v_nuevo_id AS id_empleado, 'Empleado registrado exitosamente.' AS mensaje;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION sp_actualizar_empleado(
    p_id_empleado INTEGER,
    p_nombre_completo VARCHAR,
    p_cargo VARCHAR DEFAULT NULL,
    p_fecha_nacimiento DATE DEFAULT NULL,
    p_correo VARCHAR DEFAULT NULL,
    p_telefono VARCHAR DEFAULT NULL,
    p_direccion VARCHAR DEFAULT NULL,
    p_estado VARCHAR DEFAULT 'Activo',
    p_usuario VARCHAR DEFAULT 'sistema'
)
RETURNS TABLE(id_empleado INTEGER, mensaje VARCHAR) AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM empleados WHERE id_empleado = p_id_empleado) THEN
        RAISE EXCEPTION 'El empleado no existe.';
    END IF;

    IF p_correo IS NOT NULL AND NOT fn_validar_correo(p_correo) THEN
        RAISE EXCEPTION 'El formato del correo no es válido.';
    END IF;

    UPDATE empleados SET
        nombre_completo = TRIM(p_nombre_completo),
        cargo = p_cargo,
        fecha_nacimiento = p_fecha_nacimiento,
        correo = p_correo,
        telefono = p_telefono,
        direccion = p_direccion,
        estado = p_estado,
        fecha_modificacion = CURRENT_TIMESTAMP,
        usuario_modificacion = p_usuario
    WHERE id_empleado = p_id_empleado;

    RETURN QUERY SELECT p_id_empleado AS id_empleado, 'Empleado actualizado exitosamente.' AS mensaje;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION sp_reasignar_dependencia(
    p_id_empleado INTEGER,
    p_id_dependencia_nueva INTEGER,
    p_motivo VARCHAR,
    p_usuario VARCHAR DEFAULT 'sistema'
)
RETURNS TABLE(id_empleado INTEGER, mensaje VARCHAR) AS $$
DECLARE
    v_dep_actual INTEGER;
BEGIN
    SELECT id_dependencia INTO v_dep_actual
    FROM empleados WHERE id_empleado = p_id_empleado;

    IF v_dep_actual IS NULL AND NOT EXISTS (SELECT 1 FROM empleados WHERE id_empleado = p_id_empleado) THEN
        RAISE EXCEPTION 'El empleado no existe.';
    END IF;

    IF v_dep_actual = p_id_dependencia_nueva THEN
        RAISE EXCEPTION 'El empleado ya pertenece a esta dependencia.';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM dependencias WHERE id_dependencia = p_id_dependencia_nueva AND estado = 'Activo') THEN
        RAISE EXCEPTION 'La dependencia destino no existe o está inactiva.';
    END IF;

    IF TRIM(COALESCE(p_motivo, '')) = '' THEN
        RAISE EXCEPTION 'El motivo de reasignación es obligatorio.';
    END IF;

    -- Actualizar empleado
    UPDATE empleados SET
        id_dependencia = p_id_dependencia_nueva,
        fecha_modificacion = CURRENT_TIMESTAMP,
        usuario_modificacion = p_usuario
    WHERE id_empleado = p_id_empleado;

    -- Registrar en historial
    INSERT INTO historial_dependencia (
        id_empleado, id_dependencia_origen, id_dependencia_destino,
        motivo, usuario, usuario_creacion
    )
    VALUES (
        p_id_empleado, v_dep_actual, p_id_dependencia_nueva,
        TRIM(p_motivo), p_usuario, p_usuario
    );

    RETURN QUERY SELECT p_id_empleado AS id_empleado, 'Reasignación de dependencia registrada.' AS mensaje;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- SECCIÓN 9: STORED PROCEDURE - FELICITACIONES
-- ============================================================

CREATE OR REPLACE FUNCTION sp_verificar_felicitaciones_diarias(p_usuario VARCHAR DEFAULT 'sistema')
RETURNS TABLE(felicitaciones_enviadas INTEGER, mensaje VARCHAR) AS $$
DECLARE
    v_hoy DATE;
    v_mes INTEGER;
    v_dia INTEGER;
    v_contador INTEGER := 0;
BEGIN
    v_hoy := CAST(CURRENT_DATE AS DATE);
    v_mes := EXTRACT(MONTH FROM v_hoy)::INTEGER;
    v_dia := EXTRACT(DAY FROM v_hoy)::INTEGER;

    -- Cumpleaños clientes
    INSERT INTO registro_felicitaciones (
        id_cliente, tipo_felicitacion, fecha_envio,
        estado, mensaje, usuario_creacion
    )
    SELECT
        c.id_cliente,
        'Cumpleaños',
        v_hoy,
        'Enviado',
        '¡Feliz cumpleaños, ' || c.nombre_razon_social || '!',
        p_usuario
    FROM clientes c
    WHERE
        c.estado = 'Activo'
        AND c.fecha_nacimiento IS NOT NULL
        AND EXTRACT(MONTH FROM c.fecha_nacimiento)::INTEGER = v_mes
        AND EXTRACT(DAY FROM c.fecha_nacimiento)::INTEGER = v_dia
        AND NOT EXISTS (
            SELECT 1 FROM registro_felicitaciones rf
            WHERE rf.id_cliente = c.id_cliente
              AND rf.tipo_felicitacion = 'Cumpleaños'
              AND rf.fecha_envio = v_hoy
        );

    v_contador := v_contador + FOUND::INTEGER;

    -- Cumpleaños empleados
    INSERT INTO registro_felicitaciones (
        id_empleado, tipo_felicitacion, fecha_envio,
        estado, mensaje, usuario_creacion
    )
    SELECT
        e.id_empleado,
        'Cumpleaños',
        v_hoy,
        'Enviado',
        '¡Feliz cumpleaños, ' || e.nombre_completo || '!',
        p_usuario
    FROM empleados e
    WHERE
        e.estado = 'Activo'
        AND e.fecha_nacimiento IS NOT NULL
        AND EXTRACT(MONTH FROM e.fecha_nacimiento)::INTEGER = v_mes
        AND EXTRACT(DAY FROM e.fecha_nacimiento)::INTEGER = v_dia
        AND NOT EXISTS (
            SELECT 1 FROM registro_felicitaciones rf
            WHERE rf.id_empleado = e.id_empleado
              AND rf.tipo_felicitacion = 'Cumpleaños'
              AND rf.fecha_envio = v_hoy
        );

    v_contador := v_contador + FOUND::INTEGER;

    RETURN QUERY SELECT v_contador AS felicitaciones_enviadas,
           'Proceso de felicitaciones completado.' AS mensaje;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- SECCIÓN 10: TRIGGERS
-- ============================================================

-- Trigger: actualizar fecha_modificacion en clientes
CREATE OR REPLACE FUNCTION trg_clientes_update()
RETURNS TRIGGER AS $$
BEGIN
    NEW.fecha_modificacion := CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_clientes_update ON clientes;
CREATE TRIGGER trg_clientes_update
BEFORE UPDATE ON clientes
FOR EACH ROW
EXECUTE FUNCTION trg_clientes_update();

-- Trigger: actualizar fecha_modificacion en proveedores
CREATE OR REPLACE FUNCTION trg_proveedores_update()
RETURNS TRIGGER AS $$
BEGIN
    NEW.fecha_modificacion := CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_proveedores_update ON proveedores;
CREATE TRIGGER trg_proveedores_update
BEFORE UPDATE ON proveedores
FOR EACH ROW
EXECUTE FUNCTION trg_proveedores_update();

-- Trigger: actualizar fecha_modificacion en empleados
CREATE OR REPLACE FUNCTION trg_empleados_update()
RETURNS TRIGGER AS $$
BEGIN
    NEW.fecha_modificacion := CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_empleados_update ON empleados;
CREATE TRIGGER trg_empleados_update
BEFORE UPDATE ON empleados
FOR EACH ROW
EXECUTE FUNCTION trg_empleados_update();

-- ============================================================
-- SECCIÓN 11: DATOS INICIALES
-- ============================================================

-- Categorías de proveedor
INSERT INTO categorias_proveedor (nombre_categoria, descripcion, usuario_creacion)
VALUES
    ('Tecnología',   'Equipos, software y servicios tecnológicos', 'sistema'),
    ('Papelería',    'Útiles de oficina y papelería',               'sistema'),
    ('Logística',    'Transporte y distribución',                   'sistema'),
    ('Servicios',    'Servicios profesionales y consultoría',       'sistema'),
    ('Alimentación', 'Productos alimenticios',                      'sistema'),
    ('Otros',        'Categoría general',                           'sistema')
ON CONFLICT (nombre_categoria) DO NOTHING;

-- Dependencias
INSERT INTO dependencias (nombre_dependencia, usuario_creacion)
VALUES
    ('Gerencia General',    'sistema'),
    ('Recursos Humanos',    'sistema'),
    ('Tecnología',          'sistema'),
    ('Contabilidad',        'sistema'),
    ('Ventas',              'sistema'),
    ('Logística',           'sistema')
ON CONFLICT DO NOTHING;

-- Usuario administrador
INSERT INTO usuarios (nombre, email, username, password_hash, rol, usuario_creacion)
VALUES (
    'Administrador',
    'admin@crm.com',
    'admin',
    '$2b$12$rIo8uK9cgE/P5hgJ.20BEO7I0WmLVr7z.D3.TQ33YiwjA5GlrkGcm',
    'admin',
    'sistema'
)
ON CONFLICT (username) DO NOTHING;

-- Datos de ejemplo - Clientes
SELECT sp_registrar_cliente(
    'Juan Carlos Pérez',
    '1234567890',
    'Cliente',
    'Activo',
    NULL,
    'juan.perez@email.com',
    TRUE,
    FALSE,
    'sistema'
);

SELECT sp_registrar_cliente(
    'Empresa ABC S.A.S',
    '900123456',
    'Cliente',
    'Activo',
    NULL,
    'info@abc.com',
    TRUE,
    TRUE,
    'sistema'
);

SELECT sp_registrar_cliente(
    'María López Torres',
    '0987654321',
    'Prospecto',
    'Activo',
    NULL,
    'maria.lopez@gmail.com',
    FALSE,
    FALSE,
    'sistema'
);

-- Datos de ejemplo - Proveedores
SELECT sp_registrar_proveedor(
    'TechCorp Colombia',
    '900111222-1',
    1,
    '6015551234',
    NULL,
    'ventas@techcorp.co',
    'Av. El Dorado 92-32, Bogotá',
    'Proveedor principal de equipos',
    'sistema'
);

SELECT sp_registrar_proveedor(
    'Papelería Central',
    '800333444-5',
    2,
    '6015555678',
    NULL,
    'info@papelcentral.com',
    NULL,
    NULL,
    'sistema'
);

-- ============================================================
-- SECCIÓN 12: MENSAJES FINALES
-- ============================================================

SELECT 'CRM Ing Software - Base de datos PostgreSQL completada exitosamente.' AS mensaje;
SELECT 'Tablas: 10 | Functions: 21 | Triggers: 3' AS estadísticas;
