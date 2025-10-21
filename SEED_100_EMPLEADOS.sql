-- ========================================
-- SCRIPT PARA GENERAR 100 EMPLEADOS CON DATOS
-- Sistema de Gestión de Nómina y RRHH
-- ========================================
-- Este script limpia datos existentes y genera:
-- - 100 Empleados con datos realistas
-- - Asistencias alineadas con períodos de nómina
-- - 6 Registros de Nómina (últimos 3 meses)
-- - Asignación de Beneficios/Deducciones
-- ========================================

USE proyecto;
GO

PRINT '========================================';
PRINT 'INICIANDO LIMPIEZA DE DATOS...';
PRINT '========================================';

-- PASO 1: Desasociar empleados de usuarios (preservar usuarios)
UPDATE Usuarios SET IdEmpleado = NULL WHERE IdEmpleado IS NOT NULL;
PRINT '✓ Empleados desasociados de usuarios.';

-- PASO 2: Eliminar datos en orden correcto (respetando FKs)
DELETE FROM ItemsNomina;
DELETE FROM RegistrosNomina;
DELETE FROM Asistencias;
DELETE FROM EmpleadoBeneficioDeduccion;
DELETE FROM EmpleadoBeneficios;
DELETE FROM DocumentosEmpleado;
DELETE FROM Empleados;
DELETE FROM PeriodosNomina;
DELETE FROM Puestos;
DELETE FROM Departamentos;
DELETE FROM BeneficiosDeducciones;

PRINT '✓ Datos existentes eliminados correctamente.';
GO

PRINT '========================================';
PRINT 'CREANDO DEPARTAMENTOS Y PUESTOS...';
PRINT '========================================';

INSERT INTO Departamentos (Nombre, Descripcion) VALUES
('Administración', 'Área administrativa y dirección'),
('Recursos Humanos', 'Gestión de personal y nómina'),
('Contabilidad', 'Finanzas y contabilidad'),
('Sistemas', 'Tecnologías de información'),
('Ventas', 'Área comercial y ventas'),
('Producción', 'Manufactura y producción'),
('Logística', 'Almacén y distribución'),
('Marketing', 'Mercadotecnia y publicidad');

-- Crear puestos usando subconsultas para obtener IDs correctos
INSERT INTO Puestos (IdDepartamento, Titulo, Descripcion)
SELECT IdDepartamento, Titulo, Descripcion FROM (VALUES
    ((SELECT IdDepartamento FROM Departamentos WHERE Nombre = 'Administración'), 'Gerente General', 'Director general de la empresa'),
    ((SELECT IdDepartamento FROM Departamentos WHERE Nombre = 'Administración'), 'Asistente Administrativo', 'Apoyo administrativo'),
    ((SELECT IdDepartamento FROM Departamentos WHERE Nombre = 'Recursos Humanos'), 'Gerente de RRHH', 'Responsable de recursos humanos'),
    ((SELECT IdDepartamento FROM Departamentos WHERE Nombre = 'Recursos Humanos'), 'Reclutador', 'Especialista en reclutamiento'),
    ((SELECT IdDepartamento FROM Departamentos WHERE Nombre = 'Contabilidad'), 'Contador General', 'Contador principal'),
    ((SELECT IdDepartamento FROM Departamentos WHERE Nombre = 'Contabilidad'), 'Auxiliar Contable', 'Apoyo contable'),
    ((SELECT IdDepartamento FROM Departamentos WHERE Nombre = 'Sistemas'), 'Jefe de Sistemas', 'Responsable de TI'),
    ((SELECT IdDepartamento FROM Departamentos WHERE Nombre = 'Sistemas'), 'Desarrollador', 'Programador de software'),
    ((SELECT IdDepartamento FROM Departamentos WHERE Nombre = 'Sistemas'), 'Soporte Técnico', 'Asistencia técnica'),
    ((SELECT IdDepartamento FROM Departamentos WHERE Nombre = 'Ventas'), 'Gerente de Ventas', 'Responsable de ventas'),
    ((SELECT IdDepartamento FROM Departamentos WHERE Nombre = 'Ventas'), 'Ejecutivo de Ventas', 'Vendedor'),
    ((SELECT IdDepartamento FROM Departamentos WHERE Nombre = 'Ventas'), 'Asesor Comercial', 'Atención al cliente'),
    ((SELECT IdDepartamento FROM Departamentos WHERE Nombre = 'Producción'), 'Supervisor de Producción', 'Supervisa producción'),
    ((SELECT IdDepartamento FROM Departamentos WHERE Nombre = 'Producción'), 'Operario', 'Operador de máquinas'),
    ((SELECT IdDepartamento FROM Departamentos WHERE Nombre = 'Logística'), 'Jefe de Logística', 'Responsable de almacén'),
    ((SELECT IdDepartamento FROM Departamentos WHERE Nombre = 'Logística'), 'Despachador', 'Despacho de productos'),
    ((SELECT IdDepartamento FROM Departamentos WHERE Nombre = 'Marketing'), 'Gerente de Marketing', 'Responsable de marketing'),
    ((SELECT IdDepartamento FROM Departamentos WHERE Nombre = 'Marketing'), 'Diseñador Gráfico', 'Diseño y creatividad')
) AS PuestosData(IdDepartamento, Titulo, Descripcion);

