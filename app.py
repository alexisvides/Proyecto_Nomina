import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from dotenv import load_dotenv
from db import get_connection
from datetime import datetime

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key-change-me")


@app.route("/", methods=["GET"])
def index():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario_o_correo = request.form.get("usuario")
        clave = request.form.get("clave")

        if not usuario_o_correo or not clave:
            flash("Por favor, completa todos los campos.", "warning")
            return render_template("login.html")

        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    # Permitir login por NombreUsuario o Correo
                    cur.execute(
                        """
                        SELECT TOP 1 IdUsuario, NombreUsuario, Correo, ClaveHash, Activo
                        FROM Usuarios
                        WHERE (NombreUsuario = ? OR Correo = ?)
                        """,
                        (usuario_o_correo, usuario_o_correo),
                    )
                    row = cur.fetchone()

            if not row:
                flash("Usuario o contraseña incorrectos.", "danger")
                return render_template("login.html")

            id_usuario, nombre_usuario, correo, clave_hash, activo = row

            if not activo:
                flash("Tu usuario está inactivo. Contacta al administrador.", "danger")
                return render_template("login.html")

            # Comparación en texto plano (temporal, no recomendado para producción)
            if str(clave_hash) != clave:
                flash("Usuario o contraseña incorrectos.", "danger")
                return render_template("login.html")

            # Autenticado
            session["user_id"] = int(id_usuario)
            session["username"] = nombre_usuario
            flash("¡Bienvenido!", "success")
            return redirect(url_for("dashboard"))

        except Exception as e:
            # En producción, registra e de forma segura
            flash(f"Error de conexión o consulta a la base de datos: {e}", "danger")
            return render_template("login.html")

    # GET
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada.", "info")
    return redirect(url_for("login"))


@app.route("/dashboard")
def dashboard():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    return render_template("dashboard.html", usuario=session.get("username"))


@app.route("/nomina/periodos")
def periodos_listado():
    # Ignoramos seguridad por ahora según indicación
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
def periodos_nuevo():
    if request.method == "POST":
        fecha_inicio = request.form.get("fecha_inicio")
        fecha_fin = request.form.get("fecha_fin")
        tipo = request.form.get("tipo_periodo")

        if not fecha_inicio or not fecha_fin or not tipo:
            flash("Completa todos los campos.", "warning")
            return render_template("nomina/periodos_new.html")

        try:
            # Validación simple de rango
            fi = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
            ff = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
            if ff < fi:
                flash("La fecha fin no puede ser menor a la fecha inicio.", "warning")
                return render_template("nomina/periodos_new.html")

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


@app.route("/nomina/periodos/<int:id_periodo>/generar", methods=["POST"])
def generar_nomina(id_periodo: int):
    # Genera registros de nómina para todos los empleados que no tengan registro en el periodo
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Verificar que exista el periodo
                cur.execute(
                    "SELECT COUNT(1) FROM PeriodosNomina WHERE IdPeriodo = ?",
                    (id_periodo,),
                )
                exists = cur.fetchone()[0]
                if not exists:
                    flash("El periodo no existe.", "warning")
                    return redirect(url_for("periodos_listado"))

                # Insertar RegistrosNomina para empleados que aún no lo tengan
                # Usa SalarioBase desde Empleados, y 0 en totales; trigger se encargará de neto al agregar items
                cur.execute(
                    """
                    INSERT INTO RegistrosNomina (IdEmpleado, IdPeriodo, SalarioBase, TotalPrestaciones, TotalDeducciones, SalarioNeto)
                    SELECT e.IdEmpleado, ?, e.SalarioBase, 0, 0, e.SalarioBase
                    FROM Empleados e
                    WHERE NOT EXISTS (
                        SELECT 1 FROM RegistrosNomina rn
                        WHERE rn.IdEmpleado = e.IdEmpleado AND rn.IdPeriodo = ?
                    )
                    """,
                    (id_periodo, id_periodo),
                )
                conn.commit()
        flash("Registros de nómina generados para el periodo.", "success")
    except Exception as e:
        flash(f"Error generando registros de nómina: {e}", "danger")
    return redirect(url_for("periodos_listado"))


# =============================
# Beneficios / Deducciones
# =============================
@app.route("/catalogos/beneficios")
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


@app.route("/catalogos/beneficios/<int:bid>/toggle", methods=["POST"])
def beneficios_toggle(bid: int):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Alterna el estado Activo
                cur.execute(
                    "UPDATE BeneficiosDeducciones SET Activo = CASE WHEN Activo=1 THEN 0 ELSE 1 END WHERE IdBeneficioDeduccion = ?",
                    (bid,),
                )
            conn.commit()
        flash("Estado actualizado.", "success")
    except Exception as e:
        flash(f"Error actualizando estado: {e}", "danger")
    return redirect(url_for("beneficios_listado"))


# =============================
# Control de Asistencia (esquema sugerido)
# =============================
@app.route("/asistencia")
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
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT TOP 100 a.IdAsistencia, a.FechaHora, a.Tipo, a.Observacion,
                           e.IdEmpleado, e.Nombres, e.Apellidos
                    FROM Asistencias a
                    JOIN Empleados e ON e.IdEmpleado = a.IdEmpleado
                    ORDER BY a.FechaHora DESC
                    """
                )
                rows = cur.fetchall()
        return render_template("asistencia/list.html", items=rows, tabla_ok=True)
    except Exception as e:
        flash(f"No se pudo consultar asistencias: {e}", "warning")
        return render_template("asistencia/list.html", items=[], tabla_ok=False)


@app.route("/asistencia/nuevo", methods=["GET", "POST"])
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

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", 5000)), debug=True)
