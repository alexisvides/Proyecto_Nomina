import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from dotenv import load_dotenv
from db import get_connection
from datetime import datetime
import io
import csv
import hashlib
import pandas as pd
from flask import send_file
import zipfile
import logging
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.pagesizes import landscape
import importlib
try:
    _openpyxl = importlib.import_module("openpyxl")
    Workbook = getattr(_openpyxl, "Workbook", None)
except Exception:
    Workbook = None

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key-change-me")

# Logging básico para la aplicación
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("proyecto_nomina")


@app.route("/", methods=["GET"])
def index():
    # Forzar redirección al login incluso si hay sesión activa
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
        # Obtener campos del formulario (coinciden con los names en templates/empleados/new.html)
        codigo = (request.form.get("codigo") or "").strip()
        nombres = (request.form.get("nombres") or "").strip()
        apellidos = (request.form.get("apellidos") or "").strip()
        dpi = (request.form.get("dpi") or "").strip()
        correo = (request.form.get("correo") or "").strip()
        igss = (request.form.get("igss") or "").strip()
        salario = (request.form.get("salario") or "").strip()
        fecha_inicio = (request.form.get("fecha_inicio") or "").strip()
        fecha_fin = (request.form.get("fecha_fin") or "").strip()
        fecha_nac = (request.form.get("fecha_nacimiento") or "").strip()

        # Si no se proporciona código, generarlo automáticamente
        if not codigo:
            codigo = f"EMP-{int(datetime.now().timestamp())}"

        # Validaciones básicas
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

# =============================
# Parte de James
# =============================

