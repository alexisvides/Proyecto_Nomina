# 💰 Sistema de Préstamos a Empleados

## Descripción General
Sistema completo para gestionar préstamos a empleados con descuento automático en nómina, configuración flexible de cuotas y seguimiento de pagos.

## 🚀 Funcionalidades Implementadas

### 1. **Creación de Préstamos**
- Monto total configurable
- Dos tipos de descuento:
  - **Monto Fijo**: Se descuenta la misma cantidad cada periodo
  - **Porcentaje del Salario**: Se descuenta un % del salario base cada periodo
- Campo de descripción opcional
- Registro de usuario que creó el préstamo
- Auditoría completa

### 2. **Descuento Automático en Nómina**
- Se ejecuta automáticamente al generar un periodo de nómina
- Calcula el monto según el tipo configurado:
  - Fijo: Descuenta el monto exacto (o lo que quede si es menor)
  - Porcentaje: Calcula el % del salario del periodo actual
- Nunca descuenta más del monto pendiente
- Crea un ítem de deducción en la nómina llamado "Préstamo"
- Registra cada pago en el historial

### 3. **Control Automático de Estado**
- **Activo**: Préstamo con saldo pendiente
- **Pagado**: Se completa automáticamente cuando MontoPendiente = 0
- **Cancelado**: Cancelado manualmente por el usuario

### 4. **Seguimiento y Visualización**
- Lista de préstamos por empleado
- Indicadores visuales de estado y progreso
- Barra de progreso visual
- Colores según pendiente:
  - 🔴 Rojo: >70% pendiente
  - 🟡 Amarillo: 30-70% pendiente
  - 🟢 Verde: <30% pendiente o pagado

### 5. **Historial de Pagos**
- Registro de cada descuento realizado
- Asociado al periodo y registro de nómina
- Fecha, monto y periodo de cada pago
- Total pagado acumulado

## 📊 Estructura de Base de Datos

### Tabla: `Prestamos`
```sql
IdPrestamo INT IDENTITY(1,1) PRIMARY KEY
IdEmpleado INT NOT NULL
MontoTotal DECIMAL(18, 4)
MontoPendiente DECIMAL(18, 4)
TipoDescuento VARCHAR(20) -- 'fijo' o 'porcentaje'
ValorDescuento DECIMAL(18, 4)
FechaInicio DATE
FechaFin DATE NULL
Estado VARCHAR(20) -- 'activo', 'pagado', 'cancelado'
Descripcion VARCHAR(500)
FechaCreacion DATETIME2
UsuarioCreacion INT
```

### Tabla: `PrestamoPagos`
```sql
IdPago INT IDENTITY(1,1) PRIMARY KEY
IdPrestamo INT NOT NULL
IdPeriodo INT NOT NULL
IdNomina INT NULL
MontoPagado DECIMAL(18, 4)
FechaPago DATETIME2
```

## 🔧 Instalación

1. **Ejecutar el script SQL:**
   ```bash
   CREATE_PRESTAMOS_TABLE.sql
   ```

2. **Verificar permisos:**
   - El módulo "Empleados" debe tener permisos habilitados
   - Usuario debe tener acceso a `/empleados/<id>/beneficios`

## 📝 Uso

### Crear un Préstamo

1. Ir a **Empleados** → Seleccionar empleado → **Beneficios**
2. En la sección "💰 Préstamos", click en **Nuevo Préstamo**
3. Completar el formulario:
   - Monto Total (ej: 5000.00)
   - Tipo de Descuento (Fijo o Porcentaje)
   - Valor del Descuento (ej: 500.00 o 10.00%)
   - Descripción opcional
4. Click en **Crear Préstamo**

### Generar Nómina con Préstamos

1. Ir a **Nómina** → **Periodos**
2. Seleccionar un periodo y click en **Generar Nómina**
3. El sistema automáticamente:
   - Detecta préstamos activos
   - Calcula el descuento correspondiente
   - Lo añade como deducción en la nómina
   - Registra el pago
   - Actualiza el saldo pendiente
   - Marca como "pagado" si se completa

### Ver Detalle de un Préstamo

