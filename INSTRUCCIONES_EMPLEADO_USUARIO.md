# Asociación de Empleados a Usuarios

## ⚠️ IMPORTANTE: Configuración de Base de Datos Requerida

Para usar la funcionalidad de asociar empleados a usuarios, **debes ejecutar primero** el script SQL que agrega la columna necesaria a la tabla `Usuarios`.

---

## 📋 Pasos para Habilitar la Funcionalidad

### 1. Ejecutar el Script SQL

Abre **SQL Server Management Studio** o tu herramienta de administración de SQL Server y ejecuta el archivo:

```
ADD_IDEMPLEADO_TO_USUARIOS.sql
```

O copia y ejecuta este código SQL:

```sql
-- Agregar columna IdEmpleado
ALTER TABLE Usuarios
ADD IdEmpleado INT NULL;

-- Agregar Foreign Key
ALTER TABLE Usuarios
ADD CONSTRAINT FK_Usuarios_Empleados 
FOREIGN KEY (IdEmpleado) REFERENCES Empleados(IdEmpleado);

-- Crear índice
CREATE INDEX IX_Usuarios_IdEmpleado ON Usuarios(IdEmpleado);
```

### 2. Reiniciar el Servidor

Una vez ejecutado el script, reinicia el servidor Flask para que los cambios surtan efecto.

### 3. Usar la Funcionalidad

Ahora podrás:
- ✅ Ver la lista de empleados al crear un usuario
- ✅ Asociar un empleado a un usuario
- ✅ Un empleado solo puede tener un usuario
- ✅ Los usuarios pueden existir sin empleado asociado (opcional)

---

## 🎯 Características

### Filtrado Inteligente
El sistema solo muestra empleados que:
- ✅ Están activos
- ✅ NO tienen ya un usuario asignado

### Validaciones
- ❌ No permite asignar el mismo empleado a múltiples usuarios
- ❌ Verifica que el empleado exista antes de asignarlo
- ✅ Permite crear usuarios sin empleado asociado

### Información Mostrada
Para cada empleado verás:
- Nombre completo
- Puesto actual
- Departamento

Ejemplo: `Juan Pérez - Vendedor (Ventas)`

---

## ⚠️ Solución de Problemas

### Error: "Invalid column name 'IdEmpleado'"

**Causa:** No has ejecutado el script SQL para agregar la columna.

**Solución:** Ejecuta el script `ADD_IDEMPLEADO_TO_USUARIOS.sql` en tu base de datos.

### No aparecen empleados en la lista

**Causas posibles:**
1. Todos los empleados ya tienen usuario asignado
2. No hay empleados activos en el sistema

**Solución:** Verifica que existan empleados activos sin usuario en la tabla `Empleados`.

---

## 📊 Estructura de la Base de Datos

Después de ejecutar el script, la tabla `Usuarios` tendrá:

```
Usuarios
├── IdUsuario (PK)
├── NombreUsuario
├── Correo
├── ClaveHash
├── IdRol (FK → Roles)
├── IdEmpleado (FK → Empleados) ← NUEVA COLUMNA
├── Activo
└── FechaCreacion
```

---

## 🔄 Relación Usuario-Empleado

```
Usuarios (1) ←→ (0..1) Empleados
```

- Un **usuario** puede tener **0 o 1 empleado** asociado
- Un **empleado** puede tener **0 o 1 usuario** asociado

---

## 📝 Notas Adicionales

- La columna `IdEmpleado` permite valores `NULL` (usuarios sin empleado)
- El Foreign Key garantiza integridad referencial
- El índice mejora el rendimiento de las consultas
- La auditoría registra qué empleado se asoció a cada usuario
