import os
from dotenv import load_dotenv
from db import get_connection

load_dotenv()

SQL_ADD_NUMERO_IGSS = r'''
IF NOT EXISTS (
    SELECT 1 FROM sys.columns 
    WHERE Name = N'NumeroIGSS' AND Object_ID = Object_ID(N'[dbo].[Empleados]')
)
BEGIN
    ALTER TABLE [dbo].[Empleados]
    ADD [NumeroIGSS] VARCHAR(50) NULL;

    -- Índice sugerido para búsquedas por IGSS
    CREATE INDEX IX_Empleados_NumeroIGSS ON [dbo].[Empleados]([NumeroIGSS]);
END
'''

SQL_ADD_FECHA_FIN = r'''
IF NOT EXISTS (
    SELECT 1 FROM sys.columns 
    WHERE Name = N'FechaFin' AND Object_ID = Object_ID(N'[dbo].[Empleados]')
)
BEGIN
    ALTER TABLE [dbo].[Empleados]
    ADD [FechaFin] DATE NULL;
END
'''

SQL_ADD_FECHA_NAC = r'''
IF NOT EXISTS (
    SELECT 1 FROM sys.columns 
    WHERE Name = N'FechaNacimiento' AND Object_ID = Object_ID(N'[dbo].[Empleados]')
)
BEGIN
    ALTER TABLE [dbo].[Empleados]
    ADD [FechaNacimiento] DATE NULL;
END
'''

def add_missing_columns():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(SQL_ADD_NUMERO_IGSS)
            cur.execute(SQL_ADD_FECHA_FIN)
            cur.execute(SQL_ADD_FECHA_NAC)
            conn.commit()

if __name__ == '__main__':
    try:
        add_missing_columns()
        print('Verificación/creación de columnas faltantes completada.')
    except Exception as e:
        print(f'Error actualizando tablas: {e}')