1. En la lista de préstamos del empleado
2. Click en el botón 👁️ (Ver detalle)
3. Visualiza:
   - Información completa del préstamo
   - Progreso de pago
   - Historial de todos los pagos realizados
   - Periodos en que se descontó

### Cancelar un Préstamo

1. En la lista de préstamos
2. Click en el botón ❌ (Cancelar)
3. Confirmar la acción
4. El préstamo se marca como "cancelado" y deja de descontarse

## ⚙️ Rutas Implementadas

```python
# Crear préstamo
POST /empleados/<id_empleado>/prestamos/crear

# Cancelar préstamo
POST /prestamos/<id_prestamo>/cancelar

# Ver detalle de préstamo
GET /prestamos/<id_prestamo>/detalle

# Ver préstamos de empleado (integrado en)
GET /empleados/<id_empleado>/beneficios
```

## 🎯 Casos de Uso

### Ejemplo 1: Descuento Fijo
- **Préstamo**: Q 6,000.00
- **Descuento**: Q 500.00 por periodo
- **Resultado**: Se descuenta Q 500.00 cada vez
- **Pagos totales**: 12 pagos de Q 500.00

### Ejemplo 2: Descuento por Porcentaje
- **Préstamo**: Q 5,000.00
- **Descuento**: 10% del salario
- **Salario empleado**: Q 4,000.00
- **Descuento por periodo**: Q 400.00
- **Pagos totales**: ~13 pagos (varía si el salario cambia)

### Ejemplo 3: Pago Final
- **Préstamo**: Q 3,000.00
- **Descuento**: Q 500.00 por periodo
- **Último pago**: Solo Q 500.00 (porque es lo que queda)
- **Estado**: Se marca automáticamente como "pagado"

## 🔒 Seguridad

- ✅ Requiere autenticación
- ✅ Requiere permiso del módulo "Empleados"
- ✅ Solo usuarios autorizados pueden crear/cancelar préstamos
- ✅ Auditoría de todas las acciones
- ✅ Validaciones en backend:
  - Monto positivo
  - Tipo de descuento válido
  - Porcentaje ≤ 100%
  - No puede descontar más del saldo pendiente

## 🎨 Interfaz

### Modal de Creación
- Formulario limpio y moderno
- Campos dinámicos según tipo de descuento
- Placeholders informativos
- Cierre con ESC o click fuera

### Lista de Préstamos
- Tabla responsive
- Estados con badges de colores
- Acciones inline (ver/cancelar)
- Indicadores visuales de pendiente

### Detalle del Préstamo
- Cards informativos
- Barra de progreso animada
- Historial de pagos completo
- Resumen de totales

## 📋 Notas Importantes

1. **Descuento Inteligente**: Nunca descuenta más del saldo pendiente
2. **Cierre Automático**: El préstamo se marca como "pagado" cuando MontoPendiente = 0
3. **Sin Duplicados**: No se descuenta dos veces en el mismo periodo
4. **Tolerante a Errores**: Si la tabla no existe, continúa sin errores
5. **Auditoría**: Todos los eventos se registran en logs

## 🔄 Flujo Completo

```
1. Admin crea préstamo → Estado: Activo
                       ↓
2. Genera nómina → Calcula descuento → Crea ítem deducción
                       ↓
3. Registra pago → Actualiza MontoPendiente
                       ↓
4. ¿Saldo = 0? → SÍ → Estado: Pagado ✓
               → NO → Sigue Activo (continúa en siguiente periodo)
```

## 🐛 Troubleshooting

### El préstamo no se descuenta
- Verificar que el estado sea "activo"
- Verificar que MontoPendiente > 0
- Verificar que el empleado tenga nómina generada en el periodo

### Error al crear tabla
- Verificar permisos de CREATE TABLE en SQL Server
- Ejecutar script CREATE_PRESTAMOS_TABLE.sql manualmente

### No aparecen los préstamos
- Verificar que la tabla Prestamos exista
- Revisar logs del servidor para errores SQL

## 📞 Soporte

Para dudas o problemas:
1. Revisar logs de auditoría
2. Verificar estructura de base de datos
3. Comprobar permisos de usuario
4. Revisar console del navegador (F12)

---

**Desarrollado como parte del sistema de nómina integrado** 🚀
