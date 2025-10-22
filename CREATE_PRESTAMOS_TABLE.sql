-- ======================================================
-- SCRIPT: Crear tabla de Préstamos a Empleados
-- ======================================================

-- Tabla principal de Préstamos
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Prestamos')
BEGIN
    CREATE TABLE Prestamos (
        IdPrestamo INT IDENTITY(1,1) PRIMARY KEY,
        IdEmpleado INT NOT NULL,
        MontoTotal DECIMAL(18, 4) NOT NULL,
        MontoPendiente DECIMAL(18, 4) NOT NULL,
        TipoDescuento VARCHAR(20) NOT NULL CHECK (TipoDescuento IN ('fijo', 'porcentaje')),
        ValorDescuento DECIMAL(18, 4) NOT NULL, -- Monto fijo o % del salario
        FechaInicio DATE NOT NULL DEFAULT GETDATE(),
        FechaFin DATE NULL, -- Se completa cuando se paga
        Estado VARCHAR(20) NOT NULL DEFAULT 'activo' CHECK (Estado IN ('activo', 'pagado', 'cancelado')),
        Descripcion VARCHAR(500) NULL,
        FechaCreacion DATETIME2 NOT NULL DEFAULT GETDATE(),
        UsuarioCreacion INT NULL, -- IdUsuario que registró el préstamo
        CONSTRAINT FK_Prestamos_Empleado FOREIGN KEY (IdEmpleado) REFERENCES Empleados(IdEmpleado) ON DELETE CASCADE
    );
END
GO

-- Tabla de pagos/descuentos realizados
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'PrestamoPagos')
BEGIN
    CREATE TABLE PrestamoPagos (
        IdPago INT IDENTITY(1,1) PRIMARY KEY,
        IdPrestamo INT NOT NULL,
        IdPeriodo INT NOT NULL, -- Periodo en que se descontó
        IdNomina INT NULL, -- Registro de nómina asociado
        MontoPagado DECIMAL(18, 4) NOT NULL,
        FechaPago DATETIME2 NOT NULL DEFAULT GETDATE(),
        CONSTRAINT FK_PrestamoPagos_Prestamo FOREIGN KEY (IdPrestamo) REFERENCES Prestamos(IdPrestamo) ON DELETE CASCADE,
        CONSTRAINT FK_PrestamoPagos_Periodo FOREIGN KEY (IdPeriodo) REFERENCES PeriodosNomina(IdPeriodo),
        CONSTRAINT FK_PrestamoPagos_Nomina FOREIGN KEY (IdNomina) REFERENCES RegistrosNomina(IdNomina)
    );
END
GO

-- Índices para optimización
CREATE INDEX IX_Prestamos_Empleado ON Prestamos(IdEmpleado);
CREATE INDEX IX_Prestamos_Estado ON Prestamos(Estado);
CREATE INDEX IX_PrestamoPagos_Prestamo ON PrestamoPagos(IdPrestamo);
CREATE INDEX IX_PrestamoPagos_Periodo ON PrestamoPagos(IdPeriodo);
GO

PRINT 'Tabla de Préstamos creada exitosamente.';
GO