# ============================================================
#  MÓDULO DE COMPROBANTES Y RECIBOS DE NÓMINA
# ============================================================
@app.route("/comprobantes", endpoint="comprobantes_listado", methods=["GET", "POST"])
def comprobantes_listado():
    conn = get_connection()
    cursor = conn.cursor()

    # Listado de empleados (mostrar todos y marcar si tienen nómina)
    cursor.execute("""
        SELECT 
            e.IdEmpleado,
            e.Nombres + ' ' + e.Apellidos AS NombreCompleto,
            CASE 
                WHEN EXISTS (SELECT 1 FROM RegistrosNomina rn WHERE rn.IdEmpleado = e.IdEmpleado)
                THEN 1 ELSE 0 
            END AS TieneNomina
        FROM Empleados e
        ORDER BY NombreCompleto;
    """)
    empleados = cursor.fetchall()

    comprobantes = []
    accion = request.form.get("accion")
    empleado_id = request.form.get("empleado")

    # ==============================================
    #  1) GENERACIÓN INDIVIDUAL DE COMPROBANTE
    # ==============================================
    if request.method == "POST" and accion == "individual":
        cursor.execute("""
            SELECT TOP 1 
                e.Nombres + ' ' + e.Apellidos AS NombreCompleto,
                d.Nombre AS Departamento,
                p.Titulo AS Puesto,
                rn.SalarioBase, rn.TotalPrestaciones, rn.TotalDeducciones,
                rn.SalarioNeto, pn.FechaInicio, pn.FechaFin, rn.IdNomina
            FROM RegistrosNomina rn
            INNER JOIN Empleados e ON rn.IdEmpleado = e.IdEmpleado
            INNER JOIN PeriodosNomina pn ON rn.IdPeriodo = pn.IdPeriodo
            LEFT JOIN Departamentos d ON e.IdDepartamento = d.IdDepartamento
            LEFT JOIN Puestos p ON e.IdPuesto = p.IdPuesto
            WHERE e.IdEmpleado = ?
            ORDER BY rn.FechaGeneracion DESC;
        """, (empleado_id,))
        row = cursor.fetchone()

        if not row:
            flash(" No se encontró una nómina para este empleado.", "warning")
            return render_template("Comprobantes/comprobantes.html", empleados=empleados)

        (nombre, depto, puesto, base, prest, deduc, neto, f_ini, f_fin, id_nomina) = row

        # Detalle de items (deducciones y prestaciones)
        cursor.execute("""
            SELECT bd.Nombre, i.TipoItem, i.Monto
            FROM ItemsNomina i
            LEFT JOIN BeneficiosDeducciones bd ON bd.IdBeneficioDeduccion = i.IdBeneficioDeduccion
            WHERE i.IdNomina = ?;
        """, (id_nomina,))
        items = cursor.fetchall()

        # Firma digital (hash único)
        firma = hashlib.sha256(f"{id_nomina}{nombre}{f_fin}".encode()).hexdigest()[:16]

        # === Generar PDF ===
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(200, 760, "Comprobante de Pago - Nómina")
        c.setFont("Helvetica", 10)
        c.drawString(50, 740, f"Empleado: {nombre}")
        c.drawString(50, 725, f"Departamento: {depto or 'N/A'}")
        c.drawString(50, 710, f"Puesto: {puesto or 'N/A'}")
        c.drawString(50, 695, f"Período: {f_ini.strftime('%Y-%m-%d')} a {f_fin.strftime('%Y-%m-%d')}")
        c.line(50, 685, 550, 685)

        c.setFont("Helvetica-Bold", 10)
        c.drawString(50, 670, "DETALLES DE NÓMINA")
        c.setFont("Helvetica", 10)
        c.drawString(50, 655, f"Salario Base: Q {base:,.2f}")
        c.drawString(50, 640, f"Prestaciones: Q {prest:,.2f}")
        c.drawString(50, 625, f"Deducciones: Q {deduc:,.2f}")
        c.line(50, 615, 550, 615)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(50, 600, f"Salario Neto: Q {neto:,.2f}")

        y = 580
        if items:
            c.setFont("Helvetica-Bold", 10)
            c.drawString(50, y, "Concepto")
            c.drawString(250, y, "Tipo")
            c.drawString(400, y, "Monto")
            y -= 15
            c.setFont("Helvetica", 9)
            for item in items:
                c.drawString(50, y, item[0] or "—")
                c.drawString(250, y, item[1])
                c.drawString(400, y, f"Q {item[2]:,.2f}")
                y -= 15
                if y < 60:
                    c.showPage()
                    y = 760

        c.setFont("Helvetica", 9)
        c.line(50, y - 5, 550, y - 5)
        c.drawString(50, y - 20, f"Firma Digital: {firma}")
        c.save()
        buffer.seek(0)
        pdf_bytes = buffer.getvalue()

        # Guardar comprobante en la base
        cursor.execute("""
            INSERT INTO ComprobantesEmitidos (IdNomina, FirmaDigital, ArchivoPDF)
            VALUES (?, ?, ?)
        """, (id_nomina, firma, pdf_bytes))
        conn.commit()

        flash(" Comprobante generado correctamente.", "success")

        return send_file(
            io.BytesIO(pdf_bytes),
            as_attachment=True,
            download_name=f"Comprobante_{nombre}_{f_fin.strftime('%Y%m%d')}.pdf",
            mimetype="application/pdf"
        )

    # ==============================================
    #  2) GENERACIÓN MASIVA
    # ==============================================
    elif request.method == "POST" and accion == "masiva":
        cursor.execute("""
            SELECT rn.IdNomina, e.Nombres + ' ' + e.Apellidos AS NombreCompleto,
                   rn.SalarioNeto, pn.FechaFin
            FROM RegistrosNomina rn
            INNER JOIN Empleados e ON rn.IdEmpleado = e.IdEmpleado
            INNER JOIN PeriodosNomina pn ON rn.IdPeriodo = pn.IdPeriodo
            ORDER BY e.Nombres;
        """)
        filas = cursor.fetchall()

        if not filas:
            flash(" No hay nóminas generadas para exportar.", "warning")
            return render_template("Comprobantes/comprobantes.html", empleados=empleados)

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zipf:
            for (id_nomina, nombre, neto, fecha_fin) in filas:
                firma = hashlib.sha256(f"{id_nomina}{nombre}{fecha_fin}".encode()).hexdigest()[:16]

                # Crear PDF individual
                pdf_buffer = io.BytesIO()
                c = canvas.Canvas(pdf_buffer, pagesize=letter)
                c.setFont("Helvetica-Bold", 14)
                c.drawString(200, 760, "Comprobante de Pago - Nómina")
                c.setFont("Helvetica", 10)
                c.drawString(50, 740, f"Empleado: {nombre}")
                c.drawString(50, 725, f"Salario Neto: Q {neto:,.2f}")
                c.drawString(50, 710, f"Firma Digital: {firma}")
                c.save()
                pdf_buffer.seek(0)

                zipf.writestr(f"Comprobante_{nombre}_{fecha_fin.strftime('%Y%m%d')}.pdf", pdf_buffer.read())

                cursor.execute("""
                    INSERT INTO ComprobantesEmitidos (IdNomina, FirmaDigital)
                    VALUES (?, ?)
                """, (id_nomina, firma))
        conn.commit()
        zip_buffer.seek(0)

        flash(f" {len(filas)} comprobantes generados y comprimidos exitosamente.", "success")
        return send_file(zip_buffer, as_attachment=True, download_name="Comprobantes_Masivos.zip")

    # ==============================================
    #  3) HISTORIAL DE COMPROBANTES
    # ==============================================
    elif request.method == "POST" and accion == "historial":
        cursor.execute("""
            SELECT c.IdComprobante, e.Nombres + ' ' + e.Apellidos AS Empleado, 
                   c.FechaEmision, c.FirmaDigital
            FROM ComprobantesEmitidos c
            INNER JOIN RegistrosNomina rn ON c.IdNomina = rn.IdNomina
            INNER JOIN Empleados e ON rn.IdEmpleado = e.IdEmpleado
            ORDER BY c.FechaEmision DESC;
        """)
        comprobantes = cursor.fetchall()

    # ==============================================
    #  4) DESCARGA DE COMPROBANTE EXISTENTE
    # ==============================================
    if request.args.get("descargar"):
        comprobante_id = request.args.get("descargar")
        cursor.execute("SELECT ArchivoPDF, FirmaDigital FROM ComprobantesEmitidos WHERE IdComprobante = ?", (comprobante_id,))
        row = cursor.fetchone()
        if not row:
            flash(" Comprobante no encontrado.", "warning")
        else:
            pdf_bytes, firma = row
            return send_file(
                io.BytesIO(pdf_bytes),
                as_attachment=True,
                download_name=f"Comprobante_{firma}.pdf",
                mimetype="application/pdf"
            )

    cursor.close()
    conn.close()
    return render_template("Comprobantes/comprobantes.html", empleados=empleados, comprobantes=comprobantes)