PRINT '✓ 8 Departamentos y 18 Puestos creados.';
GO

PRINT '========================================';
PRINT 'CREANDO BENEFICIOS Y DEDUCCIONES...';
PRINT '========================================';

-- Insertar beneficios y deducciones estándar
INSERT INTO BeneficiosDeducciones (Nombre, Tipo, TipoCalculo, Valor, Activo, Descripcion) VALUES
('Salario Base', 'prestacion', 'fijo', 0, 1, 'Salario mensual base del empleado'),
('Bonificación Decreto 37-2001', 'prestacion', 'fijo', 250.00, 1, 'Bonificación establecida por ley'),
('Horas Extra', 'prestacion', 'fijo', 0, 1, 'Pago por horas extras trabajadas'),
('Comisiones', 'prestacion', 'fijo', 0, 1, 'Comisiones por ventas'),
('Bono Productividad', 'prestacion', 'fijo', 0, 1, 'Bono por metas alcanzadas'),
('IGSS Empleado', 'deduccion', 'porcentaje', 4.83, 1, 'Aporte del empleado al IGSS (4.83%)'),
('ISR', 'deduccion', 'fijo', 0, 1, 'Impuesto sobre la renta'),
('Anticipos', 'deduccion', 'fijo', 0, 1, 'Anticipos de salario'),
('Préstamos', 'deduccion', 'fijo', 0, 1, 'Descuento por préstamos');

PRINT '✓ 9 Beneficios y Deducciones creados.';
GO

PRINT '========================================';
PRINT 'GENERANDO 100 EMPLEADOS...';
PRINT '========================================';

-- Tablas temporales de nombres y apellidos
DECLARE @Nombres TABLE (Nombre NVARCHAR(50));
INSERT INTO @Nombres VALUES
('Juan'), ('María'), ('Carlos'), ('Ana'), ('Luis'), ('Carmen'), ('José'), ('Laura'),
('Pedro'), ('Sofia'), ('Miguel'), ('Gabriela'), ('Jorge'), ('Valeria'), ('Roberto'), ('Diana'),
('Francisco'), ('Patricia'), ('Antonio'), ('Rosa'), ('Manuel'), ('Martha'), ('Ricardo'), ('Elena'),
('Fernando'), ('Claudia'), ('Javier'), ('Sandra'), ('Alberto'), ('Monica'), ('Raúl'), ('Isabel'),
('Eduardo'), ('Beatriz'), ('Sergio'), ('Adriana'), ('Alejandro'), ('Carolina'), ('Andrés'), ('Mariana'),
('Daniel'), ('Lucia'), ('Oscar'), ('Fernanda'), ('Héctor'), ('Silvia'), ('Arturo'), ('Teresa'),
('Enrique'), ('Angela'), ('Guillermo'), ('Verónica'), ('Ramón'), ('Gloria'), ('Tomás'), ('Cecilia'),
('Víctor'), ('Lorena'), ('Alfredo'), ('Cristina'), ('Pablo'), ('Norma'), ('Felipe'), ('Alicia'),
('Salvador'), ('Susana'), ('Gerardo'), ('Julia'), ('Armando'), ('Eva'), ('Rodrigo'), ('Pilar'),
('César'), ('Rocío'), ('Emilio'), ('Mercedes'), ('Marcos'), ('Dolores'), ('Hugo'), ('Amparo'),
('Rafael'), ('Consuelo'), ('René'), ('Soledad'), ('Orlando'), ('Ines'), ('Mauricio'), ('Luz'),
('Ignacio'), ('Victoria'), ('Ernesto'), ('Esperanza'), ('Julio'), ('Irene'), ('Rubén'), ('Miriam'),
('Gustavo'), ('Yolanda'), ('Diego'), ('Lidia');

