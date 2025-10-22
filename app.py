import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, Response
from dotenv import load_dotenv
from db import get_connection
from datetime import datetime
import io
import csv
from functools import wraps
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key-change-me")


# =============================
# Utilidades: Auditoría y Roles (JAMES) GENERAR EXCEL PARA EL MÓDULO DE AUDITORÍA PARA FILTRAR POR FECHAS Y USUARIOS
# =============================
def registrar_auditoria(accion: str, modulo: str = None, detalles: str = None):
    """Registra una acción en la tabla Auditoria."""
    try:
        id_usuario = session.get("user_id")
        nombre_usuario = session.get("username")
        ip = request.remote_addr
        
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO Auditoria (IdUsuario, NombreUsuario, Accion, Modulo, Detalles, DireccionIP)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (id_usuario, nombre_usuario, accion, modulo, detalles, ip)
                )
                conn.commit()
    except Exception:
        # Si falla auditoría, no interrumpimos la operación principal
        pass

#modificar para que los botones no sean visibles si no se tiene permisos de editar (JAMES)
def requiere_rol(*roles_permitidos):
    """Decorador para validar que el usuario tenga uno de los roles permitidos."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get("user_id"):
                flash("Debes iniciar sesión.", "warning")
                return redirect(url_for("login"))
            
            # Obtener rol del usuario
            try:
                with get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            SELECT r.Nombre
                            FROM Usuarios u
                            LEFT JOIN Roles r ON r.IdRol = u.IdRol
                            WHERE u.IdUsuario = ?
                            """,
                            (session.get("user_id"),)
                        )
                        row = cur.fetchone()
                        rol_usuario = row[0] if row and row[0] else None
            except Exception:
                flash("Error verificando permisos.", "danger")
                return redirect(url_for("dashboard"))
            
            if not rol_usuario or rol_usuario not in roles_permitidos:
                flash(f"No tienes permisos para acceder a esta sección. Se requiere rol: {', '.join(roles_permitidos)}", "danger")
                registrar_auditoria(f"Acceso denegado a {request.endpoint}", request.endpoint, f"Rol requerido: {roles_permitidos}")
                return redirect(url_for("dashboard"))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def obtener_permisos_usuario():
    """Obtiene la lista de módulos a los que el usuario tiene acceso."""
    if not session.get("user_id"):
        return []
    
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT m.Nombre
                    FROM PermisosUsuarios pu
                    JOIN Modulos m ON m.IdModulo = pu.IdModulo
                    WHERE pu.IdUsuario = ? 
                      AND pu.TieneAcceso = 1
                      AND m.Activo = 1
                """, (session.get("user_id"),))
                
                return [row[0] for row in cur.fetchall()]
    except Exception:
        return []


def requiere_permiso_modulo(nombre_modulo):
    """Decorador para validar que el usuario tenga permiso para acceder a un módulo específico."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get("user_id"):
                flash("Debes iniciar sesión.", "warning")
                return redirect(url_for("login"))
            
            # Verificar si el usuario tiene permiso para este módulo
            try:
                with get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            SELECT COUNT(*)
                            FROM PermisosUsuarios pu
                            JOIN Modulos m ON m.IdModulo = pu.IdModulo
                            WHERE pu.IdUsuario = ? 
                              AND m.Nombre = ? 
                              AND pu.TieneAcceso = 1
                              AND m.Activo = 1
                        """, (session.get("user_id"), nombre_modulo))
                        
                        tiene_permiso = cur.fetchone()[0] > 0
            except Exception as e:
                flash("Error verificando permisos de módulo.", "danger")
                return redirect(url_for("sin_permisos"))
            
            if not tiene_permiso:
                flash(f"No tienes permisos para acceder al módulo '{nombre_modulo}'.", "warning")
                registrar_auditoria(f"Acceso denegado al módulo {nombre_modulo}", nombre_modulo, f"Ruta: {request.endpoint}")
                return redirect(url_for("sin_permisos"))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def get_role_color(role_id):
    """Devuelve un color para un ID de rol específico."""
    role_colors = {
        1: '#3b82f6',  # Azul para Administrador
        2: '#10b981',  # Verde para Gerente
        3: '#f59e0b',  # Amarillo para Supervisor
        4: '#6366f1',  # Índigo para Empleado
    }
    return role_colors.get(role_id, '#6b7280')  # Gris por defecto

# Registrar la función en el contexto de Jinja2
app.jinja_env.globals.update(get_role_color=get_role_color)

# Context processor para hacer permisos disponibles en todos los templates
@app.context_processor
def inject_permisos():
    """Inyecta los permisos del usuario en todos los templates."""
    if "user_id" in session:
        permisos = obtener_permisos_usuario()
        return dict(
            permisos_usuario=permisos,
            obtener_permisos_rol=obtener_permisos_rol
        )
    return dict(
        permisos_usuario={},
        obtener_permisos_rol=lambda *args: (False, False, False, False)
    )


def obtener_permisos_rol(id_rol):
    """Obtiene los permisos de un rol específico."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT p.Modulo 
                    FROM PermisosRol p 
                    WHERE p.IdRol = ? 
                    AND (p.Ver = 1 OR p.Crear = 1 OR p.Editar = 1 OR p.Eliminar = 1)
                    ORDER BY p.Modulo
                """, (id_rol,))
                return [row[0] for row in cur.fetchall()]
    except Exception as e:
        print(f"Error obteniendo permisos del rol: {e}")
        return []

# Registrar la función en el contexto de Jinja2
app.jinja_env.globals.update(obtener_permisos_rol=obtener_permisos_rol)


def obtener_permisos_usuario_modulo(nombre_modulo):
    """
    Obtiene los permisos específicos del usuario actual para un módulo.
    Retorna un diccionario con: ver, crear, editar, eliminar
    """
    if not session.get("user_id"):
        return {'ver': False, 'crear': False, 'editar': False, 'eliminar': False}
    
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT pu.TieneAcceso, pu.PuedeCrear, pu.PuedeEditar, pu.PuedeEliminar
                    FROM PermisosUsuarios pu
                    JOIN Modulos m ON m.IdModulo = pu.IdModulo
                    WHERE pu.IdUsuario = ? 
                      AND m.Nombre = ? 
                      AND pu.TieneAcceso = 1
                      AND m.Activo = 1
                """, (session.get("user_id"), nombre_modulo))
                
                row = cur.fetchone()
                if row:
                    permisos = {
                        'ver': bool(row[0]),
                        'crear': bool(row[1]),
                        'editar': bool(row[2]),
                        'eliminar': bool(row[3])
                    }
                    # Debug: imprimir permisos en consola
                    print(f"DEBUG: Usuario {session.get('user_id')} - Módulo '{nombre_modulo}' - Permisos: {permisos}")
                    return permisos
                print(f"DEBUG: Usuario {session.get('user_id')} - Módulo '{nombre_modulo}' - SIN PERMISOS (no hay registro)")
                return {'ver': False, 'crear': False, 'editar': False, 'eliminar': False}
    except Exception as e:
        print(f"Error obteniendo permisos del usuario: {e}")
        return {'ver': False, 'crear': False, 'editar': False, 'eliminar': False}


def puede_crear(nombre_modulo):
    """Verifica si el usuario puede crear en el módulo."""
    permisos = obtener_permisos_usuario_modulo(nombre_modulo)
    return permisos.get('crear', False)


def puede_editar(nombre_modulo):
    """Verifica si el usuario puede editar en el módulo."""
    permisos = obtener_permisos_usuario_modulo(nombre_modulo)
    return permisos.get('editar', False)


def puede_eliminar(nombre_modulo):
    """Verifica si el usuario puede eliminar en el módulo."""
    permisos = obtener_permisos_usuario_modulo(nombre_modulo)
    return permisos.get('eliminar', False)


# Registrar las funciones en el contexto de Jinja2 para usar en templates
app.jinja_env.globals.update(
    obtener_permisos_usuario_modulo=obtener_permisos_usuario_modulo,
    puede_crear=puede_crear,
    puede_editar=puede_editar,
    puede_eliminar=puede_eliminar
)
#finaliza roles (JAMES )

def obtener_pagina_inicio_por_rol(rol_nombre):
    """
    Determina la página de inicio según el rol del usuario.
    """
    # Normalizar el nombre del rol (quitar espacios y convertir a minúsculas)
    rol = (rol_nombre or "").strip().lower()
    
    # Mapeo de roles a páginas de inicio
    mapeo_roles = {
        "admin": "dashboard",
        "administrador": "nominas_listado",
        "rrhh": "empleados_listado",
        "recursos humanos": "empleados_listado",
        "contador": "nominas_listado",
        "contabilidad": "nominas_listado",
        "gerente": "dashboard",
        "supervisor": "empleados_listado",
        "empleado": "dashboard",
    }
    
    # Buscar coincidencia exacta o parcial
    for key, endpoint in mapeo_roles.items():
        if key in rol:
            return endpoint
    
    # Por defecto, redirigir al dashboard
    return "dashboard"


