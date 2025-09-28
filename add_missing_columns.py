import os
from dotenv import load_dotenv
from db import get_connection

load_dotenv()

SQL_ADD_NUMERO_IGSS = r'''
IF NOT EXISTS (
    SELECT 1 FROM sys.columns 
    WHERE Name = N'NumeroIGSS' AND Object_ID = OBJECT_ID(N'[dbo].[Empleados]')
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

DDL_EMPLEADO_BENEFICIOS = r'''
IF NOT EXISTS (
    SELECT 1 FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[EmpleadoBeneficios]') AND type in (N'U')
)
BEGIN
    CREATE TABLE [dbo].[EmpleadoBeneficios] (
        [IdEmpleado] INT NOT NULL,
        [IdBeneficioDeduccion] INT NOT NULL,
        [Activo] BIT NOT NULL DEFAULT (1),
        [TipoCalculo] VARCHAR(20) NULL, -- si NULL, usa el del catálogo
        [Valor] DECIMAL(18,4) NULL,     -- si NULL, usa el del catálogo
        CONSTRAINT PK_EmpleadoBeneficios PRIMARY KEY (IdEmpleado, IdBeneficioDeduccion),
        CONSTRAINT FK_EB_Empleado FOREIGN KEY (IdEmpleado) REFERENCES [dbo].[Empleados]([IdEmpleado]) ON DELETE CASCADE,
        CONSTRAINT FK_EB_Beneficio FOREIGN KEY (IdBeneficioDeduccion) REFERENCES [dbo].[BeneficiosDeducciones]([IdBeneficioDeduccion]) ON DELETE CASCADE
    );

    CREATE INDEX IX_EB_Beneficio ON [dbo].[EmpleadoBeneficios]([IdBeneficioDeduccion]);
END
'''

def add_missing_columns():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(SQL_ADD_NUMERO_IGSS)
            cur.execute(SQL_ADD_FECHA_FIN)
            cur.execute(SQL_ADD_FECHA_NAC)
            cur.execute(DDL_EMPLEADO_BENEFICIOS)
            conn.commit()

if __name__ == '__main__':
    try:
        add_missing_columns()
        print('Verificación/creación de columnas faltantes completada.')
    except Exception as e:
        print(f'Error actualizando tablas: {e}')
