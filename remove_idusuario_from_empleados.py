from db import get_connection

SQL = r"""
-- Elimina todas las llaves foráneas relacionadas con IdUsuario
DECLARE fk_cursor CURSOR FOR
SELECT fk.name
FROM sys.foreign_keys fk
JOIN sys.foreign_key_columns fkc ON fkc.constraint_object_id = fk.object_id
JOIN sys.columns c ON c.object_id = fkc.parent_object_id AND c.column_id = fkc.parent_column_id
JOIN sys.tables t ON t.object_id = fk.parent_object_id
WHERE t.name = 'Empleados' AND c.name = 'IdUsuario';
DECLARE @fk sysname;
OPEN fk_cursor;
FETCH NEXT FROM fk_cursor INTO @fk;
WHILE @@FETCH_STATUS = 0
BEGIN
    DECLARE @sql nvarchar(max);
    SET @sql = N'ALTER TABLE dbo.Empleados DROP CONSTRAINT ' + QUOTENAME(@fk) + N';';
    EXEC sp_executesql @sql;
    FETCH NEXT FROM fk_cursor INTO @fk;
END
CLOSE fk_cursor;
DEALLOCATE fk_cursor;

-- Elimina todas las restricciones únicas relacionadas con IdUsuario
DECLARE uq_cursor CURSOR FOR
SELECT name FROM sys.objects WHERE type = 'UQ' AND object_id = OBJECT_ID('dbo.Empleados');
DECLARE @uq sysname;
OPEN uq_cursor;
FETCH NEXT FROM uq_cursor INTO @uq;
WHILE @@FETCH_STATUS = 0
BEGIN
    DECLARE @sql2 nvarchar(max);
    SET @sql2 = N'ALTER TABLE dbo.Empleados DROP CONSTRAINT ' + QUOTENAME(@uq) + N';';
    EXEC sp_executesql @sql2;
    FETCH NEXT FROM uq_cursor INTO @uq;
END
CLOSE uq_cursor;
DEALLOCATE uq_cursor;

-- Elimina todos los índices relacionados con IdUsuario
DECLARE idx_cursor CURSOR FOR
SELECT name FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.Empleados') AND name LIKE '%IdUsuario%';
DECLARE @idx sysname;
OPEN idx_cursor;
FETCH NEXT FROM idx_cursor INTO @idx;
WHILE @@FETCH_STATUS = 0
BEGIN
    DECLARE @sql3 nvarchar(max);
    SET @sql3 = N'DROP INDEX ' + QUOTENAME(@idx) + N' ON dbo.Empleados;';
    EXEC sp_executesql @sql3;
    FETCH NEXT FROM idx_cursor INTO @idx;
END
CLOSE idx_cursor;
DEALLOCATE idx_cursor;

-- Finalmente, elimina la columna
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
