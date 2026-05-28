import json
import os
import requests
from collections import deque

CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
CLAUDE_MODEL = "claude-sonnet-4-20250514"

historial = deque(maxlen=10)

def get_sistema():
    """Genera el prompt del sistema con datos reales en el momento."""
    from config import PRODUCTOS
    from ml_api import get_reputacion

    productos_txt = ""
    for p in PRODUCTOS:
        estado = "activo" if p.get("activo") else "inactivo"
        productos_txt += f"- {p['nombre']} (min ${p['precio_min']:,}, max ${p['precio_max']:,}, costo ${p['costo']:,}, estado: {estado})\n"

    try:
        rep = get_reputacion()
        reputacion_txt = f"Nivel: {rep['nivel']}, Transacciones: {rep['transacciones']}"
    except:
        reputacion_txt = "No disponible"

    return f"""
Sos el asistente de gestión de una tienda en MercadoLibre Argentina llamada MLVentasBot.
El dueño te manda mensajes en lenguaje natural y vos tenés que interpretarlos,
mantener el hilo de la conversación, y devolver UNA acción concreta en formato JSON.

PRODUCTOS ACTUALES DE LA TIENDA:
{productos_txt}

REPUTACIÓN ML: {reputacion_txt}

ACCIONES DISPONIBLES:
- bajar_precios_minimo: baja todos los productos al precio mínimo
- subir_precios_maximo: sube todos (o uno) al precio máximo
- cambiar_precio: cambia precio de un producto específico
- pausar_producto: pausa una publicación
- activar_producto: activa una publicación
- pausar_todo: pausa todas las publicaciones
- activar_todo: activa todas las publicaciones
- ver_stock: muestra el stock actual
- ver_ventas: muestra las ventas del día
- ver_publicaciones: muestra estado actual de publicaciones en ML
- reporte: genera el reporte semanal ahora
- analizar_campanas: analiza campañas con IA
- proponer_restock: analiza si hay que reponer stock
- mensaje_libre: cuando el dueño hace una pregunta o charla

REGLAS IMPORTANTES:
- Mantené el hilo de la conversación
- Si el dueño dice "dale" o "sí" después de que propusiste algo, ejecutá esa acción
- Si no está claro qué quiere, preguntá antes de ejecutar
- Respondé siempre en español, tono directo y amigable
- Para acciones de dinero importantes, confirmá antes de ejecutar
- Nunca inventes datos — si no tenés el dato real, decí que vas a buscarlo

Respondé SOLO con JSON sin texto adicional ni markdown:
{{
  "accion": "nombre_accion",
  "producto": "nombre_producto_o_null",
  "precio_nuevo": numero_o_null,
  "respuesta": "lo que le vas a decir al dueño"
}}
"""

def interpretar(mensaje):
    historial.append({"role": "user", "content": mensaje})

    headers = {
        "Content-Type": "application/json",
        "x-api-key": os.getenv("ANTHROPIC_API_KEY", ""),
        "anthropic-version": "2023-06-01"
    }
    body = {
        "model": CLAUDE_MODEL,
        "max_tokens": 400,
        "system": get_sistema(),
        "messages": list(historial)
    }
    try:
        r = requests.post(CLAUDE_API_URL, headers=headers, json=body, timeout=30)
        data = r.json()
        if "content" not in data:
            print(f"❌ Claude API error: {data}")
            return {"accion": "mensaje_libre", "respuesta": "Hubo un error procesando tu mensaje."}
        texto = data["content"][0]["text"].strip()
        texto = texto.replace("```json", "").replace("```", "").strip()
        resultado = json.loads(texto)
        historial.append({"role": "assistant", "content": texto})
        return resultado
    except Exception as e:
        print(f"❌ Error interpretando mensaje: {e}")
        historial.append({"role": "assistant", "content": '{"accion":"mensaje_libre","respuesta":"Hubo un error."}'})
        return {"accion": "mensaje_libre", "respuesta": "Hubo un error procesando tu mensaje. Podés intentar de nuevo."}

