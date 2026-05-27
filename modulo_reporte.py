from ml_api import get_ventas_recientes, get_reputacion
from telegram_utils import reporte_semanal
from config import PRODUCTOS
from datetime import datetime, timedelta

def generar_reporte():
    ventas = get_ventas_recientes()
    hace_7_dias = datetime.now() - timedelta(days=7)

    ventas_semana = [
        v for v in ventas
        if datetime.fromisoformat(v["date_created"].replace("Z", "")) > hace_7_dias
    ]

    total_unidades = len(ventas_semana)
    ingresos_brutos = sum(v.get("total_amount", 0) for v in ventas_semana)

    costos = {p["id"]: p["costo"] for p in PRODUCTOS}
    margen_estimado = 0
    conteo_productos = {}

    for v in ventas_semana:
        for item in v.get("order_items", []):
            item_id = item.get("item", {}).get("id")
            cantidad = item.get("quantity", 1)
            precio = item.get("unit_price", 0)
            costo = costos.get(item_id, 0)
            margen_estimado += (precio - costo) * cantidad
            conteo_productos[item_id] = conteo_productos.get(item_id, 0) + cantidad

    mejor_id = max(conteo_productos, key=conteo_productos.get) if conteo_productos else None
    nombres = {p["id"]: p["nombre"] for p in PRODUCTOS}
    mejor_producto = nombres.get(mejor_id, "N/A")

    rep = get_reputacion()
    reputacion_str = f"{rep['nivel']} ({rep['transacciones']} ventas)"

    reporte_semanal(
        ventas=total_unidades,
        ingresos=int(ingresos_brutos),
        margen=int(margen_estimado),
        mejor_producto=mejor_producto,
        reputacion=reputacion_str
    )