@app.route("/", methods=["GET"])
def index():
    if session.get("user_id"):
        return redirect(url_for("inicio"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario_o_correo = request.form.get("usuario")
        clave = request.form.get("clave")

        if not usuario_o_correo or not clave:
            flash("Por favor, completa todos los campos.", "warning")
            return render_template("login.html", hide_sidebar=True)

        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    # Permitir login por NombreUsuario o Correo, incluir rol
                    cur.execute(
                        """
                        SELECT TOP 1 u.IdUsuario, u.NombreUsuario, u.Correo, u.ClaveHash, u.Activo, r.Nombre as RolNombre
                        FROM Usuarios u
                        LEFT JOIN Roles r ON r.IdRol = u.IdRol
                        WHERE (u.NombreUsuario = ? OR u.Correo = ?)
                        """,
                        (usuario_o_correo, usuario_o_correo),
                    )
                    row = cur.fetchone()

            if not row:
                registrar_auditoria("Intento de login fallido", "Login", f"Usuario: {usuario_o_correo}")
                flash("Usuario o contraseña incorrectos.", "danger")
                return render_template("login.html", hide_sidebar=True)

            id_usuario, nombre_usuario, correo, clave_hash, activo, rol_nombre = row

            if not activo:
                registrar_auditoria("Intento de login con usuario inactivo", "Login", f"Usuario: {nombre_usuario}")
                flash("Tu usuario está inactivo. Contacta al administrador.", "danger")
                return render_template("login.html", hide_sidebar=True)

            # Comparación en texto plano (temporal, no recomendado para producción)
            if str(clave_hash) != clave:
                registrar_auditoria("Intento de login con contraseña incorrecta", "Login", f"Usuario: {nombre_usuario}")
                flash("Usuario o contraseña incorrectos.", "danger")
                return render_template("login.html", hide_sidebar=True)

            # Autenticado
            session["user_id"] = int(id_usuario)
            session["username"] = nombre_usuario
            session["rol"] = rol_nombre if rol_nombre else "Sin rol"
            registrar_auditoria("Login exitoso", "Login", f"Usuario: {nombre_usuario}, Rol: {session['rol']}")
            flash("¡Bienvenido!", "success")
            
            # Redirigir a la página de inicio
            return redirect(url_for("inicio"))

        except Exception as e:
            # En producción, registra e de forma segura
            flash(f"Error de conexión o consulta a la base de datos: {e}", "danger")
            return render_template("login.html", hide_sidebar=True)

    # GET
    return render_template("login.html", hide_sidebar=True)


@app.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada.", "info")
    return redirect(url_for("login"))


@app.route("/inicio")
def inicio():
    """Página de inicio para todos los usuarios. No requiere permisos específicos."""
    if not session.get("user_id"):
        return redirect(url_for("login"))
    
    # Obtener información básica del usuario
    usuario = {
        'username': session.get('username', 'Usuario'),
        'rol': session.get('rol', 'Sin rol')
    }
    
    return render_template("inicio.html", usuario=usuario)


@app.route("/mis-comprobantes")
def mis_comprobantes():
    """Página para que los empleados vean sus propios comprobantes de nómina."""
    if not session.get("user_id"):
        return redirect(url_for("login"))
    
    # Obtener el IdEmpleado del usuario logueado
    id_empleado = None
    nombre_empleado = ""
    comprobantes = []
    
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Obtener el IdEmpleado asociado al usuario
                cur.execute("""
                    SELECT u.IdEmpleado, e.Nombres, e.Apellidos, e.CodigoEmpleado
                    FROM Usuarios u
                    LEFT JOIN Empleados e ON e.IdEmpleado = u.IdEmpleado
                    WHERE u.IdUsuario = ?
                """, (session.get("user_id"),))
                
                row = cur.fetchone()
                if row and row[0]:
                    id_empleado = row[0]
                    nombre_empleado = f"{row[1]} {row[2]}" if row[1] else "Empleado"
                    codigo_empleado = row[3] if row[3] else ""
                    
                    # Obtener los comprobantes (registros de nómina) del empleado
                    cur.execute("""
                        SELECT 
                            rn.IdNomina,
                            p.TipoPeriodo + ' - ' + CONVERT(varchar(10), p.FechaInicio, 103) + ' a ' + CONVERT(varchar(10), p.FechaFin, 103) as Periodo,
                            p.FechaInicio,
                            p.FechaFin,
                            rn.SalarioBase,
                            rn.TotalDeducciones,
                            rn.SalarioNeto,
                            DATEDIFF(DAY, p.FechaInicio, p.FechaFin) as DiasLaborados,
                            'Procesado' as Estado
                        FROM RegistrosNomina rn
                        INNER JOIN PeriodosNomina p ON p.IdPeriodo = rn.IdPeriodo
                        WHERE rn.IdEmpleado = ?
                        ORDER BY p.FechaInicio DESC
                    """, (id_empleado,))
                    
                    comprobantes = [dict(zip([column[0] for column in cur.description], row)) 
                                  for row in cur.fetchall()]
                else:
                    flash("Tu usuario no está asociado a ningún empleado. Contacta al administrador.", "warning")
                    
    except Exception as e:
        print(f"Error obteniendo comprobantes: {e}")
        flash(f"Error al cargar tus comprobantes: {e}", "danger")
    
    return render_template("mis_comprobantes.html", 
                         comprobantes=comprobantes, 
                         nombre_empleado=nombre_empleado,
                         id_empleado=id_empleado)


@app.route("/mis-comprobantes/<int:id_registro>")
def mi_comprobante_detalle(id_registro: int):
    """Detalle de un comprobante específico del empleado."""
    if not session.get("user_id"):
        return redirect(url_for("login"))
    
    # Verificar que el comprobante pertenece al usuario logueado
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Obtener IdEmpleado del usuario
                cur.execute("""
                    SELECT IdEmpleado FROM Usuarios WHERE IdUsuario = ?
                """, (session.get("user_id"),))
                row = cur.fetchone()
                
                if not row or not row[0]:
                    flash("Tu usuario no está asociado a ningún empleado.", "warning")
                    return redirect(url_for("inicio"))
                
                id_empleado_usuario = row[0]
                
                # Obtener el registro de nómina con información del periodo
                cur.execute("""
                    SELECT 
                        rn.IdNomina,
                        rn.IdEmpleado,
                        e.Nombres + ' ' + e.Apellidos as NombreEmpleado,
                        e.CodigoEmpleado,
                        p.TipoPeriodo,
                        p.FechaInicio,
                        p.FechaFin,
                        'Procesado' as Estado,
                        rn.SalarioBase,
                        rn.TotalDeducciones,
                        rn.SalarioNeto,
                        DATEDIFF(DAY, p.FechaInicio, p.FechaFin) as DiasLaborados,
                        pu.Titulo as Puesto,
                        d.Nombre as Departamento
                    FROM RegistrosNomina rn
                    INNER JOIN PeriodosNomina p ON p.IdPeriodo = rn.IdPeriodo
                    INNER JOIN Empleados e ON e.IdEmpleado = rn.IdEmpleado
                    LEFT JOIN Puestos pu ON pu.IdPuesto = e.IdPuesto
                    LEFT JOIN Departamentos d ON d.IdDepartamento = pu.IdDepartamento
                    WHERE rn.IdNomina = ?
                """, (id_registro,))
                
                row = cur.fetchone()
                if not row:
                    flash("Comprobante no encontrado.", "danger")
                    return redirect(url_for("mis_comprobantes"))
                
                # Verificar que el comprobante pertenece al empleado del usuario
                if row[1] != id_empleado_usuario:
                    flash("No tienes permiso para ver este comprobante.", "danger")
                    return redirect(url_for("mis_comprobantes"))
                
                comprobante = dict(zip([column[0] for column in cur.description], row))
                
                # Obtener los items (percepciones y deducciones) del comprobante
                cur.execute("""
                    SELECT 
                        bd.Nombre as Descripcion,
                        i.Monto,
                        i.TipoItem as Tipo
                    FROM ItemsNomina i
                    LEFT JOIN BeneficiosDeducciones bd ON bd.IdBeneficioDeduccion = i.IdBeneficioDeduccion
                    WHERE i.IdNomina = ?
                    ORDER BY i.TipoItem, bd.Nombre
                """, (id_registro,))
                
                items = [dict(zip([column[0] for column in cur.description], row)) 
                        for row in cur.fetchall()]
                
                # Separar percepciones y deducciones
                percepciones = [item for item in items if item['Tipo'] == 'prestacion']
                deducciones = [item for item in items if item['Tipo'] == 'deduccion']
                
                return render_template("mi_comprobante_detalle.html",
                                     comprobante=comprobante,
                                     percepciones=percepciones,
                                     deducciones=deducciones)
                
    except Exception as e:
        print(f"Error obteniendo detalle del comprobante: {e}")
        flash(f"Error al cargar el comprobante: {e}", "danger")
        return redirect(url_for("mis_comprobantes"))


@app.route("/debug-permisos")
def debug_permisos():
    """Ruta de depuración para ver los permisos actuales del usuario."""
    if not session.get("user_id"):
        return "No hay sesión activa", 403
    
    permisos_detalle = []
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        m.Nombre as Modulo,
                        pu.Ver,
                        pu.Crear,
                        pu.Editar,
                        pu.Eliminar,
                        pu.TieneAcceso
                    FROM PermisosUsuarios pu
                    JOIN Modulos m ON m.IdModulo = pu.IdModulo
                    WHERE pu.IdUsuario = ?
                    ORDER BY m.Nombre
                """, (session.get("user_id"),))
                
                for row in cur.fetchall():
                    permisos_detalle.append({
                        'modulo': row[0],
                        'ver': bool(row[1]),
                        'crear': bool(row[2]),
                        'editar': bool(row[3]),
                        'eliminar': bool(row[4]),
                        'tiene_acceso': bool(row[5])
                    })
    except Exception as e:
        return f"Error: {e}", 500
    
    html = f"""
    <html>
    <head><title>Debug Permisos</title></head>
    <body style="font-family: monospace; padding: 20px;">
        <h1>Permisos del Usuario ID: {session.get('user_id')}</h1>
        <h2>Usuario: {session.get('username')}</h2>
        <h3>Rol: {session.get('rol')}</h3>
        <hr>
        <table border="1" cellpadding="10" style="border-collapse: collapse;">
            <thead>
                <tr style="background: #333; color: white;">
                    <th>Módulo</th>
                    <th>Tiene Acceso</th>
                    <th>Ver</th>
                    <th>Crear</th>
                    <th>Editar</th>
                    <th>Eliminar</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for p in permisos_detalle:
        color = "#e8f5e9" if p['tiene_acceso'] else "#ffebee"
        html += f"""
                <tr style="background: {color};">
                    <td><strong>{p['modulo']}</strong></td>
                    <td>{'✅' if p['tiene_acceso'] else '❌'}</td>
                    <td>{'✅' if p['ver'] else '❌'}</td>
                    <td>{'✅' if p['crear'] else '❌'}</td>
                    <td>{'✅' if p['editar'] else '❌'}</td>
                    <td>{'✅' if p['eliminar'] else '❌'}</td>
                </tr>
        """
    
    html += """
            </tbody>
        </table>
        <hr>
        <p><a href="javascript:history.back()">← Volver</a> | <a href="/logout">Cerrar Sesión</a></p>
    </body>
    </html>
    """
    return html


@app.route("/sin-permisos")
def sin_permisos():
    """Página que se muestra cuando el usuario no tiene permisos para acceder a un módulo."""
    if not session.get("user_id"):
        return redirect(url_for("login"))
    
    # Obtener los módulos a los que el usuario SÍ tiene acceso
    modulos_disponibles = []
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT DISTINCT m.Nombre, m.Descripcion
                    FROM PermisosUsuarios pu
                    JOIN Modulos m ON m.IdModulo = pu.IdModulo
                    WHERE pu.IdUsuario = ? 
                      AND pu.TieneAcceso = 1
                      AND m.Activo = 1
                    ORDER BY m.Nombre
                """, (session.get("user_id"),))
                modulos_disponibles = [{'nombre': row[0], 'descripcion': row[1]} for row in cur.fetchall()]
    except Exception as e:
        print(f"Error obteniendo módulos disponibles: {e}")
    
    return render_template("sin_permisos.html", modulos=modulos_disponibles, hide_sidebar=False)


@app.route("/dashboard")
@requiere_permiso_modulo("Dashboard")
def dashboard():
    # Obtener estadísticas básicas
    stats = {"empleados": 0, "periodos": 0, "departamentos": 0, "usuarios": 0, "total_dias_laborados": 0}
    
    # Datos para gráficas
    empleados_mejor_pagados = []
    empleados_por_departamento = []
    nomina_ultimos_meses = []
    asistencia_semanal = []
    
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Estadísticas básicas
                try:
                    cur.execute("SELECT COUNT(*) FROM Empleados WHERE FechaFin IS NULL OR FechaFin >= GETDATE()")
                    stats["empleados"] = cur.fetchone()[0]
                except Exception as e:
                    print(f"Error contando empleados: {e}")
                
                try:
                    cur.execute("SELECT COUNT(*) FROM PeriodosNomina")
                    stats["periodos"] = cur.fetchone()[0]
                except Exception as e:
                    print(f"Error contando periodos: {e}")
                
                try:
                    cur.execute("SELECT COUNT(*) FROM Departamentos")
                    stats["departamentos"] = cur.fetchone()[0]
                except Exception as e:
                    print(f"Error contando departamentos: {e}")
                
                try:
                    cur.execute("SELECT COUNT(*) FROM Usuarios WHERE Activo = 1")
                    stats["usuarios"] = cur.fetchone()[0]
                except Exception as e:
                    print(f"Error contando usuarios: {e}")
                
                # Total de días laborados
                try:
                    cur.execute("""
                        SELECT COUNT(DISTINCT CONCAT(IdEmpleado, '_', CAST(FechaHora AS DATE)))
                        FROM Asistencias
                        WHERE Tipo = 'entrada'
                    """)
                    row = cur.fetchone()
                    stats["total_dias_laborados"] = row[0] if row else 0
                except Exception as e:
                    print(f"Error contando días laborados: {e}")
                
                # Top 10 empleados mejor pagados
                try:
                    cur.execute("""
                        SELECT TOP 10 
                            e.Nombres + ' ' + e.Apellidos as Nombre,
                            e.SalarioBase
                        FROM Empleados e
                        ORDER BY e.SalarioBase DESC
                    """)
                    rows = cur.fetchall()
                    empleados_mejor_pagados = [list(row) for row in rows]
                    print(f"Empleados mejor pagados: {len(empleados_mejor_pagados)} registros")
                except Exception as e:
                    print(f"Error obteniendo empleados mejor pagados: {e}")
                
                # Empleados por departamento
                try:
                    cur.execute("""
                        SELECT 
                            ISNULL(d.Nombre, 'Sin Departamento') as Departamento,
                            COUNT(e.IdEmpleado) as Total
                        FROM Empleados e
                        LEFT JOIN Puestos p ON p.IdPuesto = e.IdPuesto
                        LEFT JOIN Departamentos d ON d.IdDepartamento = p.IdDepartamento
                        GROUP BY d.Nombre
                    """)
                    rows = cur.fetchall()
                    empleados_por_departamento = [list(row) for row in rows]
                    print(f"Empleados por departamento: {len(empleados_por_departamento)} registros")
                except Exception as e:
                    print(f"Error obteniendo empleados por departamento: {e}")
                
                # Nómina de últimos 6 meses
                try:
                    cur.execute("""
                        SELECT TOP 6
                            FORMAT(p.FechaInicio, 'MMM yyyy') as Mes,
                            ISNULL(SUM(rn.SalarioNeto), 0) as TotalPagado
                        FROM PeriodosNomina p
                        LEFT JOIN RegistrosNomina rn ON rn.IdPeriodo = p.IdPeriodo
                        WHERE p.FechaInicio >= DATEADD(MONTH, -6, GETDATE())
                        GROUP BY p.FechaInicio, FORMAT(p.FechaInicio, 'MMM yyyy')
                        ORDER BY p.FechaInicio DESC
                    """)
                    rows = cur.fetchall()
                    nomina_ultimos_meses = [list(row) for row in reversed(rows)]
                    print(f"Nómina últimos meses: {len(nomina_ultimos_meses)} registros")
                except Exception as e:
                    print(f"Error obteniendo nómina: {e}")
                
                # Asistencia de última semana
                try:
                    cur.execute("""
                        SELECT 
                            FORMAT(CAST(FechaHora AS DATE), 'ddd dd/MM') as Dia,
                            COUNT(DISTINCT IdEmpleado) as Empleados
                        FROM Asistencias
                        WHERE Tipo = 'entrada'
                          AND FechaHora >= DATEADD(DAY, -7, GETDATE())
                        GROUP BY CAST(FechaHora AS DATE), FORMAT(CAST(FechaHora AS DATE), 'ddd dd/MM')
                        ORDER BY CAST(FechaHora AS DATE)
                    """)
                    rows = cur.fetchall()
                    asistencia_semanal = [list(row) for row in rows]
                    print(f"Asistencia semanal: {len(asistencia_semanal)} registros")
                except Exception as e:
                    print(f"Error obteniendo asistencia: {e}")
                
    except Exception as e:
        print(f"Error general en dashboard: {e}")
        import traceback
        traceback.print_exc()
    
    return render_template(
        "dashboard_v2.html", 
        usuario=session.get("username"),
        rol=session.get("rol", "Sin rol"),
        stats=stats,
        empleados_mejor_pagados=empleados_mejor_pagados,
        empleados_por_departamento=empleados_por_departamento,
        nomina_ultimos_meses=nomina_ultimos_meses,
        asistencia_semanal=asistencia_semanal
    )


@app.route("/nomina/periodos")
@requiere_permiso_modulo("Periodos")
def periodos_listado():
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT IdPeriodo, CONVERT(varchar(10), FechaInicio, 23) as FechaInicio,
                           CONVERT(varchar(10), FechaFin, 23) as FechaFin,
                           TipoPeriodo, CONVERT(varchar(19), FechaCreacion, 120) as FechaCreacion
                    FROM PeriodosNomina
                    ORDER BY FechaInicio DESC
                    """
                )
                periodos = cur.fetchall()
        return render_template("nomina/periodos_list.html", periodos=periodos)
    except Exception as e:
        flash(f"Error cargando periodos: {e}", "danger")
        return render_template("nomina/periodos_list.html", periodos=[])


@app.route("/nomina/periodos/nuevo", methods=["GET", "POST"])
@requiere_permiso_modulo("Periodos")
def periodos_nuevo():
    if request.method == "POST":
        modalidad = (request.form.get("modalidad") or "").strip()
        mes_txt = (request.form.get("mes") or "").strip()
        anio_txt = (request.form.get("anio") or "").strip()
        quincena_txt = (request.form.get("quincena") or "").strip()

        if modalidad not in ("mensual", "quincenal") or not mes_txt or not anio_txt:
            flash("Completa modalidad, mes y año.", "warning")
            return render_template("nomina/periodos_new.html")

        try:
            mes = int(mes_txt)
            anio = int(anio_txt)
            if mes < 1 or mes > 12:
                raise ValueError
        except Exception:
            flash("Mes/Año inválidos.", "warning")
            return render_template("nomina/periodos_new.html")

        try:
            # Calcular fechas según modalidad
            if modalidad == "mensual":
                from calendar import monthrange
                dia_fin = monthrange(anio, mes)[1]
                fi = datetime(anio, mes, 1).date()
                ff = datetime(anio, mes, dia_fin).date()
                tipo = "mensual"
            else:  # quincenal
                from calendar import monthrange
                q = int(quincena_txt or "1")
                dia_fin_mes = monthrange(anio, mes)[1]
                if q == 1:
                    fi = datetime(anio, mes, 1).date()
                    ff = datetime(anio, mes, 15).date()
                    tipo = "quincena1"
                else:
                    fi = datetime(anio, mes, 16).date()
                    ff = datetime(anio, mes, dia_fin_mes).date()
                    tipo = "quincena2"

            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO PeriodosNomina (FechaInicio, FechaFin, TipoPeriodo)
                        VALUES (?, ?, ?)
                        """,
                        (fi, ff, tipo),
                    )
                    conn.commit()
            flash("Periodo creado correctamente.", "success")
            return redirect(url_for("periodos_listado"))
        except Exception as e:
            flash(f"Error creando periodo: {e}", "danger")
            return render_template("nomina/periodos_new.html")
    # GET
    return render_template("nomina/periodos_new.html")

@app.route("/nomina/periodos/<int:id_periodo>/recalcular", methods=["POST"])
@requiere_permiso_modulo("Periodos")
def periodos_recalcular(id_periodo: int):
    """Elimina ItemsNomina del periodo y los vuelve a calcular con catálogo y overrides por empleado.
    No toca RegistrosNomina."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # 1) Borrar Items del periodo
                cur.execute(
                    """
                    DELETE i
                    FROM ItemsNomina i
                    JOIN RegistrosNomina rn ON rn.IdNomina = i.IdNomina
                    WHERE rn.IdPeriodo = ?
                    """,
                    (id_periodo,),
                )

                # 2) Asegurar IGSS en catálogo con IGSS_PCT
                try:
                    igss_pct = float(os.getenv("IGSS_PCT", "4.83"))
                except Exception:
                    igss_pct = 4.83
                cur.execute(
                    """
                    IF NOT EXISTS (SELECT 1 FROM BeneficiosDeducciones WHERE Nombre = 'IGSS')
                    BEGIN
                        INSERT INTO BeneficiosDeducciones (Nombre, Tipo, TipoCalculo, Valor, Activo, Descripcion)
                        VALUES ('IGSS','deduccion','porcentaje',?,1,'Deducción IGSS porcentaje variable')
                    END
                    ELSE
                    BEGIN
                        UPDATE BeneficiosDeducciones SET Valor = ? WHERE Nombre = 'IGSS' AND TipoCalculo='porcentaje'
                    END
                    """,
                    (igss_pct, igss_pct),
                )

                # 3) Reinsertar Items desde Catálogo y Overrides (excluir ISR)
                cur.execute(
                    """
                    WITH Cat AS (
                        SELECT b.IdBeneficioDeduccion, b.Nombre, b.Tipo, b.TipoCalculo, b.Valor, b.Activo
                        FROM BeneficiosDeducciones b
                    ),
                    Src AS (
                        SELECT rn.IdNomina,
                               c.IdBeneficioDeduccion,
                               CASE WHEN COALESCE(eb.Activo, c.Activo) = 1 THEN 1 ELSE 0 END AS Usar,
                               CASE 
                                   WHEN COALESCE(eb.TipoCalculo, c.TipoCalculo) = 'porcentaje'
                                       THEN ROUND(rn.SalarioBase * COALESCE(eb.Valor, c.Valor) / 100.0, 2)
                                   ELSE COALESCE(eb.Valor, c.Valor)
                               END AS Monto,
                               CASE WHEN c.Tipo = 'prestacion' THEN 'prestacion' ELSE 'deduccion' END AS TipoItem
                        FROM RegistrosNomina rn
                        CROSS JOIN Cat c
                        LEFT JOIN EmpleadoBeneficios eb 
                               ON eb.IdBeneficioDeduccion = c.IdBeneficioDeduccion AND eb.IdEmpleado = rn.IdEmpleado
                        WHERE rn.IdPeriodo = ?
                          AND c.Nombre <> 'ISR'
                    )
                    INSERT INTO ItemsNomina (IdNomina, IdBeneficioDeduccion, TipoItem, Monto)
                    SELECT s.IdNomina, s.IdBeneficioDeduccion, s.TipoItem, s.Monto
                    FROM Src s
                    WHERE s.Usar = 1
                    """,
                    (id_periodo,),
                )
                conn.commit()
        flash("Ítems del periodo recalculados.", "success")
    except Exception as e:
        flash(f"No se pudo recalcular el periodo: {e}", "danger")
    return redirect(url_for("periodos_listado"))


# =============================
# Reportes
# =============================
@app.route("/reportes")
@requiere_permiso_modulo("Reportes")
def reportes_listado():
    """Lista de reportes disponibles."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Cargar periodos para el selector
                cur.execute("""
                    SELECT IdPeriodo, FechaInicio, FechaFin, TipoPeriodo
                    FROM PeriodosNomina
                    ORDER BY FechaInicio DESC
                """)
                periodos = cur.fetchall()
        return render_template("reportes/list.html", periodos=periodos)
    except Exception as e:
        flash(f"Error cargando reportes: {e}", "danger")
        return render_template("reportes/list.html", periodos=[])


@app.route("/reportes/empleados/pdf")
@requiere_permiso_modulo("Reportes")
def reporte_empleados_pdf():
    """Genera reporte PDF de empleados."""
    try:
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        from datetime import datetime
        
        # Obtener datos
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT e.CodigoEmpleado, e.Nombres, e.Apellidos, 
                           p.Titulo, e.SalarioBase,
                           CONVERT(VARCHAR(10), e.FechaContratacion, 103) as FechaInicio,
                           CASE WHEN e.FechaFin IS NULL THEN 'Activo' 
                                ELSE CONVERT(VARCHAR(10), e.FechaFin, 103) END as Estado
                    FROM Empleados e
                    LEFT JOIN Puestos p ON p.IdPuesto = e.IdPuesto
                    ORDER BY e.Apellidos, e.Nombres
                """)
                empleados = cur.fetchall()
        
        # Crear PDF en memoria
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), 
                                rightMargin=30, leftMargin=30, topMargin=40, bottomMargin=30)
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Título
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=6,
            alignment=TA_CENTER
        )
        elements.append(Paragraph("REPORTE DE EMPLEADOS", title_style))
        
        # Fecha de generación
        subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'], 
                                       fontSize=10, textColor=colors.grey, alignment=TA_CENTER)
        elements.append(Paragraph(f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", subtitle_style))
        elements.append(Spacer(1, 20))
        
        # Tabla de datos
        data = [['Código', 'Nombre Completo', 'Puesto', 'Salario Base', 'Fecha Inicio', 'Estado']]
        
        for emp in empleados:
            data.append([
                emp[0],  # Código
                f"{emp[1]} {emp[2]}",  # Nombre completo
                emp[3] or 'N/A',  # Puesto
                f"Q {emp[4]:,.2f}",  # Salario
                emp[5],  # Fecha inicio
                emp[6]   # Estado
            ])
        
        # Crear tabla
        table = Table(data, colWidths=[0.8*inch, 2.2*inch, 1.8*inch, 1.2*inch, 1.2*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 20))
        elements.append(Paragraph(f"<b>Total de empleados:</b> {len(empleados)}", styles['Normal']))
        
        doc.build(elements)
        buffer.seek(0)
        
        registrar_auditoria("Reporte de empleados generado", "Reportes", "PDF")
        
        return Response(
            buffer.getvalue(),
            mimetype='application/pdf',
            headers={'Content-Disposition': f'attachment; filename="reporte_empleados_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'}
        )
    except Exception as e:
        flash(f"Error generando reporte: {e}", "danger")
        return redirect(url_for("reportes_listado"))


@app.route("/reportes/nomina/periodo/pdf")
@requiere_permiso_modulo("Reportes")
def reporte_nomina_periodo_pdf():
    """Genera reporte PDF de nómina por periodo."""
    id_periodo = request.args.get("id_periodo")
    
    if not id_periodo:
        flash("Debe seleccionar un periodo.", "warning")
        return redirect(url_for("reportes_listado"))
    
    try:
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER
        from datetime import datetime
        
        # Obtener datos del periodo y nómina
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Info del periodo
                cur.execute("""
                    SELECT FechaInicio, FechaFin, TipoPeriodo
                    FROM PeriodosNomina
                    WHERE IdPeriodo = ?
                """, (id_periodo,))
                periodo = cur.fetchone()
                
                if not periodo:
                    flash("Periodo no encontrado.", "warning")
                    return redirect(url_for("reportes_listado"))
                
                # Detalle de nómina
                cur.execute("""
                    SELECT e.CodigoEmpleado, e.Nombres, e.Apellidos,
                           rn.SalarioBase,
                           ISNULL((SELECT SUM(i.Monto) FROM ItemsNomina i 
                                   JOIN BeneficiosDeducciones b ON b.IdBeneficioDeduccion = i.IdBeneficioDeduccion
                                   WHERE i.IdNomina = rn.IdNomina AND b.Tipo = 'prestacion'), 0) as Prestaciones,
                           ISNULL((SELECT SUM(i.Monto) FROM ItemsNomina i 
                                   JOIN BeneficiosDeducciones b ON b.IdBeneficioDeduccion = i.IdBeneficioDeduccion
                                   WHERE i.IdNomina = rn.IdNomina AND b.Tipo = 'deduccion'), 0) as Deducciones,
                           rn.SalarioNeto
                    FROM RegistrosNomina rn
                    JOIN Empleados e ON e.IdEmpleado = rn.IdEmpleado
                    WHERE rn.IdPeriodo = ?
                    ORDER BY e.Apellidos, e.Nombres
                """, (id_periodo,))
                nominas = cur.fetchall()
        
        # Crear PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(letter),
                                rightMargin=30, leftMargin=30, topMargin=40, bottomMargin=30)
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Título
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'],
                                     fontSize=18, textColor=colors.HexColor('#059669'),
                                     spaceAfter=6, alignment=TA_CENTER)
        elements.append(Paragraph("REPORTE DE NÓMINA POR PERIODO", title_style))
        
        # Info del periodo
        subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'],
                                       fontSize=10, textColor=colors.grey, alignment=TA_CENTER)
        elements.append(Paragraph(
            f"Periodo: {periodo[0].strftime('%d/%m/%Y')} - {periodo[1].strftime('%d/%m/%Y')} ({periodo[2]})",
            subtitle_style
        ))
        elements.append(Paragraph(f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", subtitle_style))
        elements.append(Spacer(1, 20))
        
        # Tabla
        data = [['Código', 'Empleado', 'Salario Base', 'Prestaciones', 'Deducciones', 'Salario Neto']]
        
        total_base = 0
        total_prest = 0
        total_ded = 0
        total_neto = 0
        
        for nom in nominas:
            data.append([
                nom[0],
                f"{nom[1]} {nom[2]}",
                f"Q {nom[3]:,.2f}",
                f"Q {nom[4]:,.2f}",
                f"Q {nom[5]:,.2f}",
                f"Q {nom[6]:,.2f}"
            ])
            total_base += nom[3]
            total_prest += nom[4]
            total_ded += nom[5]
            total_neto += nom[6]
        
        # Fila de totales
        data.append(['', 'TOTALES', f"Q {total_base:,.2f}", f"Q {total_prest:,.2f}",
                     f"Q {total_ded:,.2f}", f"Q {total_neto:,.2f}"])
        
        table = Table(data, colWidths=[0.9*inch, 2.5*inch, 1.3*inch, 1.3*inch, 1.3*inch, 1.3*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#059669')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f8f9fa')]),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#d1fae5')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold')
        ]))
        
        elements.append(table)
        
        doc.build(elements)
        buffer.seek(0)
        
        registrar_auditoria("Reporte de nómina generado", "Reportes", f"Periodo: {id_periodo}")
        
        return Response(
            buffer.getvalue(),
            mimetype='application/pdf',
            headers={'Content-Disposition': f'attachment; filename="reporte_nomina_{id_periodo}_{datetime.now().strftime("%Y%m%d")}.pdf"'}
        )
    except Exception as e:
        flash(f"Error generando reporte: {e}", "danger")
        return redirect(url_for("reportes_listado"))


@app.route("/reportes/asistencia/pdf")
@requiere_permiso_modulo("Reportes")
def reporte_asistencia_pdf():
    """Genera reporte PDF de asistencia."""
    try:
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER
        from datetime import datetime
        
        # Obtener datos (últimos 500 registros)
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT TOP 500
                           e.CodigoEmpleado, e.Nombres, e.Apellidos,
                           CONVERT(VARCHAR(10), a.FechaHora, 103) as Fecha,
                           CONVERT(VARCHAR(5), a.FechaHora, 108) as Hora,
                           a.Tipo,
                           ISNULL(a.Observacion, '') as Obs
                    FROM Asistencias a
                    JOIN Empleados e ON e.IdEmpleado = a.IdEmpleado
                    ORDER BY a.FechaHora DESC
                """)
                asistencias = cur.fetchall()
        
        # Crear PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(letter),
                                rightMargin=30, leftMargin=30, topMargin=40, bottomMargin=30)
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Título
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'],
                                     fontSize=18, textColor=colors.HexColor('#7c3aed'),
                                     spaceAfter=6, alignment=TA_CENTER)
        elements.append(Paragraph("REPORTE DE ASISTENCIA", title_style))
        
        subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'],
                                       fontSize=10, textColor=colors.grey, alignment=TA_CENTER)
        elements.append(Paragraph(f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", subtitle_style))
        elements.append(Paragraph(f"Últimos {len(asistencias)} registros", subtitle_style))
        elements.append(Spacer(1, 20))
        
        # Tabla
        data = [['Código', 'Empleado', 'Fecha', 'Hora', 'Tipo', 'Observación']]
        
        for asist in asistencias:
            data.append([
                asist[0],
                f"{asist[1]} {asist[2]}",
                asist[3],
                asist[4],
                asist[5].capitalize(),
                asist[6][:30] if len(asist[6]) > 30 else asist[6]
            ])
        
        table = Table(data, colWidths=[0.8*inch, 2.2*inch, 1*inch, 0.8*inch, 0.9*inch, 2.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7c3aed')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (4, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
        ]))
        
        elements.append(table)
        
        doc.build(elements)
        buffer.seek(0)
        
        registrar_auditoria("Reporte de asistencia generado", "Reportes", "PDF")
        
        return Response(
            buffer.getvalue(),
            mimetype='application/pdf',
            headers={'Content-Disposition': f'attachment; filename="reporte_asistencia_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'}
        )
    except Exception as e:
        flash(f"Error generando reporte: {e}", "danger")
        return redirect(url_for("reportes_listado"))


@app.route("/reportes/usuarios/pdf")
@requiere_permiso_modulo("Reportes")
def reporte_usuarios_pdf():
    """Genera reporte PDF de usuarios activos."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER
        from datetime import datetime
        
        # Obtener datos
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT u.NombreUsuario, r.Nombre as NombreRol,
                           ISNULL(e.Nombres + ' ' + e.Apellidos, 'N/A') as Empleado,
                           CASE WHEN u.Activo = 1 THEN 'Activo' ELSE 'Inactivo' END as Estado,
                           CONVERT(VARCHAR(10), u.FechaCreacion, 103) as FechaCreacion
                    FROM Usuarios u
                    LEFT JOIN Roles r ON r.IdRol = u.IdRol
                    LEFT JOIN Empleados e ON e.IdEmpleado = u.IdEmpleado
                    WHERE u.Activo = 1
                    ORDER BY u.NombreUsuario
                """)
                usuarios = cur.fetchall()
        
        # Crear PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                                rightMargin=30, leftMargin=30, topMargin=40, bottomMargin=30)
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Título
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'],
                                     fontSize=18, textColor=colors.HexColor('#dc2626'),
                                     spaceAfter=6, alignment=TA_CENTER)
        elements.append(Paragraph("REPORTE DE USUARIOS ACTIVOS", title_style))
        
        subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'],
                                       fontSize=10, textColor=colors.grey, alignment=TA_CENTER)
        elements.append(Paragraph(f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", subtitle_style))
        elements.append(Spacer(1, 20))
        
        # Tabla
        data = [['Usuario', 'Rol', 'Empleado Asociado', 'Estado', 'Fecha Creación']]
        
        for usr in usuarios:
            data.append([
                usr[0],
                usr[1] or 'N/A',
                usr[2],
                usr[3],
                usr[4]
            ])
        
        table = Table(data, colWidths=[1.5*inch, 1.3*inch, 2*inch, 1*inch, 1.2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dc2626')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (3, 0), (3, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 20))
        elements.append(Paragraph(f"<b>Total de usuarios activos:</b> {len(usuarios)}", styles['Normal']))
        
        doc.build(elements)
        buffer.seek(0)
        
        registrar_auditoria("Reporte de usuarios generado", "Reportes", "PDF")
        
        return Response(
            buffer.getvalue(),
            mimetype='application/pdf',
            headers={'Content-Disposition': f'attachment; filename="reporte_usuarios_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'}
        )
    except Exception as e:
        flash(f"Error generando reporte: {e}", "danger")
        return redirect(url_for("reportes_listado"))


@app.route("/nomina/periodos/<int:id_periodo>/generar", methods=["POST"])
def generar_nomina(id_periodo: int):
    # Genera registros de nómina para empleados activos en el periodo, prorrateando salario por días de asistencia
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Verificar que exista el periodo y obtener rango
                cur.execute(
                    "SELECT COUNT(1) FROM PeriodosNomina WHERE IdPeriodo = ?",
                    (id_periodo,),
                )
                exists = cur.fetchone()[0]
                if not exists:
                    flash("El periodo no existe.", "warning")
                    return redirect(url_for("periodos_listado"))
                cur.execute("SELECT FechaInicio, FechaFin FROM PeriodosNomina WHERE IdPeriodo = ?", (id_periodo,))
                fi, ff = cur.fetchone()

                # Insertar RegistrosNomina para empleados activos que aún no lo tengan, prorrateado por asistencia
                cur.execute(
                    """
                    DECLARE @fi DATE = ?, @ff DATE = ?;
                    DECLARE @diasPeriodo INT = DATEDIFF(DAY, @fi, @ff) + 1;

                    INSERT INTO RegistrosNomina (IdEmpleado, IdPeriodo, SalarioBase, TotalPrestaciones, TotalDeducciones, SalarioNeto)
                    SELECT e.IdEmpleado,
                           ?,
                           -- Regla: si días asistencia > 26 => salario completo; si no, proporcional por días/periodo
                           CASE 
                             WHEN (
                               SELECT COUNT(DISTINCT CAST(a.FechaHora AS DATE))
                               FROM Asistencias a
                               WHERE a.IdEmpleado = e.IdEmpleado
                                 AND a.Tipo = 'entrada'
                                 AND CAST(a.FechaHora AS DATE) BETWEEN @fi AND @ff
                             ) > 26 THEN e.SalarioBase
                             WHEN @diasPeriodo > 0 THEN ROUND(
                               e.SalarioBase * ISNULL(CAST((
                                 SELECT COUNT(DISTINCT CAST(a.FechaHora AS DATE))
                                 FROM Asistencias a
                                 WHERE a.IdEmpleado = e.IdEmpleado
                                   AND a.Tipo = 'entrada'
                                   AND CAST(a.FechaHora AS DATE) BETWEEN @fi AND @ff
                               ) AS FLOAT) / @diasPeriodo, 0), 2)
                             ELSE e.SalarioBase
                           END AS SalarioCalculado,
                           0,
                           0,
                           -- Neto inicial igual al salario calculado (antes de ítems)
                           CASE 
                             WHEN (
                               SELECT COUNT(DISTINCT CAST(a.FechaHora AS DATE))
                               FROM Asistencias a
                               WHERE a.IdEmpleado = e.IdEmpleado
                                 AND a.Tipo = 'entrada'
                                 AND CAST(a.FechaHora AS DATE) BETWEEN @fi AND @ff
                             ) > 26 THEN e.SalarioBase
                             WHEN @diasPeriodo > 0 THEN ROUND(
                               e.SalarioBase * ISNULL(CAST((
                                 SELECT COUNT(DISTINCT CAST(a.FechaHora AS DATE))
                                 FROM Asistencias a
                                 WHERE a.IdEmpleado = e.IdEmpleado
                                   AND a.Tipo = 'entrada'
                                   AND CAST(a.FechaHora AS DATE) BETWEEN @fi AND @ff
                               ) AS FLOAT) / @diasPeriodo, 0), 2)
                             ELSE e.SalarioBase
                           END
                    FROM Empleados e
                    WHERE e.FechaContratacion <= @ff
                      AND (e.FechaFin IS NULL OR e.FechaFin >= @fi)
                      AND NOT EXISTS (
                        SELECT 1 FROM RegistrosNomina rn
                        WHERE rn.IdEmpleado = e.IdEmpleado AND rn.IdPeriodo = ?
                      )
                    """,
                    (fi, ff, id_periodo, id_periodo),
                )
                # Porcentaje IGSS desde .env (default 4.83)
                try:
                    igss_pct = float(os.getenv("IGSS_PCT", "4.83"))
                except Exception:
                    igss_pct = 4.83

                # Asegurar beneficio IGSS (porcentaje IGSS_PCT) existe
                cur.execute(
                    """
                    IF NOT EXISTS (SELECT 1 FROM BeneficiosDeducciones WHERE Nombre = 'IGSS')
                    BEGIN
                        INSERT INTO BeneficiosDeducciones (Nombre, Tipo, TipoCalculo, Valor, Activo, Descripcion)
                        VALUES ('IGSS','deduccion','porcentaje',?,1,'Deducción IGSS porcentaje variable')
                    END
                    """,
                    (igss_pct,)
                )
                # Aplicar automáticamente beneficios/deducciones activos usando overrides por empleado (EmpleadoBeneficios)
                # Excluye ISR de auto-aplicación. IGSS se incluye aquí (con valor del catálogo o override).
                cur.execute(
                    f"""
                    WITH Cat AS (
                        SELECT b.IdBeneficioDeduccion, b.Nombre, b.Tipo, b.TipoCalculo, b.Valor, b.Activo
                        FROM BeneficiosDeducciones b
                    ),
                    Src AS (
                        SELECT rn.IdNomina,
                               c.IdBeneficioDeduccion,
                               CASE WHEN COALESCE(eb.Activo, c.Activo) = 1 THEN 1 ELSE 0 END AS Usar,
                               CASE 
                                   WHEN COALESCE(eb.TipoCalculo, c.TipoCalculo) = 'porcentaje'
                                       THEN ROUND(rn.SalarioBase * COALESCE(eb.Valor, c.Valor) / 100.0, 2)
                                   ELSE COALESCE(eb.Valor, c.Valor)
                               END AS Monto,
                               CASE WHEN c.Tipo = 'prestacion' THEN 'prestacion' ELSE 'deduccion' END AS TipoItem
                        FROM RegistrosNomina rn
                        CROSS JOIN Cat c
                        LEFT JOIN EmpleadoBeneficios eb 
                               ON eb.IdBeneficioDeduccion = c.IdBeneficioDeduccion AND eb.IdEmpleado = rn.IdEmpleado
                        WHERE rn.IdPeriodo = ?
                          AND c.Nombre <> 'ISR'
                    )
                    INSERT INTO ItemsNomina (IdNomina, IdBeneficioDeduccion, TipoItem, Monto)
                    SELECT s.IdNomina, s.IdBeneficioDeduccion, s.TipoItem, s.Monto
                    FROM Src s
                    WHERE s.Usar = 1
                      AND NOT EXISTS (
                          SELECT 1 FROM ItemsNomina i
                          WHERE i.IdNomina = s.IdNomina AND i.IdBeneficioDeduccion = s.IdBeneficioDeduccion
                      )
                    """,
                    (id_periodo,)
                )
                
                # Procesar descuentos de préstamos activos
                try:
                    # Obtener préstamos activos con empleados que tienen nómina en este periodo
                    cur.execute(
                        """
                        SELECT p.IdPrestamo, p.IdEmpleado, p.TipoDescuento, p.ValorDescuento, 
                               p.MontoPendiente, rn.IdNomina, rn.SalarioBase
                        FROM Prestamos p
                        JOIN RegistrosNomina rn ON rn.IdEmpleado = p.IdEmpleado
                        WHERE p.Estado = 'activo'
                          AND p.MontoPendiente > 0
                          AND rn.IdPeriodo = ?
                        """,
                        (id_periodo,)
                    )
                    prestamos_activos = cur.fetchall()
                    
                    # Buscar o crear el beneficio/deducción "Préstamo"
                    cur.execute("SELECT IdBeneficioDeduccion FROM BeneficiosDeducciones WHERE Nombre = 'Préstamo'")
                    concepto_prestamo = cur.fetchone()
                    
                    if not concepto_prestamo:
                        cur.execute(
                            """
                            INSERT INTO BeneficiosDeducciones (Nombre, Tipo, TipoCalculo, Valor, Activo, Descripcion)
                            VALUES ('Préstamo', 'deduccion', 'fijo', 0, 1, 'Descuento por préstamo a empleado')
                            """
                        )
                        cur.execute("SELECT IdBeneficioDeduccion FROM BeneficiosDeducciones WHERE Nombre = 'Préstamo'")
                        concepto_prestamo = cur.fetchone()
                    
                    id_concepto_prestamo = concepto_prestamo[0]
                    
                    # Procesar cada préstamo
                    for prestamo in prestamos_activos:
                        id_prestamo = prestamo[0]
                        id_empleado = prestamo[1]
                        tipo_descuento = prestamo[2]
                        valor_descuento = prestamo[3]
                        monto_pendiente = prestamo[4]
                        id_nomina = prestamo[5]
                        salario_base = prestamo[6]
                        
                        # Calcular monto a descontar
                        if tipo_descuento == 'fijo':
                            monto_descuento = min(valor_descuento, monto_pendiente)
                        else:  # porcentaje
                            monto_descuento = round(salario_base * valor_descuento / 100, 2)
                            monto_descuento = min(monto_descuento, monto_pendiente)
                        
                        # No descontar si el monto es 0
                        if monto_descuento <= 0:
                            continue
                        
                        # Insertar el item de nómina
                        cur.execute(
                            """
                            INSERT INTO ItemsNomina (IdNomina, IdBeneficioDeduccion, TipoItem, Monto, Descripcion)
                            VALUES (?, ?, 'deduccion', ?, ?)
                            """,
                            (id_nomina, id_concepto_prestamo, monto_descuento, f'Préstamo #{id_prestamo}')
                        )
                        
                        # Registrar el pago
                        cur.execute(
                            """
                            INSERT INTO PrestamoPagos (IdPrestamo, IdPeriodo, IdNomina, MontoPagado)
                            VALUES (?, ?, ?, ?)
                            """,
                            (id_prestamo, id_periodo, id_nomina, monto_descuento)
                        )
                        
                        # Actualizar el monto pendiente del préstamo
                        nuevo_pendiente = monto_pendiente - monto_descuento
                        cur.execute(
                            "UPDATE Prestamos SET MontoPendiente = ? WHERE IdPrestamo = ?",
                            (nuevo_pendiente, id_prestamo)
                        )
                        
                        # Si el préstamo está completamente pagado, marcar como pagado
                        if nuevo_pendiente <= 0:
                            cur.execute(
                                "UPDATE Prestamos SET Estado = 'pagado', FechaFin = GETDATE() WHERE IdPrestamo = ?",
                                (id_prestamo,)
                            )
                
                except Exception as e_prestamo:
                    # Si hay error con préstamos, continuar con el resto
                    print(f"Error procesando préstamos: {e_prestamo}")
                
                conn.commit()
        flash("Registros de nómina generados para el periodo.", "success")
    except Exception as e:
        flash(f"Error generando registros de nómina: {e}", "danger")
    return redirect(url_for("periodos_listado"))

def _consultar_detalle_periodo(id_periodo: int):
    """Obtiene el detalle de nómina del periodo con agregados por empleado."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 
                    e.IdEmpleado,
                    e.Apellidos,
                    e.Nombres,
                    e.SalarioBase,
                    -- Días laborados (conteo de días con 'entrada' dentro del rango del periodo)
                    ISNULL((
                        SELECT COUNT(*) 
                        FROM (
                            SELECT DISTINCT CAST(a.FechaHora AS date) AS Dia
                            FROM Asistencias a
                            WHERE a.IdEmpleado = e.IdEmpleado
                              AND a.Tipo = 'entrada'
                              AND CAST(a.FechaHora AS date) BETWEEN p.FechaInicio AND p.FechaFin
                        ) d
                    ), 0) AS DiasLaborados,
                    -- Número IGSS (columna dedicada)
                    e.NumeroIGSS AS NumeroIGSS,
                    -- Total deducciones (según tipo del catálogo)
                    ISNULL((
                        SELECT SUM(i.Monto)
                        FROM RegistrosNomina rn
                        JOIN ItemsNomina i ON i.IdNomina = rn.IdNomina
                        JOIN BeneficiosDeducciones b ON b.IdBeneficioDeduccion = i.IdBeneficioDeduccion
                        WHERE rn.IdPeriodo = p.IdPeriodo
                          AND rn.IdEmpleado = e.IdEmpleado
                          AND b.Tipo = 'deduccion'
                    ), 0) AS TotalDeducciones,
                    -- Total bonificaciones (prestaciones) (según tipo del catálogo)
                    ISNULL((
                        SELECT SUM(i.Monto)
                        FROM RegistrosNomina rn
                        JOIN ItemsNomina i ON i.IdNomina = rn.IdNomina
                        JOIN BeneficiosDeducciones b ON b.IdBeneficioDeduccion = i.IdBeneficioDeduccion
                        WHERE rn.IdPeriodo = p.IdPeriodo
                          AND rn.IdEmpleado = e.IdEmpleado
                          AND b.Tipo = 'prestacion'
                    ), 0) AS TotalBonificaciones,
                    -- IGSS calculado por ItemsNomina con Beneficio 'IGSS'
                    ISNULL((
                        SELECT SUM(i.Monto)
                        FROM RegistrosNomina rn
                        JOIN ItemsNomina i ON i.IdNomina = rn.IdNomina
                        JOIN BeneficiosDeducciones b ON b.IdBeneficioDeduccion = i.IdBeneficioDeduccion
                        WHERE rn.IdPeriodo = p.IdPeriodo
                          AND rn.IdEmpleado = e.IdEmpleado
                          AND i.TipoItem = 'deduccion'
                          AND b.Nombre = 'IGSS'
                    ), 0) AS IGSSMonto,
                    -- Descuento ISR (si existe un concepto llamado 'ISR')
                    ISNULL((
                        SELECT SUM(i.Monto)
                        FROM RegistrosNomina rn
                        JOIN ItemsNomina i ON i.IdNomina = rn.IdNomina
                        JOIN BeneficiosDeducciones b ON b.IdBeneficioDeduccion = i.IdBeneficioDeduccion
                        WHERE rn.IdPeriodo = p.IdPeriodo
                          AND rn.IdEmpleado = e.IdEmpleado
                          AND i.TipoItem = 'deduccion'
                          AND b.Nombre = 'ISR'
                    ), 0) AS DescuentoISR,
                    -- Salario bruto (base + bonificaciones)
                    (rn0.SalarioBase + ISNULL((
                        SELECT SUM(i.Monto)
                        FROM RegistrosNomina rn
                        JOIN ItemsNomina i ON i.IdNomina = rn.IdNomina
                        JOIN BeneficiosDeducciones b ON b.IdBeneficioDeduccion = i.IdBeneficioDeduccion
                        WHERE rn.IdPeriodo = p.IdPeriodo
                          AND rn.IdEmpleado = e.IdEmpleado
                          AND b.Tipo = 'prestacion'
                    ), 0)) AS SalarioBruto,
                    -- Salario neto (base + bonificaciones - deducciones)
                    (rn0.SalarioBase + ISNULL((
                        SELECT SUM(i.Monto)
                        FROM RegistrosNomina rn
                        JOIN ItemsNomina i ON i.IdNomina = rn.IdNomina
                        JOIN BeneficiosDeducciones b ON b.IdBeneficioDeduccion = i.IdBeneficioDeduccion
                        WHERE rn.IdPeriodo = p.IdPeriodo
                          AND rn.IdEmpleado = e.IdEmpleado
                          AND b.Tipo = 'prestacion'
                    ), 0)
                    - ISNULL((
                        SELECT SUM(i.Monto)
                        FROM RegistrosNomina rn
                        JOIN ItemsNomina i ON i.IdNomina = rn.IdNomina
                        JOIN BeneficiosDeducciones b ON b.IdBeneficioDeduccion = i.IdBeneficioDeduccion
                        WHERE rn.IdPeriodo = p.IdPeriodo
                          AND rn.IdEmpleado = e.IdEmpleado
                          AND b.Tipo = 'deduccion'
                    ), 0)) AS SalarioNeto,
                    -- IdNomina (para acciones, no se exporta en CSV)
                    (
                        SELECT TOP 1 rn.IdNomina
                        FROM RegistrosNomina rn
                        WHERE rn.IdPeriodo = p.IdPeriodo AND rn.IdEmpleado = e.IdEmpleado
                        ORDER BY rn.IdNomina DESC
                    ) AS IdNomina
                FROM Empleados e
                CROSS JOIN PeriodosNomina p
                LEFT JOIN RegistrosNomina rn0 ON rn0.IdEmpleado = e.IdEmpleado AND rn0.IdPeriodo = p.IdPeriodo
                WHERE p.IdPeriodo = ?
                  AND e.FechaContratacion <= p.FechaFin
                  AND (e.FechaFin IS NULL OR e.FechaFin >= p.FechaInicio)
                ORDER BY e.Apellidos, e.Nombres
                """,
                (id_periodo,),
            )
            return cur.fetchall()


@app.route("/nomina/periodos/<int:id_periodo>")
@requiere_permiso_modulo("Periodos")
def periodo_detalle(id_periodo: int):
    try:
        datos = _consultar_detalle_periodo(id_periodo)
        return render_template("nomina/periodo_detalle.html", filas=datos, id_periodo=id_periodo)
    except Exception as e:
        flash(f"Error consultando detalle del periodo: {e}", "danger")
        return render_template("nomina/periodo_detalle.html", filas=[], id_periodo=id_periodo)


@app.route("/nomina/periodos/<int:id_periodo>/csv")
@requiere_permiso_modulo("Periodos")
def periodo_csv(id_periodo: int):
    try:
        datos = _consultar_detalle_periodo(id_periodo)
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "IdEmpleado",
            "Apellidos",
            "Nombres",
            "SalarioBase",
            "DiasLaborados",
            "NumeroIGSS",
            "TotalDeducciones",
            "TotalBonificaciones",
            "IGSSMonto",
            "DescuentoISR",
            "SalarioBruto",
            "SalarioNeto",
        ])
        for r in datos:
            # Excluir cualquier columna agregada al final (p.ej., IdNomina para acciones)
            writer.writerow(list(r)[:12])
        csv_data = output.getvalue()
        output.close()

        from flask import Response
        return Response(
            csv_data,
            mimetype="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=periodo_{id_periodo}.csv"
            },
        )
    except Exception as e:
        flash(f"No se pudo generar CSV: {e}", "danger")
        return redirect(url_for("periodos_listado"))


# =============================
# Beneficios / Deducciones
# =============================
@app.route("/catalogos/beneficios")
@requiere_permiso_modulo("Beneficios")
def beneficios_listado():
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT IdBeneficioDeduccion, Nombre, Tipo, TipoCalculo, Valor, Activo, Descripcion
                    FROM BeneficiosDeducciones
                    ORDER BY Nombre
                    """
                )
                items = cur.fetchall()
        return render_template("beneficios/list.html", items=items)
    except Exception as e:
        flash(f"Error cargando beneficios/deducciones: {e}", "danger")
        return render_template("beneficios/list.html", items=[])


