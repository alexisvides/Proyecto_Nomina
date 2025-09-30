import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from dotenv import load_dotenv
from db import get_connection
from datetime import datetime
import io
import csv

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
            return render_template("login.html", hide_sidebar=True)

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
                return render_template("login.html", hide_sidebar=True)

            id_usuario, nombre_usuario, correo, clave_hash, activo = row

            if not activo:
                flash("Tu usuario está inactivo. Contacta al administrador.", "danger")
                return render_template("login.html", hide_sidebar=True)

            # Comparación en texto plano (temporal, no recomendado para producción)
            if str(clave_hash) != clave:
                flash("Usuario o contraseña incorrectos.", "danger")
                return render_template("login.html", hide_sidebar=True)

            # Autenticado
            session["user_id"] = int(id_usuario)
            session["username"] = nombre_usuario
            flash("¡Bienvenido!", "success")
            return redirect(url_for("dashboard"))

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
            rows = cur.fetchall()
    return rows


@app.route("/nomina/periodos/<int:id_periodo>/detalle")
def periodo_detalle(id_periodo: int):
    try:
        datos = _consultar_detalle_periodo(id_periodo)
        return render_template("nomina/periodo_detalle.html", filas=datos, id_periodo=id_periodo)
    except Exception as e:
        flash(f"Error consultando detalle del periodo: {e}", "danger")
        return render_template("nomina/periodo_detalle.html", filas=[], id_periodo=id_periodo)


@app.route("/nomina/periodos/<int:id_periodo>/csv")
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


