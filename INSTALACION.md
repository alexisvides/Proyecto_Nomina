# 🚀 Guía de Instalación y Configuración - Sistema de Nómina

Esta guía te ayudará a configurar el proyecto en cualquier equipo Windows.

## 📋 Requisitos Previos

### Software Necesario:
1. **Python 3.8 o superior**
   - Descarga: https://www.python.org/downloads/
   - ✅ Asegúrate de marcar "Add Python to PATH" durante la instalación

2. **SQL Server** (cualquier edición)
   - SQL Server Express: https://www.microsoft.com/sql-server/sql-server-downloads
   - O SQL Server Developer/Standard/Enterprise

3. **ODBC Driver for SQL Server**
   - ODBC Driver 17 o 18: https://learn.microsoft.com/sql/connect/odbc/download-odbc-driver-for-sql-server
   - Usualmente se instala con SQL Server

## 🎯 Método 1: Instalación Automática (Recomendado)

### Paso 1: Descargar el Proyecto
```powershell
git clone https://github.com/tu-usuario/Proyecto_Nomina.git
cd Proyecto_Nomina
```

O descarga el ZIP y extráelo.

### Paso 2: Ejecutar Script de Configuración
```powershell
# Permitir ejecución de scripts (solo la primera vez)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Ejecutar configuración automática
.\setup.ps1
```

El script automáticamente:
- ✅ Verifica Python instalado
- ✅ Crea el entorno virtual
- ✅ Instala todas las dependencias
- ✅ Verifica SQL Server
- ✅ Crea archivo `.env`
- ✅ Prueba la conexión
- ✅ Ofrece ejecutar la aplicación

### Paso 3: Configurar Base de Datos

Si aún no tienes la base de datos creada:

```powershell
# Opción A: Usar SQL Server Management Studio (SSMS)
# 1. Abre SSMS
# 2. Conéctate a tu servidor
# 3. Abre el archivo CREATE_DATABASE_COMPLETE.sql
# 4. Ejecuta el script (F5)

# Opción B: Desde línea de comandos
sqlcmd -S localhost -E -i CREATE_DATABASE_COMPLETE.sql
```

### Paso 4: Ejecutar la Aplicación
```powershell
# Activar entorno virtual
.venv\Scripts\Activate.ps1

# Ejecutar aplicación
python app.py
```

Abre tu navegador en: **http://127.0.0.1:5000**

---

## 🔧 Método 2: Instalación Manual

### Paso 1: Crear Entorno Virtual
```powershell
python -m venv .venv
```

### Paso 2: Activar Entorno Virtual
```powershell
.venv\Scripts\Activate.ps1
```

Si tienes error de permisos:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Paso 3: Actualizar pip
```powershell
python -m pip install --upgrade pip
```

### Paso 4: Instalar Dependencias
```powershell
pip install flask python-dotenv pyodbc reportlab
```

O si existe `requirements.txt`:
```powershell
pip install -r requirements.txt
```

### Paso 5: Configurar Conexión a Base de Datos

Edita `db.py` y ajusta los parámetros:
- `server`: Nombre de tu servidor (ej: `localhost`, `.`, `servidor\instancia`)
- `database`: Nombre de tu base de datos (ej: `proyecto`)
- `use_windows_auth`: `True` para Windows Auth, `False` para SQL Auth

### Paso 6: Verificar Conexión
```powershell
python test_conexion.py
```

### Paso 7: Ejecutar Aplicación
```powershell
python app.py
```

---

## ⚙️ Configuración Avanzada

### Archivo `.env` (Opcional)
Crea un archivo `.env` en la raíz del proyecto:

```env
SECRET_KEY=tu-clave-secreta-super-segura
FLASK_ENV=development
FLASK_DEBUG=True

DB_SERVER=localhost
DB_NAME=proyecto
USE_WINDOWS_AUTH=True

IGSS_PCT=4.83
PORT=5000
```

### Configurar SQL Server Authentication (en lugar de Windows Auth)

