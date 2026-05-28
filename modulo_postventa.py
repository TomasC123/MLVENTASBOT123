import requests
import json
import os
from modulo_auth import get_access_token
from modulo_ia import consultar_claude
from modulo_decisiones import registrar
from telegram_utils import enviar_mensaje

BASE = "https://api.mercadolibre.com"
PROCESADAS_FILE = "ventas_procesadas.json"

def get_headers():
    return {"Authorization": f"Bearer {get_access_token()}"}

def cargar_procesadas():
    try:
        with open(PROCESADAS_FILE, "r") as f:
            return set(json.load(f))
    except:
        return set()

def guardar_procesadas(procesadas):
    try:
        with open(PROCESADAS_FILE, "w") as f:
            json.dump(list(procesadas), f)
    except Exception as e:
        print(f"⚠️ No se pudo guardar ventas procesadas: {e}")

def enviar_mensaje_comprador(pack_id, texto):
    try:
        r = requests.post(
            f"{BASE}/messages/packs/{pack_id}/sellers/me",
            headers=get_headers(),
            json={"text": texto},
            timeout=15
        )
        return r.json()
    except Exception as e:
        print(f"❌ Error enviando mensaje: {e}")
        return None

def procesar_postventa():
    from ml_api import get_ventas_recientes
    ventas_procesadas = cargar_procesadas()
    ventas = get_ventas_recientes()
    
    for venta in ventas:
        order_id = str(venta.get("id", ""))
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
            resultado = enviar_mensaje_comprador(pack_id, mensaje)
            if resultado and not resultado.get("error"):
                ventas_procesadas.add(order_id)
                guardar_procesadas(ventas_procesadas)
                registrar("POST-VENTA", producto, f"Mensaje enviado a {comprador} — estado: {status}")
                print(f"✅ Mensaje post-venta enviado a {comprador}")
            else:
                print(f"⚠️ No se pudo enviar mensaje a {comprador}: {resultado}")

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