@app.route("/catalogos/beneficios/<int:bid>/editar", methods=["GET", "POST"])
def beneficios_editar(bid: int):
    if request.method == "POST":
        nombre = request.form.get("nombre")
        tipo = request.form.get("tipo")
        tipo_calc = request.form.get("tipo_calculo")
        valor = request.form.get("valor")
        descripcion = request.form.get("descripcion")
        try:
            valor_num = float(valor)
        except Exception:
            flash("Valor inválido.", "warning")
            return redirect(url_for("beneficios_editar", bid=bid))

        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE BeneficiosDeducciones
                        SET Nombre = ?, Tipo = ?, TipoCalculo = ?, Valor = ?, Descripcion = ?
                        WHERE IdBeneficioDeduccion = ?
                        """,
                        (nombre, tipo, tipo_calc, valor_num, descripcion, bid),
                    )
                    conn.commit()
            flash("Registro actualizado.", "success")
            return redirect(url_for("beneficios_listado"))
        except Exception as e:
            flash(f"No se pudo actualizar: {e}", "danger")
            return redirect(url_for("beneficios_editar", bid=bid))

    # GET: cargar el registro
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT IdBeneficioDeduccion, Nombre, Tipo, TipoCalculo, Valor, Activo, Descripcion FROM BeneficiosDeducciones WHERE IdBeneficioDeduccion = ?",
                    (bid,),
                )
                row = cur.fetchone()
        if not row:
            flash("Registro no encontrado.", "warning")
            return redirect(url_for("beneficios_listado"))
        return render_template("beneficios/edit.html", item=row)
    except Exception as e:
        flash(f"Error cargando registro: {e}", "danger")
        return redirect(url_for("beneficios_listado"))


@app.route("/catalogos/beneficios/<int:bid>/eliminar", methods=["POST"])
def beneficios_eliminar(bid: int):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Eliminar primero items que lo referencian
                cur.execute("DELETE FROM ItemsNomina WHERE IdBeneficioDeduccion = ?", (bid,))
                # Luego el catálogo
                cur.execute("DELETE FROM BeneficiosDeducciones WHERE IdBeneficioDeduccion = ?", (bid,))
            conn.commit()
        flash("Beneficio/Deducción eliminado.", "success")
    except Exception as e:
        flash(f"No se pudo eliminar: {e}", "danger")
    return redirect(url_for("beneficios_listado"))


@app.route("/nomina/periodos/<int:id_periodo>/eliminar", methods=["POST"])
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


# =============================
# Empleados (listar y crear)
# =============================
@app.route("/empleados")
def empleados_listado():
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
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
        return render_template("empleados/list.html", empleados=empleados)
    except Exception as e:
        flash(f"Error cargando empleados: {e}", "danger")
        return render_template("empleados/list.html", empleados=[])


@app.route("/empleados/nuevo", methods=["GET", "POST"])
def empleados_nuevo():
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

        if not codigo:
            codigo = f"EMP-{int(datetime.now().timestamp())}"
        if not (nombres and apellidos and fecha_inicio and salario and dpi):
            flash("Nombres, Apellidos, Fecha de inicio, Salario y DPI son obligatorios.", "warning")
            return render_template("empleados/new.html")
        try:
            salario_num = float(salario)
            if salario_num < 0:
                raise ValueError
        except Exception:
            flash("Salario inválido.", "warning")
            return render_template("empleados/new.html")

        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    # Unicidad básicas
                    cur.execute("SELECT COUNT(1) FROM Empleados WHERE CodigoEmpleado = ?", (codigo,))
                    if cur.fetchone()[0]:
                        flash("El código de empleado ya existe.", "warning")
                        return render_template("empleados/new.html")
                    cur.execute("SELECT COUNT(1) FROM Empleados WHERE DocumentoIdentidad = ?", (dpi,))
                    if cur.fetchone()[0]:
                        flash("El DPI ya existe en otro empleado.", "warning")
                        return render_template("empleados/new.html")
                    if igss:
                        cur.execute("SELECT COUNT(1) FROM Empleados WHERE NumeroIGSS = ?", (igss,))
                        if cur.fetchone()[0]:
                            flash("El Número IGSS ya existe en otro empleado.", "warning")
                            return render_template("empleados/new.html")
                    if correo:
                        cur.execute("SELECT COUNT(1) FROM Empleados WHERE Correo = ?", (correo,))
                        if cur.fetchone()[0]:
                            flash("El correo ya existe en otro empleado.", "warning")
                            return render_template("empleados/new.html")

                    fi = fecha_inicio if fecha_inicio else None
                    ff = fecha_fin if fecha_fin else None
                    fn = fecha_nac if fecha_nac else None
                    cur.execute(
                        """
                        INSERT INTO Empleados (
                            CodigoEmpleado, Nombres, Apellidos, DocumentoIdentidad,
                            FechaContratacion, FechaFin, SalarioBase, NumeroIGSS, FechaNacimiento,
                            Correo
                        ) VALUES (?,?,?,?,?,?,?,?,?,?)
                        """,
                        (
                            codigo, nombres, apellidos, dpi,
                            fi, ff, salario_num, igss, fn, correo
                        ),
                    )
                    conn.commit()
            flash("Empleado creado.", "success")
            return redirect(url_for("empleados_listado"))
        except Exception as e:
            flash(f"No se pudo crear el empleado: {e}", "danger")
            return render_template("empleados/new.html")

    return render_template("empleados/new.html")


@app.route("/empleados/<int:id_empleado>/beneficios", methods=["GET", "POST"])
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

    # GET: listar catálogo con overrides del empleado
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
        if not emp:
            flash("Empleado no encontrado.", "warning")
            return redirect(url_for("empleados_listado"))
        return render_template("empleados/beneficios.html", filas=filas, emp=emp)
    except Exception as e:
        flash(f"Error cargando beneficios del empleado: {e}", "danger")
        return redirect(url_for("empleados_listado"))

@app.route("/empleados/<int:id_empleado>/eliminar", methods=["POST"])
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

 # HECHO POR JAMES
@app.route("/reportes", methods=["GET", "POST"])
def reportes():
    if request.method == "POST":
        depto = request.form.get("departamento")
        fecha = request.form.get("fecha")
        # TODO: Lógica para generar reporte
        return f"Reporte generado para {depto} en fecha {fecha}"
    return render_template("reportes.html")


@app.route("/comprobantes", methods=["GET", "POST"])
def comprobantes():
    if request.method == "POST":
        empleado = request.form.get("empleado")
        # TODO: lógica para generar comprobante
        return f"Comprobante generado para {empleado}"
    return render_template("comprobantes.html")


@app.route("/seguridad", methods=["GET", "POST"])
def seguridad():
    if request.method == "POST":
        usuario = request.form.get("usuario")
        rol = request.form.get("rol")
        # TODO: lógica para asignar rol
        return f"Rol {rol} asignado a usuario {usuario}"
    return render_template("seguridad.html")
#Hecho por James hasta aca

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", 5000)), debug=True)
