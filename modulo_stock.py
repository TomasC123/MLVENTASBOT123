from ml_api import get_publicacion
from telegram_utils import alerta_stock
from config import PRODUCTOS

def verificar_stock():
    for producto in PRODUCTOS:
        try:
            pub = get_publicacion(producto["id"])
            stock_actual = pub.get("available_quantity", 0)
            alerta_minima = producto["stock_alerta"]

            print(f"📦 {producto['nombre']}: {stock_actual} unidades")

            if stock_actual <= alerta_minima:
                alerta_stock(producto["nombre"], stock_actual)

        except Exception as e:
            print(f"Error verificando stock de {producto['nombre']}: {e}")
