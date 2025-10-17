-- ========================================
-- SCRIPT COMPLETO DE CREACIÓN DE BASE DE DATOS
-- Sistema de Gestión de Nómina y RRHH
-- ========================================
-- Este script crea todas las tablas, relaciones y datos iniciales
-- Ejecutar en SQL Server
-- ========================================

USE master;
GO

-- Eliminar base de datos si existe (CUIDADO: esto borra todos los datos)
IF EXISTS (SELECT name FROM sys.databases WHERE name = 'NominaDB')
BEGIN
    ALTER DATABASE NominaDB SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE NominaDB;
END
GO

-- Crear la base de datos
CREATE DATABASE NominaDB;
GO

USE NominaDB;
GO

-- ========================================
-- TABLAS DE SEGURIDAD Y USUARIOS
-- ========================================

-- Tabla: Roles
CREATE TABLE Roles (
    IdRol INT IDENTITY(1,1) PRIMARY KEY,
    Nombre NVARCHAR(100) NOT NULL UNIQUE,
    Descripcion NVARCHAR(255),
    EsPredefinido BIT DEFAULT 1,
    FechaCreacion DATETIME DEFAULT GETDATE()
);
GO

-- Tabla: Módulos del Sistema
CREATE TABLE Modulos (
    IdModulo INT IDENTITY(1,1) PRIMARY KEY,
    Nombre NVARCHAR(100) NOT NULL UNIQUE,
    Descripcion NVARCHAR(255),
    Ruta NVARCHAR(255),
    Icono NVARCHAR(50),
    Orden INT DEFAULT 0,
    Activo BIT DEFAULT 1,
    FechaCreacion DATETIME DEFAULT GETDATE()
);
GO

-- Tabla: Permisos por Rol (permisos predefinidos)
CREATE TABLE PermisosRol (
    IdPermisoRol INT IDENTITY(1,1) PRIMARY KEY,
    IdRol INT NOT NULL,
    Modulo NVARCHAR(100) NOT NULL,
    Ver BIT DEFAULT 0,
    Crear BIT DEFAULT 0,
    Editar BIT DEFAULT 0,
    Eliminar BIT DEFAULT 0,
    FOREIGN KEY (IdRol) REFERENCES Roles(IdRol) ON DELETE CASCADE,
    CONSTRAINT UQ_PermisoRol_Modulo UNIQUE (IdRol, Modulo)
);
GO

-- Tabla: Usuarios
CREATE TABLE Usuarios (
    IdUsuario INT IDENTITY(1,1) PRIMARY KEY,
    NombreUsuario NVARCHAR(100) NOT NULL UNIQUE,
    Correo NVARCHAR(255) NOT NULL UNIQUE,
    ClaveHash NVARCHAR(255) NOT NULL,
    IdRol INT NOT NULL,
    IdEmpleado INT NULL,
    Activo BIT DEFAULT 1,
    FechaCreacion DATETIME DEFAULT GETDATE(),
    UltimoAcceso DATETIME NULL,
    FOREIGN KEY (IdRol) REFERENCES Roles(IdRol)
);
GO

-- Tabla: Permisos por Usuario (permisos personalizados)
CREATE TABLE PermisosUsuarios (
    IdPermisoUsuario INT IDENTITY(1,1) PRIMARY KEY,
    IdUsuario INT NOT NULL,
    IdModulo INT NOT NULL,
    Ver BIT DEFAULT 0,
    Crear BIT DEFAULT 0,
    Editar BIT DEFAULT 0,
    Eliminar BIT DEFAULT 0,
    TieneAcceso BIT DEFAULT 1,
    FechaAsignacion DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (IdUsuario) REFERENCES Usuarios(IdUsuario) ON DELETE CASCADE,
    FOREIGN KEY (IdModulo) REFERENCES Modulos(IdModulo) ON DELETE CASCADE,
    CONSTRAINT UQ_PermisoUsuario_Modulo UNIQUE (IdUsuario, IdModulo)
);
GO

-- Tabla: Auditoría
CREATE TABLE Auditoria (
    IdAuditoria INT IDENTITY(1,1) PRIMARY KEY,
    IdUsuario INT NULL,
    Accion NVARCHAR(255) NOT NULL,
    Tabla NVARCHAR(100),
    Detalles NVARCHAR(MAX),
    FechaHora DATETIME DEFAULT GETDATE(),
    DireccionIP NVARCHAR(45),
    FOREIGN KEY (IdUsuario) REFERENCES Usuarios(IdUsuario) ON DELETE SET NULL
);
GO

