import os
import pyodbc
from typing import Optional


def _get_driver() -> str:
    # Intenta drivers comunes en Windows. Puedes cambiar por tu versión instalada.
    preferred = os.getenv("SQLSERVER_DRIVER")
    if preferred:
        return preferred
    candidates = [
        "{ODBC Driver 18 for SQL Server}",
        "{ODBC Driver 17 for SQL Server}",
        "{SQL Server}",
    ]
    for d in candidates:
        try:
            if d in pyodbc.drivers():
                return d
        except Exception:
            pass
    # fallback a 17 si no se puede detectar
    return "{ODBC Driver 17 for SQL Server}"


def _build_connection_string() -> str:
    server = "VICTUS-JAMES\\SQLSERVER"
    database = "proyecto"
    username = "sa"
    password = "123"
    driver = "{ODBC Driver 17 for SQL Server}"  # o 17 si lo tienes
    encrypt = "yes"
    trust = "yes"

    conn_str = (
        f"DRIVER={driver};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
        f"Encrypt={encrypt};"
        f"TrustServerCertificate={trust};"
    )
    return conn_str

def get_connection() -> pyodbc.Connection:
    conn_str = _build_connection_string()
    return pyodbc.connect(conn_str)
