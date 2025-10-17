# 📚 Guía de Instalación de Base de Datos

## 🎯 Descripción

Este documento explica cómo instalar y configurar la base de datos del Sistema de Gestión de Nómina y RRHH desde cero.

---

## 📋 Requisitos Previos

- **SQL Server** 2016 o superior instalado
- **SQL Server Management Studio (SSMS)** o Azure Data Studio
- Permisos de administrador en SQL Server
- Python 3.8+ (para ejecutar la aplicación)

---

## 🚀 Instalación Paso a Paso

### **Opción 1: Instalación Completa (Recomendada)**

Esta opción crea la base de datos completa con todos los datos iniciales.

#### **Paso 1: Abrir el Script**
1. Abre **SQL Server Management Studio (SSMS)**
2. Conéctate a tu servidor SQL Server
3. Ve a: `File > Open > File...`
4. Selecciona: `CREATE_DATABASE_COMPLETE.sql`

#### **Paso 2: Revisar el Script**
⚠️ **IMPORTANTE**: El script eliminará la base de datos `NominaDB` si ya existe.

Revisa las primeras líneas:
```sql
-- Eliminar base de datos si existe (CUIDADO: esto borra todos los datos)
IF EXISTS (SELECT name FROM sys.databases WHERE name = 'NominaDB')
BEGIN
    ALTER DATABASE NominaDB SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE NominaDB;
END
```

#### **Paso 3: Ejecutar el Script**
1. Presiona `F5` o click en **Execute**
2. Espera a que termine (puede tardar 1-2 minutos)
3. Verifica que no haya errores en el panel de mensajes

#### **Paso 4: Verificar la Instalación**
Ejecuta esta consulta para verificar:
```sql
USE NominaDB;

-- Ver todas las tablas creadas
SELECT TABLE_NAME 
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_TYPE = 'BASE TABLE'
ORDER BY TABLE_NAME;

-- Ver usuario administrador
SELECT * FROM Usuarios;

-- Ver roles creados
SELECT * FROM Roles;

-- Ver módulos del sistema
SELECT * FROM Modulos;
```

---

### **Opción 2: Instalación Manual por Secciones**

Si prefieres ejecutar el script en partes:

#### **1. Crear Base de Datos**
```sql
USE master;
CREATE DATABASE NominaDB;
USE NominaDB;
```

#### **2. Crear Tablas de Seguridad**
Ejecuta las secciones:
- Roles
- Modulos
- PermisosRol
- Usuarios
- PermisosUsuarios
- Auditoria

#### **3. Crear Tablas Organizacionales**
- Departamentos
- Puestos
- Empleados

#### **4. Crear Tablas de Nómina**
- BeneficiosDeducciones
- EmpleadoBeneficiosDeduccioness
- Periodos
- RegistrosNomina
- ItemsNomina

#### **5. Crear Tablas de Asistencia**
- Asistencia

#### **6. Insertar Datos Iniciales**
- Roles
- Módulos
- Permisos
- Usuario admin
- Datos de ejemplo

---

## 🔑 Credenciales Iniciales

Después de la instalación, el sistema tendrá un usuario administrador:

- **Usuario:** `admin`
- **Contraseña:** `admin123`
- **Correo:** `admin@sistema.com`

⚠️ **IMPORTANTE**: Cambia esta contraseña inmediatamente después del primer acceso.

---

## 📊 Estructura de la Base de Datos

### **Tablas Principales**

| Tabla | Descripción | Registros Iniciales |
|-------|-------------|---------------------|
| `Roles` | Roles del sistema | 4 roles |
| `Modulos` | Módulos del sistema | 10 módulos |
| `Usuarios` | Usuarios del sistema | 1 (admin) |
| `PermisosUsuarios` | Permisos personalizados | 10 (admin) |
| `Empleados` | Empleados de la empresa | 0 |
| `Departamentos` | Departamentos | 5 ejemplos |
| `Puestos` | Puestos de trabajo | 6 ejemplos |
| `BeneficiosDeducciones` | Beneficios/Deducciones | 7 ejemplos |
| `Periodos` | Períodos de nómina | 0 |
| `RegistrosNomina` | Registros de nómina | 0 |
| `Asistencia` | Control de asistencia | 0 |
| `Auditoria` | Log de auditoría | 0 |

### **Relaciones (Foreign Keys)**

```
Usuarios
├─→ Roles (IdRol)
└─→ Empleados (IdEmpleado)

Empleados
└─→ Puestos (IdPuesto)
    └─→ Departamentos (IdDepartamento)

RegistrosNomina
├─→ Empleados (IdEmpleado)
└─→ Periodos (IdPeriodo)

ItemsNomina
├─→ RegistrosNomina (IdRegistroNomina)
└─→ BeneficiosDeducciones (IdBeneficioDeduccion)

Asistencia
└─→ Empleados (IdEmpleado)

PermisosUsuarios
├─→ Usuarios (IdUsuario)
└─→ Modulos (IdModulo)
```

---

## 🔧 Configuración de la Aplicación

Después de crear la base de datos, configura la conexión en tu aplicación:

