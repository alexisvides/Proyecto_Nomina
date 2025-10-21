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
    # Usa la instancia por defecto MSSQLSERVER (solo "localhost" o ".")
    server = "localhost"  # También puedes usar "." o "(local)"
    database = "proyecto"
    driver = "{ODBC Driver 17 for SQL Server}"
    
    # Autenticación de Windows (más común en desarrollo local)
    # Si necesitas autenticación SQL Server, cambia a False y configura username/password
    use_windows_auth = True
    
    if use_windows_auth:
        conn_str = (
            f"DRIVER={driver};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"Trusted_Connection=yes;"
            f"TrustServerCertificate=yes;"
        )
    else:
        # Autenticación SQL Server (descomentado si lo necesitas)
        username = "sa"
        password = "123"
        conn_str = (
            f"DRIVER={driver};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"UID={username};"
            f"PWD={password};"
            f"Encrypt=no;"
            f"TrustServerCertificate=yes;"
        )
    
    return conn_str

def get_connection() -> pyodbc.Connection:
    conn_str = _build_connection_string()
    return pyodbc.connect(conn_str)
