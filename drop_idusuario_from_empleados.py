from db import get_connection

SQL = r"""
-- Drop possible foreign key constraint from Empleados(IdUsuario) to Usuarios(IdUsuario)
DECLARE @fk sysname;
SELECT @fk = fk.name
FROM sys.foreign_keys fk
JOIN sys.foreign_key_columns fkc ON fkc.constraint_object_id = fk.object_id
JOIN sys.columns c ON c.object_id = fkc.parent_object_id AND c.column_id = fkc.parent_column_id
JOIN sys.tables t ON t.object_id = fk.parent_object_id
WHERE t.name = 'Empleados' AND c.name = 'IdUsuario';
IF @fk IS NOT NULL
BEGIN
    DECLARE @sql nvarchar(max);
    SET @sql = N'ALTER TABLE dbo.Empleados DROP CONSTRAINT ' + QUOTENAME(@fk) + N';';
    EXEC sp_executesql @sql;
END

-- Drop unique constraint name if it exists (old auto-name) and filtered index if it exists
IF EXISTS (SELECT 1 FROM sys.objects WHERE name = 'UQ__Empleado__5B65BF960CF11B5F' AND type = 'UQ')
BEGIN
    ALTER TABLE dbo.Empleados DROP CONSTRAINT [UQ__Empleado__5B65BF960CF11B5F];
END
IF EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'UX_Empleados_IdUsuario_NN' AND object_id = OBJECT_ID('dbo.Empleados'))
BEGIN
    DROP INDEX [UX_Empleados_IdUsuario_NN] ON dbo.Empleados;
END

-- Finally, drop the column if it exists
IF EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.Empleados') AND name = 'IdUsuario')
BEGIN
    ALTER TABLE dbo.Empleados DROP COLUMN IdUsuario;
END
"""

def run():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(SQL)
            conn.commit()

if __name__ == '__main__':
    run()
    print('Columna IdUsuario eliminada de Empleados (incluyendo FK/índices asociados si existían).')
