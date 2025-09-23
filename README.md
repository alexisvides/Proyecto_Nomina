# App Nómina (Login mínimo)

Este proyecto inicia con un módulo de login en Flask contra SQL Server. Está pensado para ser sencillo y escalable posteriormente con el resto de módulos (empleados, nómina, etc.).

## Requisitos (Windows)
- Python 3.10+
- ODBC Driver para SQL Server (recomendado 17 u 18). Descarga: https://learn.microsoft.com/sql/connect/odbc/download-odbc-driver-for-sql-server
- Tener una base de datos SQL Server accesible y con la tabla `Usuarios` del esquema proporcionado.

## Instalación
1. Crear y activar entorno virtual (opcional pero recomendado)
```
python -m venv .venv
.\.venv\Scripts\activate
```

2. Instalar dependencias
```
pip install -r requirements.txt
```

3. Configurar variables de entorno
- Copia `.env.example` a `.env` y completa los valores (SECRET_KEY, SQLSERVER_*).

4. Ejecutar la app
```
python app.py
```
La app iniciará en http://127.0.0.1:5000

## Notas de seguridad y hashing (bcrypt)
- El campo `ClaveHash` usa bcrypt (formato `$2a$`/`$2b$`) y se verifica con `bcrypt.checkpw`.
- Para crear un hash bcrypt en Python:
```python
import bcrypt

password = b"MiPasswordSeguro123"
salt = bcrypt.gensalt(rounds=12)
print(bcrypt.hashpw(password, salt).decode('utf-8'))
```
  Copia el resultado en `ClaveHash` al insertar en la tabla `Usuarios`.

Ejemplo de INSERT (ajusta columnas según tu esquema):
```sql
INSERT INTO Usuarios (NombreUsuario, Correo, ClaveHash, Activo)
VALUES ('admin', 'admin@ejemplo.com', '$2b$12$XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX', 1);
```

## Estructura
- `app.py`: aplicación Flask con rutas `/login`, `/logout`, `/dashboard`.
- `db.py`: utilitario para obtener conexión `pyodbc` a SQL Server.
- `templates/`: vistas Jinja2 (`login.html`, `dashboard.html`, `base.html`).
- `static/css/styles.css`: estilos con un diseño vistoso y moderno.
- `.env.example`: plantilla de configuración.
- `requirements.txt`: dependencias.

## Próximos pasos (futuros)
- Protección de rutas con decoradores.
- Gestión de roles basados en tablas `Roles` y `UsuarioRol`.
- Manejo de errores y logging estructurado.
- Registro de usuarios y recuperación de contraseña.

## Notas de conexión
- Por defecto se usa autenticación SQL (UID/PWD). Si prefieres autenticación integrada de Windows, puedes adaptar `db.py` para usar `Trusted_Connection=yes` y omitir `UID`/`PWD`.
