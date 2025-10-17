-- Crear tabla de Roles
CREATE TABLE Roles (
    IdRol INT IDENTITY(1,1) PRIMARY KEY,
    Nombre NVARCHAR(100) NOT NULL,
    Descripcion NVARCHAR(255),
    EsPredefinido BIT DEFAULT 1,
    FechaCreacion DATETIME DEFAULT GETDATE()
);
GO

-- Crear tabla de PermisosRol
CREATE TABLE PermisosRol (
    IdPermisoRol INT IDENTITY(1,1) PRIMARY KEY,
    IdRol INT NOT NULL,
    Modulo NVARCHAR(100) NOT NULL,
    Ver BIT DEFAULT 0,
    Crear BIT DEFAULT 0,
    Editar BIT DEFAULT 0,
    Eliminar BIT DEFAULT 0,
    FOREIGN KEY (IdRol) REFERENCES Roles(IdRol) ON DELETE CASCADE
);
GO

-- Insertar roles predefinidos
INSERT INTO Roles (Nombre, Descripcion, EsPredefinido) VALUES 
('Administrador', 'Acceso completo al sistema', 1),
('Gerente', 'Acceso a la mayoría de módulos excepto configuración', 1),
('Supervisor', 'Puede ver reportes y gestionar empleados', 1),
('Empleado', 'Acceso limitado a funciones básicas', 1);

-- Insertar permisos para Administrador (acceso total)
INSERT INTO PermisosRol (IdRol, Modulo, Ver, Crear, Editar, Eliminar)
SELECT IdRol, Modulo, 1, 1, 1, 1
FROM Roles, (VALUES 
    ('Dashboard'),
    ('Empleados'),
    ('Departamentos'),
    ('Puestos'),
    ('Asistencia'),
    ('Nómina'),
    ('Reportes'),
    ('Configuración')
) AS Modulos(Modulo)
WHERE Nombre = 'Administrador';

-- Insertar permisos para Gerente
INSERT INTO PermisosRol (IdRol, Modulo, Ver, Crear, Editar, Eliminar)
SELECT IdRol, Modulo, 1, 1, 1, 0
FROM Roles, (VALUES 
    ('Dashboard'),
    ('Empleados'),
    ('Departamentos'),
    ('Puestos'),
    ('Asistencia'),
    ('Nómina'),
    ('Reportes')
) AS Modulos(Modulo)
WHERE Nombre = 'Gerente';

-- Insertar permisos para Supervisor
INSERT INTO PermisosRol (IdRol, Modulo, Ver, Crear, Editar, Eliminar)
SELECT IdRol, Modulo, 1, 1, 1, 0
FROM Roles, (VALUES 
    ('Dashboard'),
    ('Empleados'),
    ('Asistencia'),
    ('Reportes')
) AS Modulos(Modulo)
WHERE Nombre = 'Supervisor';

-- Insertar permisos para Empleado
INSERT INTO PermisosRol (IdRol, Modulo, Ver, Crear, Editar, Eliminar)
SELECT IdRol, Modulo, 1, 0, 0, 0
FROM Roles, (VALUES 
    ('Dashboard'),
    ('Asistencia')
) AS Modulos(Modulo)
WHERE Nombre = 'Empleado';

-- Agregar columna IdRol a la tabla Usuarios si no existe
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('Usuarios') AND name = 'IdRol')
BEGIN
    ALTER TABLE Usuarios ADD IdRol INT NULL;
    
    -- Asignar rol de Administrador a usuarios existentes (si es necesario)
    UPDATE Usuarios SET IdRol = (SELECT TOP 1 IdRol FROM Roles WHERE Nombre = 'Administrador');
    
    -- Hacer la columna requerida después de asignar valores por defecto
    ALTER TABLE Usuarios ALTER COLUMN IdRol INT NOT NULL;
    
    -- Agregar la relación de clave foránea
    ALTER TABLE Usuarios 
    ADD CONSTRAINT FK_Usuarios_Roles FOREIGN KEY (IdRol) REFERENCES Roles(IdRol);
END
GO