# =========================
#   SEGURIDAD
# =========================
@app.route("/seguridad", endpoint="seguridad_listado", methods=["GET", "POST"])
def seguridad_listado():
    conn = get_connection()
    cursor = conn.cursor()

    # ============================================================
    #  Cargar usuarios y roles disponibles
    # ============================================================
    cursor.execute("""
        SELECT IdUsuario, NombreUsuario, Activo 
        FROM Usuarios 
        ORDER BY NombreUsuario ASC;
    """)
    usuarios = cursor.fetchall()

    cursor.execute("""
        SELECT IdRol, Nombre, Descripcion 
        FROM Roles 
        ORDER BY Nombre ASC;
    """)
    roles = cursor.fetchall()

    # ============================================================
    #  Mostrar asignaciones actuales (usuarios con roles)
    # ============================================================
    cursor.execute("""
        SELECT 
            ur.IdUsuario, u.NombreUsuario, 
            ur.IdRol, r.Nombre AS Rol, 
            ISNULL(r.Descripcion, '') AS Descripcion
        FROM UsuarioRol ur
        INNER JOIN Usuarios u ON ur.IdUsuario = u.IdUsuario
        INNER JOIN Roles r ON ur.IdRol = r.IdRol
        ORDER BY u.NombreUsuario, r.Nombre;
    """)
    asignaciones = cursor.fetchall()

    # ============================================================
    #  Procesar acciones del formulario
    # ============================================================
    if request.method == "POST":
        usuario_id = request.form.get("usuario")
        rol_id = request.form.get("rol")
        accion = request.form.get("accion")

        if not usuario_id or not rol_id:
            flash("Debe seleccionar un usuario y un rol.", "warning")
            return redirect(url_for("seguridad_listado"))

        try:
            # Forzar a enteros y validar existencia en tablas PK antes de tocar UsuarioRol
            try:
                usuario_id_int = int(usuario_id)
            except Exception:
                logger.warning("Valor de usuario inválido recibido: %s", usuario_id)
                flash("Usuario inválido.", "warning")
                return redirect(url_for("seguridad_listado"))

            try:
                rol_id_int = int(rol_id)
            except Exception:
                logger.warning("Valor de rol inválido recibido: %s", rol_id)
                flash("Rol inválido.", "warning")
                return redirect(url_for("seguridad_listado"))

            # Comprobar existencia en Usuarios
            cursor.execute("SELECT COUNT(1) FROM Usuarios WHERE IdUsuario = ?", (usuario_id_int,))
            if cursor.fetchone()[0] == 0:
                logger.info("Intento de asignar rol a usuario inexistente: %s", usuario_id_int)
                flash("El usuario seleccionado no existe.", "warning")
                return redirect(url_for("seguridad_listado"))

            # Comprobar existencia en Roles
            cursor.execute("SELECT COUNT(1) FROM Roles WHERE IdRol = ?", (rol_id_int,))
            if cursor.fetchone()[0] == 0:
                logger.info("Intento de asignar rol inexistente: %s", rol_id_int)
                flash("El rol seleccionado no existe.", "warning")
                return redirect(url_for("seguridad_listado"))

            if accion == "asignar":
                #  Verificar si la asignación ya existe
                cursor.execute("SELECT 1 FROM UsuarioRol WHERE IdUsuario = ? AND IdRol = ?", (usuario_id_int, rol_id_int))
                existe = cursor.fetchone()

                if existe:
                    logger.info("Asignación ya existente: usuario=%s rol=%s", usuario_id_int, rol_id_int)
                    flash("Este usuario ya tiene asignado ese rol.", "info")
                else:
                    cursor.execute("INSERT INTO UsuarioRol (IdUsuario, IdRol) VALUES (?, ?)", (usuario_id_int, rol_id_int))
                    conn.commit()

                    # Registrar en auditoría: usa quien realizó la acción si está en sesión
                    actor = session.get("user_id") or usuario_id_int
                    cursor.execute("INSERT INTO Auditoria (IdUsuario, Accion) VALUES (?, ?)", (actor, f"Asignó rol ID={rol_id_int} al usuario ID={usuario_id_int}"))
                    conn.commit()

                    logger.info("Rol asignado: usuario=%s rol=%s por actor=%s", usuario_id_int, rol_id_int, actor)
                    flash("Rol asignado correctamente.", "success")

            elif accion == "eliminar":
                cursor.execute("SELECT 1 FROM UsuarioRol WHERE IdUsuario = ? AND IdRol = ?", (usuario_id_int, rol_id_int))
                existe = cursor.fetchone()

                if not existe:
                    logger.info("Intento de eliminar asignación inexistente: usuario=%s rol=%s", usuario_id_int, rol_id_int)
                    flash("El usuario no tiene asignado ese rol.", "warning")
                else:
                    cursor.execute("DELETE FROM UsuarioRol WHERE IdUsuario = ? AND IdRol = ?", (usuario_id_int, rol_id_int))
                    conn.commit()

                    actor = session.get("user_id") or usuario_id_int
                    cursor.execute("INSERT INTO Auditoria (IdUsuario, Accion) VALUES (?, ?)", (actor, f"Eliminó rol ID={rol_id_int} del usuario ID={usuario_id_int}"))
                    conn.commit()

                    logger.info("Rol eliminado: usuario=%s rol=%s por actor=%s", usuario_id_int, rol_id_int, actor)
                    flash("Rol eliminado correctamente.", "danger")

        except Exception as e:
            conn.rollback()
            flash(f"Error en la operación: {e}", "danger")

        finally:
            cursor.close()
            conn.close()
            return redirect(url_for("seguridad_listado"))

    cursor.close()
    conn.close()
    return render_template("Seguridad/seguridad.html", usuarios=usuarios, roles=roles, asignaciones=asignaciones)