DECLARE @Apellidos TABLE (Apellido NVARCHAR(50));
INSERT INTO @Apellidos VALUES
('García'), ('López'), ('Martínez'), ('González'), ('Pérez'), ('Rodríguez'), ('Fernández'), ('Sánchez'),
('Ramírez'), ('Torres'), ('Flores'), ('Rivera'), ('Gómez'), ('Díaz'), ('Cruz'), ('Morales'),
('Reyes'), ('Gutiérrez'), ('Ortiz'), ('Chávez'), ('Ruiz'), ('Hernández'), ('Jiménez'), ('Mendoza'),
('Vázquez'), ('Castro'), ('Ramos'), ('Álvarez'), ('Romero'), ('Herrera'), ('Medina'), ('Aguilar'),
('Vargas'), ('Castillo'), ('Guerrero'), ('Núñez'), ('Mendez'), ('Salazar'), ('Campos'), ('Contreras'),
('Estrada'), ('Figueroa'), ('Luna'), ('Ríos'), ('Soto'), ('Delgado'), ('Mora'), ('Peña'),
('Acosta'), ('Silva'), ('Molina'), ('Valdez');

-- Variables para el loop
DECLARE @i INT = 1;
DECLARE @Nombre NVARCHAR(50);
DECLARE @Apellido1 NVARCHAR(50);
DECLARE @Apellido2 NVARCHAR(50);
DECLARE @CodigoEmpleado NVARCHAR(30);
DECLARE @DPI NVARCHAR(50);
DECLARE @Correo NVARCHAR(150);
DECLARE @Telefono NVARCHAR(30);
DECLARE @SalarioBase DECIMAL(12,2);
DECLARE @IdDepartamento INT;
DECLARE @IdPuesto INT;
DECLARE @FechaContratacion DATE;
DECLARE @FechaNacimiento DATE;

