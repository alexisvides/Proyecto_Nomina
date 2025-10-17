# Sistema de Permisos por Módulo

## 📋 Descripción

Sistema granular de permisos que permite al Administrador controlar qué módulos de la aplicación puede acceder cada usuario mediante checkboxes.

## 🎯 Características

### Gestión Visual de Permisos
- ✅ Tabla interactiva con usuarios en filas y módulos en columnas
- ✅ Checkboxes para habilitar/deshabilitar acceso por módulo
- ✅ Iconos visuales para cada módulo
- ✅ Muestra el rol de cada usuario
- ✅ Solo usuarios activos aparecen en la lista
- ✅ Scroll horizontal para muchos módulos

### Módulos del Sistema
1. **Dashboard** - Panel principal con estadísticas
2. **Periodos** - Gestión de periodos de nómina
3. **Empleados** - Gestión de empleados
4. **Departamentos** - Gestión de departamentos y puestos
5. **Beneficios** - Catálogo de beneficios y deducciones
6. **Asistencia** - Control de asistencia
7. **Usuarios** - Gestión de usuarios del sistema
8. **Permisos** - Gestión de permisos por usuario
9. **Auditoría** - Registro de auditoría del sistema
10. **Reportes** - Reportes y análisis
11. **Comprobantes** - Comprobantes de pago

## 🗄️ Estructura de Base de Datos

### Tabla `Modulos`
```sql
CREATE TABLE Modulos (
    IdModulo INT IDENTITY(1,1) PRIMARY KEY,
    Nombre VARCHAR(50) NOT NULL UNIQUE,
    Descripcion VARCHAR(255) NULL,
    Ruta VARCHAR(100) NOT NULL,
    Icono VARCHAR(50) NULL,
    Orden INT NOT NULL DEFAULT 0,
    Activo BIT NOT NULL DEFAULT 1
);
```

### Tabla `PermisosUsuarios`
```sql
CREATE TABLE PermisosUsuarios (
    IdPermiso INT IDENTITY(1,1) PRIMARY KEY,
    IdUsuario INT NOT NULL,
    IdModulo INT NOT NULL,
    TieneAcceso BIT NOT NULL DEFAULT 1,
    FOREIGN KEY (IdUsuario) REFERENCES Usuarios(IdUsuario) ON DELETE CASCADE,
    FOREIGN KEY (IdModulo) REFERENCES Modulos(IdModulo) ON DELETE CASCADE,
    UNIQUE(IdUsuario, IdModulo)
);
```

## 🚀 Instalación

### 1. Ejecutar Script de Migración
```bash
python create_permisos_modulos.py
```

Este script:
- Crea la tabla `Modulos`
- Inserta los 11 módulos del sistema
- Crea la tabla `PermisosUsuarios`
- Asigna acceso completo al usuario admin

### 2. Acceder al Módulo
1. Inicia sesión como **Administrador**
2. Ve a **Seguridad → Permisos por Módulo**
3. Marca/desmarca checkboxes según necesites
4. Haz clic en **Guardar Permisos**

## 📖 Uso

### Asignar Permisos a un Usuario

1. **Accede al módulo de permisos**
   - Menú: Seguridad → Permisos por Módulo
   - Solo accesible para rol Administrador

2. **Configura los checkboxes**
   - Cada fila representa un usuario
   - Cada columna representa un módulo
   - ✅ Marcado = Usuario tiene acceso
   - ☐ Desmarcado = Usuario NO tiene acceso

3. **Guarda los cambios**
   - Haz clic en "Guardar Permisos"
   - Los cambios se aplican inmediatamente
   - Se registra en auditoría

### Ejemplo de Configuración

**Usuario: Juan Pérez (Rol: RRHH)**
- ✅ Dashboard
- ✅ Periodos
- ✅ Empleados
- ✅ Beneficios
- ✅ Asistencia
- ✅ Comprobantes
- ☐ Departamentos
- ☐ Usuarios
- ☐ Permisos
- ☐ Auditoría
- ☐ Reportes

## 🔐 Validación de Permisos

### Próxima Implementación (Opcional)

