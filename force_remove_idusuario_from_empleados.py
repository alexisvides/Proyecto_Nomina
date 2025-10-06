from db import get_connection

CONSTRAINTS = [
    'UQ__Empleado__5B65BF96DAA862D3',
    'UQ__Empleado__60695A19F16AD42B',
    'UQ__Empleado__049E81A9519CE192',
    'UQ__Empleado__324FED72F74620B9',
    'FK__Empleados__IdUsu__628FA481',
]

SQL_TEMPLATE = "ALTER TABLE dbo.Empleados DROP CONSTRAINT [{}];"
DROP_COLUMN_SQL = "ALTER TABLE dbo.Empleados DROP COLUMN IdUsuario;"


def run():
    with get_connection() as conn:
        with conn.cursor() as cur:
            for constraint in CONSTRAINTS:
                try:
                    cur.execute(SQL_TEMPLATE.format(constraint))
                    print(f"Restricción {constraint} eliminada.")
                except Exception as e:
                    print(f"No se pudo eliminar {constraint}: {e}")
            try:
                cur.execute(DROP_COLUMN_SQL)
                print("Columna IdUsuario eliminada de Empleados.")
            except Exception as e:
                print(f"No se pudo eliminar la columna IdUsuario: {e}")
            conn.commit()

if __name__ == '__main__':
    run()