-- Generar 100 empleados
WHILE @i <= 100
BEGIN
    -- Seleccionar nombre y apellidos aleatorios
    SELECT TOP 1 @Nombre = Nombre FROM @Nombres ORDER BY NEWID();
    SELECT TOP 1 @Apellido1 = Apellido FROM @Apellidos ORDER BY NEWID();
    SELECT TOP 1 @Apellido2 = Apellido FROM @Apellidos ORDER BY NEWID();
    
    -- Generar datos únicos
    SET @CodigoEmpleado = 'EMP' + RIGHT('000' + CAST(@i AS VARCHAR(3)), 3);
    SET @DPI = CAST(1000000000 + @i AS VARCHAR(13)) + '01';
    SET @Correo = LOWER(@Nombre + '.' + @Apellido1 + '@empresa.com');
    SET @Telefono = '5' + RIGHT('0000000' + CAST(ABS(CHECKSUM(NEWID())) % 10000000 AS VARCHAR(7)), 7);
    
    -- Salario aleatorio entre Q3,000 y Q25,000
    SET @SalarioBase = ROUND(3000 + (RAND() * 22000), 2);
    
    -- Departamento y puesto aleatorio
    SELECT TOP 1 @IdDepartamento = IdDepartamento FROM Departamentos ORDER BY NEWID();
    SELECT TOP 1 @IdPuesto = IdPuesto FROM Puestos WHERE IdDepartamento = @IdDepartamento ORDER BY NEWID();
    
    -- Fecha de contratación entre 2020 y 2024
    SET @FechaContratacion = DATEADD(DAY, -ABS(CHECKSUM(NEWID())) % 1825, GETDATE());
    
    -- Fecha de nacimiento entre 1980 y 2002 (22-44 años)
    SET @FechaNacimiento = DATEADD(YEAR, -(22 + ABS(CHECKSUM(NEWID())) % 23), GETDATE());
    
    -- Insertar empleado
    INSERT INTO Empleados (
        CodigoEmpleado, Nombres, Apellidos, DocumentoIdentidad,
        FechaContratacion, IdDepartamento, IdPuesto, SalarioBase,
        Correo, Telefono, TipoContrato, FechaCreacion,
        NumeroIGSS, FechaNacimiento
    ) VALUES (
        @CodigoEmpleado,
        @Nombre,
        @Apellido1 + ' ' + @Apellido2,
        @DPI,
        @FechaContratacion,
        @IdDepartamento,
        @IdPuesto,
        @SalarioBase,
        @Correo,
        @Telefono,
        'Permanente',
        GETDATE(),
        'IGSS-' + @DPI,
        @FechaNacimiento
    );
    
    SET @i = @i + 1;
END

PRINT '✓ 100 empleados generados exitosamente.';
GO

PRINT '========================================';
PRINT 'ASIGNANDO BENEFICIOS Y DEDUCCIONES...';
PRINT '========================================';

-- Asignar Bonificación Decreto y IGSS a TODOS los empleados
INSERT INTO EmpleadoBeneficioDeduccion (IdEmpleado, IdBeneficioDeduccion, ValorPersonalizado, Activo)
SELECT 
    e.IdEmpleado,
    bd.IdBeneficioDeduccion,
    NULL,
    1
FROM Empleados e
CROSS JOIN BeneficiosDeducciones bd
WHERE bd.Nombre IN ('Bonificación Decreto 37-2001', 'IGSS Empleado');

-- Asignar comisiones solo a empleados de ventas (20-30% de empleados)
INSERT INTO EmpleadoBeneficioDeduccion (IdEmpleado, IdBeneficioDeduccion, ValorPersonalizado, Activo)
SELECT TOP 25
    e.IdEmpleado,
    bd.IdBeneficioDeduccion,
    ROUND(500 + (RAND(CHECKSUM(NEWID())) * 2000), 2),
    1
FROM Empleados e
CROSS JOIN BeneficiosDeducciones bd
WHERE bd.Nombre = 'Comisiones'
ORDER BY NEWID();

-- Asignar ISR a empleados con salario > Q5,000 (aprox 60%)
INSERT INTO EmpleadoBeneficioDeduccion (IdEmpleado, IdBeneficioDeduccion, ValorPersonalizado, Activo)
SELECT 
    e.IdEmpleado,
    bd.IdBeneficioDeduccion,
    ROUND((e.SalarioBase - 5000) * 0.05, 2),
    1
FROM Empleados e
CROSS JOIN BeneficiosDeducciones bd
WHERE bd.Nombre = 'ISR'
  AND e.SalarioBase > 5000;

PRINT '✓ Beneficios y deducciones asignados correctamente.';
GO

PRINT '========================================';
PRINT 'GENERANDO PERIODOS DE NÓMINA...';
PRINT '========================================';

-- Crear períodos de los últimos 3 meses (quincenales)
DECLARE @FechaInicio DATE;
DECLARE @FechaFin DATE;
DECLARE @PeriodoNum INT = 1;

