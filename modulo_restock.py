import os
from config import PRODUCTOS
from modulo_ia import consultar_claude
from modulo_decisiones import registrar
from telegram_utils import enviar_mensaje
import json

PROVEEDOR_EMAIL = os.getenv("PROVEEDOR_EMAIL", "")
PROVEEDOR_WHATSAPP = os.getenv("PROVEEDOR_WHATSAPP", "")

_restocks_pendientes = {}

def analizar_necesidad_restock(producto, stock_actual, ventas_semana):
    prompt = f"""
Analizá si este producto necesita restock:

Producto: {producto['nombre']}
Código ULI: {producto.get('codigo_uli', '')}
Costo unitario: ${producto['costo']:,}
Stock actual: {stock_actual} unidades
Ventas últimos 7 días: {ventas_semana} unidades
Stock mínimo configurado: {producto['stock_alerta']} unidades

¿Cuántas unidades conviene pedir?
Respondé exactamente:
PEDIR: [número de unidades o 0 si no hace falta]
URGENCIA: [BAJA / MEDIA / ALTA]
RAZON: [una línea]
"""
    return consultar_claude(prompt, max_tokens=150)

def generar_orden_restock(items_a_pedir):
    lineas = ["Estimados,\n\nSolicito el siguiente pedido:\n"]
    total = 0
    for item in items_a_pedir:
        subtotal = item["cantidad"] * item["costo"]
        total += subtotal
        lineas.append(
            f"- {item['codigo']}: {item['nombre']} x{item['cantidad']} "
            f"unidades — ${subtotal:,}"
        )
    lineas.append(f"\nTotal estimado: ${total:,}")
    lineas.append("\nQuedo a disposición para coordinar entrega y pago.")
    lineas.append("\nSaludos,\nMLVentasBot")
    return "\n".join(lineas), total

def proponer_restock():
    from ml_api import get_publicacion, get_ventas_recientes
    from datetime import datetime, timedelta

    ventas = get_ventas_recientes()
    hace_7_dias = datetime.now() - timedelta(days=7)

    ventas_por_producto = {}
    for v in ventas:
        if datetime.fromisoformat(v["date_created"].replace("Z", "")) > hace_7_dias:
            for item in v.get("order_items", []):
                item_id = item.get("item", {}).get("id")
                ventas_por_producto[item_id] = ventas_por_producto.get(item_id, 0) + item.get("quantity", 1)

    items_a_pedir = []

    for producto in PRODUCTOS:
        try:
            pub = get_publicacion(producto["id"])
            stock_actual = pub.get("available_quantity", 0)
            ventas_semana = ventas_por_producto.get(producto["id"], 0)

            if stock_actual <= producto["stock_alerta"] * 2:
                respuesta = analizar_necesidad_restock(producto, stock_actual, ventas_semana)
                if not respuesta:
                    continue

                lineas = respuesta.strip().split("\n")
                try:
                    cantidad = int([l for l in lineas if l.startswith("PEDIR:")][0].split(":")[1].strip())
                    urgencia = [l for l in lineas if l.startswith("URGENCIA:")][0].split(":")[1].strip()
                    razon = [l for l in lineas if l.startswith("RAZON:")][0].split(":")[1].strip()
                except:
                    continue

                if cantidad > 0:
                    items_a_pedir.append({
                        "id": producto["id"],
                        "codigo": producto.get("codigo_uli", ""),
                        "nombre": producto["nombre"],
                        "cantidad": cantidad,
                        "costo": producto["costo"],
                        "urgencia": urgencia,
                        "razon": razon,
                        "stock_actual": stock_actual,
                    })
        except Exception as e:
            print(f"Error analizando restock de {producto['nombre']}: {e}")

    if not items_a_pedir:
        print("Sin necesidad de restock")
        return

    orden, total = generar_orden_restock(items_a_pedir)

    _restocks_pendientes["pendiente"] = {
        "items": items_a_pedir,
        "orden": orden,
        "total": total
    }

    lineas_msg = ["📦 <b>PROPUESTA DE RESTOCK — necesito tu aprobación</b>\n"]
    for item in items_a_pedir:
        icono = "🔴" if item["urgencia"] == "ALTA" else "🟡" if item["urgencia"] == "MEDIA" else "🟢"
        lineas_msg.append(
            f"{icono} <b>{item['nombre']}</b>\n"
            f"   Stock actual: {item['stock_actual']} | Pedir: {item['cantidad']} unidades\n"
            f"   Costo: ${item['cantidad'] * item['costo']:,} | {item['razon']}"
        )

    lineas_msg.append(f"\n💵 <b>Total estimado: ${total:,}</b>")
    lineas_msg.append("\n¿Aprobás el pedido?\n/aprobar_restock — confirmar\n/rechazar_restock — cancelar")

    enviar_mensaje("\n".join(lineas_msg))
    registrar("RESTOCK", "propuesta", f"{len(items_a_pedir)} productos — ${total:,}")

def aprobar_restock():
    if "pendiente" not in _restocks_pendientes:
        return "No hay restock pendiente de aprobación."

    datos = _restocks_pendientes.pop("pendiente")
    orden = datos["orden"]
    total = datos["total"]

    enviar_mensaje(
        f"✅ <b>Restock aprobado — ${total:,}</b>\n\n"
        f"Orden generada y lista para enviar a Importadora ULI.\n"
        f"Copiá el texto de abajo y mandáselo:\n\n"
        f"<code>{orden}</code>"
    )
    registrar("RESTOCK", "aprobado", f"Orden por ${total:,} enviada")
    return f"✅ Orden de restock aprobada — ${total:,}"

def rechazar_restock():
    if "pendiente" not in _restocks_pendientes:
        return "No hay restock pendiente."
    _restocks_pendientes.pop("pendiente")
    registrar("RESTOCK", "rechazado", "Propuesta descartada por el dueño")
    return "🚫 Propuesta de restock descartada."
