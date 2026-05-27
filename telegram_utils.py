import requests
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

def enviar_mensaje(texto, chat_id=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id or TELEGRAM_CHAT_ID,
        "text": texto,
        "parse_mode": "HTML"
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        return r.json()
    except Exception as e:
        print(f"Error Telegram: {e}")
        return None

def alerta_stock(producto, unidades):
    msg = (
        f"⚠️ <b>ALERTA STOCK BAJO</b>\n\n"
        f"Producto: {producto}\n"
        f"Unidades restantes: <b>{unidades}</b>\n\n"
        f"👉 Hacer pedido a Importadora ULI"
    )
    enviar_mensaje(msg)

def alerta_precio(producto, precio_viejo, precio_nuevo, motivo):
    msg = (
        f"💰 <b>PRECIO ACTUALIZADO</b>\n\n"
        f"Producto: {producto}\n"
        f"Anterior: ${precio_viejo:,}\n"
        f"Nuevo: ${precio_nuevo:,}\n"
        f"Motivo: {motivo}"
    )
    enviar_mensaje(msg)

def alerta_venta(producto, precio, comprador):
    msg = (
        f"🛒 <b>NUEVA VENTA</b>\n\n"
        f"Producto: {producto}\n"
        f"Precio: ${precio:,}\n"
        f"Comprador: {comprador}"
    )
    enviar_mensaje(msg)

def reporte_semanal(ventas, ingresos, margen, mejor_producto, reputacion):
    msg = (
        f"📊 <b>REPORTE SEMANAL</b>\n"
        f"━━━━━━━━━━━━━━━━\n\n"
        f"🛒 Ventas: <b>{ventas}</b> unidades\n"
        f"💵 Ingresos brutos: <b>${ingresos:,}</b>\n"
        f"📈 Margen estimado: <b>${margen:,}</b>\n"
        f"⭐ Mejor producto: <b>{mejor_producto}</b>\n"
        f"🏆 Reputación ML: <b>{reputacion}</b>\n\n"
        f"━━━━━━━━━━━━━━━━"
    )
    enviar_mensaje(msg)