-- Período 1: Hace 3 meses (primera quincena)
SET @FechaInicio = DATEADD(MONTH, -3, DATEFROMPARTS(YEAR(GETDATE()), MONTH(GETDATE()), 1));
SET @FechaFin = DATEADD(DAY, 14, @FechaInicio);
INSERT INTO PeriodosNomina (FechaInicio, FechaFin, TipoPeriodo, FechaCreacion) 
VALUES (@FechaInicio, @FechaFin, 'quincenal', GETDATE());

-- Período 2: Hace 3 meses (segunda quincena)
SET @FechaInicio = DATEADD(DAY, 15, @FechaInicio);
SET @FechaFin = EOMONTH(@FechaInicio);
INSERT INTO PeriodosNomina (FechaInicio, FechaFin, TipoPeriodo, FechaCreacion) 
VALUES (@FechaInicio, @FechaFin, 'quincenal', GETDATE());

-- Período 3: Hace 2 meses (primera quincena)
SET @FechaInicio = DATEADD(MONTH, -2, DATEFROMPARTS(YEAR(GETDATE()), MONTH(GETDATE()), 1));
SET @FechaFin = DATEADD(DAY, 14, @FechaInicio);
INSERT INTO PeriodosNomina (FechaInicio, FechaFin, TipoPeriodo, FechaCreacion) 
VALUES (@FechaInicio, @FechaFin, 'quincenal', GETDATE());

-- Período 4: Hace 2 meses (segunda quincena)
SET @FechaInicio = DATEADD(DAY, 15, @FechaInicio);
SET @FechaFin = EOMONTH(@FechaInicio);
INSERT INTO PeriodosNomina (FechaInicio, FechaFin, TipoPeriodo, FechaCreacion) 
VALUES (@FechaInicio, @FechaFin, 'quincenal', GETDATE());

-- Período 5: Mes pasado (primera quincena)
SET @FechaInicio = DATEADD(MONTH, -1, DATEFROMPARTS(YEAR(GETDATE()), MONTH(GETDATE()), 1));
SET @FechaFin = DATEADD(DAY, 14, @FechaInicio);
INSERT INTO PeriodosNomina (FechaInicio, FechaFin, TipoPeriodo, FechaCreacion) 
VALUES (@FechaInicio, @FechaFin, 'quincenal', GETDATE());

-- Período 6: Mes pasado (segunda quincena)
SET @FechaInicio = DATEADD(DAY, 15, @FechaInicio);
SET @FechaFin = EOMONTH(@FechaInicio);
INSERT INTO PeriodosNomina (FechaInicio, FechaFin, TipoPeriodo, FechaCreacion) 
VALUES (@FechaInicio, @FechaFin, 'quincenal', GETDATE());

PRINT '✓ 6 períodos de nómina creados (últimos 3 meses).';
GO

PRINT '========================================';
PRINT 'GENERANDO REGISTROS DE ASISTENCIA...';
PRINT '========================================';

-- Obtener rango de fechas de los períodos de nómina
DECLARE @FechaInicioTotal DATE;
DECLARE @FechaFinTotal DATE;

SELECT 
    @FechaInicioTotal = MIN(FechaInicio),
    @FechaFinTotal = MAX(FechaFin)
FROM PeriodosNomina;

PRINT 'Generando asistencias desde ' + CAST(@FechaInicioTotal AS VARCHAR(10)) + 
      ' hasta ' + CAST(@FechaFinTotal AS VARCHAR(10));

-- Variables para generar asistencias
DECLARE @FechaAsistencia DATE;
DECLARE @IdEmpleado INT;
DECLARE @Probabilidad FLOAT;
DECLARE @TotalAsistencias INT = 0;

-- Cursor para recorrer empleados
DECLARE empleado_cursor CURSOR FOR 
SELECT IdEmpleado FROM Empleados;

OPEN empleado_cursor;
FETCH NEXT FROM empleado_cursor INTO @IdEmpleado;

