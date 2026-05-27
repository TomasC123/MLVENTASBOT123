from ml_api import get_competidores, actualizar_precio, get_publicacion
from telegram_utils import alerta_precio
from config import PRODUCTOS

MARGEN_COMPETENCIA = 0.02  # Bajar 2% respecto al competidor más barato

def ajustar_precio(producto):
    item_id = producto["id"]
    nombre = producto["nombre"]
    precio_min = producto["precio_min"]
    precio_max = producto["precio_max"]

    # Precio actual
    pub = get_publicacion(item_id)
    precio_actual = pub.get("price", 0)

    # Buscar competidores
    competidores = get_competidores(nombre)
    precios_competencia = [
        c["price"] for c in competidores
        if c.get("id") != item_id and c.get("price", 0) > 0
    ]

    if not precios_competencia:
        print(f"Sin competidores encontrados para {nombre}")
        return

    precio_competidor_min = min(precios_competencia)
    precio_sugerido = round(precio_competidor_min * (1 - MARGEN_COMPETENCIA))

    # Aplicar límites
    precio_nuevo = max(precio_min, min(precio_max, precio_sugerido))

    # Solo actualizar si cambió más del 1%
    if abs(precio_nuevo - precio_actual) / precio_actual > 0.01:
        actualizar_precio(item_id, precio_nuevo)
        motivo = (
            f"Competidor más barato: ${precio_competidor_min:,} → "
            f"Nuevo precio: ${precio_nuevo:,}"
        )
        alerta_precio(nombre, precio_actual, precio_nuevo, motivo)
        print(f"💰 {nombre}: ${precio_actual:,} → ${precio_nuevo:,}")
    else:
        print(f"✅ {nombre}: precio OK (${precio_actual:,})")

def procesar_precios():
    for producto in PRODUCTOS:
        try:
            ajustar_precio(producto)
        except Exception as e:
            print(f"Error en {producto['nombre']}: {e}")