# ==============================
#   Módulo de Auditoría
# ==============================
@app.route("/auditoria", endpoint="auditoria_listado")
def auditoria_listado():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT TOP 50 a.IdAuditoria, u.NombreUsuario, a.Accion, a.Fecha
        FROM Auditoria a
        LEFT JOIN Usuarios u ON a.IdUsuario = u.IdUsuario
        ORDER BY a.Fecha DESC;
    """)
    registros = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("Seguridad/auditoria.html", registros=registros)

# ============================================================
# 🔹 MÓDULO DE REPORTES Y EXPORTACIONES
# ============================================================
@app.route("/reportes", endpoint="reportes_listado", methods=["GET", "POST"])
def reportes_listado():
    conn = get_connection()
    cursor = conn.cursor()

    # Obtener filtros dinámicos
    cursor.execute("SELECT IdDepartamento, Nombre FROM Departamentos ORDER BY Nombre;")
    departamentos = cursor.fetchall()
    cursor.execute("SELECT IdPuesto, Titulo FROM Puestos ORDER BY Titulo;")
    cargos = cursor.fetchall()

    data = []
    formato = request.form.get("formato")

    if request.method == "POST":
        departamento = request.form.get("departamento") or None
        cargo = request.form.get("cargo") or None
        fecha_inicio = request.form.get("fecha_inicio") or "1900-01-01"
        fecha_fin = request.form.get("fecha_fin") or "2100-12-31"

        # Consulta principal — construir condiciones dinámicamente para usar marcadores ? compatibles con pyodbc
        base_sql = """
            SELECT 
                e.Nombres + ' ' + e.Apellidos AS Empleado,
                d.Nombre AS Departamento,
                p.Titulo AS Puesto,
                e.SalarioBase,
                rn.TotalPrestaciones,
                rn.TotalDeducciones,
                rn.SalarioNeto,
                pn.FechaInicio,
                pn.FechaFin
            FROM RegistrosNomina rn
            INNER JOIN Empleados e ON rn.IdEmpleado = e.IdEmpleado
            INNER JOIN PeriodosNomina pn ON rn.IdPeriodo = pn.IdPeriodo
            LEFT JOIN Departamentos d ON e.IdDepartamento = d.IdDepartamento
            LEFT JOIN Puestos p ON e.IdPuesto = p.IdPuesto
        """

        conditions = []
        params = []

        # El formulario puede enviar nombres o IDs. Normalizar a IDs enteros.
        def resolve_id(table, id_col, name_col, value):
            # si es vacío/None -> None
            if not value:
                return None
            # si parece un entero, devolver como int
            try:
                return int(value)
            except Exception:
                pass
            # intentar buscar por nombre en la tabla correspondiente
            try:
                lookup_sql = f"SELECT {id_col} FROM {table} WHERE {name_col} = ?"
                cursor.execute(lookup_sql, (value,))
                row = cursor.fetchone()
                if row:
                    return row[0]
            except Exception:
                # si algo falla, ignoramos y devolvemos None
                pass
            return None

        departamento_id = resolve_id('Departamentos', 'IdDepartamento', 'Nombre', departamento)
        cargo_id = resolve_id('Puestos', 'IdPuesto', 'Titulo', cargo)

        if departamento_id is not None:
            conditions.append("e.IdDepartamento = ?")
            params.append(departamento_id)

        if cargo_id is not None:
            conditions.append("e.IdPuesto = ?")
            params.append(cargo_id)

        # Siempre filtrar por fechas (se usan valores por defecto si no se proporcionan)
        conditions.append("pn.FechaInicio >= ?")
        params.append(fecha_inicio)
        conditions.append("pn.FechaFin <= ?")
        params.append(fecha_fin)

        if conditions:
            base_sql += "\n WHERE " + " AND ".join(conditions)

        base_sql += "\n ORDER BY e.Nombres;"

        cursor.execute(base_sql, params)
        data = cursor.fetchall()

        if not data:
            flash(" No se encontraron resultados para los filtros seleccionados.", "warning")
            return render_template("Reportes/reportes.html", departamentos=departamentos, cargos=cargos, data=[])

        # ======================
        # Exportar a diferentes formatos
        # ======================
        if formato == "pdf":
            buffer = io.BytesIO()
            c = canvas.Canvas(buffer, pagesize=landscape(A4))
            c.setFont("Helvetica-Bold", 14)
            c.drawString(280, 560, "REPORTE DE NÓMINA")
            c.setFont("Helvetica", 10)
            # datetime imported as `datetime` from datetime, use datetime.now()
            c.drawString(50, 530, f"Fecha de generación: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            c.line(50, 520, 800, 520)
            y = 500
            for row in data:
                c.drawString(50, y, f"{row[0]} | {row[1]} | {row[2]} | Q{row[3]:,.2f} | Q{row[6]:,.2f}")
                y -= 15
                if y < 50:
                    c.showPage()
                    y = 550
            c.save()
            buffer.seek(0)
            return send_file(buffer, as_attachment=True, download_name="Reporte_Nomina.pdf", mimetype="application/pdf")

        elif formato == "excel":
            # Prefer openpyxl Workbook if available, otherwise use pandas to produce an Excel file.
            try:
                if Workbook:
                    wb = Workbook()
                    ws = wb.active
                    ws.title = "Reporte Nómina"
                    ws.append(["Empleado", "Departamento", "Puesto", "Salario Base", "Prestaciones", "Deducciones", "Salario Neto", "Inicio", "Fin"])
                    for row in data:
                        ws.append(row)
                    output = io.BytesIO()
                    wb.save(output)
                    output.seek(0)
                    return send_file(output, as_attachment=True, download_name="Reporte_Nomina.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                else:
                    # Build a DataFrame and use pandas to_excel (requires an engine like openpyxl or xlsxwriter).
                    cols = ["Empleado", "Departamento", "Puesto", "Salario Base", "Prestaciones", "Deducciones", "Salario Neto", "Inicio", "Fin"]
                    df = pd.DataFrame(list(data), columns=cols)
                    output = io.BytesIO()
                    try:
                        with pd.ExcelWriter(output, engine="openpyxl") as writer:
                            df.to_excel(writer, index=False, sheet_name="Reporte")
                        output.seek(0)
                        return send_file(output, as_attachment=True, download_name="Reporte_Nomina.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                    except Exception:
                        # Fall back to CSV if Excel writing is not available
                        output = io.StringIO()
                        df.to_csv(output, index=False)
                        output.seek(0)
                        return send_file(io.BytesIO(output.getvalue().encode()), as_attachment=True, download_name="Reporte_Nomina.csv", mimetype="text/csv")
            except Exception as e:
                flash(f"No se pudo generar Excel: {e}", "danger")
                # fall through to render page

        elif formato == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["Empleado", "Departamento", "Puesto", "Salario Base", "Prestaciones", "Deducciones", "Salario Neto", "Inicio", "Fin"])
            writer.writerows(data)
            output.seek(0)
            return send_file(io.BytesIO(output.getvalue().encode()), as_attachment=True, download_name="Reporte_Nomina.csv", mimetype="text/csv")

    cursor.close()
    conn.close()
    return render_template("Reportes/reportes.html", departamentos=departamentos, cargos=cargos, data=data)

@app.route("/departamentos")
def departamentos_listado():
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT IdDepartamento, nombre, descripcion 
                    FROM Departamentos
                    """
                )
                departamentos = cur.fetchall()
        return render_template("departamentos/list.html", departamentos=departamentos)
    except Exception as e:
        flash(f"Error cargando departamentos: {e}", "danger")
        return render_template("departamentos/list.html", departamentos=[])
    