-- ========================================
-- TABLAS DE ESTRUCTURA ORGANIZACIONAL
-- ========================================

-- Tabla: Departamentos
CREATE TABLE Departamentos (
    IdDepartamento INT IDENTITY(1,1) PRIMARY KEY,
    Nombre NVARCHAR(255) NOT NULL,
    Descripcion NVARCHAR(MAX),
    Activo BIT DEFAULT 1,
    FechaCreacion DATETIME DEFAULT GETDATE()
);
GO

-- Tabla: Puestos
CREATE TABLE Puestos (
    IdPuesto INT IDENTITY(1,1) PRIMARY KEY,
    Titulo NVARCHAR(255) NOT NULL,
    Descripcion NVARCHAR(MAX),
    IdDepartamento INT NULL,
    SalarioBase DECIMAL(18,2) DEFAULT 0,
    Activo BIT DEFAULT 1,
    FechaCreacion DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (IdDepartamento) REFERENCES Departamentos(IdDepartamento) ON DELETE SET NULL
);
GO

-- Tabla: Empleados
CREATE TABLE Empleados (
    IdEmpleado INT IDENTITY(1,1) PRIMARY KEY,
    CodigoEmpleado NVARCHAR(50) UNIQUE,
    Nombres NVARCHAR(255) NOT NULL,
    Apellidos NVARCHAR(255) NOT NULL,
    DPI NVARCHAR(20) UNIQUE,
    NIT NVARCHAR(20),
    FechaNacimiento DATE,
    Genero NVARCHAR(20),
    EstadoCivil NVARCHAR(50),
    Direccion NVARCHAR(MAX),
    Telefono NVARCHAR(20),
    Correo NVARCHAR(255),
    IdPuesto INT NULL,
    FechaIngreso DATE,
    FechaEgreso DATE NULL,
    TipoPago NVARCHAR(50) DEFAULT 'Mensual',
    SalarioBase DECIMAL(18,2) DEFAULT 0,
    CuentaBancaria NVARCHAR(50),
    Banco NVARCHAR(100),
    Activo BIT DEFAULT 1,
    FechaCreacion DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (IdPuesto) REFERENCES Puestos(IdPuesto) ON DELETE SET NULL
);
GO

-- Agregar FK de IdEmpleado en Usuarios (después de crear Empleados)
ALTER TABLE Usuarios
ADD CONSTRAINT FK_Usuarios_Empleados 
FOREIGN KEY (IdEmpleado) REFERENCES Empleados(IdEmpleado) ON DELETE SET NULL;
GO

-- ========================================
-- TABLAS DE NÓMINA
-- ========================================

-- Tabla: Beneficios y Deducciones
CREATE TABLE BeneficiosDeducciones (
    IdBeneficioDeduccion INT IDENTITY(1,1) PRIMARY KEY,
    Nombre NVARCHAR(255) NOT NULL,
    Descripcion NVARCHAR(MAX),
    Tipo NVARCHAR(50) NOT NULL CHECK (Tipo IN ('Percepción', 'Deducción')),
    Calculo NVARCHAR(50) NOT NULL CHECK (Calculo IN ('Fijo', 'Porcentaje')),
    Valor DECIMAL(18,2) DEFAULT 0,
    EsObligatorio BIT DEFAULT 0,
    AplicaIGSS BIT DEFAULT 0,
    AplicaISR BIT DEFAULT 0,
    Activo BIT DEFAULT 1,
    FechaCreacion DATETIME DEFAULT GETDATE()
);
GO

-- Tabla: Asignación de Beneficios/Deducciones a Empleados
CREATE TABLE EmpleadoBeneficiosDeduccioness (
    IdEmpleadoBeneficioDeduccion INT IDENTITY(1,1) PRIMARY KEY,
    IdEmpleado INT NOT NULL,
    IdBeneficioDeduccion INT NOT NULL,
    ValorPersonalizado DECIMAL(18,2) NULL,
    FechaInicio DATE NOT NULL,
    FechaFin DATE NULL,
    Activo BIT DEFAULT 1,
    FOREIGN KEY (IdEmpleado) REFERENCES Empleados(IdEmpleado) ON DELETE CASCADE,
    FOREIGN KEY (IdBeneficioDeduccion) REFERENCES BeneficiosDeducciones(IdBeneficioDeduccion) ON DELETE CASCADE
);
GO

