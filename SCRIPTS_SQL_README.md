# 📚 Guía de Scripts SQL del Proyecto

## 📋 Índice de Scripts

Este proyecto incluye 4 scripts SQL para diferentes propósitos:

| Script | Propósito | Cuándo Usarlo |
|--------|-----------|---------------|
| `CREATE_DATABASE_COMPLETE.sql` | Crear base de datos completa desde cero | Nueva instalación |
| `UPDATE_DATABASE_STRUCTURE.sql` | Actualizar estructura sin perder datos | Migración/Actualización |
| `INSERT_TEST_DATA.sql` | Insertar datos de prueba | Testing/Demo |
| `ADD_IDEMPLEADO_TO_USUARIOS.sql` | Agregar columna específica | Migración antigua |

---

## 🎯 Script 1: CREATE_DATABASE_COMPLETE.sql

### **Descripción**
Script completo que crea la base de datos desde cero con todas las tablas, relaciones, datos iniciales e índices.

### **¿Cuándo usarlo?**
- ✅ Primera instalación del sistema
- ✅ Crear ambiente de desarrollo nuevo
- ✅ Resetear base de datos completamente
- ❌ **NO usar** si tienes datos que quieres conservar

### **⚠️ ADVERTENCIA**
**Este script ELIMINA la base de datos `NominaDB` si existe.**

### **Contenido**
- Creación de 13 tablas principales
- Relaciones (Foreign Keys)
- 4 Roles predefinidos
- 10 Módulos del sistema
- Permisos iniciales para cada rol
- Usuario administrador (admin/admin123)
- Datos de ejemplo (departamentos, puestos, beneficios)
- Índices para optimización
- 2 Vistas útiles

### **Cómo ejecutar**
```sql
-- En SQL Server Management Studio (SSMS):
-- 1. Abrir archivo CREATE_DATABASE_COMPLETE.sql
-- 2. Verificar conexión al servidor correcto
-- 3. Presionar F5 o click en "Execute"
```

### **Tiempo estimado**
1-2 minutos

### **Resultado esperado**
```
Base de datos creada exitosamente
Usuario por defecto: admin / admin123
```

---

## 🔄 Script 2: UPDATE_DATABASE_STRUCTURE.sql

### **Descripción**
Actualiza la estructura de una base de datos EXISTENTE sin eliminar datos. Agrega tablas, columnas e índices faltantes.

### **¿Cuándo usarlo?**
- ✅ Actualizar base de datos antigua
- ✅ Agregar nuevas funcionalidades sin perder datos
- ✅ Migrar de versión anterior
- ✅ Reparar estructura incompleta

### **✅ SEGURO PARA DATOS EXISTENTES**
Este script NO elimina datos, solo agrega estructura faltante.

### **Contenido**
- Verifica y crea tablas faltantes (Modulos, PermisosUsuarios)
- Agrega columnas faltantes (IdEmpleado, UltimoAcceso, CodigoEmpleado)
- Crea permisos para usuarios existentes basados en su rol
- Agrega índices faltantes
- Crea vistas si no existen
- Muestra reporte de verificación

### **Cómo ejecutar**
```sql
-- IMPORTANTE: Hacer backup primero
BACKUP DATABASE NominaDB TO DISK = 'C:\Backup\NominaDB_backup.bak';

-- Luego ejecutar el script
-- 1. Abrir UPDATE_DATABASE_STRUCTURE.sql
-- 2. Ejecutar (F5)
```

### **Tiempo estimado**
30 segundos - 1 minuto

### **Resultado esperado**
```
Tabla Modulos ya existe.
Columna IdEmpleado agregada a Usuarios.
Permisos creados para usuarios existentes.
ACTUALIZACIÓN COMPLETADA
```

---

## 🧪 Script 3: INSERT_TEST_DATA.sql

### **Descripción**
Inserta datos de prueba para testing y demos del sistema.

### **¿Cuándo usarlo?**
- ✅ Crear ambiente de pruebas
- ✅ Demo del sistema
- ✅ Training de usuarios
- ✅ Testing de funcionalidades
- ❌ **NO usar** en producción

### **Prerequisitos**
- Base de datos creada (ejecutar `CREATE_DATABASE_COMPLETE.sql` primero)
- Estructura completa instalada

### **Contenido**
- 6 Empleados de ejemplo
- 3 Usuarios de prueba (diferentes roles)
- Permisos configurados para cada usuario
- 2 Períodos de nómina
- Beneficios asignados a empleados
- Registros de asistencia de una semana
- Registro de auditoría

### **Usuarios de Prueba**

