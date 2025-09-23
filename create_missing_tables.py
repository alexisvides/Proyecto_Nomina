import os
from dotenv import load_dotenv
from db import get_connection

load_dotenv()

DDL_ASISTENCIAS = r'''
IF NOT EXISTS (
    SELECT 1 FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Asistencias]') AND type in (N'U')
)
BEGIN
    CREATE TABLE [dbo].[Asistencias] (
        [IdAsistencia] INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        [IdEmpleado] INT NOT NULL,
        [FechaHora] DATETIME2 NOT NULL CONSTRAINT DF_Asistencias_FechaHora DEFAULT (GETDATE()),
        [Tipo] VARCHAR(20) NOT NULL,
        [Observacion] VARCHAR(255) NULL,
        CONSTRAINT CK_Asistencias_Tipo CHECK ([Tipo] IN ('entrada','salida')),
        CONSTRAINT FK_Asistencias_Empleados FOREIGN KEY ([IdEmpleado])
            REFERENCES [dbo].[Empleados]([IdEmpleado]) ON DELETE CASCADE
    );

    -- Índices sugeridos
    CREATE INDEX IX_Asistencias_FechaHora ON [dbo].[Asistencias]([FechaHora] DESC);
    CREATE INDEX IX_Asistencias_IdEmpleado ON [dbo].[Asistencias]([IdEmpleado]);
END
'''


def ensure_tables():
    created = []
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Asistencias
            cur.execute(DDL_ASISTENCIAS)
            conn.commit()
            # Comprobar si existe ahora
            cur.execute("SELECT 1 FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Asistencias]') AND type = 'U'")
            if cur.fetchone():
                created.append('Asistencias (ok)')
    return created


if __name__ == '__main__':
    try:
        results = ensure_tables()
        if results:
            print('Verificación completada:')
            for r in results:
                print(f'- {r}')
        else:
            print('No se realizaron cambios (las tablas ya existían o no aplicaba).')
    except Exception as e:
        print(f'Error creando tablas faltantes: {e}')
