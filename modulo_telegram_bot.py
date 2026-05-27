import requests
import json
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, PRODUCTOS
from telegram_utils import enviar_mensaje
from modulo_ia import responder_pregunta_inteligente

BASE = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
ultimo_update = 0

AYUDA = """
🤖 <b>Comandos disponibles</b>

<b>Precios:</b>
/precio [producto] min [X] max [X]

<b>Productos:</b>
/activar [producto]
/desactivar [producto]
/precios — ver rangos actuales

<b>Stock y ventas:</b>
/stock — stock actual
/ventas — ventas del día
/reporte — reporte semanal ahora

<b>Campañas:</b>
/campanas — ver campañas activas
/analizar_campanas — analizar con IA
/aprobar_campana [n]
/rechazar_campana [n]
/aprobar_campanas_todas
/pausar_campana [id]
/activar_campana [id]

<b>Restock:</b>
/aprobar_restock
/rechazar_restock

<b>Sistema:</b>
/reautenticar — reconectar ML
/estado — estado del sistema

<b>Productos:</b> cable, hub, hdmi, microfono, impresora

/ayuda — este mensaje
"""

ALIAS = {
    "cable": "AUCATCAC",
    "hub": "AUHUB271",
    "hdmi": "AUCHDMI2",
    "microfono": "AUMICOK8",
    "impresora": "AUIMPTMI",
}

def get_updates():
    global ultimo_update
    try:
        r = requests.get(
            f"{BASE}/getUpdates",
            params={"offset": ultimo_update + 1, "timeout": 10},
            timeout=15
        )
        updates = r.json().get("result", [])
        if updates:
            ultimo_update = updates[-1]["update_id"]
        return updates
    except:
        return []

def procesar_comando(texto, sheets_service=None):
    partes = texto.strip().lower().split()
    cmd = partes[0] if partes else ""

    if cmd == "/ayuda":
        return AYUDA

    elif cmd == "/stock":
        from modulo_stock import verificar_stock
        verificar_stock()
        return "📦 Verificando stock... Te mando el resumen en segundos."

    elif cmd == "/ventas":
        from modulo_reporte import generar_reporte
        generar_reporte()
        return "📊 Generando resumen de ventas..."

    elif cmd == "/reporte":
        from modulo_reporte import generar_reporte
        generar_reporte()
        return "📊 Generando reporte completo..."

    elif cmd == "/precios":
        lineas = ["💰 <b>Rangos de precio actuales:</b>\n"]
        for p in PRODUCTOS:
            lineas.append(f"• {p['nombre']}\n  Min: ${p['precio_min']:,} | Max: ${p['precio_max']:,}")
        return "\n".join(lineas)

    elif cmd == "/precio" and len(partes) >= 5:
        # /precio cable min 6000 max 9000
        try:
            alias = partes[1]
            codigo = ALIAS.get(alias)
            if not codigo:
                return f"❌ Producto '{alias}' no encontrado. Usá: {', '.join(ALIAS.keys())}"

            min_idx = partes.index("min")
            max_idx = partes.index("max")
            nuevo_min = int(partes[min_idx + 1])
            nuevo_max = int(partes[max_idx + 1])

            if nuevo_min >= nuevo_max:
                return "❌ El precio mínimo debe ser menor al máximo."

            # Actualizar en memoria
            for p in PRODUCTOS:
                if p["id"] == codigo:
                    viejo_min = p["precio_min"]
                    viejo_max = p["precio_max"]
                    p["precio_min"] = nuevo_min
                    p["precio_max"] = nuevo_max
                    nombre = p["nombre"]
                    break

            # Actualizar en Sheets si está conectado
            if sheets_service:
                sheets_service.actualizar_rango(codigo, nuevo_min, nuevo_max)

            return (
                f"✅ <b>Precio actualizado</b>\n\n"
                f"Producto: {nombre}\n"
                f"Min: ${viejo_min:,} → ${nuevo_min:,}\n"
                f"Max: ${viejo_max:,} → ${nuevo_max:,}\n\n"
                f"Se aplica en el próximo ciclo de pricing."
            )
        except (ValueError, IndexError):
            return "❌ Formato incorrecto. Usá: /precio cable min 6000 max 9000"

    elif cmd in ["/activar", "/desactivar"] and len(partes) >= 2:
        alias = partes[1]
        codigo = ALIAS.get(alias)
        if not codigo:
            return f"❌ Producto '{alias}' no encontrado."

        activo = cmd == "/activar"
        for p in PRODUCTOS:
            if p["id"] == codigo:
                p["activo"] = activo
                nombre = p["nombre"]
                break

        if sheets_service:
            sheets_service.actualizar_estado(codigo, "SI" if activo else "NO")

        estado = "activado ✅" if activo else "pausado ⏸"
        return f"Producto <b>{nombre}</b> {estado}."

    # Campañas
    resultado_campana = procesar_comando_campanas(texto, partes)
    if resultado_campana:
        return resultado_campana

    # Restock
    elif cmd == "/aprobar_restock":
        from modulo_restock import aprobar_restock
        return aprobar_restock()

    elif cmd == "/rechazar_restock":
        from modulo_restock import rechazar_restock
        return rechazar_restock()

    # Sistema
    elif cmd == "/estado":
        from modulo_monitor import verificar_sistema
        verificar_sistema()
        return "🔍 Verificando sistema... Te aviso el resultado."

    elif cmd == "/reautenticar":
        from modulo_auth import get_url_autenticacion
        url = get_url_autenticacion()
        return (
            f"🔐 <b>Re-autenticación ML</b>\n\n"
            f"Abrí este link en el navegador:\n"
            f"{url}\n\n"
            f"Después de autorizar, el sistema se reconecta solo."
        )

    else:
        return f"❓ Comando no reconocido.\n\n{AYUDA}"