Edita `db.py`, línea 34:
```python
use_windows_auth = False  # Cambiar a False
```

Y configura usuario/contraseña en las líneas 46-47:
```python
username = "tu_usuario"
password = "tu_contraseña"
```

---

## 🔐 Credenciales Iniciales

### Usuario Administrador:
- **Usuario**: `admin`
- **Contraseña**: Consulta la tabla `Usuarios` en la base de datos

Para asignar todos los permisos al admin:
```powershell
python scripts\ejecutar_permisos_admin.py
```

---

## 🐛 Solución de Problemas

### Error: "Python no reconocido"
**Solución**: Reinstala Python y marca "Add to PATH"

### Error: "SQL Server no está corriendo"
**Solución**: 
```powershell
# Verificar servicio
Get-Service -Name MSSQLSERVER

# Iniciar servicio (requiere admin)
Start-Service -Name MSSQLSERVER
```

### Error: "Login failed for user"
**Solución**: 
- Verifica que SQL Server permita autenticación mixta (SQL + Windows)
- O usa Windows Authentication (recomendado)

### Error: "ODBC Driver no encontrado"
**Solución**: Instala ODBC Driver 17 o 18 desde el link en requisitos

### Error: "Invalid column name"
**Solución**: 
- Verifica que ejecutaste el script `CREATE_DATABASE_COMPLETE.sql`
- Verifica que la base de datos se llama `proyecto`

### Puerto 5000 en uso
**Solución**: Cambia el puerto en `app.py` línea final:
```python
app.run(debug=True, port=5001)  # Cambiar a otro puerto
```

---

## 📁 Estructura del Proyecto

```
Proyecto_Nomina/
├── app.py                  # Aplicación principal Flask
├── db.py                   # Conexión a base de datos
├── setup.ps1              # Script de instalación automática
├── test_conexion.py       # Script de prueba de conexión
├── CREATE_DATABASE_COMPLETE.sql  # Script de creación de BD
├── .env                   # Configuración (crear manualmente)
├── .venv/                 # Entorno virtual (se crea automáticamente)
├── templates/             # Plantillas HTML
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   └── ...
├── static/
│   └── css/
│       └── styles.css
└── scripts/
    ├── ejecutar_permisos_admin.py
    └── DATOS_100_EMPLEADOS.sql
```

---

## 📚 Comandos Útiles

```powershell
# Activar entorno virtual
.venv\Scripts\Activate.ps1

# Desactivar entorno virtual
deactivate

# Ver paquetes instalados
pip list

# Actualizar un paquete
pip install --upgrade nombre-paquete

# Congelar dependencias
pip freeze > requirements.txt

# Verificar base de datos
python test_conexion.py

# Asignar permisos admin
python scripts\ejecutar_permisos_admin.py

# Ver logs de SQL Server
Get-EventLog -LogName Application -Source "MSSQL*" -Newest 10
```

---

## 🎯 Próximos Pasos Después de la Instalación

1. ✅ Verifica que puedes acceder al login
2. ✅ Inicia sesión con el usuario admin
3. ✅ Explora los módulos disponibles
4. ✅ Crea algunos empleados de prueba
5. ✅ Genera un periodo de nómina
6. ✅ Procesa la nómina

---

## 📞 Soporte

Si tienes problemas durante la instalación:

1. Ejecuta el diagnóstico:
   ```powershell
   python test_conexion.py
   ```

2. Verifica los logs en la consola donde ejecutas `app.py`

3. Revisa la sección de "Solución de Problemas" arriba

---

## 📝 Notas Importantes

- ⚠️ Este proyecto está configurado para desarrollo local
- ⚠️ No uses las credenciales por defecto en producción
- ⚠️ Cambia el `SECRET_KEY` antes de desplegar
- ⚠️ Habilita HTTPS en producción
- ⚠️ Configura backups regulares de la base de datos

---

**¡Listo! 🎉 Tu sistema de nómina está configurado y listo para usar.**