-- Tabla: Periodos de Nómina
CREATE TABLE Periodos (
    IdPeriodo INT IDENTITY(1,1) PRIMARY KEY,
    Descripcion NVARCHAR(255) NOT NULL,
    FechaInicio DATE NOT NULL,
    FechaFin DATE NOT NULL,
    Modalidad NVARCHAR(50) NOT NULL CHECK (Modalidad IN ('Quincenal', 'Mensual', 'Semanal')),
    Estado NVARCHAR(50) DEFAULT 'Borrador' CHECK (Estado IN ('Borrador', 'Procesado', 'Cerrado')),
    FechaCreacion DATETIME DEFAULT GETDATE(),
    FechaCierre DATETIME NULL,
    CONSTRAINT UQ_Periodo_Fechas UNIQUE (FechaInicio, FechaFin)
);
GO

-- Tabla: Registros de Nómina
CREATE TABLE RegistrosNomina (
    IdRegistroNomina INT IDENTITY(1,1) PRIMARY KEY,
    IdEmpleado INT NOT NULL,
    IdPeriodo INT NOT NULL,
    DiasLaborados INT DEFAULT 0,
    HorasExtras DECIMAL(10,2) DEFAULT 0,
    SalarioBruto DECIMAL(18,2) DEFAULT 0,
    TotalPercepciones DECIMAL(18,2) DEFAULT 0,
    TotalDeducciones DECIMAL(18,2) DEFAULT 0,
    SalarioNeto DECIMAL(18,2) DEFAULT 0,
    FechaCreacion DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (IdEmpleado) REFERENCES Empleados(IdEmpleado) ON DELETE CASCADE,
    FOREIGN KEY (IdPeriodo) REFERENCES Periodos(IdPeriodo) ON DELETE CASCADE,
    CONSTRAINT UQ_Registro_Periodo_Empleado UNIQUE (IdEmpleado, IdPeriodo)
);
GO

-- Tabla: Items de Nómina (detalle de percepciones y deducciones)
CREATE TABLE ItemsNomina (
    IdItemNomina INT IDENTITY(1,1) PRIMARY KEY,
    IdRegistroNomina INT NOT NULL,
    IdBeneficioDeduccion INT NULL,
    Descripcion NVARCHAR(255) NOT NULL,
    Monto DECIMAL(18,2) DEFAULT 0,
    FOREIGN KEY (IdRegistroNomina) REFERENCES RegistrosNomina(IdRegistroNomina) ON DELETE CASCADE,
    FOREIGN KEY (IdBeneficioDeduccion) REFERENCES BeneficiosDeducciones(IdBeneficioDeduccion) ON DELETE SET NULL
);
GO

-- ========================================
-- TABLAS DE ASISTENCIA
-- ========================================

-- Tabla: Registros de Asistencia
CREATE TABLE Asistencia (
    IdAsistencia INT IDENTITY(1,1) PRIMARY KEY,
    IdEmpleado INT NOT NULL,
    Fecha DATE NOT NULL,
    HoraEntrada TIME NULL,
    HoraSalida TIME NULL,
    HorasTrabajadas DECIMAL(10,2) DEFAULT 0,
    Observaciones NVARCHAR(MAX),
    Estado NVARCHAR(50) DEFAULT 'Presente' CHECK (Estado IN ('Presente', 'Ausente', 'Tardanza', 'Permiso', 'Vacaciones', 'Incapacidad')),
    FechaCreacion DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (IdEmpleado) REFERENCES Empleados(IdEmpleado) ON DELETE CASCADE,
    CONSTRAINT UQ_Asistencia_Empleado_Fecha UNIQUE (IdEmpleado, Fecha)
);
GO

-- ========================================
-- DATOS INICIALES (SEED DATA)
-- ========================================

-- Insertar Roles Predefinidos
INSERT INTO Roles (Nombre, Descripcion, EsPredefinido) VALUES 
('Administrador', 'Acceso completo al sistema', 1),
('RRHH', 'Gestión de recursos humanos y nómina', 1),
('Gerente', 'Acceso a reportes y gestión limitada', 1),
('Empleado', 'Acceso limitado a funciones básicas', 1);
GO