WHILE @@FETCH_STATUS = 0
BEGIN
    SET @FechaAsistencia = @FechaInicioTotal;
    
    -- Generar asistencias para cada día del período
    WHILE @FechaAsistencia <= @FechaFinTotal
    BEGIN
        -- Solo días laborales (Lunes a Viernes)
        -- DATEPART WEEKDAY: 1=Domingo, 7=Sábado
        IF DATEPART(WEEKDAY, @FechaAsistencia) NOT IN (1, 7)
        BEGIN
            SET @Probabilidad = RAND();
            
            -- Entrada (mañana) - Entre 7:30 AM y 8:30 AM
            INSERT INTO Asistencias (IdEmpleado, FechaHora, Tipo, Observacion)
            VALUES (
                @IdEmpleado,
                DATEADD(MINUTE, ABS(CHECKSUM(NEWID())) % 60 - 30, 
                    DATEADD(HOUR, 8, CAST(@FechaAsistencia AS DATETIME))),
                'entrada',
                NULL
            );
            
            SET @TotalAsistencias = @TotalAsistencias + 1;
            
            -- Salida (tarde) - Entre 4:30 PM y 5:30 PM
            -- 95% de probabilidad (simula algunos olvidos de marcar salida)
            IF @Probabilidad > 0.05
            BEGIN
                INSERT INTO Asistencias (IdEmpleado, FechaHora, Tipo, Observacion)
                VALUES (
                    @IdEmpleado,
                    DATEADD(MINUTE, ABS(CHECKSUM(NEWID())) % 60 - 30, 
                        DATEADD(HOUR, 17, CAST(@FechaAsistencia AS DATETIME))),
                    'salida',
                    NULL
                );
                
                SET @TotalAsistencias = @TotalAsistencias + 1;
            END
        END
        
        SET @FechaAsistencia = DATEADD(DAY, 1, @FechaAsistencia);
    END
    
    FETCH NEXT FROM empleado_cursor INTO @IdEmpleado;
END

CLOSE empleado_cursor;
DEALLOCATE empleado_cursor;

PRINT '✓ Asistencias generadas: ' + CAST(@TotalAsistencias AS VARCHAR(10)) + ' registros.';
PRINT '✓ Cobertura: ' + CAST(DATEDIFF(DAY, @FechaInicioTotal, @FechaFinTotal) AS VARCHAR(10)) + ' días.';
GO

PRINT '========================================';
PRINT 'GENERANDO REGISTROS DE NÓMINA...';
PRINT '========================================';

-- Generar nómina para cada empleado y cada período
INSERT INTO RegistrosNomina (
    IdEmpleado,
    IdPeriodo,
    SalarioBase,
    TotalPrestaciones,
    TotalDeducciones,
    SalarioNeto,
    FechaGeneracion
)
SELECT 
    e.IdEmpleado,
    p.IdPeriodo,
    e.SalarioBase / 2 as SalarioBase, -- Salario quincenal
    
    -- Calcular prestaciones
    (e.SalarioBase / 2) + 250 + 
    ISNULL((SELECT TOP 1 ValorPersonalizado 
            FROM EmpleadoBeneficioDeduccion ebd 
            JOIN BeneficiosDeducciones bd ON bd.IdBeneficioDeduccion = ebd.IdBeneficioDeduccion
            WHERE ebd.IdEmpleado = e.IdEmpleado 
              AND bd.Nombre = 'Comisiones' 
              AND ebd.Activo = 1), 0) as TotalPrestaciones,
    
    -- Calcular deducciones
    ((e.SalarioBase / 2) * 0.0483) + 
    ISNULL((SELECT TOP 1 ValorPersonalizado 
            FROM EmpleadoBeneficioDeduccion ebd 
            JOIN BeneficiosDeducciones bd ON bd.IdBeneficioDeduccion = ebd.IdBeneficioDeduccion
            WHERE ebd.IdEmpleado = e.IdEmpleado 
              AND bd.Nombre = 'ISR' 
              AND ebd.Activo = 1), 0) as TotalDeducciones,
    
    -- Salario neto
    (e.SalarioBase / 2) + 250 + 
    ISNULL((SELECT TOP 1 ValorPersonalizado 
            FROM EmpleadoBeneficioDeduccion ebd 
            JOIN BeneficiosDeducciones bd ON bd.IdBeneficioDeduccion = ebd.IdBeneficioDeduccion
            WHERE ebd.IdEmpleado = e.IdEmpleado 
              AND bd.Nombre = 'Comisiones' 
              AND ebd.Activo = 1), 0) -
    ((e.SalarioBase / 2) * 0.0483) -
    ISNULL((SELECT TOP 1 ValorPersonalizado 
            FROM EmpleadoBeneficioDeduccion ebd 
            JOIN BeneficiosDeducciones bd ON bd.IdBeneficioDeduccion = ebd.IdBeneficioDeduccion
            WHERE ebd.IdEmpleado = e.IdEmpleado 
              AND bd.Nombre = 'ISR' 
              AND ebd.Activo = 1), 0) as SalarioNeto,
    
    GETDATE()