@app.route("/catalogos/beneficios/nuevo", methods=["GET", "POST"])
@requiere_permiso_modulo("Beneficios")
def beneficios_nuevo():
    if request.method == "POST":
        nombre = request.form.get("nombre")
        tipo = request.form.get("tipo")  # 'deduccion' o 'prestacion'
        tipo_calc = request.form.get("tipo_calculo")  # 'porcentaje' o 'fijo'
        valor = request.form.get("valor")
        descripcion = request.form.get("descripcion")

        if not nombre or not tipo or not tipo_calc or valor is None:
            flash("Completa todos los campos obligatorios.", "warning")
            return render_template("beneficios/new.html")

        try:
            valor_num = float(valor)
            if valor_num < 0:
                raise ValueError("El valor no puede ser negativo")
        except Exception:
            flash("Valor inválido.", "warning")
            return render_template("beneficios/new.html")

        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO BeneficiosDeducciones (Nombre, Tipo, TipoCalculo, Valor, Activo, Descripcion)
                        VALUES (?, ?, ?, ?, 1, ?)
                        """,
                        (nombre, tipo, tipo_calc, valor_num, descripcion),
                    )
                    conn.commit()
            flash("Creado correctamente.", "success")
            return redirect(url_for("beneficios_listado"))
        except Exception as e:
            flash(f"Error creando registro: {e}", "danger")
            return render_template("beneficios/new.html")

    return render_template("beneficios/new.html")


@app.route("/catalogos/beneficios/<int:id_beneficio>/toggle", methods=["POST"])
@requiere_permiso_modulo("Beneficios")
def beneficios_toggle(id_beneficio: int):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Alterna el estado Activo
                cur.execute(
                    "UPDATE BeneficiosDeducciones SET Activo = CASE WHEN Activo=1 THEN 0 ELSE 1 END WHERE IdBeneficioDeduccion = ?",
                    (id_beneficio,),
                )
            conn.commit()
        flash("Estado actualizado.", "success")
    except Exception as e:
        flash(f"Error actualizando estado: {e}", "danger")
    return redirect(url_for("beneficios_listado"))


@app.route("/catalogos/beneficios/<int:id_beneficio>/editar", methods=["GET", "POST"])
def beneficios_editar(id_beneficio: int):
    if request.method == "POST":
        nombre = request.form.get("nombre")
        tipo = request.form.get("tipo")
        tipo_calc = request.form.get("tipo_calculo")
        valor = request.form.get("valor")
        descripcion = request.form.get("descripcion")
        activo = 1 if request.form.get("activo") else 0
        
        try:
            valor_num = float(valor)
        except Exception:
            flash("Valor inválido.", "warning")
            return redirect(url_for("beneficios_editar", id_beneficio=id_beneficio))

        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE BeneficiosDeducciones
                        SET Nombre = ?, Tipo = ?, TipoCalculo = ?, Valor = ?, Descripcion = ?, Activo = ?
                        WHERE IdBeneficioDeduccion = ?
                        """,
                        (nombre, tipo, tipo_calc, valor_num, descripcion, activo, id_beneficio),
                    )
                    conn.commit()
            registrar_auditoria("Beneficio/Deducción actualizado", "BeneficiosDeducciones", f"ID: {id_beneficio}, Nombre: {nombre}")
            flash("Registro actualizado.", "success")
            return redirect(url_for("beneficios_listado"))
        except Exception as e:
            flash(f"No se pudo actualizar: {e}", "danger")
            return redirect(url_for("beneficios_editar", id_beneficio=id_beneficio))

    # GET: cargar el registro
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT IdBeneficioDeduccion, Nombre, Tipo, TipoCalculo, Valor, Activo, Descripcion FROM BeneficiosDeducciones WHERE IdBeneficioDeduccion = ?",
                    (id_beneficio,),
                )
                row = cur.fetchone()
        if not row:
            flash("Registro no encontrado.", "warning")
            return redirect(url_for("beneficios_listado"))
        return render_template("beneficios/edit.html", item=row)
    except Exception as e:
        flash(f"Error cargando registro: {e}", "danger")
        return redirect(url_for("beneficios_listado"))


