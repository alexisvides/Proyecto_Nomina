-- Script para agregar la columna IdEmpleado a la tabla Usuarios
-- Ejecuta este script en tu base de datos antes de usar la funcionalidad

-- Agregar columna IdEmpleado (NULL permitido porque no todos los usuarios serán empleados)
ALTER TABLE Usuarios
ADD IdEmpleado INT NULL;

-- Agregar Foreign Key para mantener integridad referencial
ALTER TABLE Usuarios
ADD CONSTRAINT FK_Usuarios_Empleados 
FOREIGN KEY (IdEmpleado) REFERENCES Empleados(IdEmpleado);

-- Crear índice para mejorar consultas
CREATE INDEX IX_Usuarios_IdEmpleado ON Usuarios(IdEmpleado);

PRINT 'Columna IdEmpleado agregada exitosamente a la tabla Usuarios';
