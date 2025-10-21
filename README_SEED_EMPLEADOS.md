# 📊 Generador de 100 Empleados con Datos Completos

## 🎯 Descripción

Este script genera una base de datos completa de prueba con:
- ✅ **100 empleados** con nombres realistas
- ✅ **90 días de asistencia** (últimos 3 meses)
- ✅ **6 períodos de nómina** quincenales
- ✅ **~600 registros de nómina** completos
- ✅ **Prestaciones y deducciones** asignadas
- ✅ **Datos realistas** listos para reportes

---

## ⚠️ ADVERTENCIA

**Este script ELIMINA todos los datos existentes de:**
- Empleados
- Asistencias
- Registros de Nómina
- Períodos
- Beneficios/Deducciones asignados

**NO elimina:**
- Usuarios
- Roles
- Módulos
- Permisos

---

## 🚀 Cómo Ejecutar

### **Paso 1: Hacer Backup (IMPORTANTE)**
```sql
BACKUP DATABASE [proyecto] 
TO DISK = 'C:\Backup\proyecto_antes_seed.bak'
WITH FORMAT;
```

### **Paso 2: Ejecutar el Script**
1. Abre **SQL Server Management Studio (SSMS)**
2. Abre el archivo: `SEED_100_EMPLEADOS.sql`
3. Asegúrate de estar conectado a tu servidor
4. Presiona `F5` o click en **Execute**
5. Espera de 2-5 minutos (genera muchos datos)

### **Paso 3: Verificar**
```sql
-- Ver resumen
SELECT 'Empleados', COUNT(*) FROM Empleados
UNION ALL SELECT 'Asistencias', COUNT(*) FROM Asistencias
UNION ALL SELECT 'Nóminas', COUNT(*) FROM RegistrosNomina;
```

---

## 📊 Datos Generados

### **Empleados (100)**
- Códigos: EMP001 a EMP100
- Nombres y apellidos aleatorios realistas
- DPI único generado
- Correos: nombre.apellido@empresa.com
- Teléfonos aleatorios (5XXX-XXXX)
- Salarios: Q3,000 - Q25,000
- Fechas de contratación: 2020-2024
- Edades: 22-44 años

### **Departamentos (8)**
1. Administración
2. Recursos Humanos
3. Contabilidad
4. Sistemas
5. Ventas
6. Producción
7. Logística
8. Marketing

### **Puestos (18)**
Desde Gerente General hasta Operarios, distribuidos en todos los departamentos.

### **Beneficios y Deducciones (9)**

**Prestaciones:**
- Salario Base
- Bonificación Decreto 37-2001 (Q250)
- Horas Extra
- Comisiones (solo ventas)
- Bono Productividad

**Deducciones:**
- IGSS Empleado (4.83%)
- ISR (calculado según salario)
- Anticipos
- Préstamos

### **Asistencias (~6,000 registros)**
- **Período:** Últimos 90 días
- **Días:** Solo lunes a viernes
- **Horario:** 8:00 AM entrada, 5:00 PM salida
- **Variación:** ±30 minutos aleatorios
- **Ausentismo:** ~5% no registran salida

### **Períodos de Nómina (6)**
- **Tipo:** Quincenal
- **Cobertura:** Últimos 3 meses
- Fechas calculadas automáticamente

### **Registros de Nómina (~600)**
- Cada empleado x cada período = 600 registros
- Cálculos automáticos:
  - Salario quincenal (base/2)
  - Total prestaciones
  - Total deducciones
  - Salario neto

### **Items de Nómina (detallado)**
- Cada prestación/deducción como item individual
- Listo para generar comprobantes de pago

---

## 📈 Distribución de Datos

### **Salarios**
- Q3,000 - Q7,000: ~40% (Operativos)
- Q7,000 - Q15,000: ~45% (Administrativos)
- Q15,000 - Q25,000: ~15% (Gerenciales)

### **Comisiones**
- ~25% de empleados (área de ventas)
- Monto: Q500 - Q2,500

### **ISR**
- Solo empleados con salario > Q5,000
- ~60% de la plantilla

### **Asistencia**
- 95% de días laborales con entrada/salida
- 5% solo con entrada (ausentismo simulado)

---

## 🔍 Consultas Útiles

### **Ver Empleados por Departamento**
```sql
SELECT 
    d.Nombre as Departamento,
    COUNT(e.IdEmpleado) as CantidadEmpleados,
    AVG(e.SalarioBase) as SalarioPromedio
FROM Empleados e
JOIN Departamentos d ON d.IdDepartamento = e.IdDepartamento
GROUP BY d.Nombre
ORDER BY CantidadEmpleados DESC;
```

### **Ver Nómina del Último Período**
```sql
SELECT TOP 10
    e.CodigoEmpleado,
    e.Nombres + ' ' + e.Apellidos as NombreCompleto,
    rn.SalarioBase,
    rn.TotalPrestaciones,
    rn.TotalDeducciones,
    rn.SalarioNeto
FROM RegistrosNomina rn
JOIN Empleados e ON e.IdEmpleado = rn.IdEmpleado
JOIN PeriodosNomina p ON p.IdPeriodo = rn.IdPeriodo
WHERE p.IdPeriodo = (SELECT MAX(IdPeriodo) FROM PeriodosNomina)
ORDER BY rn.SalarioNeto DESC;
```

