from datetime import datetime
import json

_decisiones_hoy = []

def registrar(tipo, producto, detalle, resultado=None):
    _decisiones_hoy.append({
        "hora": datetime.now().strftime("%H:%M"),
        "tipo": tipo,
        "producto": producto,
        "detalle": detalle,
        "resultado": resultado
    })

def get_decisiones():
    return _decisiones_hoy.copy()

def limpiar():
    _decisiones_hoy.clear()
