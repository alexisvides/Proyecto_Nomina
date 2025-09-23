import os
from dotenv import load_dotenv
from db import get_connection

load_dotenv()

ADMIN_USER = os.getenv("SEED_ADMIN_USER", "admin")
ADMIN_EMAIL = os.getenv("SEED_ADMIN_EMAIL", "admin@ejemplo.com")
ADMIN_PASS = os.getenv("SEED_ADMIN_PASS", "123")  # Texto plano temporal


def ensure_admin():
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Verificar si existe por usuario o correo
                cur.execute(
                    """
                    SELECT TOP 1 IdUsuario, NombreUsuario, Correo
                    FROM Usuarios
                    WHERE NombreUsuario = ? OR Correo = ?
                    """,
                    (ADMIN_USER, ADMIN_EMAIL),
                )
                row = cur.fetchone()
                if row:
                    print(f"Usuario admin ya existe: Id={row[0]}, Usuario={row[1]}, Correo={row[2]}")
                    return

                # Insertar admin con contraseña en texto plano (temporal)
                cur.execute(
                    """
                    INSERT INTO Usuarios (NombreUsuario, Correo, ClaveHash, Activo)
                    VALUES (?, ?, ?, 1)
                    """,
                    (ADMIN_USER, ADMIN_EMAIL, ADMIN_PASS),
                )
                conn.commit()
                print("Usuario admin creado con éxito (contraseña: 123)")
    except Exception as e:
        print(f"Error creando usuario admin: {e}")


if __name__ == "__main__":
    ensure_admin()
