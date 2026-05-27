from ml_api import get_publicacion
from telegram_utils import alerta_stock
from config import PRODUCTOS

PLACEHOLDERS = ["MLA_CABLE_USBC", "MLA_HUB_7EN1", "MLA_CABLE_HDMI", 
                "MLA_MICROFONO", "MLA_IMPRESORA"]

def verificar_stock():
    for producto in PRODUCTOS:
        try:
            # Ignorar productos sin ID real
            if producto["id"] in PLACEHOLDERS or not producto["id"].startswith("MLA"):
                print(f"⏭ {producto['nombre']}: sin publicación activa, ignorando")
                continue

            pub = get_publicacion(producto["id"])
            stock_actual = pub.get("available_quantity", 0)
            alerta_minima = producto["stock_alerta"]

            print(f"📦 {producto['nombre']}: {stock_actual} unidades")

            if stock_actual <= alerta_minima:
                alerta_stock(producto["nombre"], stock_actual)

        except Exception as e:
            print(f"Error verificando stock de {producto['nombre']}: {e}")