### **Archivo: `app.py`**

```python
def get_connection():
    return pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=localhost;'  # Cambia si es necesario
        'DATABASE=NominaDB;'
        'UID=tu_usuario;'    # Cambia por tu usuario
        'PWD=tu_password;'   # Cambia por tu contraseña
        'Trusted_Connection=yes;'  # Usa esto si tienes Windows Auth
    )
```

### **Opción 1: Autenticación de Windows**
```python
'Trusted_Connection=yes;'
```

### **Opción 2: Autenticación SQL Server**
```python
'UID=tu_usuario;'
'PWD=tu_password;'
```

---

## 🧪 Probar la Instalación

### **1. Desde SQL Server**

```sql
USE NominaDB;

-- Ver estadísticas
SELECT 
    'Usuarios' AS Tabla, COUNT(*) AS Total FROM Usuarios
UNION ALL
SELECT 'Roles', COUNT(*) FROM Roles
UNION ALL
SELECT 'Módulos', COUNT(*) FROM Modulos
UNION ALL
SELECT 'Departamentos', COUNT(*) FROM Departamentos
UNION ALL
SELECT 'Puestos', COUNT(*) FROM Puestos;
```

### **2. Desde la Aplicación**

1. Inicia el servidor Flask:
   ```bash
   python app.py
   ```

2. Abre el navegador:
   ```
   http://localhost:5000
   ```

3. Inicia sesión con:
   - Usuario: `admin`
   - Contraseña: `admin123`

4. Verifica que puedas acceder al Dashboard

---

## 🛠️ Mantenimiento

### **Backup de la Base de Datos**

```sql
BACKUP DATABASE NominaDB
TO DISK = 'C:\Backups\NominaDB_Backup.bak'
WITH FORMAT,
     NAME = 'NominaDB Full Backup';
```

### **Restaurar desde Backup**

```sql
USE master;
RESTORE DATABASE NominaDB
FROM DISK = 'C:\Backups\NominaDB_Backup.bak'
WITH REPLACE;
```

### **Limpiar Datos de Prueba**

Si instalaste datos de ejemplo y quieres eliminarlos:

```sql
USE NominaDB;

-- NO eliminar estos datos
-- DELETE FROM Roles;
-- DELETE FROM Modulos;
-- DELETE FROM Usuarios WHERE NombreUsuario = 'admin';

-- Puedes eliminar datos de ejemplo
DELETE FROM ItemsNomina;
DELETE FROM RegistrosNomina;
DELETE FROM Asistencia;
DELETE FROM Periodos;
DELETE FROM EmpleadoBeneficiosDeduccioness;
DELETE FROM Empleados;

-- Opcional: Eliminar departamentos y puestos de ejemplo
-- DELETE FROM Puestos;
-- DELETE FROM Departamentos;
```

---

## ❗ Solución de Problemas

### **Error: "Database already exists"**
El script automáticamente elimina la base de datos si existe. Si quieres conservar datos:
1. Haz un backup primero
2. Comenta las líneas de DROP DATABASE

### **Error: "Cannot open database requested by the login"**
- Verifica que el usuario tenga permisos
- Verifica que el servidor SQL esté corriendo
- Revisa la cadena de conexión

### **Error: "Invalid object name"**
- Asegúrate de estar usando: `USE NominaDB;`
- Verifica que todas las tablas se crearon correctamente

### **Los permisos no funcionan**
1. Verifica que existan registros en `PermisosUsuarios`
2. Ejecuta: `/debug-permisos` en la aplicación
3. Verifica que `TieneAcceso = 1`

---

## 📝 Notas Adicionales

- El script crea índices automáticamente para mejorar el rendimiento
- Se incluyen 2 vistas útiles: `vw_EmpleadosCompleto` y `vw_UsuariosCompleto`
- Todos los campos de fecha/hora usan `GETDATE()` como valor por defecto
- Las relaciones tienen configurado `ON DELETE CASCADE` o `ON DELETE SET NULL` según corresponda

---

## 📚 Recursos Adicionales

- **Documentación de Permisos:** `SETUP_ROLES_AUDITORIA.md`
- **Guía de Permisos en Templates:** `GUIA_PERMISOS_TEMPLATES.md`
- **Mejoras Implementadas:** `MEJORAS_IMPLEMENTADAS.md`
- **README Principal:** `README.md`

---

## ✅ Checklist de Instalación

- [ ] SQL Server instalado y corriendo
- [ ] Script `CREATE_DATABASE_COMPLETE.sql` ejecutado sin errores
- [ ] Base de datos `NominaDB` creada
- [ ] Usuario `admin` existe y funciona
- [ ] Configuración de conexión en `app.py` actualizada
- [ ] Aplicación Flask inicia sin errores
- [ ] Login exitoso con credenciales de admin
- [ ] Dashboard carga correctamente
- [ ] Contraseña de admin cambiada

---

## 🆘 Soporte

Si encuentras problemas durante la instalación:
1. Revisa los logs de SQL Server
2. Verifica los mensajes de error en SSMS
3. Consulta la sección de Solución de Problemas
4. Revisa la documentación adicional del proyecto
