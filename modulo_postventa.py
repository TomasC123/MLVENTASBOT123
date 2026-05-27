import requests
import time
from config import ML_ACCESS_TOKEN, PRODUCTOS
from modulo_ia import consultar_claude
from modulo_decisiones import registrar
from telegram_utils import enviar_mensaje

BASE = "https://api.mercadolibre.com"
HEADERS = {"Authorization": f"Bearer {ML_ACCESS_TOKEN}"}

ventas_procesadas = set()

def enviar_mensaje_comprador(pack_id, texto):
    try:
        r = requests.post(
            f"{BASE}/messages/packs/{pack_id}/sellers/me",
            headers=HEADERS,
            json={"text": texto}
        )
        return r.json()
    except Exception as e:
        print(f"Error enviando mensaje: {e}")
        return None

def procesar_postventa():
    from ml_api import get_ventas_recientes
    ventas = get_ventas_recientes()

    for venta in ventas:
        order_id = venta.get("id")
        if order_id in ventas_procesadas:
            continue

        status = venta.get("status", "")
        if status not in ["paid", "delivered"]:
            continue

        items = venta.get("order_items", [])
        if not items:
            continue

        producto = items[0].get("item", {}).get("title", "tu producto")
        comprador = venta.get("buyer", {}).get("nickname", "")
        pack_id = venta.get("pack_id") or order_id
        shipping = venta.get("shipping", {})
        tracking = shipping.get("id", "")

        if status == "paid":
            mensaje = generar_mensaje_confirmacion(producto, comprador, tracking)
        elif status == "delivered":
            mensaje = generar_mensaje_calificacion(producto, comprador)
        else:
            continue

        if mensaje:
            enviar_mensaje_comprador(pack_id, mensaje)
            ventas_procesadas.add(order_id)
            registrar("POST-VENTA", producto, f"Mensaje enviado a {comprador} — estado: {status}")
            print(f"✅ Mensaje post-venta enviado a {comprador}")

def generar_mensaje_confirmacion(producto, comprador, tracking):
    prompt = f"""
Escribí un mensaje breve y amigable para un comprador de MercadoLibre.
Producto comprado: {producto}
Nombre del comprador: {comprador}
Número de tracking: {tracking if tracking else "en proceso"}

El mensaje debe:
- Agradecer la compra
- Confirmar que está siendo preparado
- Mencionar el tracking si hay
- Invitarlos a consultar cualquier duda
- Máximo 3 oraciones, tono cálido y profesional
- NO mencionar calificaciones todavía
"""
    return consultar_claude(prompt, max_tokens=150)

def generar_mensaje_calificacion(producto, comprador):
    prompt = f"""
Escribí un mensaje breve para pedirle una calificación a un comprador de MercadoLibre.
Producto: {producto}
Nombre: {comprador}

El mensaje debe:
- Confirmar que recibió el producto
- Preguntar si todo llegó bien
- Pedirle amablemente que califique la compra
- Máximo 2 oraciones, muy natural y sin ser insistente
"""
    return consultar_claude(prompt, max_tokens=100)