def escuchar_comandos(sheets_service=None):
    updates = get_updates()
    for update in updates:
        msg = update.get("message", {})
        chat_id = str(msg.get("chat", {}).get("id", ""))
        texto = msg.get("text", "")

        if chat_id != str(TELEGRAM_CHAT_ID):
            continue

        if texto.startswith("/"):
            respuesta = procesar_comando(texto, sheets_service)
            enviar_mensaje(respuesta, chat_id=chat_id)


def procesar_comando_campanas(texto, partes):
    from modulo_campanas import (
        get_campanas_activas, analizar_campanas,
        pausar_campana, activar_campana,
        aprobar_campana, rechazar_campana, aprobar_todas
    )

    cmd = partes[0]

    if cmd == "/campanas":
        campanas = get_campanas_activas()
        if not campanas:
            return "📢 No tenés campañas activas todavía."
        lineas = ["📢 <b>Campañas activas:</b>\n"]
        for c in campanas:
            lineas.append(
                f"• <b>{c.get('name')}</b>\n"
                f"  Status: {c.get('status')} | Presupuesto: ${c.get('daily_budget',0):,}/día\n"
                f"  ID: {c['id']}"
            )
        return "\n".join(lineas)

    elif cmd == "/analizar_campanas":
        analizar_campanas()
        return "🤖 Analizando campañas... Te mando las sugerencias para que apruebes."

    elif cmd == "/aprobar_campana" and len(partes) >= 2:
        return aprobar_campana(partes[1])

    elif cmd == "/rechazar_campana" and len(partes) >= 2:
        return rechazar_campana(partes[1])

    elif cmd == "/aprobar_campanas_todas":
        return aprobar_todas()

    elif cmd == "/pausar_campana" and len(partes) >= 2:
        pausar_campana(partes[1])
        return f"⏸ Campaña {partes[1]} pausada."

    elif cmd == "/activar_campana" and len(partes) >= 2:
        activar_campana(partes[1])
        return f"▶️ Campaña {partes[1]} activada."

    return None