| Usuario | Contraseña | Rol | Empleado | Permisos |
|---------|------------|-----|----------|----------|
| admin | admin123 | Administrador | - | Todos |
| maria.lopez | password123 | RRHH | María López | RRHH completo |
| juan.perez | password123 | Gerente | Juan Pérez | Solo lectura |
| ana.garcia | password123 | Empleado | Ana García | Solo dashboard |

### **Empleados de Prueba**

1. **Juan Pérez González** (EMP001) - Gerente General - Q15,000
2. **María López Martínez** (EMP002) - Gerente de RRHH - Q12,000
3. **Carlos Ramírez Soto** (EMP003) - Contador - Q10,000
4. **Ana García Flores** (EMP004) - Desarrollador - Q8,000
5. **Luis Hernández Cruz** (EMP005) - Vendedor - Q6,000
6. **Sofia Morales Díaz** (EMP006) - Asistente - Q5,000

### **Cómo ejecutar**
```sql
-- Ejecutar DESPUÉS de CREATE_DATABASE_COMPLETE.sql
-- 1. Abrir INSERT_TEST_DATA.sql
-- 2. Ejecutar (F5)
```

### **Tiempo estimado**
30 segundos

### **Limpiar datos de prueba**
```sql
-- Si quieres eliminar solo los datos de prueba:
DELETE FROM ItemsNomina;
DELETE FROM RegistrosNomina;
DELETE FROM Asistencia;
DELETE FROM Periodos WHERE Descripcion LIKE '%2025%';
DELETE FROM EmpleadoBeneficiosDeduccioness;
DELETE FROM Usuarios WHERE NombreUsuario IN ('maria.lopez', 'juan.perez', 'ana.garcia');
DELETE FROM Empleados WHERE CodigoEmpleado LIKE 'EMP%';
```

---

## 🔧 Script 4: ADD_IDEMPLEADO_TO_USUARIOS.sql

### **Descripción**
Script específico para agregar la columna `IdEmpleado` a la tabla `Usuarios` y su relación con `Empleados`.

### **¿Cuándo usarlo?**
- ✅ Si tienes una base de datos antigua sin esta columna
- ✅ Migración específica de esta funcionalidad
- ❌ NO necesario si usas `CREATE_DATABASE_COMPLETE.sql`
- ❌ NO necesario si usas `UPDATE_DATABASE_STRUCTURE.sql`

### **Nota**
Este script está incluido en `UPDATE_DATABASE_STRUCTURE.sql`, así que normalmente no necesitas ejecutarlo por separado.

---

## 📖 Guía de Uso Según Escenario

### **Escenario 1: Nueva Instalación**
```
1. CREATE_DATABASE_COMPLETE.sql    ← Crear todo
2. INSERT_TEST_DATA.sql            ← (Opcional) Solo para pruebas
```

### **Escenario 2: Actualizar Base Existente**
```
1. Hacer BACKUP                    ← ¡Importante!
2. UPDATE_DATABASE_STRUCTURE.sql   ← Actualizar estructura
```

### **Escenario 3: Ambiente de Desarrollo/Testing**
```
1. CREATE_DATABASE_COMPLETE.sql    ← Base limpia
2. INSERT_TEST_DATA.sql            ← Datos para probar
```

### **Escenario 4: Migración desde Versión Antigua**
```
1. Hacer BACKUP                    ← ¡Muy importante!
2. UPDATE_DATABASE_STRUCTURE.sql   ← Actualizar
3. Verificar con /debug-permisos   ← Probar permisos
```

### **Escenario 5: Ambiente de Producción**
```
1. Hacer BACKUP                    ← ¡Crítico!
2. Probar scripts en ambiente de prueba primero
3. UPDATE_DATABASE_STRUCTURE.sql   ← Solo actualizar
4. NO ejecutar INSERT_TEST_DATA.sql
```

---

## ✅ Checklist de Instalación

### **Para Nueva Instalación:**
- [ ] SQL Server instalado y corriendo
- [ ] SSMS o Azure Data Studio instalado
- [ ] Permisos de administrador en SQL Server
- [ ] `CREATE_DATABASE_COMPLETE.sql` ejecutado sin errores
- [ ] Verificar que existan 13 tablas
- [ ] Verificar que exista usuario `admin`
- [ ] Verificar que existan 4 roles
- [ ] Verificar que existan 10 módulos
- [ ] (Opcional) `INSERT_TEST_DATA.sql` ejecutado
- [ ] Configurar conexión en `app.py`
- [ ] Probar login con `admin/admin123`
- [ ] Cambiar contraseña de admin