@app.route("/departamentos/nuevo", methods=["GET", "POST"])
def departamento_nuevo():
    if request.method == "POST":
        #codigo = (request.form.get("codigo") or "").strip()
        nombre = (request.form.get("nombre") or "").strip()
        descripcion = (request.form.get("descripcion") or "").strip()

     
        if not (nombre and descripcion):
            flash("Nombre del departamento y descripcoin son obligatorios.", "warning")
            return render_template("departamentos/new.html")
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    # Unicidad básicas

                    cur.execute("SELECT COUNT(1) FROM Departamentos WHERE nombre = ?", (nombre,))
                    if cur.fetchone()[0]:
                        flash("El nombre del departamento ya existe.", "warning")
                        return render_template("empleados/new.html")
                    
                    cur.execute(
                        """
                        INSERT INTO Departamentos (
                        nombre, descripcion
                        ) VALUES (?,?)
                        """,
                        (
                        nombre, descripcion
                        ),
                    )
                    conn.commit()
            flash("Departamento creado.", "success")
            return redirect(url_for("departamentos_listado"))
        except Exception as e:
            flash(f"No se pudo crear el departamento leado: {e}", "danger")
            return render_template("departamentos/new.html")

    return render_template("departamentos/new.html")

@app.route("/departamentos/<int:IdDepartamento>/eliminar", methods=["POST"])
def departamentos_eliminar(IdDepartamento: int):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM Departamentos WHERE IdDepartamento = ?", (IdDepartamento,))
            conn.commit()
        flash("Empleado eliminado.", "success")
    except Exception as e:
        flash(f"No se pudo eliminar el empleado: {e}", "danger")
    return redirect(url_for("empleados_listado"))

