-- ============================================================
-- FIX: Actualizar hash de contraseña del usuario admin
-- El hash original estaba truncado y causaba fallo en bcrypt.
-- Contraseña: admin123
-- ============================================================

USE crm_ing_software;
GO

-- Actualizar el hash correcto (bcrypt $2b$12$, 60 caracteres)
UPDATE usuarios
SET password_hash = '$2b$12$rIo8uK9cgE/P5hgJ.20BEO7I0WmLVr7z.D3.TQ33YiwjA5GlrkGcm',
    estado = 'Activo',
    fecha_modificacion = GETDATE(),
    usuario_modificacion = 'fix_script'
WHERE username = 'admin';

-- Verificar
SELECT id_usuario, username, nombre, rol, estado, LEN(password_hash) AS largo_hash
FROM usuarios
WHERE username = 'admin';
-- largo_hash debe ser 60

GO
PRINT '>>> Hash de admin actualizado correctamente. Login: admin / admin123';