-- Insertar Módulos del Sistema
INSERT INTO Modulos (Nombre, Descripcion, Ruta, Icono, Orden, Activo) VALUES
('Dashboard', 'Panel de control principal', '/dashboard', 'home', 1, 1),
('Empleados', 'Gestión de empleados', '/empleados', 'users', 2, 1),
('Departamentos', 'Gestión de departamentos', '/departamentos', 'briefcase', 3, 1),
('Puestos', 'Gestión de puestos de trabajo', '/puestos', 'clipboard', 4, 1),
('Beneficios', 'Beneficios y deducciones', '/beneficios', 'dollar-sign', 5, 1),
('Periodos', 'Períodos de nómina', '/periodos', 'calendar', 6, 1),
('Asistencia', 'Control de asistencia', '/asistencia', 'clock', 7, 1),
('Usuarios', 'Gestión de usuarios', '/seguridad/usuarios', 'user-check', 8, 1),
('Permisos', 'Gestión de permisos', '/seguridad/permisos', 'shield', 9, 1),
('Reportes', 'Reportes del sistema', '/reportes', 'bar-chart', 10, 1);
GO

-- Insertar Permisos para Rol: Administrador (acceso total)
INSERT INTO PermisosRol (IdRol, Modulo, Ver, Crear, Editar, Eliminar)
SELECT r.IdRol, m.Nombre, 1, 1, 1, 1
FROM Roles r
CROSS JOIN Modulos m
WHERE r.Nombre = 'Administrador';
GO

-- Insertar Permisos para Rol: RRHH
INSERT INTO PermisosRol (IdRol, Modulo, Ver, Crear, Editar, Eliminar)
SELECT r.IdRol, m.Nombre, 1, 1, 1, 1
FROM Roles r
CROSS JOIN Modulos m
WHERE r.Nombre = 'RRHH' 
  AND m.Nombre IN ('Dashboard', 'Empleados', 'Departamentos', 'Puestos', 'Beneficios', 'Periodos', 'Asistencia', 'Reportes');
GO

-- Insertar Permisos para Rol: Gerente
INSERT INTO PermisosRol (IdRol, Modulo, Ver, Crear, Editar, Eliminar)
SELECT r.IdRol, m.Nombre, 1, 0, 0, 0
FROM Roles r
CROSS JOIN Modulos m
WHERE r.Nombre = 'Gerente' 
  AND m.Nombre IN ('Dashboard', 'Empleados', 'Departamentos', 'Asistencia', 'Reportes');
GO

-- Insertar Permisos para Rol: Empleado
INSERT INTO PermisosRol (IdRol, Modulo, Ver, Crear, Editar, Eliminar)
SELECT r.IdRol, m.Nombre, 1, 0, 0, 0
FROM Roles r
CROSS JOIN Modulos m
WHERE r.Nombre = 'Empleado' 
  AND m.Nombre IN ('Dashboard');
GO

-- Usuario Administrador por defecto
-- Contraseña: admin123 (cambiar después del primer acceso)
INSERT INTO Usuarios (NombreUsuario, Correo, ClaveHash, IdRol, Activo)
VALUES ('admin', 'admin@sistema.com', 'admin123', 
    (SELECT IdRol FROM Roles WHERE Nombre = 'Administrador'), 1);
GO

-- Crear permisos personalizados para el usuario admin
INSERT INTO PermisosUsuarios (IdUsuario, IdModulo, Ver, Crear, Editar, Eliminar, TieneAcceso)
SELECT 
    u.IdUsuario,
    m.IdModulo,
    1, 1, 1, 1, 1
FROM Usuarios u
CROSS JOIN Modulos m
WHERE u.NombreUsuario = 'admin';
GO

-- Datos de ejemplo para Departamentos
INSERT INTO Departamentos (Nombre, Descripcion, Activo) VALUES
('Administración', 'Departamento de administración general', 1),
('Recursos Humanos', 'Gestión de personal', 1),
('Contabilidad', 'Departamento de contabilidad y finanzas', 1),
('Sistemas', 'Tecnologías de la información', 1),
('Ventas', 'Departamento de ventas', 1);
GO

