import requests
from config import ML_ACCESS_TOKEN, PRODUCTOS
from modulo_ia import consultar_claude
from modulo_decisiones import registrar
from telegram_utils import enviar_mensaje
import json

BASE = "https://api.mercadolibre.com"
HEADERS = {"Authorization": f"Bearer {ML_ACCESS_TOKEN}"}

# Decisiones pendientes de aprobación
_pendientes = {}

def get_campanas_activas():
    try:
        r = requests.get(f"{BASE}/advertising/product_ads/campaigns", headers=HEADERS)
        return r.json().get("results", [])
    except Exception as e:
        print(f"Error obteniendo campañas: {e}")
        return []

def get_metricas_campana(campaign_id):
    try:
        r = requests.get(
            f"{BASE}/advertising/product_ads/campaigns/{campaign_id}/metrics",
            headers=HEADERS
        )
        return r.json()
    except:
        return {}

def pausar_campana(campaign_id):
    try:
        r = requests.put(
            f"{BASE}/advertising/product_ads/campaigns/{campaign_id}",
            headers=HEADERS,
            json={"status": "paused"}
        )
        return r.json()
    except:
        return None

def activar_campana(campaign_id):
    try:
        r = requests.put(
            f"{BASE}/advertising/product_ads/campaigns/{campaign_id}",
            headers=HEADERS,
            json={"status": "active"}
        )
        return r.json()
    except:
        return None

def actualizar_presupuesto(campaign_id, nuevo_presupuesto):
    try:
        r = requests.put(
            f"{BASE}/advertising/product_ads/campaigns/{campaign_id}",
            headers=HEADERS,
            json={"daily_budget": nuevo_presupuesto}
        )
        return r.json()
    except:
        return None

def analizar_campanas():
    """
    Analiza campañas con IA y te manda sugerencias por Telegram.
    NUNCA ejecuta cambios solo — siempre espera tu aprobación.
    """
    campanas = get_campanas_activas()
    if not campanas:
        print("Sin campañas activas")
        return

    resumen = []
    for c in campanas:
        metricas = get_metricas_campana(c["id"])
        resumen.append({
            "id": c["id"],
            "nombre": c.get("name"),
            "status": c.get("status"),
            "presupuesto_diario": c.get("daily_budget", 0),
            "impresiones": metricas.get("impressions", 0),
            "clicks": metricas.get("clicks", 0),
            "ctr": metricas.get("ctr", 0),
            "ventas": metricas.get("sales", 0),
            "gasto": metricas.get("spend", 0),
            "roas": metricas.get("roas", 0),
        })

    prompt = f"""
Analizá el rendimiento de estas campañas de Product Ads en MercadoLibre:

{json.dumps(resumen, ensure_ascii=False, indent=2)}

Para cada campaña sugerí UNA acción. Formato exacto:
CAMPAÑA: [nombre]
ACCION: [MANTENER / AUMENTAR_PRESUPUESTO / REDUCIR_PRESUPUESTO / PAUSAR]
NUEVO_PRESUPUESTO: [número en pesos o IGUAL]
RAZON: [una línea breve]
---
"""
    decision = consultar_claude(prompt, max_tokens=600)
    if not decision:
        return

    # Parsear sugerencias
    bloques = decision.strip().split("---")
    sugerencias = []

    for bloque in bloques:
        lineas = [l.strip() for l in bloque.strip().split("\n") if l.strip()]
        if not lineas:
            continue
        try:
            nombre = [l for l in lineas if l.startswith("CAMPAÑA:")][0].split(":", 1)[1].strip()
            accion = [l for l in lineas if l.startswith("ACCION:")][0].split(":", 1)[1].strip()
            ppto = [l for l in lineas if l.startswith("NUEVO_PRESUPUESTO:")][0].split(":", 1)[1].strip()
            razon = [l for l in lineas if l.startswith("RAZON:")][0].split(":", 1)[1].strip()
            campana = next((c for c in resumen if c["nombre"] == nombre), None)
            if campana:
                sugerencias.append({
                    "id": campana["id"],
                    "nombre": nombre,
                    "accion": accion,
                    "presupuesto_actual": campana["presupuesto_diario"],
                    "nuevo_presupuesto": ppto,
                    "razon": razon,
                    "roas": campana["roas"],
                })
        except:
            continue

    if not sugerencias:
        enviar_mensaje("📢 <b>Análisis de campañas</b>\n\nSin sugerencias de cambio por ahora.")
        return

    # Guardar pendientes y mandar para aprobación
    _pendientes.clear()
    msg_lineas = ["📢 <b>Sugerencias de campañas — necesito tu aprobación</b>\n"]

    for i, s in enumerate(sugerencias):
        key = str(i)
        _pendientes[key] = s

        icono = {"MANTENER": "✅", "AUMENTAR_PRESUPUESTO": "📈", "REDUCIR_PRESUPUESTO": "📉", "PAUSAR": "⏸"}.get(s["accion"], "•")
        ppto_txt = f"${int(s['nuevo_presupuesto']):,}/día" if s["nuevo_presupuesto"] != "IGUAL" else "sin cambio"

        msg_lineas.append(
            f"{icono} <b>{s['nombre']}</b>\n"
            f"   Acción: {s['accion']}\n"
            f"   Presupuesto: ${s['presupuesto_actual']:,} → {ppto_txt}\n"
            f"   ROAS: {s['roas']} | Motivo: {s['razon']}\n"
            f"   → Aprobá con: /aprobar_campana {key} | Rechazá: /rechazar_campana {key}\n"
        )

    msg_lineas.append("\nO aprobá todo junto: /aprobar_campanas_todas")
    enviar_mensaje("\n".join(msg_lineas))
    registrar("CAMPAÑAS", "análisis", f"{len(sugerencias)} sugerencias enviadas para aprobación")

def aprobar_campana(key):
    if key not in _pendientes:
        return "❌ Sugerencia no encontrada o ya procesada."

    s = _pendientes.pop(key)

    if s["accion"] == "PAUSAR":
        pausar_campana(s["id"])
        registrar("CAMPAÑA", s["nombre"], f"Pausada — aprobado por vos")
        return f"⏸ Campaña <b>{s['nombre']}</b> pausada."

    elif s["accion"] in ["AUMENTAR_PRESUPUESTO", "REDUCIR_PRESUPUESTO"] and s["nuevo_presupuesto"] != "IGUAL":
        nuevo = int(s["nuevo_presupuesto"])
        actualizar_presupuesto(s["id"], nuevo)
        registrar("CAMPAÑA", s["nombre"], f"Presupuesto actualizado a ${nuevo:,} — aprobado por vos")
        return f"✅ Campaña <b>{s['nombre']}</b> — presupuesto actualizado a ${nuevo:,}/día."

    elif s["accion"] == "MANTENER":
        return f"✅ Campaña <b>{s['nombre']}</b> sin cambios."

    return "✅ Ejecutado."

def rechazar_campana(key):
    if key not in _pendientes:
        return "❌ Sugerencia no encontrada."
    s = _pendientes.pop(key)
    registrar("CAMPAÑA", s["nombre"], "Sugerencia rechazada por vos")
    return f"🚫 Sugerencia para <b>{s['nombre']}</b> descartada."

def aprobar_todas():
    if not _pendientes:
        return "No hay sugerencias pendientes."
    keys = list(_pendientes.keys())
    resultados = [aprobar_campana(k) for k in keys]
    return "\n".join(resultados)

def get_pendientes():
    return _pendientes