### **Ver Asistencia de un Empleado**
```sql
SELECT 
    e.Nombres + ' ' + e.Apellidos as Empleado,
    CAST(a.FechaHora as DATE) as Fecha,
    MIN(CASE WHEN a.Tipo = 'entrada' THEN CAST(a.FechaHora as TIME) END) as Entrada,
    MAX(CASE WHEN a.Tipo = 'salida' THEN CAST(a.FechaHora as TIME) END) as Salida
FROM Asistencias a
JOIN Empleados e ON e.IdEmpleado = a.IdEmpleado
WHERE e.CodigoEmpleado = 'EMP001'
  AND a.FechaHora >= DATEADD(DAY, -30, GETDATE())
GROUP BY e.Nombres, e.Apellidos, CAST(a.FechaHora as DATE)
ORDER BY Fecha DESC;
```

### **Reporte de Nómina Total por Período**
```sql
SELECT 
    p.FechaInicio,
    p.FechaFin,
    COUNT(rn.IdNomina) as EmpleadosPagados,
    SUM(rn.SalarioBase) as TotalSalarios,
    SUM(rn.TotalPrestaciones) as TotalPrestaciones,
    SUM(rn.TotalDeducciones) as TotalDeducciones,
    SUM(rn.SalarioNeto) as TotalAPagar
FROM RegistrosNomina rn
JOIN PeriodosNomina p ON p.IdPeriodo = rn.IdPeriodo
GROUP BY p.IdPeriodo, p.FechaInicio, p.FechaFin
ORDER BY p.FechaInicio DESC;
```

---

## 🎨 Características de los Datos

### **Realismo**
- Nombres y apellidos hispanos comunes
- Distribución de salarios realista
- Asistencias con variación natural
- Empleados contratados en diferentes fechas

### **Variedad**
- Diferentes departamentos y puestos
- Mezcla de salarios bajos, medios y altos
- Algunos con comisiones, otros no
- ISR solo para salarios correspondientes

### **Completitud**
- Todos los empleados tienen:
  - Datos personales completos
  - Salario base asignado
  - Prestaciones obligatorias (Bono, IGSS)
  - Asistencias de 3 meses
  - Nóminas de 3 meses

---

## 🔧 Personalización

### **Cambiar Cantidad de Empleados**
Modifica la línea:
```sql
WHILE @i <= 100  -- Cambiar 100 por la cantidad deseada
```

### **Cambiar Rango de Salarios**
Modifica la línea:
```sql
SET @SalarioBase = ROUND(3000 + (RAND() * 22000), 2);
-- Mínimo: 3000, Máximo: 25000
```

### **Cambiar Período de Asistencia**
Modifica la línea:
```sql
DECLARE @FechaAsistencia DATE = DATEADD(DAY, -90, GETDATE());
-- Cambiar -90 por los días deseados
```

---

## 📊 Casos de Uso

### **1. Pruebas de Reportes**
Con 100 empleados y 3 meses de datos, puedes probar:
- Reportes de nómina
- Reportes de asistencia
- Dashboards con gráficas
- Exportaciones masivas

### **2. Pruebas de Rendimiento**
- ~6,000 registros de asistencia
- ~600 registros de nómina
- Ideal para pruebas de consultas complejas

### **3. Demos y Presentaciones**
- Datos realistas para mostrar el sistema
- Nombres en español
- Montos y fechas coherentes

### **4. Training de Usuarios**
- Cada usuario puede practicar con datos variados
- Sin riesgo de afectar datos reales

---

## ⚡ Tiempo de Ejecución

- **Limpieza de datos:** ~5 segundos
- **Generación de empleados:** ~10 segundos
- **Asignación de beneficios:** ~5 segundos
- **Generación de asistencias:** ~60-90 segundos
- **Generación de nóminas:** ~10 segundos
- **Total:** ~2-3 minutos

---

## 🔄 Ejecutar Nuevamente

Si quieres regenerar los datos:
1. El script limpia automáticamente los datos existentes
2. Puedes ejecutarlo cuantas veces quieras
3. Cada ejecución generará empleados con nombres diferentes

---

## ⚠️ Notas Importantes

1. **NO afecta usuarios:** Los usuarios del sistema se mantienen intactos
2. **NO afecta permisos:** Roles y permisos permanecen sin cambios
3. **NO afecta módulos:** Configuración del sistema intacta
4. **Solo datos operativos:** Empleados, nómina y asistencia

---

## 🆘 Problemas Comunes

### **Error: "Cannot truncate table" o FK conflicts**
- **Causa:** Datos relacionados en otras tablas
- **Solución:** El script elimina en el orden correcto de FKs

### **Script tarda mucho**
- **Normal:** Genera ~6,000 registros de asistencia
- **Espera:** 2-5 minutos dependiendo del servidor

### **Algunos empleados sin asistencias**
- **Causa:** Contratados después del período de asistencia
- **Normal:** Solo se generan asistencias para últimos 90 días

---

## 📞 Verificación Post-Ejecución

```sql
-- Debe retornar exactamente 100
SELECT COUNT(*) FROM Empleados;

-- Debe retornar ~6000 (100 empleados x 60 días x 2 registros)
SELECT COUNT(*) FROM Asistencias;

-- Debe retornar 600 (100 empleados x 6 períodos)
SELECT COUNT(*) FROM RegistrosNomina;

-- Debe retornar 6
SELECT COUNT(*) FROM PeriodosNomina;
```

---

## ✅ Resultado Esperado

Al finalizar, verás un resumen como este:

```
Tabla                    | Total
------------------------|-------
Empleados               | 100
Departamentos           | 8
Puestos                 | 18
Beneficios/Deducciones  | 9
Asignaciones BD         | ~300
Períodos de Nómina      | 6
Registros de Nómina     | 600
Items de Nómina         | ~2400
Asistencias            | ~6000
```

**¡Sistema listo para uso con datos realistas!** 🎉