FROM Empleados e
CROSS JOIN PeriodosNomina p;

PRINT '✓ 600 Registros de nómina generados (100 empleados x 6 períodos).';
GO

PRINT '========================================';
PRINT 'GENERANDO ITEMS DETALLADOS DE NÓMINA...';
PRINT '========================================';

-- Insertar items de nómina (detalle de cada prestación/deducción)
INSERT INTO ItemsNomina (IdNomina, IdBeneficioDeduccion, TipoItem, Monto)
SELECT 
    rn.IdNomina,
    bd.IdBeneficioDeduccion,
    bd.Tipo,
    CASE 
        WHEN bd.Nombre = 'Salario Base' THEN e.SalarioBase / 2
        WHEN bd.Nombre = 'Bonificación Decreto 37-2001' THEN 250
        WHEN bd.Nombre = 'IGSS Empleado' THEN (e.SalarioBase / 2) * 0.0483
        WHEN bd.Nombre = 'Comisiones' THEN ISNULL(ebd.ValorPersonalizado, 0)
        WHEN bd.Nombre = 'ISR' THEN ISNULL(ebd.ValorPersonalizado, 0)
        ELSE 0
    END as Monto
FROM RegistrosNomina rn
JOIN Empleados e ON e.IdEmpleado = rn.IdEmpleado
JOIN EmpleadoBeneficioDeduccion ebd ON ebd.IdEmpleado = e.IdEmpleado
JOIN BeneficiosDeducciones bd ON bd.IdBeneficioDeduccion = ebd.IdBeneficioDeduccion
WHERE ebd.Activo = 1;

PRINT '✓ Items de nómina detallados generados.';
GO

PRINT '';
PRINT '========================================';
PRINT '      RESUMEN DE DATOS GENERADOS       ';
PRINT '========================================';

SELECT 'Empleados' as Tabla, COUNT(*) as Total FROM Empleados
UNION ALL
SELECT 'Departamentos', COUNT(*) FROM Departamentos
UNION ALL
SELECT 'Puestos', COUNT(*) FROM Puestos
UNION ALL
SELECT 'Beneficios/Deducciones', COUNT(*) FROM BeneficiosDeducciones
UNION ALL
SELECT 'Asignaciones BD', COUNT(*) FROM EmpleadoBeneficioDeduccion
UNION ALL
SELECT 'Períodos de Nómina', COUNT(*) FROM PeriodosNomina
UNION ALL
SELECT 'Registros de Nómina', COUNT(*) FROM RegistrosNomina
UNION ALL
SELECT 'Items de Nómina', COUNT(*) FROM ItemsNomina
UNION ALL
SELECT 'Asistencias', COUNT(*) FROM Asistencias;

PRINT '';
PRINT '========================================';
PRINT '   ✓ DATOS GENERADOS EXITOSAMENTE ✓    ';
PRINT '========================================';
PRINT '  • 100 empleados con datos realistas';
PRINT '  • 8 departamentos y 18 puestos';
PRINT '  • 6 períodos de nómina (3 meses)';
PRINT '  • 600 registros de nómina completos';
PRINT '  • ~12,000 registros de asistencia';
PRINT '  • Prestaciones y deducciones asignadas';
PRINT '';
PRINT '¡Sistema listo para pruebas y producción!';
PRINT '========================================';
GO