-- Datos de ejemplo para Puestos
INSERT INTO Puestos (Titulo, Descripcion, IdDepartamento, SalarioBase, Activo) VALUES
('Gerente General', 'Gerente general de la empresa', 1, 15000.00, 1),
('Gerente de RRHH', 'Responsable de recursos humanos', 2, 12000.00, 1),
('Contador', 'Contador general', 3, 10000.00, 1),
('Desarrollador', 'Desarrollador de software', 4, 8000.00, 1),
('Vendedor', 'Ejecutivo de ventas', 5, 6000.00, 1),
('Asistente Administrativo', 'Asistente de administración', 1, 5000.00, 1);
GO

-- Datos de ejemplo para Beneficios y Deducciones
INSERT INTO BeneficiosDeducciones (Nombre, Descripcion, Tipo, Calculo, Valor, EsObligatorio, Activo) VALUES
('Salario Base', 'Salario base del empleado', 'Percepción', 'Fijo', 0, 1, 1),
('Bonificación Decreto 37-2001', 'Bonificación establecida por ley', 'Percepción', 'Fijo', 250.00, 1, 1),
('Horas Extra', 'Pago por horas extras trabajadas', 'Percepción', 'Fijo', 0, 0, 1),
('Comisiones', 'Comisiones por ventas', 'Percepción', 'Fijo', 0, 0, 1),
('IGSS (Empleado)', 'Aporte del empleado al IGSS', 'Deducción', 'Porcentaje', 4.83, 1, 1),
('ISR', 'Impuesto sobre la renta', 'Deducción', 'Fijo', 0, 1, 1),
('Anticipos', 'Anticipos de salario', 'Deducción', 'Fijo', 0, 0, 1);
GO

-- ========================================
-- ÍNDICES PARA MEJORAR RENDIMIENTO
-- ========================================

-- Índices en Empleados
CREATE INDEX IX_Empleados_Activo ON Empleados(Activo);
CREATE INDEX IX_Empleados_IdPuesto ON Empleados(IdPuesto);
GO

-- Índices en Usuarios
CREATE INDEX IX_Usuarios_Activo ON Usuarios(Activo);
CREATE INDEX IX_Usuarios_IdRol ON Usuarios(IdRol);
GO

-- Índices en Asistencia
CREATE INDEX IX_Asistencia_Fecha ON Asistencia(Fecha);
CREATE INDEX IX_Asistencia_IdEmpleado ON Asistencia(IdEmpleado);
GO

-- Índices en RegistrosNomina
CREATE INDEX IX_RegistrosNomina_IdPeriodo ON RegistrosNomina(IdPeriodo);
CREATE INDEX IX_RegistrosNomina_IdEmpleado ON RegistrosNomina(IdEmpleado);
GO

-- ========================================
-- VISTAS ÚTILES
-- ========================================

-- Vista: Empleados con información completa
CREATE VIEW vw_EmpleadosCompleto AS
SELECT 
    e.IdEmpleado,
    e.CodigoEmpleado,
    e.Nombres,
    e.Apellidos,
    e.Nombres + ' ' + e.Apellidos AS NombreCompleto,
    e.DPI,
    e.NIT,
    e.FechaNacimiento,
    e.Genero,
    e.Telefono,
    e.Correo,
    p.Titulo AS Puesto,
    d.Nombre AS Departamento,
    e.FechaIngreso,
    e.SalarioBase,
    e.Activo,
    DATEDIFF(YEAR, e.FechaIngreso, GETDATE()) AS AntiguedadAnios
FROM Empleados e
LEFT JOIN Puestos p ON e.IdPuesto = p.IdPuesto
LEFT JOIN Departamentos d ON p.IdDepartamento = d.IdDepartamento;
GO

-- Vista: Usuarios con información de rol
CREATE VIEW vw_UsuariosCompleto AS
SELECT 
    u.IdUsuario,
    u.NombreUsuario,
    u.Correo,
    r.Nombre AS Rol,
    u.Activo,
    u.FechaCreacion,
    u.UltimoAcceso,
    e.Nombres + ' ' + e.Apellidos AS EmpleadoAsociado
FROM Usuarios u
INNER JOIN Roles r ON u.IdRol = r.IdRol
LEFT JOIN Empleados e ON u.IdEmpleado = e.IdEmpleado;
GO

-- ========================================
-- SCRIPT COMPLETADO
-- ========================================
PRINT 'Base de datos creada exitosamente';
PRINT 'Usuario por defecto: admin / admin123';
PRINT 'IMPORTANTE: Cambiar la contraseña del administrador después del primer acceso';
GO
