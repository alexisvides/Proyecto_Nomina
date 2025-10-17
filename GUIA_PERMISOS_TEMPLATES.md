# Guía de Implementación de Permisos en Templates

## 📋 Funciones Disponibles

El sistema proporciona las siguientes funciones para verificar permisos en los templates:

### **1. `obtener_permisos_usuario_modulo(nombre_modulo)`**
Retorna un diccionario con todos los permisos del usuario para un módulo:
```python
{
    'ver': True/False,
    'crear': True/False,
    'editar': True/False,
    'eliminar': True/False
}
```

### **2. `puede_crear(nombre_modulo)`**
Verifica si el usuario puede crear en el módulo.

### **3. `puede_editar(nombre_modulo)`**
Verifica si el usuario puede editar en el módulo.

### **4. `puede_eliminar(nombre_modulo)`**
Verifica si el usuario puede eliminar en el módulo.

---

## 🎯 Cómo Implementar en un Template

### **Paso 1: Obtener Permisos al Inicio del Template**

Al inicio del contenido, obtén los permisos del módulo:

```jinja2
{% block content %}
<section class="section">
  <div class="card">
    {% set permisos = obtener_permisos_usuario_modulo('NombreModulo') %}
    
    <!-- Resto del contenido -->
  </div>
</section>
{% endblock %}
```

### **Paso 2: Condicionar Botones Según Permisos**

#### **Botón "Nuevo" (Crear)**
```jinja2
{% if permisos.crear %}
<a class="btn btn-primary" href="{{ url_for('ruta_nuevo') }}">
  Nuevo
</a>
{% endif %}
```

#### **Botón "Editar"**
```jinja2
{% if permisos.editar %}
<button id="btnEditar" class="btn btn-outline" type="button" disabled>
  Editar
</button>
{% endif %}
```

#### **Botón "Eliminar"**
```jinja2
{% if permisos.eliminar %}
<button id="btnEliminar" class="btn btn-outline" type="button" disabled>
  Eliminar
</button>
{% endif %}
```

#### **Toolbar Completo**
```jinja2
{% if permisos.editar or permisos.eliminar %}
<div id="toolbar" style="display:flex; gap:6px;">
  {% if permisos.editar %}
  <button id="btnEditar" class="btn btn-outline" type="button" disabled>
    Editar
  </button>
  {% endif %}
  
  {% if permisos.eliminar %}
  <button id="btnEliminar" class="btn btn-outline" type="button" disabled>
    Eliminar
  </button>
  {% endif %}
</div>
{% endif %}
```

---

## 📝 Ejemplos Completos

### **Ejemplo 1: Lista de Empleados**

```jinja2
{% extends 'base.html' %}
{% block title %}Empleados{% endblock %}

{% block content %}
<section class="section">
  <div class="card">
    {% set permisos = obtener_permisos_usuario_modulo('Empleados') %}
    
    <div style="display:flex; justify-content:space-between; margin-bottom:1rem;">
      <h2>Empleados</h2>
      
      <div style="display:flex; gap:8px;">
        {% if permisos.editar or permisos.eliminar %}
        <div id="toolbarEmp" style="display:flex; gap:6px;">
          {% if permisos.editar %}
          <button id="btnEmpEditar" class="btn btn-outline" disabled>
            Editar
          </button>
          {% endif %}
          
          {% if permisos.eliminar %}
          <button id="btnEmpEliminar" class="btn btn-outline" disabled>
            Eliminar
          </button>
          {% endif %}
        </div>
        {% endif %}
        
        {% if permisos.crear %}
        <a class="btn btn-primary" href="{{ url_for('empleados_nuevo') }}">
          Nuevo Empleado
        </a>
        {% endif %}
      </div>
    </div>
    
    <!-- Tabla de empleados -->
    <table>
      <!-- ... contenido de la tabla ... -->
    </table>
  </div>
</section>
{% endblock %}
```

### **Ejemplo 2: Acciones por Fila**

Si tienes botones en cada fila de la tabla:

```jinja2
{% for item in items %}
<tr>
  <td>{{ item.Nombre }}</td>
  <td>{{ item.Descripcion }}</td>
  <td style="text-align:right;">
    {% if permisos.editar %}
    <a href="{{ url_for('ruta_editar', id=item.Id) }}" class="btn btn-sm btn-outline">
      Editar
    </a>
    {% endif %}
    
    {% if permisos.eliminar %}
    <form method="post" action="{{ url_for('ruta_eliminar', id=item.Id) }}" style="display:inline;">
      <button type="submit" class="btn btn-sm btn-outline" onclick="return confirm('¿Eliminar?')">
        Eliminar
      </button>
    </form>
    {% endif %}
  </td>
</tr>
{% endfor %}
```

### **Ejemplo 3: Usando Funciones Individuales**

Puedes usar las funciones helper directamente:

```jinja2
{% if puede_crear('Departamentos') %}
<a href="{{ url_for('departamentos_nuevo') }}" class="btn btn-primary">
  Nuevo Departamento
</a>
{% endif %}

{% if puede_editar('Departamentos') %}
<button id="btnEditar" class="btn btn-outline" disabled>
  Editar
</button>
{% endif %}

{% if puede_eliminar('Departamentos') %}
<button id="btnEliminar" class="btn btn-outline" disabled>
  Eliminar
</button>
{% endif %}
```

---

## 🔒 Importante: Seguridad

### **Los permisos en templates son solo para UX**

Los permisos en los templates **ocultan botones**, pero **NO protegen las rutas**. 

**Debes SIEMPRE validar permisos en el backend:**

```python
@app.route("/ruta/editar/<int:id>", methods=["GET", "POST"])
@requiere_permiso_modulo("NombreModulo")  # ✅ Protección básica
def editar_item(id):
    # ✅ Validación adicional de permiso específico
    permisos = obtener_permisos_usuario_modulo("NombreModulo")
    if not permisos.get('editar'):
        flash("No tienes permiso para editar.", "danger")
        return redirect(url_for("sin_permisos"))
    
    # ... resto de la lógica
```

---

## 📊 Nombres de Módulos

Asegúrate de usar los nombres exactos de los módulos en la base de datos:

- `Dashboard`
- `Empleados`
- `Departamentos`
- `Beneficios`
- `Periodos`
- `Asistencia`
- `Usuarios`
- `Permisos`
- `Reportes`

---

## ✅ Checklist de Implementación

Para cada template de listado:

- [ ] Agregar `{% set permisos = obtener_permisos_usuario_modulo('Modulo') %}`
- [ ] Condicionar botón "Nuevo" con `{% if permisos.crear %}`
- [ ] Condicionar botón "Editar" con `{% if permisos.editar %}`
- [ ] Condicionar botón "Eliminar" con `{% if permisos.eliminar %}`
- [ ] Verificar permisos en el backend de las rutas
- [ ] Probar con usuarios de diferentes permisos

---

## 🎨 Mejora de UX

Si un usuario solo tiene permiso de "Ver":
- ✅ No verá botones de crear/editar/eliminar
- ✅ Solo podrá ver la lista
- ✅ El sistema es más limpio y claro

Si un usuario tiene todos los permisos:
- ✅ Verá todos los botones
- ✅ Puede realizar todas las acciones

---

## 🔧 Troubleshooting

### **Los botones no se ocultan**
- Verifica que el nombre del módulo sea correcto
- Revisa que los permisos estén configurados en la base de datos
- Asegúrate de que el usuario tenga `TieneAcceso = 1`

### **Error al obtener permisos**
- Verifica que exista el módulo en la tabla `Modulos`
- Asegúrate de que existan registros en `PermisosUsuarios`
- Revisa los logs del servidor para errores SQL

---

## 📚 Referencias

- Función principal: `obtener_permisos_usuario_modulo()` en `app.py`
- Ejemplo implementado: `templates/beneficios/list.html`
- Documentación de permisos: `SETUP_ROLES_AUDITORIA.md`
