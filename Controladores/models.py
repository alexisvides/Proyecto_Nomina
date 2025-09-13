from . import db
from datetime import date

class Empleado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    salario_base = db.Column(db.Float, nullable=False)
    
    nominas = db.relationship('Nomina', backref='empleado', lazy=True)

class Nomina(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    empleado_id = db.Column(db.Integer, db.ForeignKey('empleado.id'), nullable=False)
    periodo_inicio = db.Column(db.Date, nullable=False)
    periodo_fin = db.Column(db.Date, nullable=False)
    horas_extra = db.Column(db.Float, default=0.0)
    bonificaciones = db.Column(db.Float, default=0.0)
    descuentos = db.Column(db.Float, default=0.0)
    total_pagar = db.Column(db.Float, default=0.0)