@app.route("/catalogos/beneficios/<int:id_beneficio>/eliminar", methods=["POST"])
@requiere_permiso_modulo("Beneficios")
def beneficios_eliminar(id_beneficio: int):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Eliminar primero items que lo referencian
                cur.execute("DELETE FROM ItemsNomina WHERE IdBeneficioDeduccion = ?", (id_beneficio,))
                # Luego el catálogo
                cur.execute("DELETE FROM BeneficiosDeducciones WHERE IdBeneficioDeduccion = ?", (id_beneficio,))
            conn.commit()
        flash("Beneficio/Deducción eliminado.", "success")
    except Exception as e:
        flash(f"No se pudo eliminar: {e}", "danger")
    return redirect(url_for("beneficios_listado"))


@app.route("/nomina/periodos/<int:id_periodo>/eliminar", methods=["POST"])
@requiere_permiso_modulo("Periodos")
def periodos_eliminar(id_periodo: int):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Borrar Items de todos los registros del periodo
                cur.execute(
                    """
                    DELETE i
                    FROM ItemsNomina i
                    JOIN RegistrosNomina rn ON rn.IdNomina = i.IdNomina
                    WHERE rn.IdPeriodo = ?
                    """,
                    (id_periodo,),
                )
                # Borrar registros nómina del periodo
                cur.execute("DELETE FROM RegistrosNomina WHERE IdPeriodo = ?", (id_periodo,))
                # Borrar el periodo
                cur.execute("DELETE FROM PeriodosNomina WHERE IdPeriodo = ?", (id_periodo,))
            conn.commit()
        flash("Periodo eliminado.", "success")
    except Exception as e:
        flash(f"No se pudo eliminar el periodo: {e}", "danger")
    return redirect(url_for("periodos_listado"))