Para validar permisos en las rutas, puedes agregar un decorador adicional:

```python
def requiere_permiso_modulo(nombre_modulo):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get("user_id"):
                return redirect(url_for("login"))
            
            # Verificar si el usuario tiene permiso para este módulo
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT COUNT(*)
                        FROM PermisosUsuarios pu
                        JOIN Modulos m ON m.IdModulo = pu.IdModulo
                        WHERE pu.IdUsuario = ? 
                          AND m.Nombre = ? 
                          AND pu.TieneAcceso = 1
                    """, (session.get("user_id"), nombre_modulo))
                    
                    if cur.fetchone()[0] == 0:
                        flash("No tienes permisos para acceder a este módulo.", "warning")
                        return redirect(url_for("dashboard"))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Uso:
@app.route("/empleados")
@requiere_permiso_modulo("Empleados")
def empleados_listado():
    # ...
```

## 🎨 Interfaz de Usuario

### Características Visuales
- **Tabla responsive** con scroll horizontal
- **Iconos SVG** para cada módulo
- **Colores distintivos** por rol
- **Sticky columns** para usuario y rol
- **Hover effects** en checkboxes
- **Diseño moderno** consistente con el resto de la app

### Accesibilidad
- ✅ Labels para checkboxes
- ✅ Aria attributes
- ✅ Contraste de colores adecuado
- ✅ Navegación por teclado

## 📊 Auditoría

Todas las acciones se registran en la tabla `Auditoria`:
- Cambios en permisos de usuarios
- Usuario que realizó el cambio
- Fecha y hora
- Dirección IP

## 🔄 Flujo de Trabajo

1. **Crear Usuario**
   - Ve a Seguridad → Usuarios y Roles
   - Crea un nuevo usuario
   - Asigna un rol

2. **Configurar Permisos**
   - Ve a Seguridad → Permisos por Módulo
   - Marca los módulos que el usuario puede acceder
   - Guarda los cambios

3. **Usuario Inicia Sesión**
   - El usuario inicia sesión
   - Solo ve los módulos permitidos en el menú
   - Si intenta acceder a un módulo no permitido, es redirigido

## 🛠️ Mantenimiento

### Agregar un Nuevo Módulo

```sql
INSERT INTO Modulos (Nombre, Descripcion, Ruta, Icono, Orden)
VALUES ('NuevoModulo', 'Descripción', '/ruta', 'icono', 12);
```

### Desactivar un Módulo

```sql
UPDATE Modulos SET Activo = 0 WHERE Nombre = 'NombreModulo';
```

### Ver Permisos de un Usuario

```sql
SELECT u.NombreUsuario, m.Nombre as Modulo, pu.TieneAcceso
FROM PermisosUsuarios pu
JOIN Usuarios u ON u.IdUsuario = pu.IdUsuario
JOIN Modulos m ON m.IdModulo = pu.IdModulo
WHERE u.IdUsuario = 1;
```

## 📝 Notas Importantes

1. **Usuario Admin**: Siempre debe tener acceso a todos los módulos
2. **Usuarios Inactivos**: No aparecen en la lista de permisos
3. **Módulos Inactivos**: No aparecen en la lista de permisos
4. **Cascada**: Al eliminar un usuario, sus permisos se eliminan automáticamente
5. **Unicidad**: Un usuario no puede tener permisos duplicados para el mismo módulo

## 🎯 Ventajas del Sistema

- ✅ **Granularidad**: Control fino sobre qué puede ver cada usuario
- ✅ **Flexibilidad**: Independiente del rol asignado
- ✅ **Visual**: Interfaz intuitiva con checkboxes
- ✅ **Escalable**: Fácil agregar nuevos módulos
- ✅ **Auditable**: Todos los cambios se registran
- ✅ **Seguro**: Solo Administrador puede modificar permisos

## 🚀 Próximas Mejoras

- [ ] Filtros por rol en la vista de permisos
- [ ] Plantillas de permisos predefinidas
- [ ] Copiar permisos de un usuario a otro
- [ ] Exportar/importar configuración de permisos
- [ ] Vista de permisos por módulo (invertida)
- [ ] Historial de cambios de permisos
