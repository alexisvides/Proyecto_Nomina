# Configuración de Roles y Auditoría

## Scripts de Migración

Ejecuta estos scripts en orden para implementar las nuevas funcionalidades:

### 1. Crear tabla Departamentos y Puestos
```bash
python create_departamentos_table.py
```
Crea:
- Tabla `Departamentos` (IdDepartamento, Nombre, Descripcion, Activo, FechaCreacion)
- Tabla `Puestos` (IdPuesto, IdDepartamento, Nombre, Descripcion, SalarioBase, Activo, FechaCreacion)
- Columna `IdPuesto` en `Empleados` (FK a Puestos)

### 2. Crear tabla Auditoría
```bash
python create_auditoria_table.py
```
Crea:
- Tabla `Auditoria` (IdLog, IdUsuario, NombreUsuario, Accion, Modulo, Detalles, FechaHora, DireccionIP)
- Índices para búsquedas por fecha y usuario

### 3. Crear tabla Roles y asignar roles
```bash
python create_roles_table.py
```
Crea:
- Tabla `Roles` (IdRol, Nombre, Descripcion, Activo, FechaCreacion)
- Roles por defecto:
  - **Administrador**: Acceso total al sistema
  - **RRHH**: Gestión de empleados y nómina
  - **Supervisor**: Consulta de reportes y asistencia
  - **Empleado**: Consulta de comprobantes propios
- Columna `IdRol` en `Usuarios` (FK a Roles)
- Asigna rol Administrador al primer usuario

## Sistema de Roles Implementado

### Decorador `@requiere_rol()`
Protege rutas según el rol del usuario:

```python
@app.route("/catalogos/departamentos")
@requiere_rol("Administrador", "RRHH")
def departamentos_listado():
    # Solo Administrador y RRHH pueden acceder
    ...
```

### Permisos por Módulo

| Módulo | Administrador | RRHH | Supervisor | Empleado |
|--------|--------------|------|------------|----------|
| Departamentos | ✅ | ✅ | ❌ | ❌ |
| Usuarios | ✅ | ❌ | ❌ | ❌ |
| Auditoría | ✅ | ❌ | ✅ | ❌ |
| Empleados | ✅ | ✅ | ✅ (solo lectura) | ❌ |
| Nómina | ✅ | ✅ | ✅ (solo lectura) | ❌ |
| Reportes | ✅ | ✅ | ✅ | ❌ |
| Comprobantes | ✅ | ✅ | ✅ | ✅ (solo propios) |

## Sistema de Auditoría

### Función `registrar_auditoria()`
Registra automáticamente acciones críticas:

```python
registrar_auditoria("Usuario creado", "Usuarios", f"Usuario: {nombre_usuario}")
```

### Eventos Auditados
- Login exitoso/fallido
- Creación/modificación/eliminación de usuarios
- Creación/modificación/eliminación de departamentos
- Accesos denegados por permisos
- Todas las acciones críticas del sistema

### Consulta de Logs
- Acceso: Menú **Seguridad → Auditoría**
- Permisos: Administrador, Supervisor
- Muestra últimos 200 registros ordenados por fecha descendente
- Información: Usuario, Acción, Módulo, Detalles, Fecha/Hora, IP

## Uso

### Asignar Rol a Usuario
1. Ejecuta `create_roles_table.py` (crea roles y asigna Administrador al primer usuario)
2. Para otros usuarios, actualiza manualmente:
```sql
UPDATE Usuarios 
SET IdRol = (SELECT IdRol FROM Roles WHERE Nombre = 'RRHH')
WHERE NombreUsuario = 'usuario_ejemplo';
```

### Verificar Rol en Sesión
El rol se guarda en la sesión al hacer login:
```python
session["rol"]  # "Administrador", "RRHH", "Supervisor", "Empleado", o "Sin rol"
```

### Crear Nuevo Rol
```sql
INSERT INTO Roles (Nombre, Descripcion, Activo)
VALUES ('NuevoRol', 'Descripción del rol', 1);
```

## Notas Importantes

1. **Primer Login**: Después de ejecutar `create_roles_table.py`, cierra sesión y vuelve a iniciar para que se cargue el rol.
2. **Sin Rol**: Si un usuario no tiene rol asignado, se muestra "Sin rol" y no podrá acceder a módulos protegidos.
3. **Auditoría Silenciosa**: Si falla el registro de auditoría, no interrumpe la operación principal.
4. **Protección de Rutas**: Todas las rutas críticas ahora requieren rol específico.

## Troubleshooting

### Error: "No tienes permisos para acceder a esta sección"
- Verifica que tu usuario tenga un rol asignado
- Verifica que el rol tenga permisos para ese módulo
- Cierra sesión y vuelve a iniciar

### Error al ejecutar scripts de migración
- Verifica conexión a SQL Server en `.env`
- Verifica que el usuario de BD tenga permisos de DDL
- Revisa que las tablas no existan ya (los scripts son idempotentes)

### No se registran logs de auditoría
- Verifica que la tabla `Auditoria` exista
- Verifica permisos de INSERT en la tabla
- Los errores de auditoría no se muestran al usuario (son silenciosos)