# =============================
# Control de Asistencia (esquema sugerido)
# =============================
@app.route("/asistencia")
@requiere_permiso_modulo("Asistencia")
def asistencia_listado():
    """
    Intenta listar asistencias. Si la tabla no existe, muestra una guía.
    Esquema sugerido:
    CREATE TABLE Asistencias (
        IdAsistencia INT IDENTITY(1,1) PRIMARY KEY,
        IdEmpleado INT NOT NULL FOREIGN KEY REFERENCES Empleados(IdEmpleado) ON DELETE CASCADE,
        FechaHora DATETIME2 NOT NULL DEFAULT GETDATE(),
        Tipo VARCHAR(20) NOT NULL CHECK (Tipo IN ('entrada','salida')),
        Observacion VARCHAR(255) NULL
    );
    """
    # Obtener filtros
    busqueda = request.args.get("busqueda", "").strip()
    
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                if busqueda:
                    # Filtrar por código o nombre
                    cur.execute(
                        """
                        SELECT TOP 100 a.IdAsistencia, a.FechaHora, a.Tipo, a.Observacion,
                               e.IdEmpleado, e.Nombres, e.Apellidos, e.CodigoEmpleado
                        FROM Asistencias a
                        JOIN Empleados e ON e.IdEmpleado = a.IdEmpleado
                        WHERE e.CodigoEmpleado LIKE ?
                           OR e.Nombres LIKE ?
                           OR e.Apellidos LIKE ?
                           OR (e.Nombres + ' ' + e.Apellidos) LIKE ?
                        ORDER BY a.FechaHora DESC
                        """,
                        (f"%{busqueda}%", f"%{busqueda}%", f"%{busqueda}%", f"%{busqueda}%")
                    )
                else:
                    # Sin filtro, mostrar todos
                    cur.execute(
                        """
                        SELECT TOP 100 a.IdAsistencia, a.FechaHora, a.Tipo, a.Observacion,
                               e.IdEmpleado, e.Nombres, e.Apellidos, e.CodigoEmpleado
                        FROM Asistencias a
                        JOIN Empleados e ON e.IdEmpleado = a.IdEmpleado
                        ORDER BY a.FechaHora DESC
                        """
                    )
                rows = cur.fetchall()
        return render_template("asistencia/list.html", items=rows, tabla_ok=True, busqueda=busqueda)
    except Exception as e:
        flash(f"No se pudo consultar asistencias: {e}", "warning")
        return render_template("asistencia/list.html", items=[], tabla_ok=False, busqueda=busqueda)


@app.route("/asistencia/nuevo", methods=["GET", "POST"])
@requiere_permiso_modulo("Asistencia")
def asistencia_nuevo():
    if request.method == "POST":
        id_empleado = request.form.get("id_empleado")
        tipo = request.form.get("tipo")
        observacion = request.form.get("observacion")

        if not id_empleado or not tipo:
            flash("Empleado y tipo son obligatorios.", "warning")
            return render_template("asistencia/new.html", empleados=[])

        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    # Verificar que exista empleado
                    cur.execute("SELECT COUNT(1) FROM Empleados WHERE IdEmpleado = ?", (id_empleado,))
                    if not cur.fetchone()[0]:
                        flash("Empleado no existe.", "warning")
                        return render_template("asistencia/new.html", empleados=[])

                    # Insertar (si la tabla existe)
                    cur.execute(
                        """
                        INSERT INTO Asistencias (IdEmpleado, FechaHora, Tipo, Observacion)
                        VALUES (?, GETDATE(), ?, ?)
                        """,
                        (id_empleado, tipo, observacion),
                    )
                    conn.commit()
            flash("Asistencia registrada.", "success")
            return redirect(url_for("asistencia_listado"))
        except Exception as e:
            flash(f"No se pudo registrar asistencia: {e}", "danger")
            # continuamos a cargar formulario con lista de empleados

    # Cargar lista simple de empleados para el select (si la tabla existe)
    empleados = []
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT IdEmpleado, Nombres, Apellidos FROM Empleados ORDER BY Nombres")
                empleados = cur.fetchall()
    except Exception:
        # si no existe la tabla empleados aún, dejamos la lista vacía
        pass
    return render_template("asistencia/new.html", empleados=empleados)


# =============================
# Empleados (listar y crear)
# =============================
@app.route("/empleados")
@requiere_permiso_modulo("Empleados")
def empleados_listado():
    # Obtener filtros
    busqueda = request.args.get("busqueda", "").strip()
    
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                if busqueda:
                    # Filtrar por código o nombre
                    cur.execute(
                        """
                        SELECT IdEmpleado, CodigoEmpleado, Nombres, Apellidos, 
                               CONVERT(varchar(10), FechaContratacion, 23) as FechaInicio,
                               CONVERT(varchar(10), FechaFin, 23) as FechaFin,
                               SalarioBase, DocumentoIdentidad, NumeroIGSS,
                               CONVERT(varchar(10), FechaNacimiento, 23) as FechaNacimiento
                        FROM Empleados
                        WHERE CodigoEmpleado LIKE ? 
                           OR Nombres LIKE ?
                           OR Apellidos LIKE ?
                           OR (Nombres + ' ' + Apellidos) LIKE ?
                        ORDER BY Apellidos, Nombres
                        """,
                        (f"%{busqueda}%", f"%{busqueda}%", f"%{busqueda}%", f"%{busqueda}%")
                    )
                else:
                    # Sin filtro, mostrar todos
                    cur.execute(
                        """
                        SELECT IdEmpleado, CodigoEmpleado, Nombres, Apellidos, 
                               CONVERT(varchar(10), FechaContratacion, 23) as FechaInicio,
                               CONVERT(varchar(10), FechaFin, 23) as FechaFin,
                               SalarioBase, DocumentoIdentidad, NumeroIGSS,
                               CONVERT(varchar(10), FechaNacimiento, 23) as FechaNacimiento
                        FROM Empleados
                        ORDER BY Apellidos, Nombres
                        """
                    )
                empleados = cur.fetchall()
        return render_template("empleados/list.html", empleados=empleados, busqueda=busqueda)
    except Exception as e:
        flash(f"Error cargando empleados: {e}", "danger")
        return render_template("empleados/list.html", empleados=[], busqueda=busqueda)


@app.route("/empleados/nuevo", methods=["GET", "POST"])
@requiere_permiso_modulo("Empleados")
def empleados_nuevo():
    # Obtener puestos agrupados por departamento
    puestos_por_depto = {}
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT p.IdPuesto, p.Titulo, d.Nombre as Departamento
                    FROM Puestos p
                    JOIN Departamentos d ON d.IdDepartamento = p.IdDepartamento
                    ORDER BY d.Nombre, p.Titulo
                """)
                for row in cur.fetchall():
                    id_puesto, titulo, depto = row
                    if depto not in puestos_por_depto:
                        puestos_por_depto[depto] = []
                    puestos_por_depto[depto].append((id_puesto, titulo))
    except Exception as e:
        print(f"Error obteniendo puestos: {e}")
    
    if request.method == "POST":
        codigo = (request.form.get("codigo") or "").strip()
        nombres = (request.form.get("nombres") or "").strip()
        apellidos = (request.form.get("apellidos") or "").strip()
        fecha_inicio = (request.form.get("fecha_inicio") or "").strip()
        fecha_fin = (request.form.get("fecha_fin") or "").strip() or None
        salario = (request.form.get("salario") or "").strip()
        dpi = (request.form.get("dpi") or "").strip()
        igss = (request.form.get("igss") or "").strip() or None
        correo = (request.form.get("correo") or "").strip() or None
        fecha_nac = (request.form.get("fecha_nacimiento") or "").strip() or None
        id_puesto = (request.form.get("id_puesto") or "").strip() or None

        if not codigo:
            codigo = f"EMP-{int(datetime.now().timestamp())}"
        if not (nombres and apellidos and fecha_inicio and salario and dpi):
            flash("Nombres, Apellidos, Fecha de inicio, Salario y DPI son obligatorios.", "warning")
            return render_template("empleados/new.html", puestos_por_depto=puestos_por_depto)
        try:
            salario_num = float(salario)
            if salario_num < 0:
                raise ValueError
        except Exception:
            flash("Salario inválido.", "warning")
            return render_template("empleados/new.html", puestos_por_depto=puestos_por_depto)

        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    # Unicidad básicas
                    cur.execute("SELECT COUNT(1) FROM Empleados WHERE CodigoEmpleado = ?", (codigo,))
                    if cur.fetchone()[0]:
                        flash("El código de empleado ya existe.", "warning")
                        return render_template("empleados/new.html", puestos_por_depto=puestos_por_depto)
                    cur.execute("SELECT COUNT(1) FROM Empleados WHERE DocumentoIdentidad = ?", (dpi,))
                    if cur.fetchone()[0]:
                        flash("El DPI ya existe en otro empleado.", "warning")
                        return render_template("empleados/new.html", puestos_por_depto=puestos_por_depto)
                    if igss:
                        cur.execute("SELECT COUNT(1) FROM Empleados WHERE NumeroIGSS = ?", (igss,))
                        if cur.fetchone()[0]:
                            flash("El Número IGSS ya existe en otro empleado.", "warning")
                            return render_template("empleados/new.html", puestos_por_depto=puestos_por_depto)
                    if correo:
                        cur.execute("SELECT COUNT(1) FROM Empleados WHERE Correo = ?", (correo,))
                        if cur.fetchone()[0]:
                            flash("El correo ya existe en otro empleado.", "warning")
                            return render_template("empleados/new.html", puestos_por_depto=puestos_por_depto)

                    fi = fecha_inicio if fecha_inicio else None
                    ff = fecha_fin if fecha_fin else None
                    fn = fecha_nac if fecha_nac else None
                    cur.execute(
                        """
                        INSERT INTO Empleados (
                            CodigoEmpleado, Nombres, Apellidos, DocumentoIdentidad,
                            FechaContratacion, FechaFin, SalarioBase, NumeroIGSS, FechaNacimiento,
                            Correo, IdPuesto
                        ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
                        """,
                        (
                            codigo, nombres, apellidos, dpi,
                            fi, ff, salario_num, igss, fn, correo, id_puesto
                        ),
                    )
                    conn.commit()
            flash("Empleado creado.", "success")
            return redirect(url_for("empleados_listado"))
        except Exception as e:
            flash(f"No se pudo crear el empleado: {e}", "danger")
            return render_template("empleados/new.html", puestos_por_depto=puestos_por_depto)

    return render_template("empleados/new.html", puestos_por_depto=puestos_por_depto)


@app.route("/empleados/<int:id_empleado>/editar", methods=["GET", "POST"])
@requiere_permiso_modulo("Empleados")
def empleados_editar(id_empleado: int):
    # Obtener puestos agrupados por departamento
    puestos_por_depto = {}
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT p.IdPuesto, p.Titulo, d.Nombre as Departamento
                    FROM Puestos p
                    JOIN Departamentos d ON d.IdDepartamento = p.IdDepartamento
                    ORDER BY d.Nombre, p.Titulo
                """)
                for row in cur.fetchall():
                    id_puesto, titulo, depto = row
                    if depto not in puestos_por_depto:
                        puestos_por_depto[depto] = []
                    puestos_por_depto[depto].append((id_puesto, titulo))
    except Exception as e:
        print(f"Error obteniendo puestos: {e}")
    
    if request.method == "POST":
        nombres = (request.form.get("nombres") or "").strip()
        apellidos = (request.form.get("apellidos") or "").strip()
        fecha_inicio = (request.form.get("fecha_inicio") or "").strip()
        fecha_fin = (request.form.get("fecha_fin") or "").strip() or None
        salario = (request.form.get("salario") or "").strip()
        dpi = (request.form.get("dpi") or "").strip()
        igss = (request.form.get("igss") or "").strip() or None
        correo = (request.form.get("correo") or "").strip() or None
        fecha_nac = (request.form.get("fecha_nacimiento") or "").strip() or None
        id_puesto = (request.form.get("id_puesto") or "").strip() or None

        if not (nombres and apellidos and fecha_inicio and salario and dpi):
            flash("Nombres, Apellidos, Fecha de inicio, Salario y DPI son obligatorios.", "warning")
            return redirect(url_for("empleados_editar", id_empleado=id_empleado))
        
        try:
            salario_num = float(salario)
            if salario_num < 0:
                raise ValueError
        except Exception:
            flash("Salario inválido.", "warning")
            return redirect(url_for("empleados_editar", id_empleado=id_empleado))

        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    # Verificar que el DPI no esté en uso por otro empleado
                    cur.execute("SELECT COUNT(1) FROM Empleados WHERE DocumentoIdentidad = ? AND IdEmpleado != ?", (dpi, id_empleado))
                    if cur.fetchone()[0]:
                        flash("El DPI ya existe en otro empleado.", "warning")
                        return redirect(url_for("empleados_editar", id_empleado=id_empleado))
                    
                    if igss:
                        cur.execute("SELECT COUNT(1) FROM Empleados WHERE NumeroIGSS = ? AND IdEmpleado != ?", (igss, id_empleado))
                        if cur.fetchone()[0]:
                            flash("El Número IGSS ya existe en otro empleado.", "warning")
                            return redirect(url_for("empleados_editar", id_empleado=id_empleado))
                    
                    if correo:
                        cur.execute("SELECT COUNT(1) FROM Empleados WHERE Correo = ? AND IdEmpleado != ?", (correo, id_empleado))
                        if cur.fetchone()[0]:
                            flash("El correo ya existe en otro empleado.", "warning")
                            return redirect(url_for("empleados_editar", id_empleado=id_empleado))

                    fi = fecha_inicio if fecha_inicio else None
                    ff = fecha_fin if fecha_fin else None
                    fn = fecha_nac if fecha_nac else None
                    
                    cur.execute("""
                        UPDATE Empleados SET
                            Nombres = ?,
                            Apellidos = ?,
                            DocumentoIdentidad = ?,
                            FechaContratacion = ?,
                            FechaFin = ?,
                            SalarioBase = ?,
                            NumeroIGSS = ?,
                            FechaNacimiento = ?,
                            Correo = ?,
                            IdPuesto = ?
                        WHERE IdEmpleado = ?
                    """, (nombres, apellidos, dpi, fi, ff, salario_num, igss, fn, correo, id_puesto, id_empleado))
                    conn.commit()
            
            flash("Empleado actualizado.", "success")
            return redirect(url_for("empleados_listado"))
        except Exception as e:
            flash(f"No se pudo actualizar el empleado: {e}", "danger")
            return redirect(url_for("empleados_editar", id_empleado=id_empleado))
    
    # GET - Cargar datos del empleado
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        CodigoEmpleado, Nombres, Apellidos, DocumentoIdentidad,
                        FechaContratacion, FechaFin, SalarioBase, NumeroIGSS, 
                        FechaNacimiento, Correo, IdPuesto
                    FROM Empleados
                    WHERE IdEmpleado = ?
                """, (id_empleado,))
                empleado = cur.fetchone()
                
                if not empleado:
                    flash("Empleado no encontrado.", "danger")
                    return redirect(url_for("empleados_listado"))
        
        return render_template("empleados/edit.html", 
                             empleado=empleado, 
                             id_empleado=id_empleado,
                             puestos_por_depto=puestos_por_depto)
    except Exception as e:
        flash(f"Error cargando empleado: {e}", "danger")
        return redirect(url_for("empleados_listado"))


@app.route("/empleados/<int:id_empleado>/beneficios", methods=["GET", "POST"])
@requiere_permiso_modulo("Empleados")
def empleados_beneficios(id_empleado: int):
    if request.method == "POST":
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    # Recorremos todos los beneficios del catálogo para leer overrides del form
                    cur.execute("SELECT IdBeneficioDeduccion FROM BeneficiosDeducciones ORDER BY IdBeneficioDeduccion")
                    ids = [row[0] for row in cur.fetchall()]
                    for bid in ids:
                        activo = 1 if request.form.get(f"activo_{bid}") == 'on' else 0
                        tipo_calc = request.form.get(f"tipo_calculo_{bid}") or None
                        valor_txt = request.form.get(f"valor_{bid}")
                        valor = None
                        if valor_txt is not None and valor_txt != "":
                            try:
                                valor = float(valor_txt)
                            except Exception:
                                # si valor invalido, ignoramos y mantenemos None
                                valor = None

                        # upsert sencillo
                        cur.execute(
                            "SELECT 1 FROM EmpleadoBeneficios WHERE IdEmpleado = ? AND IdBeneficioDeduccion = ?",
                            (id_empleado, bid),
                        )
                        exists = cur.fetchone()
                        if exists:
                            cur.execute(
                                """
                                UPDATE EmpleadoBeneficios
                                SET Activo = ?, TipoCalculo = ?, Valor = ?
                                WHERE IdEmpleado = ? AND IdBeneficioDeduccion = ?
                                """,
                                (activo, tipo_calc, valor, id_empleado, bid),
                            )
                        else:
                            cur.execute(
                                """
                                INSERT INTO EmpleadoBeneficios (IdEmpleado, IdBeneficioDeduccion, Activo, TipoCalculo, Valor)
                                VALUES (?, ?, ?, ?, ?)
                                """,
                                (id_empleado, bid, activo, tipo_calc, valor),
                            )
                conn.commit()
            flash("Cambios guardados.", "success")
        except Exception as e:
            flash(f"No se pudo guardar: {e}", "danger")
        return redirect(url_for("empleados_beneficios", id_empleado=id_empleado))

    # GET: listar catálogo con overrides del empleado y préstamos
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT b.IdBeneficioDeduccion, b.Nombre, b.Tipo, b.TipoCalculo, b.Valor, b.Activo,
                           eb.Activo as EBActivo, eb.TipoCalculo as EBTipoCalculo, eb.Valor as EBValor
                    FROM BeneficiosDeducciones b
                    LEFT JOIN EmpleadoBeneficios eb ON eb.IdBeneficioDeduccion = b.IdBeneficioDeduccion AND eb.IdEmpleado = ?
                    ORDER BY b.Tipo, b.Nombre
                    """,
                    (id_empleado,),
                )
                filas = cur.fetchall()
                # info empleado
                cur.execute("SELECT IdEmpleado, Nombres, Apellidos FROM Empleados WHERE IdEmpleado = ?", (id_empleado,))
                emp = cur.fetchone()
                
                # Obtener préstamos del empleado
                prestamos = []
                try:
                    cur.execute(
                        """
                        SELECT IdPrestamo, MontoTotal, MontoPendiente, TipoDescuento, 
                               ValorDescuento, FechaInicio, FechaFin, Estado, Descripcion
                        FROM Prestamos
                        WHERE IdEmpleado = ?
                        ORDER BY FechaCreacion DESC
                        """,
                        (id_empleado,)
                    )
                    prestamos = cur.fetchall()
                except Exception:
                    # Si la tabla no existe, continuar sin préstamos
                    pass
                
        if not emp:
            flash("Empleado no encontrado.", "warning")
            return redirect(url_for("empleados_listado"))
        return render_template("empleados/beneficios.html", filas=filas, emp=emp, prestamos=prestamos)
    except Exception as e:
        flash(f"Error cargando beneficios del empleado: {e}", "danger")
        return redirect(url_for("empleados_listado"))

