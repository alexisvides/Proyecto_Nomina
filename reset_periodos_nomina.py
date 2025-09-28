from db import get_connection

SQL = r"""
-- Eliminar ItemsNomina dependientes de registros del/los periodos
DELETE i
FROM ItemsNomina i
JOIN RegistrosNomina rn ON rn.IdNomina = i.IdNomina;

-- Eliminar RegistrosNomina
DELETE FROM RegistrosNomina;

-- Eliminar PeriodosNomina
DELETE FROM PeriodosNomina;

-- Reiniciar identidad para que el próximo IdPeriodo sea 1
-- Nota: RESEED a 0 hace que el siguiente INSERT arranque en 1
DBCC CHECKIDENT ('PeriodosNomina', RESEED, 0);
"""

def run():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(SQL)
            conn.commit()

if __name__ == '__main__':
    run()
    print('Periodos de nómina reiniciados: tablas limpiadas y identidad restablecida. El próximo periodo tendrá Id=1.')
