from db import get_connection

SQL = r"""
-- Drop unique constraints (if they exist) and recreate as filtered unique indexes to allow multiple NULLs

-- DocumentoIdentidad
IF EXISTS (SELECT 1 FROM sys.objects WHERE name = 'UQ__Empleado__049E81A96FEFEC87' AND type = 'UQ')
BEGIN
    ALTER TABLE dbo.Empleados DROP CONSTRAINT [UQ__Empleado__049E81A96FEFEC87];
END
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'UX_Empleados_DocumentoIdentidad_NN')
BEGIN
    CREATE UNIQUE INDEX UX_Empleados_DocumentoIdentidad_NN ON dbo.Empleados(DocumentoIdentidad) WHERE DocumentoIdentidad IS NOT NULL;
END

-- CodigoEmpleado
IF EXISTS (SELECT 1 FROM sys.objects WHERE name = 'UQ__Empleado__324FED728B309EEC' AND type = 'UQ')
BEGIN
    ALTER TABLE dbo.Empleados DROP CONSTRAINT [UQ__Empleado__324FED728B309EEC];
END
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'UX_Empleados_CodigoEmpleado_NN')
BEGIN
    CREATE UNIQUE INDEX UX_Empleados_CodigoEmpleado_NN ON dbo.Empleados(CodigoEmpleado) WHERE CodigoEmpleado IS NOT NULL;
END

-- IdUsuario
IF EXISTS (SELECT 1 FROM sys.objects WHERE name = 'UQ__Empleado__5B65BF960CF11B5F' AND type = 'UQ')
BEGIN
    ALTER TABLE dbo.Empleados DROP CONSTRAINT [UQ__Empleado__5B65BF960CF11B5F];
END
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'UX_Empleados_IdUsuario_NN')
BEGIN
    CREATE UNIQUE INDEX UX_Empleados_IdUsuario_NN ON dbo.Empleados(IdUsuario) WHERE IdUsuario IS NOT NULL;
END

-- Correo
IF EXISTS (SELECT 1 FROM sys.objects WHERE name = 'UQ__Empleado__60695A191F6BCB6E' AND type = 'UQ')
BEGIN
    ALTER TABLE dbo.Empleados DROP CONSTRAINT [UQ__Empleado__60695A191F6BCB6E];
END
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'UX_Empleados_Correo_NN')
BEGIN
    CREATE UNIQUE INDEX UX_Empleados_Correo_NN ON dbo.Empleados(Correo) WHERE Correo IS NOT NULL;
END
"""

SQL_NULLABLE = r"""
-- Dynamically ALTER columns to NULL (preserving current type/length)
DECLARE @cols TABLE (ColName sysname);
INSERT INTO @cols(ColName) VALUES ('DocumentoIdentidad'), ('CodigoEmpleado'), ('IdUsuario'), ('Correo');

DECLARE @c sysname, @sql nvarchar(max);
DECLARE colcur CURSOR FOR SELECT ColName FROM @cols;
OPEN colcur;
FETCH NEXT FROM colcur INTO @c;
WHILE @@FETCH_STATUS = 0
BEGIN
    DECLARE @typename sysname, @length int, @prec int, @scale int, @nullable bit;
    SELECT @typename = t.name,
           @length = c.max_length,
           @prec = c.precision,
           @scale = c.scale,
           @nullable = c.is_nullable
    FROM sys.columns c
    JOIN sys.types t ON t.user_type_id = c.user_type_id
    WHERE c.object_id = OBJECT_ID('dbo.Empleados') AND c.name = @c;

    IF @typename IS NOT NULL
    BEGIN
        DECLARE @typeExpr nvarchar(200);
        IF @typename IN ('varchar','nvarchar','char','nchar','varbinary','binary')
            SET @typeExpr = QUOTENAME(@typename) + '(' + CASE WHEN @length = -1 THEN 'max' ELSE CONVERT(varchar(10), CASE WHEN @typename LIKE 'n%' THEN @length/2 ELSE @length END) END + ')';
        ELSE IF @typename IN ('decimal','numeric')
            SET @typeExpr = QUOTENAME(@typename) + '(' + CONVERT(varchar(10), @prec) + ',' + CONVERT(varchar(10), @scale) + ')';
        ELSE
            SET @typeExpr = QUOTENAME(@typename);

        SET @sql = N'ALTER TABLE dbo.Empleados ALTER COLUMN ' + QUOTENAME(@c) + N' ' + @typeExpr + N' NULL;';
        EXEC sp_executesql @sql;
    END

    FETCH NEXT FROM colcur INTO @c;
END
CLOSE colcur; DEALLOCATE colcur;
"""

def run():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(SQL)
            cur.execute(SQL_NULLABLE)
            conn.commit()

if __name__ == '__main__':
    run()
    print('Restricciones de Empleados relajadas y columnas actualizadas a NULLABLE.')