@app.route("/empleados/<int:id_empleado>/eliminar", methods=["POST"])
@requiere_permiso_modulo("Empleados")
def empleados_eliminar(id_empleado: int):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Eliminar dependencias de nómina del empleado
                cur.execute(
                    """
                    DELETE i
                    FROM ItemsNomina i
                    JOIN RegistrosNomina rn ON rn.IdNomina = i.IdNomina
                    WHERE rn.IdEmpleado = ?
                    """,
                    (id_empleado,),
                )
                cur.execute("DELETE FROM RegistrosNomina WHERE IdEmpleado = ?", (id_empleado,))
                # Asistencias tiene ON DELETE CASCADE (según DDL sugerido)
                # Finalmente eliminar empleado
                cur.execute("DELETE FROM Empleados WHERE IdEmpleado = ?", (id_empleado,))
            conn.commit()
        flash("Empleado eliminado.", "success")
    except Exception as e:
        flash(f"No se pudo eliminar el empleado: {e}", "danger")
    return redirect(url_for("empleados_listado"))


# =============================
# Préstamos a Empleados
# =============================
@app.route("/empleados/<int:id_empleado>/prestamos/crear", methods=["POST"])
@requiere_permiso_modulo("Empleados")
def crear_prestamo(id_empleado: int):
    """Crea un nuevo préstamo para un empleado."""
    try:
        monto_total = float(request.form.get("monto_total", 0))
        tipo_descuento = request.form.get("tipo_descuento")
        valor_descuento = float(request.form.get("valor_descuento", 0))
        descripcion = request.form.get("descripcion", "").strip()
        
        # Validaciones
        if monto_total <= 0:
            flash("El monto total debe ser mayor a 0.", "warning")
            return redirect(url_for("empleados_beneficios", id_empleado=id_empleado))
        
        if tipo_descuento not in ['fijo', 'porcentaje']:
            flash("Tipo de descuento inválido.", "warning")
            return redirect(url_for("empleados_beneficios", id_empleado=id_empleado))
        
        if valor_descuento <= 0:
            flash("El valor de descuento debe ser mayor a 0.", "warning")
            return redirect(url_for("empleados_beneficios", id_empleado=id_empleado))
        
        if tipo_descuento == 'porcentaje' and valor_descuento > 100:
            flash("El porcentaje no puede ser mayor a 100%.", "warning")
            return redirect(url_for("empleados_beneficios", id_empleado=id_empleado))
        
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO Prestamos (IdEmpleado, MontoTotal, MontoPendiente, TipoDescuento, 
                                          ValorDescuento, Descripcion, UsuarioCreacion)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (id_empleado, monto_total, monto_total, tipo_descuento, valor_descuento, 
                     descripcion if descripcion else None, session.get("user_id"))
                )
                conn.commit()
        
        registrar_auditoria("Préstamo creado", "Empleados", f"IdEmpleado: {id_empleado}, Monto: {monto_total}")
        flash(f"Préstamo de Q {monto_total:.2f} creado exitosamente.", "success")
    except Exception as e:
        flash(f"Error al crear préstamo: {e}", "danger")
    
    return redirect(url_for("empleados_beneficios", id_empleado=id_empleado))


@app.route("/prestamos/<int:id_prestamo>/cancelar", methods=["POST"])
@requiere_permiso_modulo("Empleados")
def cancelar_prestamo(id_prestamo: int):
    """Cancela un préstamo activo."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Verificar que el préstamo existe y está activo
                cur.execute("SELECT IdEmpleado, Estado FROM Prestamos WHERE IdPrestamo = ?", (id_prestamo,))
                row = cur.fetchone()
                
                if not row:
                    flash("Préstamo no encontrado.", "warning")
                    return redirect(url_for("empleados_listado"))
                
                id_empleado = row[0]
                estado = row[1]
                
                if estado != 'activo':
                    flash("Solo se pueden cancelar préstamos activos.", "warning")
                    return redirect(url_for("empleados_beneficios", id_empleado=id_empleado))
                
                # Cancelar el préstamo
                cur.execute(
                    "UPDATE Prestamos SET Estado = 'cancelado', FechaFin = GETDATE() WHERE IdPrestamo = ?",
                    (id_prestamo,)
                )
                conn.commit()
        
        registrar_auditoria("Préstamo cancelado", "Empleados", f"IdPrestamo: {id_prestamo}")
        flash("Préstamo cancelado exitosamente.", "success")
        return redirect(url_for("empleados_beneficios", id_empleado=id_empleado))
    except Exception as e:
        flash(f"Error al cancelar préstamo: {e}", "danger")
        return redirect(url_for("empleados_listado"))


@app.route("/prestamos/<int:id_prestamo>/detalle")
@requiere_permiso_modulo("Empleados")
def detalle_prestamo(id_prestamo: int):
    """Muestra el detalle de un préstamo y sus pagos."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Obtener información del préstamo
                cur.execute(
                    """
                    SELECT p.IdPrestamo, p.MontoTotal, p.MontoPendiente, p.TipoDescuento,
                           p.ValorDescuento, p.FechaInicio, p.FechaFin, p.Estado, p.Descripcion,
                           e.IdEmpleado, e.Nombres, e.Apellidos, e.CodigoEmpleado
                    FROM Prestamos p
                    JOIN Empleados e ON e.IdEmpleado = p.IdEmpleado
                    WHERE p.IdPrestamo = ?
                    """,
                    (id_prestamo,)
                )
                prestamo = cur.fetchone()
                
                if not prestamo:
                    flash("Préstamo no encontrado.", "warning")
                    return redirect(url_for("empleados_listado"))
                
                # Obtener historial de pagos
                cur.execute(
                    """
                    SELECT pp.IdPago, pp.MontoPagado, pp.FechaPago,
                           pn.IdPeriodo, pn.FechaInicio, pn.FechaFin, pn.TipoPeriodo
                    FROM PrestamoPagos pp
                    JOIN PeriodosNomina pn ON pn.IdPeriodo = pp.IdPeriodo
                    WHERE pp.IdPrestamo = ?
                    ORDER BY pp.FechaPago DESC
                    """,
                    (id_prestamo,)
                )
                pagos = cur.fetchall()
        
        return render_template("prestamos/detalle.html", prestamo=prestamo, pagos=pagos)
    except Exception as e:
        flash(f"Error cargando detalle del préstamo: {e}", "danger")
        return redirect(url_for("empleados_listado"))


@app.route("/nomina/registros/<int:id_nomina>/eliminar", methods=["POST"])
def registro_nomina_eliminar(id_nomina: int):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Borrar items dependientes primero
                cur.execute("DELETE FROM ItemsNomina WHERE IdNomina = ?", (id_nomina,))
                # Borrar el registro de nómina
                cur.execute("DELETE FROM RegistrosNomina WHERE IdNomina = ?", (id_nomina,))
            conn.commit()
        flash("Registro de nómina eliminado.", "success")
    except Exception as e:
        flash(f"No se pudo eliminar el registro de nómina: {e}", "danger")
    return redirect(url_for("periodos_listado"))


# =============================
# Departamentos y Puestos
# =============================
@app.route("/catalogos/departamentos")
@requiere_permiso_modulo("Departamentos")
def departamentos_listado():
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Obtener departamentos
                cur.execute(
                    """
                    SELECT IdDepartamento, Nombre, Descripcion
                    FROM Departamentos
                    ORDER BY Nombre
                    """
                )
                departamentos = [dict(zip(['IdDepartamento', 'Nombre', 'Descripcion'], row)) 
                                for row in cur.fetchall()]
                
                # Obtener puestos para cada departamento
                for depto in departamentos:
                    cur.execute(
                        """
                        SELECT IdPuesto, Titulo, Descripcion
                        FROM Puestos
                        WHERE IdDepartamento = ?
                        ORDER BY Titulo
                        """,
                        (depto['IdDepartamento'],)
                    )
                    depto['Puestos'] = [dict(zip(['IdPuesto', 'Titulo', 'Descripcion'], row))
                                       for row in cur.fetchall()]
                
        return render_template("departamentos/list.html", departamentos=departamentos)
    except Exception as e:
        flash(f"Error cargando departamentos: {e}", "danger")
        return render_template("departamentos/list.html", departamentos=[])


@app.route("/catalogos/departamentos/nuevo", methods=["GET", "POST"])
@requiere_permiso_modulo("Departamentos")
def departamentos_nuevo():
    if request.method == "POST":
        nombre = (request.form.get("nombre") or "").strip()
        descripcion = (request.form.get("descripcion") or "").strip()

        if not nombre:
            flash("El nombre es obligatorio.", "warning")
            return render_template("departamentos/new.html")

        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    # Verificar unicidad
                    cur.execute("SELECT COUNT(1) FROM Departamentos WHERE Nombre = ?", (nombre,))
                    if cur.fetchone()[0]:
                        flash("Ya existe un departamento con ese nombre.", "warning")
                        return render_template("departamentos/new.html")

                    cur.execute(
                        """
                        INSERT INTO Departamentos (Nombre, Descripcion)
                        VALUES (?, ?)
                        """,
                        (nombre, descripcion)
                    )
                    conn.commit()
            registrar_auditoria("Departamento creado", "Departamentos", f"Nombre: {nombre}")
            flash("Departamento creado correctamente.", "success")
            return redirect(url_for("departamentos_listado"))
        except Exception as e:
            flash(f"Error creando departamento: {e}", "danger")
            return render_template("departamentos/new.html")

    return render_template("departamentos/new.html")


@app.route("/catalogos/departamentos/<int:id_departamento>/toggle", methods=["POST"])
@requiere_permiso_modulo("Departamentos")
def departamentos_toggle(id_departamento: int):
    """Función deshabilitada - La tabla Departamentos no tiene columna Activo."""
    flash("La función de activar/desactivar no está disponible para departamentos.", "warning")
    return redirect(url_for("departamentos_listado"))


@app.route("/catalogos/departamentos/<int:id_departamento>/eliminar", methods=["POST"])
@requiere_permiso_modulo("Departamentos")
def departamentos_eliminar(id_departamento: int):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Verificar si tiene puestos asociados
                cur.execute("SELECT COUNT(1) FROM Puestos WHERE IdDepartamento = ?", (id_departamento,))
                if cur.fetchone()[0] > 0:
                    flash("No se puede eliminar el departamento porque tiene puestos asociados.", "warning")
                    return redirect(url_for("departamentos_listado"))
                
                cur.execute("DELETE FROM Departamentos WHERE IdDepartamento = ?", (id_departamento,))
                conn.commit()
        registrar_auditoria("Departamento eliminado", "Departamentos", f"ID: {id_departamento}")
        flash("Departamento eliminado.", "success")
    except Exception as e:
        flash(f"Error eliminando departamento: {e}", "danger")
    return redirect(url_for("departamentos_listado"))


# Puestos
@app.route("/catalogos/puestos/nuevo/<int:id_departamento>", methods=["GET", "POST"])
@requiere_permiso_modulo("Departamentos")
def puestos_nuevo(id_departamento: int):
    """Crea un nuevo puesto en un departamento."""
    if request.method == "POST":
        titulo = (request.form.get("titulo") or "").strip()
        descripcion = (request.form.get("descripcion") or "").strip()

        if not titulo:
            flash("El título del puesto es obligatorio.", "warning")
            return redirect(url_for("departamentos_listado"))

        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    # Verificar que el departamento existe
                    cur.execute("SELECT COUNT(1) FROM Departamentos WHERE IdDepartamento = ?", (id_departamento,))
                    if not cur.fetchone()[0]:
                        flash("El departamento no existe.", "danger")
                        return redirect(url_for("departamentos_listado"))
                    
                    # Verificar unicidad del título en el departamento
                    cur.execute(
                        "SELECT COUNT(1) FROM Puestos WHERE Titulo = ? AND IdDepartamento = ?", 
                        (titulo, id_departamento)
                    )
                    if cur.fetchone()[0]:
                        flash("Ya existe un puesto con ese título en este departamento.", "warning")
                        return redirect(url_for("departamentos_listado"))

                    cur.execute(
                        """
                        INSERT INTO Puestos (IdDepartamento, Titulo, Descripcion)
                        VALUES (?, ?, ?)
                        """,
                        (id_departamento, titulo, descripcion)
                    )
                    conn.commit()
            registrar_auditoria("Puesto creado", "Puestos", f"Título: {titulo}, Departamento ID: {id_departamento}")
            flash("Puesto creado correctamente.", "success")
            return redirect(url_for("departamentos_listado"))
        except Exception as e:
            flash(f"Error creando puesto: {e}", "danger")
            return redirect(url_for("departamentos_listado"))

    # GET: Mostrar formulario
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT Nombre FROM Departamentos WHERE IdDepartamento = ?", (id_departamento,))
                row = cur.fetchone()
                if not row:
                    flash("Departamento no encontrado.", "danger")
                    return redirect(url_for("departamentos_listado"))
                departamento_nombre = row[0]
        
        return render_template("puestos/new.html", 
                             id_departamento=id_departamento,
                             departamento_nombre=departamento_nombre)
    except Exception as e:
        flash(f"Error: {e}", "danger")
        return redirect(url_for("departamentos_listado"))


@app.route("/catalogos/puestos/<int:id_puesto>/eliminar", methods=["POST"])
@requiere_permiso_modulo("Departamentos")
def puestos_eliminar(id_puesto: int):
    """Elimina un puesto."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Verificar si hay empleados con este puesto
                cur.execute("SELECT COUNT(1) FROM Empleados WHERE IdPuesto = ?", (id_puesto,))
                if cur.fetchone()[0] > 0:
                    flash("No se puede eliminar el puesto porque tiene empleados asignados.", "warning")
                    return redirect(url_for("departamentos_listado"))
                
                cur.execute("DELETE FROM Puestos WHERE IdPuesto = ?", (id_puesto,))
                conn.commit()
        registrar_auditoria("Puesto eliminado", "Puestos", f"ID: {id_puesto}")
        flash("Puesto eliminado.", "success")
    except Exception as e:
        flash(f"Error eliminando puesto: {e}", "danger")
    return redirect(url_for("departamentos_listado"))


# =============================
# Usuarios y Roles
# =============================
@app.route("/seguridad/usuarios")
@requiere_permiso_modulo("Usuarios")
def usuarios_listado():
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT u.IdUsuario, u.NombreUsuario, u.Correo, u.Activo, 
                           u.FechaCreacion, r.Nombre as NombreRol, r.IdRol
                    FROM Usuarios u
                    LEFT JOIN Roles r ON r.IdRol = u.IdRol
                    ORDER BY u.NombreUsuario
                """)
                # Convertir a lista de diccionarios para mejor manejo en la plantilla
                columns = [column[0] for column in cur.description]
                usuarios = [dict(zip(columns, row)) for row in cur.fetchall()]
                
                # Obtener todos los roles para el filtro
                cur.execute("SELECT IdRol, Nombre FROM Roles ORDER BY Nombre")
                roles = [dict(zip(['IdRol', 'Nombre'], row)) for row in cur.fetchall()]
                
        return render_template("usuarios/list.html", usuarios=usuarios, roles=roles)
    except Exception as e:
        print(f"Error en usuarios_listado: {e}")
        flash("Error al cargar la lista de usuarios. Por favor, intente nuevamente.", "danger")
        return render_template("usuarios/list.html", usuarios=[], roles=[])