def ejecutar(interpretacion, sheets_service=None):
    if not interpretacion:
        return "No entendí el mensaje. Podés intentar de nuevo o usar /ayuda."

    accion = interpretacion.get("accion")
    producto = interpretacion.get("producto")
    respuesta_base = interpretacion.get("respuesta", "")

    try:
        if accion == "ver_publicaciones":
            from ml_api import get_mis_publicaciones, get_publicacion
            items = get_mis_publicaciones()
            if not items:
                return "No encontré publicaciones activas en tu cuenta de ML."
            lineas = ["📋 <b>Tus publicaciones en ML:</b>\n"]
            for item_id in items:
                pub = get_publicacion(item_id)
                nombre = pub.get("title", item_id)
                precio = pub.get("price", 0)
                stock = pub.get("available_quantity", 0)
                estado = pub.get("status", "unknown")
                lineas.append(f"• <b>{nombre}</b>\n  Precio: ${precio:,} | Stock: {stock} | Estado: {estado}")
            return "\n".join(lineas)

        elif accion == "bajar_precios_minimo":
            from config import PRODUCTOS
            from ml_api import actualizar_precio
            for p in PRODUCTOS:
                if p.get("activo") and p.get("id"):
                    actualizar_precio(p["id"], p["precio_min"])
            from modulo_decisiones import registrar
            registrar("LENGUAJE_NATURAL", "todos", "Precios bajados al mínimo")

        elif accion == "subir_precios_maximo":
            from config import PRODUCTOS
            from ml_api import actualizar_precio
            productos_target = [p for p in PRODUCTOS if p.get("activo") and (not producto or producto.lower() in p["nombre"].lower())]
            for p in productos_target:
                actualizar_precio(p["id"], p["precio_max"])
            from modulo_decisiones import registrar
            registrar("LENGUAJE_NATURAL", producto or "todos", "Precios subidos al máximo")

        elif accion == "cambiar_precio":
            from config import PRODUCTOS
            from ml_api import actualizar_precio
            precio_nuevo = interpretacion.get("precio_nuevo")
            if producto and precio_nuevo:
                for p in PRODUCTOS:
                    if producto.lower() in p["nombre"].lower() and p.get("activo"):
                        actualizar_precio(p["id"], precio_nuevo)
                        from modulo_decisiones import registrar
                        registrar("LENGUAJE_NATURAL", p["nombre"], f"Precio cambiado a ${precio_nuevo:,}")
                        break

        elif accion == "pausar_todo":
            from ml_api import get_mis_publicaciones
            from modulo_auth import get_access_token
            items = get_mis_publicaciones()
            token = get_access_token()
            headers_ml = {"Authorization": f"Bearer {token}"}
            for item_id in items:
                requests.put(f"https://api.mercadolibre.com/items/{item_id}",
                           headers=headers_ml, json={"status": "paused"})
            from modulo_decisiones import registrar
            registrar("LENGUAJE_NATURAL", "todos", "Publicaciones pausadas")

        elif accion == "activar_todo":
            from ml_api import get_mis_publicaciones
            from modulo_auth import get_access_token
            items = get_mis_publicaciones()
            token = get_access_token()
            headers_ml = {"Authorization": f"Bearer {token}"}
            for item_id in items:
                requests.put(f"https://api.mercadolibre.com/items/{item_id}",
                           headers=headers_ml, json={"status": "active"})
            from modulo_decisiones import registrar
            registrar("LENGUAJE_NATURAL", "todos", "Publicaciones activadas")

        elif accion == "ver_stock":
            from modulo_stock import verificar_stock
            verificar_stock()

        elif accion in ["ver_ventas", "reporte"]:
            from modulo_reporte import generar_reporte
            generar_reporte()

        elif accion == "analizar_campanas":
            from modulo_campanas import analizar_campanas
            analizar_campanas()

        elif accion == "proponer_restock":
            from modulo_restock import proponer_restock
            proponer_restock()

        elif accion == "mensaje_libre":
            return respuesta_base

    except Exception as e:
        print(f"❌ Error ejecutando acción {accion}: {e}")
        return f"Entendí lo que querés pero hubo un error ejecutando: {e}"

    return f"✅ {respuesta_base}"

def limpiar_historial():
    historial.clear()