### **Para Actualización:**
- [ ] BACKUP de base de datos actual completado
- [ ] BACKUP verificado y funcional
- [ ] `UPDATE_DATABASE_STRUCTURE.sql` ejecutado sin errores
- [ ] Verificar mensajes del script
- [ ] Probar login con usuarios existentes
- [ ] Ejecutar `/debug-permisos` para verificar
- [ ] Probar funcionalidades críticas

---

## 🚨 Troubleshooting

### **Error: "Database already exists"**
- **Solución:** El script `CREATE_DATABASE_COMPLETE.sql` automáticamente elimina la BD
- **Si quieres conservar datos:** Usa `UPDATE_DATABASE_STRUCTURE.sql` en su lugar

### **Error: "Invalid object name"**
- **Causa:** Script ejecutado en BD incorrecta
- **Solución:** Asegúrate de tener `USE NominaDB;` al inicio

### **Error: "Cannot drop database because it is currently in use"**
- **Solución:** Cierra todas las conexiones activas a la BD
```sql
ALTER DATABASE NominaDB SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
DROP DATABASE NominaDB;
```

### **Usuarios sin permisos después de UPDATE**
- **Solución:** El script automáticamente crea permisos
- **Verificar:** Ejecuta `/debug-permisos` en la aplicación
- **Manual:** 
```sql
SELECT * FROM PermisosUsuarios WHERE IdUsuario = X;
```

### **Constraint conflicts**
- **Causa:** Datos existentes que violan nuevas constraints
- **Solución:** Revisar y limpiar datos inconsistentes primero

---

## 📊 Verificación Post-Instalación

### **Verificar Estructura**
```sql
USE NominaDB;

-- Contar tablas
SELECT COUNT(*) AS TotalTablas
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_TYPE = 'BASE TABLE';
-- Debe retornar: 13

-- Ver todas las tablas
SELECT TABLE_NAME 
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_TYPE = 'BASE TABLE'
ORDER BY TABLE_NAME;
```

### **Verificar Datos Iniciales**
```sql
-- Verificar roles
SELECT * FROM Roles;
-- Debe retornar: 4 roles

-- Verificar módulos
SELECT * FROM Modulos;
-- Debe retornar: 10 módulos

-- Verificar usuario admin
SELECT * FROM Usuarios WHERE NombreUsuario = 'admin';
-- Debe retornar: 1 usuario

-- Verificar permisos del admin
SELECT COUNT(*) FROM PermisosUsuarios 
WHERE IdUsuario = (SELECT IdUsuario FROM Usuarios WHERE NombreUsuario = 'admin');
-- Debe retornar: 10 (uno por cada módulo)
```

### **Verificar Desde la Aplicación**
```
1. Iniciar: python app.py
2. Navegar a: http://localhost:5000
3. Login: admin / admin123
4. Verificar acceso al Dashboard
5. Ir a: http://localhost:5000/debug-permisos
6. Verificar que todos los módulos tengan ✅ en todos los permisos
```

---

## 🔐 Seguridad

### **Contraseñas por Defecto**
⚠️ **IMPORTANTE:** Todos los scripts usan contraseñas en texto plano solo para desarrollo.

**En producción:**
1. Cambia inmediatamente la contraseña de `admin`
2. Elimina usuarios de prueba
3. Usa hashing real para contraseñas (bcrypt, scrypt, etc.)
4. No uses `password123` nunca

### **Permisos de Base de Datos**
- Crea un usuario SQL específico para la aplicación
- No uses `sa` en producción
- Limita permisos al mínimo necesario

---

## 📚 Documentación Relacionada

- **`INSTALACION_DATABASE.md`** - Guía detallada de instalación
- **`SETUP_ROLES_AUDITORIA.md`** - Sistema de roles y permisos
- **`GUIA_PERMISOS_TEMPLATES.md`** - Permisos en templates
- **`MEJORAS_IMPLEMENTADAS.md`** - Changelog del proyecto
- **`README.md`** - Documentación principal

---

## 📞 Soporte

Si encuentras problemas:
1. Revisa la sección de Troubleshooting
2. Verifica los logs de SQL Server
3. Consulta `INSTALACION_DATABASE.md`
4. Revisa la consola de Python para errores de conexión

---

## 📝 Notas Finales

- Siempre haz backup antes de ejecutar scripts de actualización
- Prueba en ambiente de desarrollo antes de producción
- Los datos de prueba son solo para testing
- Cambia las contraseñas por defecto inmediatamente
- Revisa los permisos después de cada migración

**¡Buena suerte con tu instalación!** 🚀