@app.route("/seguridad/usuarios/nuevo", methods=["GET", "POST"])
@requiere_permiso_modulo("Usuarios")
def usuarios_nuevo():
    # Obtener lista de roles y empleados para el formulario
    roles = []
    empleados = []
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Obtener roles
                cur.execute("""
                    SELECT r.IdRol, r.Nombre, r.Descripcion 
                    FROM Roles r 
                    ORDER BY r.Nombre
                """)
                roles = [dict(zip([column[0] for column in cur.description], row)) 
                        for row in cur.fetchall()]
                
                # Obtener empleados que NO tienen usuario asignado
                cur.execute("""
                    SELECT e.IdEmpleado, e.Nombres, e.Apellidos, 
                           p.Titulo as Puesto, d.Nombre as Departamento
                    FROM Empleados e
                    LEFT JOIN Puestos p ON p.IdPuesto = e.IdPuesto
                    LEFT JOIN Departamentos d ON d.IdDepartamento = p.IdDepartamento
                    WHERE e.IdEmpleado NOT IN (
                          SELECT IdEmpleado FROM Usuarios 
                          WHERE IdEmpleado IS NOT NULL
                      )
                    ORDER BY e.Apellidos, e.Nombres
                """)
                empleados = [dict(zip([column[0] for column in cur.description], row)) 
                            for row in cur.fetchall()]
    except Exception as e:
        print(f"Error obteniendo datos: {e}")
        flash(f"Error al cargar datos: {e}", "danger")
        return redirect(url_for("usuarios_listado"))

    if request.method == "POST":
        nombre_usuario = (request.form.get("nombre_usuario") or "").strip()
        correo = (request.form.get("correo") or "").strip()
        clave = (request.form.get("clave") or "").strip()
        id_rol = request.form.get("id_rol", type=int)
        id_empleado = request.form.get("id_empleado", type=int) if request.form.get("id_empleado") else None

        if not nombre_usuario or not correo or not clave or not id_rol:
            flash("Todos los campos son obligatorios.", "warning")
            return render_template("usuarios/new.html", roles=roles, empleados=empleados)

        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    # Verificar unicidad
                    cur.execute("SELECT COUNT(1) FROM Usuarios WHERE NombreUsuario = ?", (nombre_usuario,))
                    if cur.fetchone()[0]:
                        flash("El nombre de usuario ya existe.", "warning")
                        return render_template("usuarios/new.html", roles=roles, empleados=empleados)
                        
                    cur.execute("SELECT COUNT(1) FROM Usuarios WHERE Correo = ?", (correo,))
                    if cur.fetchone()[0]:
                        flash("El correo ya está registrado.", "warning")
                        return render_template("usuarios/new.html", roles=roles, empleados=empleados)
                    
                    # Verificar que el rol exista
                    cur.execute("SELECT COUNT(1) FROM Roles WHERE IdRol = ?", (id_rol,))
                    if not cur.fetchone()[0]:
                        flash("El rol seleccionado no es válido.", "danger")
                        return render_template("usuarios/new.html", roles=roles, empleados=empleados)
                    
                    # Si se seleccionó empleado, verificar que existe y no tiene usuario
                    if id_empleado:
                        cur.execute("SELECT COUNT(1) FROM Empleados WHERE IdEmpleado = ?", (id_empleado,))
                        if not cur.fetchone()[0]:
                            flash("El empleado seleccionado no es válido.", "danger")
                            return render_template("usuarios/new.html", roles=roles, empleados=empleados)
                        
                        cur.execute("SELECT COUNT(1) FROM Usuarios WHERE IdEmpleado = ?", (id_empleado,))
                        if cur.fetchone()[0]:
                            flash("El empleado seleccionado ya tiene un usuario asignado.", "warning")
                            return render_template("usuarios/new.html", roles=roles, empleados=empleados)

                    # Crear el usuario con IdEmpleado
                    cur.execute(
                        """
                        INSERT INTO Usuarios (NombreUsuario, Correo, ClaveHash, IdRol, IdEmpleado, Activo)
                        VALUES (?, ?, ?, ?, ?, 1)
                        """,
                        (nombre_usuario, correo, clave, id_rol, id_empleado),
                    )
                    conn.commit()
                    
                    # Obtener el ID del usuario recién creado
                    user_id = cur.execute("SELECT SCOPE_IDENTITY()").fetchval()
                    
                    # Registrar la acción en auditoría
                    empleado_info = f", Empleado: {id_empleado}" if id_empleado else ""
                    registrar_auditoria(
                        "Usuario creado", 
                        "Usuarios", 
                        f"ID: {user_id}, Usuario: {nombre_usuario}, Rol: {id_rol}{empleado_info}"
                    )
            
            flash("Usuario creado exitosamente.", "success")
            return redirect(url_for("usuarios_listado"))
            
        except Exception as e:
            print(f"Error al crear usuario: {e}")
            flash(f"Error al crear el usuario: {e}. Si la columna IdEmpleado no existe, ejecuta el script ADD_IDEMPLEADO_TO_USUARIOS.sql", "danger")
    
    # GET: Mostrar formulario con roles y empleados
    return render_template("usuarios/new.html", roles=roles, empleados=empleados)


@app.route("/seguridad/usuarios/<int:id_usuario>/editar", methods=["GET", "POST"])
@requiere_permiso_modulo("Usuarios")
def usuarios_editar(id_usuario: int):
    """Edita un usuario existente."""
    # Obtener lista de roles y empleados para el formulario
    roles = []
    empleados = []
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Obtener roles
                cur.execute("""
                    SELECT r.IdRol, r.Nombre, r.Descripcion 
                    FROM Roles r 
                    ORDER BY r.Nombre
                """)
                roles = [dict(zip([column[0] for column in cur.description], row)) 
                        for row in cur.fetchall()]
                
                # Obtener empleados que NO tienen usuario O que son del usuario actual
                cur.execute("""
                    SELECT e.IdEmpleado, e.Nombres, e.Apellidos, 
                           p.Titulo as Puesto, d.Nombre as Departamento
                    FROM Empleados e
                    LEFT JOIN Puestos p ON p.IdPuesto = e.IdPuesto
                    LEFT JOIN Departamentos d ON d.IdDepartamento = p.IdDepartamento
                    WHERE e.IdEmpleado NOT IN (
                          SELECT IdEmpleado FROM Usuarios 
                          WHERE IdEmpleado IS NOT NULL 
                            AND IdUsuario != ?
                      )
                    ORDER BY e.Apellidos, e.Nombres
                """, (id_usuario,))
                empleados = [dict(zip([column[0] for column in cur.description], row)) 
                            for row in cur.fetchall()]
    except Exception as e:
        print(f"Error obteniendo datos: {e}")
        flash("Error al cargar los datos. Intente nuevamente.", "danger")
        return redirect(url_for("usuarios_listado"))

    if request.method == "POST":
        nombre_usuario = (request.form.get("nombre_usuario") or "").strip()
        correo = (request.form.get("correo") or "").strip()
        clave = (request.form.get("clave") or "").strip()
        id_rol = request.form.get("id_rol", type=int)
        id_empleado = request.form.get("id_empleado", type=int) if request.form.get("id_empleado") else None
        activo = request.form.get("activo") == "1"

        if not nombre_usuario or not correo or not id_rol:
            flash("El nombre de usuario, correo y rol son obligatorios.", "warning")
            return redirect(url_for("usuarios_editar", id_usuario=id_usuario))

        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    # Verificar que el usuario exists
                    cur.execute("SELECT COUNT(1) FROM Usuarios WHERE IdUsuario = ?", (id_usuario,))
                    if not cur.fetchone()[0]:
                        flash("El usuario no existe.", "danger")
                        return redirect(url_for("usuarios_listado"))
                    
                    # Verificar unicidad del nombre de usuario (excepto el actual)
                    cur.execute(
                        "SELECT COUNT(1) FROM Usuarios WHERE NombreUsuario = ? AND IdUsuario != ?", 
                        (nombre_usuario, id_usuario)
                    )
                    if cur.fetchone()[0]:
                        flash("El nombre de usuario ya existe.", "warning")
                        return redirect(url_for("usuarios_editar", id_usuario=id_usuario))
                        
                    # Verificar unicidad del correo (excepto el actual)
                    cur.execute(
                        "SELECT COUNT(1) FROM Usuarios WHERE Correo = ? AND IdUsuario != ?", 
                        (correo, id_usuario)
                    )
                    if cur.fetchone()[0]:
                        flash("El correo ya está registrado.", "warning")
                        return redirect(url_for("usuarios_editar", id_usuario=id_usuario))
                    
                    # Verificar que el rol exista
                    cur.execute("SELECT COUNT(1) FROM Roles WHERE IdRol = ?", (id_rol,))
                    if not cur.fetchone()[0]:
                        flash("El rol seleccionado no es válido.", "danger")
                        return redirect(url_for("usuarios_editar", id_usuario=id_usuario))
                    
                    # Si se seleccionó empleado, verificar que existe y no está asignado a otro usuario
                    if id_empleado:
                        cur.execute("SELECT COUNT(1) FROM Empleados WHERE IdEmpleado = ?", (id_empleado,))
                        if not cur.fetchone()[0]:
                            flash("El empleado seleccionado no es válido.", "danger")
                            return redirect(url_for("usuarios_editar", id_usuario=id_usuario))
                        
                        # Verificar que no esté asignado a otro usuario
                        cur.execute(
                            "SELECT COUNT(1) FROM Usuarios WHERE IdEmpleado = ? AND IdUsuario != ?", 
                            (id_empleado, id_usuario)
                        )
                        if cur.fetchone()[0]:
                            flash("El empleado seleccionado ya tiene un usuario asignado.", "warning")
                            return redirect(url_for("usuarios_editar", id_usuario=id_usuario))

                    # Actualizar el usuario
                    if clave:
                        # Si se proporciona una nueva contraseña, actualizarla
                        cur.execute(
                            """
                            UPDATE Usuarios 
                            SET NombreUsuario = ?, Correo = ?, ClaveHash = ?, IdRol = ?, IdEmpleado = ?, Activo = ?
                            WHERE IdUsuario = ?
                            """,
                            (nombre_usuario, correo, clave, id_rol, id_empleado, activo, id_usuario),
                        )
                    else:
                        # Si no se proporciona contraseña, mantener la actual
                        cur.execute(
                            """
                            UPDATE Usuarios 
                            SET NombreUsuario = ?, Correo = ?, IdRol = ?, IdEmpleado = ?, Activo = ?
                            WHERE IdUsuario = ?
                            """,
                            (nombre_usuario, correo, id_rol, id_empleado, activo, id_usuario),
                        )
                    conn.commit()
                    
                    # Registrar la acción en auditoría
                    empleado_info = f", Empleado: {id_empleado}" if id_empleado else ", Sin empleado"
                    registrar_auditoria(
                        "Usuario actualizado", 
                        "Usuarios", 
                        f"ID: {id_usuario}, Usuario: {nombre_usuario}, Rol: {id_rol}{empleado_info}"
                    )
            
            flash("Usuario actualizado exitosamente.", "success")
            return redirect(url_for("usuarios_listado"))
            
        except Exception as e:
            print(f"Error al actualizar usuario: {e}")
            flash("Ocurrió un error al actualizar el usuario. Por favor, intente nuevamente.", "danger")
    
    # GET: Obtener datos del usuario y mostrar formulario
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT IdUsuario, NombreUsuario, Correo, IdRol, IdEmpleado, Activo
                    FROM Usuarios 
                    WHERE IdUsuario = ?
                """, (id_usuario,))
                row = cur.fetchone()
                
                if not row:
                    flash("Usuario no encontrado.", "danger")
                    return redirect(url_for("usuarios_listado"))
                
                usuario = {
                    'IdUsuario': row[0],
                    'NombreUsuario': row[1],
                    'Correo': row[2],
                    'IdRol': row[3],
                    'IdEmpleado': row[4],
                    'Activo': row[5]
                }
                
        return render_template("usuarios/edit.html", usuario=usuario, roles=roles, empleados=empleados)
        
    except Exception as e:
        print(f"Error al obtener usuario: {e}")
        flash("Error al cargar el usuario.", "danger")
        return redirect(url_for("usuarios_listado"))


@app.route("/seguridad/usuarios/<int:id_usuario>/toggle", methods=["POST"])
@requiere_permiso_modulo("Usuarios")
def usuarios_toggle(id_usuario: int):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE Usuarios SET Activo = CASE WHEN Activo=1 THEN 0 ELSE 1 END WHERE IdUsuario = ?",
                    (id_usuario,),
                )
                conn.commit()
        registrar_auditoria("Estado de usuario actualizado", "Usuarios", f"ID: {id_usuario}")
        flash("Estado del usuario actualizado.", "success")
    except Exception as e:
        flash(f"Error actualizando usuario: {e}", "danger")
    return redirect(url_for("usuarios_listado"))


@app.route("/seguridad/usuarios/<int:id_usuario>/eliminar", methods=["POST"])
@requiere_permiso_modulo("Usuarios")
def usuarios_eliminar(id_usuario: int):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM Usuarios WHERE IdUsuario = ?", (id_usuario,))
                conn.commit()
        registrar_auditoria("Usuario eliminado", "Usuarios", f"ID: {id_usuario}")
        flash("Usuario eliminado.", "success")
    except Exception as e:
        flash(f"Error eliminando usuario: {e}", "danger")
    return redirect(url_for("usuarios_listado"))


# =============================
# Permisos por Módulo
# =============================
@app.route("/seguridad/permisos")
@requiere_permiso_modulo("Permisos")
def permisos_listado():
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Obtener usuarios con sus roles
                cur.execute("""
                    SELECT u.IdUsuario, u.NombreUsuario, r.Nombre as Rol
                    FROM Usuarios u
                    LEFT JOIN Roles r ON r.IdRol = u.IdRol
                    WHERE u.Activo = 1
                    ORDER BY u.NombreUsuario
                """)
                usuarios = cur.fetchall()
                
                # Obtener módulos activos
                cur.execute("""
                    SELECT IdModulo, Nombre, Descripcion, Ruta, Icono, Orden
                    FROM Modulos
                    WHERE Activo = 1
                    ORDER BY Orden
                """)
                modulos = cur.fetchall()
                
                # Obtener plantillas
                cur.execute("""
                    SELECT IdPlantilla, Nombre, Descripcion
                    FROM PlantillasPermisos
                    WHERE Activo = 1
                    ORDER BY Nombre
                """)
                plantillas = cur.fetchall()
                
                # Obtener permisos actuales con acciones
                cur.execute("""
                    SELECT IdUsuario, IdModulo, TieneAcceso, PuedeCrear, PuedeEditar, PuedeEliminar
                    FROM PermisosUsuarios
                """)
                permisos_raw = cur.fetchall()
                
                # Organizar permisos en diccionario
                permisos = {}
                for p in permisos_raw:
                    id_usuario = str(p[0])
                    id_modulo = p[1]
                    if id_usuario not in permisos:
                        permisos[id_usuario] = {}
                    permisos[id_usuario][id_modulo] = {
                        'ver': p[2],
                        'crear': p[3],
                        'editar': p[4],
                        'eliminar': p[5]
                    }
        
        return render_template("permisos/list_v2.html", usuarios=usuarios, modulos=modulos, permisos=permisos, plantillas=plantillas)
    except Exception as e:
        flash(f"Error cargando permisos: {e}", "danger")
        return render_template("permisos/list_v2.html", usuarios=[], modulos=[], permisos={}, plantillas=[])


@app.route("/seguridad/permisos/guardar", methods=["POST"])
@requiere_permiso_modulo("Permisos")
def permisos_guardar():
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Obtener todos los usuarios y módulos
                cur.execute("SELECT IdUsuario FROM Usuarios WHERE Activo = 1")
                usuarios = [row[0] for row in cur.fetchall()]
                
                cur.execute("SELECT IdModulo FROM Modulos WHERE Activo = 1")
                modulos = [row[0] for row in cur.fetchall()]
                
                # Eliminar todos los permisos existentes
                cur.execute("DELETE FROM PermisosUsuarios")
                
                # Insertar nuevos permisos basados en checkboxes (con acciones)
                for id_usuario in usuarios:
                    for id_modulo in modulos:
                        ver = 1 if request.form.get(f"ver_{id_usuario}_{id_modulo}") else 0
                        crear = 1 if request.form.get(f"crear_{id_usuario}_{id_modulo}") else 0
                        editar = 1 if request.form.get(f"editar_{id_usuario}_{id_modulo}") else 0
                        eliminar = 1 if request.form.get(f"eliminar_{id_usuario}_{id_modulo}") else 0
                        
                        # Solo insertar si tiene al menos acceso de ver
                        if ver:
                            cur.execute("""
                                INSERT INTO PermisosUsuarios (IdUsuario, IdModulo, TieneAcceso, PuedeCrear, PuedeEditar, PuedeEliminar)
                                VALUES (?, ?, 1, ?, ?, ?)
                            """, (id_usuario, id_modulo, crear, editar, eliminar))
                
                conn.commit()
        
        registrar_auditoria("Permisos actualizados", "Permisos", "Permisos de módulos y acciones actualizados para todos los usuarios")
        flash("Permisos actualizados correctamente.", "success")
    except Exception as e:
        flash(f"Error guardando permisos: {e}", "danger")
    
    return redirect(url_for("permisos_listado"))


@app.route("/seguridad/permisos/aplicar-plantilla", methods=["POST"])
@requiere_permiso_modulo("Permisos")
def permisos_aplicar_plantilla():
    """Aplica una plantilla de permisos a usuarios seleccionados."""
    try:
        data = request.get_json()
        id_plantilla = data.get('id_plantilla')
        usuarios = data.get('usuarios', [])
        
        if not id_plantilla or not usuarios:
            return {"error": "Datos incompletos"}, 400
        
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Obtener permisos de la plantilla
                cur.execute("""
                    SELECT IdModulo, TieneAcceso, PuedeCrear, PuedeEditar, PuedeEliminar
                    FROM PlantillasPermisosDetalle
                    WHERE IdPlantilla = ?
                """, (id_plantilla,))
                permisos_plantilla = cur.fetchall()
                
                # Aplicar a cada usuario
                for id_usuario in usuarios:
                    # Eliminar permisos existentes del usuario
                    cur.execute("DELETE FROM PermisosUsuarios WHERE IdUsuario = ?", (id_usuario,))
                    
                    # Insertar permisos de la plantilla
                    for perm in permisos_plantilla:
                        cur.execute("""
                            INSERT INTO PermisosUsuarios (IdUsuario, IdModulo, TieneAcceso, PuedeCrear, PuedeEditar, PuedeEliminar)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (id_usuario, perm[0], perm[1], perm[2], perm[3], perm[4]))
                
                conn.commit()
        
        registrar_auditoria("Plantilla de permisos aplicada", "Permisos", f"Plantilla {id_plantilla} aplicada a {len(usuarios)} usuario(s)")
        return {"success": True}, 200
    except Exception as e:
        return {"error": str(e)}, 500