@app.route("/departamentos/buscar", methods=["GET"])
def departamentos_lista():
    # filtro por querystring ?q=...
    q = (request.args.get("q") or "").strip()

    sql = """
        SELECT IdDepartamento, Nombre, Descripcion
        FROM Departamentos
    """
    params = []
    if q:
        sql += """
            WHERE (Nombre LIKE ? OR Descripcion LIKE ? OR CAST(IdDepartamento AS VARCHAR(20)) LIKE ?)
        """
        like = f"%{q}%"
        params = [like, like, like]

    sql += " ORDER BY Nombre"

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                departamentos = cur.fetchall()
        # pasa 'q' para mantener el valor en el input
        return render_template("departamentos/list.html", departamentos=departamentos, q=q)
    except Exception as e:
        flash(f"Error cargando departamentos: {e}", "danger")
        return render_template("departamentos/list.html", departamentos=[], q=q)

@app.route("/departamentos/<int:IdDepartamento>/editar", methods=["GET", "POST"])
def departamento_editar(IdDepartamento: int):
    if request.method == "POST":
        nombre = (request.form.get("nombre") or "").strip()
        descripcion = (request.form.get("descripcion") or "").strip()

        if not (nombre and descripcion):
            flash("Nombre y descripción son obligatorios.", "warning")
            # Volvemos a cargar el registro para re-renderizar el form con error
            try:
                with get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            "SELECT IdDepartamento, Nombre, Descripcion FROM Departamentos WHERE IdDepartamento = ?",
                            (IdDepartamento,),
                        )
                        row = cur.fetchone()
                if not row:
                    flash("Departamento no encontrado.", "warning")
                    return redirect(url_for("departamentos_listado"))
                return render_template("departamentos/edit.html", item=row)
            except Exception as e:
                flash(f"Error cargando departamento: {e}", "danger")
                return redirect(url_for("departamentos_listado"))

        # Validar unicidad (mismo nombre en otro ID)
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT COUNT(1) FROM Departamentos WHERE Nombre = ? AND IdDepartamento <> ?",
                        (nombre, IdDepartamento),
                    )
                    if cur.fetchone()[0]:
                        flash("Ya existe otro departamento con ese nombre.", "warning")
                        # Recargar form con valores ingresados
                        item = (IdDepartamento, nombre, descripcion)
                        return render_template("departamentos/edit.html", item=item)

                    # Actualizar
                    cur.execute(
                        """
                        UPDATE Departamentos
                           SET Nombre = ?, Descripcion = ?
                         WHERE IdDepartamento = ?
                        """,
                        (nombre, descripcion, IdDepartamento),
                    )
                    conn.commit()
            flash("Departamento actualizado.", "success")
            return redirect(url_for("departamentos_listado"))
        except Exception as e:
            flash(f"No se pudo actualizar el departamento: {e}", "danger")
            item = (IdDepartamento, nombre, descripcion)
            return render_template("departamentos/edit.html", item=item)

    # GET: cargar registro
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT IdDepartamento, Nombre, Descripcion FROM Departamentos WHERE IdDepartamento = ?",
                    (IdDepartamento,),
                )
                row = cur.fetchone()
        if not row:
            flash("Departamento no encontrado.", "warning")
            return redirect(url_for("departamentos_listado"))
        return render_template("departamentos/edit.html", item=row)
    except Exception as e:
        flash(f"Error cargando departamento: {e}", "danger")
        return redirect(url_for("departamentos_listado"))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", 5000)), debug=True)