# =============================
# Auditoría
# =============================
@app.route("/seguridad/auditoria")
@requiere_permiso_modulo("Auditoria")
def auditoria_listado():
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT TOP 200 IdLog, NombreUsuario, Accion, Modulo, Detalles,
                           CONVERT(varchar(19), FechaHora, 120) as FechaHora, DireccionIP
                    FROM Auditoria
                    ORDER BY FechaHora DESC
                    """
                )
                logs = cur.fetchall()
        return render_template("auditoria/list.html", logs=logs)
    except Exception as e:
        flash(f"Error cargando auditoría: {e}", "danger")
        return render_template("auditoria/list.html", logs=[])


# =============================
# Comprobantes de Pago (PDF) (JAMES) GENERAR CARGA MASIVA PARA OBTENER UN DOCUMENTO CON TODOS LOS COMPROBANTES DE ACUERDO 
#CON LOS PERIODOS DE NÓMINA (POR FECHAS)
# =============================
def generar_comprobante_pdf(id_nomina: int):
    """Genera un comprobante de pago en PDF para un registro de nómina."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    # Obtener datos del comprobante
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Datos del empleado y periodo
            cur.execute("""
                SELECT 
                    e.IdEmpleado, e.CodigoEmpleado, e.Nombres, e.Apellidos, e.DocumentoIdentidad, e.NumeroIGSS,
                    p.IdPeriodo, p.FechaInicio, p.FechaFin, p.TipoPeriodo,
                    rn.SalarioBase, rn.TotalPrestaciones, rn.TotalDeducciones, rn.SalarioNeto
                FROM RegistrosNomina rn
                JOIN Empleados e ON e.IdEmpleado = rn.IdEmpleado
                JOIN PeriodosNomina p ON p.IdPeriodo = rn.IdPeriodo
                WHERE rn.IdNomina = ?
            """, (id_nomina,))
            row = cur.fetchone()
            if not row:
                return None
            
            empleado = {
                "id": row[0], "codigo": row[1], "nombres": row[2], "apellidos": row[3],
                "dpi": row[4], "igss": row[5]
            }
            periodo = {
                "id": row[6], "inicio": row[7], "fin": row[8], "tipo": row[9]
            }
            nomina = {
                "salario_base": row[10], "prestaciones": row[11], 
                "deducciones": row[12], "neto": row[13]
            }
            
            # Items de nómina (prestaciones y deducciones)
            cur.execute("""
                SELECT b.Nombre, i.TipoItem, i.Monto
                FROM ItemsNomina i
                JOIN BeneficiosDeducciones b ON b.IdBeneficioDeduccion = i.IdBeneficioDeduccion
                WHERE i.IdNomina = ?
                ORDER BY i.TipoItem DESC, b.Nombre
            """, (id_nomina,))
            items = cur.fetchall()
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor('#1e40af'), alignment=TA_CENTER)
    subtitle_style = ParagraphStyle('CustomSubtitle', parent=styles['Normal'], fontSize=10, textColor=colors.grey, alignment=TA_CENTER)
    
    # Contenido del PDF
    story = []
    
    # Encabezado
    story.append(Paragraph("COMPROBANTE DE PAGO", title_style))
    story.append(Paragraph(f"Periodo: {periodo['inicio']} - {periodo['fin']}", subtitle_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Información del empleado
    emp_data = [
        ["Código:", empleado['codigo'], "Nombre:", f"{empleado['nombres']} {empleado['apellidos']}"],
        ["DPI:", empleado['dpi'], "IGSS:", empleado['igss'] or 'N/A']
    ]
    emp_table = Table(emp_data, colWidths=[1*inch, 1.5*inch, 1*inch, 2.5*inch])
    emp_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e5e7eb')),
        ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#e5e7eb')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    story.append(emp_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Detalle de nómina
    detail_data = [["Concepto", "Tipo", "Monto"]]
    detail_data.append(["Salario Base", "Base", f"Q {nomina['salario_base']:.2f}"])
    
    for item in items:
        tipo_label = "Prestación" if item[1] == "prestacion" else "Deducción"
        detail_data.append([item[0], tipo_label, f"Q {item[2]:.2f}"])
    
    detail_table = Table(detail_data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
    detail_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f3f4f6')])
    ]))
    story.append(detail_table)
    story.append(Spacer(1, 0.2*inch))
    
    # Resumen
    summary_data = [
        ["Total Prestaciones:", f"Q {nomina['prestaciones']:.2f}"],
        ["Total Deducciones:", f"Q {nomina['deducciones']:.2f}"],
        ["SALARIO NETO:", f"Q {nomina['neto']:.2f}"]
    ]
    summary_table = Table(summary_data, colWidths=[4*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 12),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#1e40af')),
        ('LINEABOVE', (0, -1), (-1, -1), 2, colors.HexColor('#1e40af')),
        ('FONTSIZE', (0, 0), (-1, -2), 10),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 0.5*inch))
    
    # Pie de página
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey, alignment=TA_CENTER)
    story.append(Paragraph(f"Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}", footer_style))
    
    # Construir PDF
    doc.build(story)
    buffer.seek(0)
    return buffer


def generar_comprobante_html(id_nomina: int):
    """Genera un comprobante de pago en HTML para un registro de nómina."""
    # Obtener datos del comprobante
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Datos del empleado y periodo
            cur.execute("""
                SELECT 
                    e.IdEmpleado, e.CodigoEmpleado, e.Nombres, e.Apellidos, e.DocumentoIdentidad, e.NumeroIGSS,
                    p.IdPeriodo, p.FechaInicio, p.FechaFin, p.TipoPeriodo,
                    rn.SalarioBase, rn.TotalPrestaciones, rn.TotalDeducciones, rn.SalarioNeto,
                    pu.Titulo as Puesto, d.Nombre as Departamento
                FROM RegistrosNomina rn
                JOIN Empleados e ON e.IdEmpleado = rn.IdEmpleado
                JOIN PeriodosNomina p ON p.IdPeriodo = rn.IdPeriodo
                LEFT JOIN Puestos pu ON pu.IdPuesto = e.IdPuesto
                LEFT JOIN Departamentos d ON d.IdDepartamento = pu.IdDepartamento
                WHERE rn.IdNomina = ?
            """, (id_nomina,))
            row = cur.fetchone()
            if not row:
                return None
            
            empleado = {
                "id": row[0], "codigo": row[1], "nombres": row[2], "apellidos": row[3],
                "dpi": row[4], "igss": row[5], "puesto": row[14] or 'N/A', "departamento": row[15] or 'N/A'
            }
            periodo = {
                "id": row[6], "inicio": row[7], "fin": row[8], "tipo": row[9]
            }
            nomina = {
                "salario_base": row[10], "prestaciones": row[11], 
                "deducciones": row[12], "neto": row[13]
            }
            
            # Items de nómina (prestaciones y deducciones)
            cur.execute("""
                SELECT b.Nombre, i.TipoItem, i.Monto
                FROM ItemsNomina i
                JOIN BeneficiosDeducciones b ON b.IdBeneficioDeduccion = i.IdBeneficioDeduccion
                WHERE i.IdNomina = ?
                ORDER BY i.TipoItem DESC, b.Nombre
            """, (id_nomina,))
            items = cur.fetchall()
    
    # Separar prestaciones y deducciones
    prestaciones = [item for item in items if item[1] == 'prestacion']
    deducciones = [item for item in items if item[1] == 'deduccion']
    
    # Generar HTML
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Comprobante de Pago - {empleado['codigo']}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f8f9fa; padding: 20px; }}
        .container {{ max-width: 900px; margin: 0 auto; background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 30px; border-bottom: 3px solid #3b82f6; padding-bottom: 20px; }}
        .header h1 {{ color: #1e40af; font-size: 28px; margin-bottom: 10px; }}
        .header p {{ color: #64748b; font-size: 14px; }}
        .section {{ margin-bottom: 25px; }}
        .section-title {{ background: #f1f5f9; padding: 10px 15px; font-weight: 600; color: #1e293b; font-size: 16px; border-left: 4px solid #3b82f6; margin-bottom: 15px; }}
        .info-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; }}
        .info-item {{ padding: 12px; background: #f8fafc; border-radius: 6px; }}
        .info-label {{ font-size: 12px; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px; }}
        .info-value {{ font-size: 16px; color: #1e293b; font-weight: 600; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
        thead {{ background: #1e40af; color: white; }}
        th {{ padding: 12px; text-align: left; font-weight: 600; font-size: 14px; }}
        td {{ padding: 12px; border-bottom: 1px solid #e2e8f0; }}
        tbody tr:hover {{ background: #f8fafc; }}
        .text-right {{ text-align: right; }}
        .prestacion {{ color: #10b981; font-weight: 600; }}
        .deduccion {{ color: #ef4444; font-weight: 600; }}
        .resumen {{ background: #f0f9ff; border: 2px solid #3b82f6; border-radius: 8px; padding: 20px; margin-top: 30px; }}
        .resumen-row {{ display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #cbd5e1; }}
        .resumen-row:last-child {{ border-bottom: none; border-top: 2px solid #1e40af; padding-top: 15px; margin-top: 10px; }}
        .resumen-label {{ font-size: 16px; color: #475569; }}
        .resumen-value {{ font-size: 16px; font-weight: 600; }}
        .total-label {{ font-size: 20px; font-weight: 700; color: #1e40af; }}
        .total-value {{ font-size: 24px; font-weight: 700; color: #1e40af; }}
        .footer {{ text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid #e2e8f0; color: #94a3b8; font-size: 12px; }}
        @media print {{ body {{ padding: 0; background: white; }} .container {{ box-shadow: none; }} }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>COMPROBANTE DE PAGO</h1>
            <p>Período: {periodo['tipo'].capitalize()} - {periodo['inicio'].strftime('%d/%m/%Y')} al {periodo['fin'].strftime('%d/%m/%Y')}</p>
        </div>
        
        <div class="section">
            <div class="section-title">Información del Empleado</div>
            <div class="info-grid">
                <div class="info-item">
                    <div class="info-label">Código</div>
                    <div class="info-value">{empleado['codigo']}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Nombre Completo</div>
                    <div class="info-value">{empleado['nombres']} {empleado['apellidos']}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">DPI</div>
                    <div class="info-value">{empleado['dpi']}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">IGSS</div>
                    <div class="info-value">{empleado['igss'] or 'N/A'}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Puesto</div>
                    <div class="info-value">{empleado['puesto']}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Departamento</div>
                    <div class="info-value">{empleado['departamento']}</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <div class="section-title">Percepciones</div>
            <table>
                <thead>
                    <tr>
                        <th>Concepto</th>
                        <th class="text-right">Monto</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Salario Base</td>
                        <td class="text-right prestacion">Q {nomina['salario_base']:,.2f}</td>
                    </tr>
"""
    
    for item in prestaciones:
        html += f"""                    <tr>
                        <td>{item[0]}</td>
                        <td class="text-right prestacion">Q {item[2]:,.2f}</td>
                    </tr>
"""
    
    html += """                </tbody>
            </table>
        </div>
        
        <div class="section">
            <div class="section-title">Deducciones</div>
            <table>
                <thead>
                    <tr>
                        <th>Concepto</th>
                        <th class="text-right">Monto</th>
                    </tr>
                </thead>
                <tbody>
"""
    
    if deducciones:
        for item in deducciones:
            html += f"""                    <tr>
                        <td>{item[0]}</td>
                        <td class="text-right deduccion">Q {item[2]:,.2f}</td>
                    </tr>
"""
    else:
        html += """                    <tr>
                        <td colspan="2" style="text-align:center; color:#94a3b8;">Sin deducciones</td>
                    </tr>
"""
    
    html += f"""                </tbody>
            </table>
        </div>
        
        <div class="resumen">
            <div class="resumen-row">
                <span class="resumen-label">Total Prestaciones:</span>
                <span class="resumen-value prestacion">Q {nomina['prestaciones']:,.2f}</span>
            </div>
            <div class="resumen-row">
                <span class="resumen-label">Total Deducciones:</span>
                <span class="resumen-value deduccion">Q {nomina['deducciones']:,.2f}</span>
            </div>
            <div class="resumen-row">
                <span class="total-label">SALARIO NETO:</span>
                <span class="total-value">Q {nomina['neto']:,.2f}</span>
            </div>
        </div>
        
        <div class="footer">
            <p>Generado el {datetime.now().strftime('%d/%m/%Y a las %H:%M')}</p>
            <p>Este documento es un comprobante de pago oficial.</p>
        </div>
    </div>
</body>
</html>"""
    
    return html


@app.route("/comprobantes/<int:id_nomina>/pdf")
def comprobante_pdf(id_nomina: int):
    """Descarga el comprobante de pago en PDF."""
    if not session.get("user_id"):
        flash("Debes iniciar sesión para descargar comprobantes.", "warning")
        return redirect(url_for("login"))
    
    try:
        # Verificar si el usuario tiene permiso de administrador o si es su propio comprobante
        tiene_permiso_admin = 'Comprobantes' in obtener_permisos_usuario()
        
        if not tiene_permiso_admin:
            # Verificar que el comprobante pertenezca al usuario logueado
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT u.IdEmpleado
                        FROM Usuarios u
                        WHERE u.IdUsuario = ?
                    """, (session.get("user_id"),))
                    
                    row = cur.fetchone()
                    if not row or not row[0]:
                        flash("Tu usuario no está asociado a ningún empleado.", "warning")
                        return redirect(url_for("inicio"))
                    
                    id_empleado_usuario = row[0]
                    
                    # Verificar que el comprobante pertenece al empleado
                    cur.execute("""
                        SELECT IdEmpleado FROM RegistrosNomina WHERE IdNomina = ?
                    """, (id_nomina,))
                    
                    row = cur.fetchone()
                    if not row or row[0] != id_empleado_usuario:
                        flash("No tienes permiso para descargar este comprobante.", "danger")
                        return redirect(url_for("mis_comprobantes"))
        
        # Generar PDF del comprobante
        pdf_buffer = generar_comprobante_pdf(id_nomina)
        if not pdf_buffer:
            flash("No se encontró el registro de nómina.", "warning")
            return redirect(url_for("mis_comprobantes") if not tiene_permiso_admin else url_for("comprobantes_listado"))
        
        registrar_auditoria("Comprobante PDF generado", "Comprobantes", f"IdNomina: {id_nomina}")
        
        response = Response(
            pdf_buffer.getvalue(),
            mimetype='application/pdf'
        )
        response.headers['Content-Disposition'] = f'attachment; filename="comprobante_{id_nomina}.pdf"'
        response.headers['Content-Type'] = 'application/pdf'
        return response
    except Exception as e:
        print(f"Error generando PDF: {e}")
        flash(f"Error generando comprobante: {e}", "danger")
        tiene_permiso_admin = 'Comprobantes' in obtener_permisos_usuario()
        return redirect(url_for("mis_comprobantes") if not tiene_permiso_admin else url_for("comprobantes_listado"))


@app.route("/comprobantes", methods=["GET"])
@requiere_permiso_modulo("Comprobantes")
def comprobantes_listado():
    
    # Obtener filtros
    id_empleado = request.args.get("empleado")
    id_periodo = request.args.get("periodo")
    busqueda = request.args.get("busqueda", "").strip()
    
    # Obtener lista de empleados y periodos para filtros
    empleados = []
    periodos = []
    comprobantes = []
    
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Empleados
                cur.execute("SELECT IdEmpleado, Nombres, Apellidos, CodigoEmpleado FROM Empleados ORDER BY Apellidos, Nombres")
                empleados = cur.fetchall()
                
                # Periodos
                cur.execute("""
                    SELECT IdPeriodo, FechaInicio, FechaFin, TipoPeriodo 
                    FROM PeriodosNomina 
                    ORDER BY FechaInicio DESC
                """)
                periodos = cur.fetchall()
                
                # Comprobantes (registros de nómina)
                query = """
                    SELECT rn.IdNomina, e.IdEmpleado, e.Nombres, e.Apellidos, e.CodigoEmpleado,
                           p.IdPeriodo, p.FechaInicio, p.FechaFin, p.TipoPeriodo,
                           rn.SalarioNeto
                    FROM RegistrosNomina rn
                    JOIN Empleados e ON e.IdEmpleado = rn.IdEmpleado
                    JOIN PeriodosNomina p ON p.IdPeriodo = rn.IdPeriodo
                    WHERE 1=1
                """
                params = []
                
                if id_empleado:
                    query += " AND e.IdEmpleado = ?"
                    params.append(id_empleado)
                
                if id_periodo:
                    query += " AND p.IdPeriodo = ?"
                    params.append(id_periodo)
                
                if busqueda:
                    query += """ AND (e.CodigoEmpleado LIKE ? 
                                   OR e.Nombres LIKE ? 
                                   OR e.Apellidos LIKE ?
                                   OR (e.Nombres + ' ' + e.Apellidos) LIKE ?)"""
                    params.extend([f"%{busqueda}%", f"%{busqueda}%", f"%{busqueda}%", f"%{busqueda}%"])
                
                query += " ORDER BY p.FechaInicio DESC, e.Apellidos, e.Nombres"
                
                cur.execute(query, params)
                comprobantes = cur.fetchall()
    except Exception as e:
        flash(f"Error cargando comprobantes: {e}", "danger")
    
    return render_template(
        "comprobantes/list.html",
        empleados=empleados,
        periodos=periodos,
        comprobantes=comprobantes,
        filtro_empleado=id_empleado,
        filtro_periodo=id_periodo,
        busqueda=busqueda
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", 5000)), debug=True)
