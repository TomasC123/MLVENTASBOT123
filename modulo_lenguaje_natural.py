import json
import os
import requests

CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
CLAUDE_MODEL = "claude-sonnet-4-20250514"

SISTEMA = """
Sos el asistente de gestión de una tienda en MercadoLibre Argentina.
El dueño te manda mensajes en lenguaje natural y vos tenés que interpretarlos
y devolver UNA acción concreta en formato JSON.

ACCIONES DISPONIBLES:
- bajar_precios_minimo: baja todos los productos al precio mínimo
- subir_precios_maximo: sube todos los productos al precio máximo
- cambiar_precio: cambia el precio de un producto específico
- pausar_producto: pausa una publicación
- activar_producto: activa una publicación
- pausar_todo: pausa todas las publicaciones
- activar_todo: activa todas las publicaciones
- ver_stock: muestra el stock actual
- ver_ventas: muestra las ventas del día
- reporte: genera el reporte semanal ahora
- analizar_campanas: analiza campañas con IA
- proponer_restock: analiza si hay que reponer stock
- mensaje_libre: cuando el dueño hace una pregunta o pide info sin acción concreta

PRODUCTOS VÁLIDOS: cable, hub, hdmi, microfono, impresora

Respondé SOLO con JSON, sin texto adicional, sin markdown:
{
  "accion": "nombre_accion",
  "producto": "nombre_producto_o_null",
  "precio_min": numero_o_null,
  "precio_max": numero_o_null,
  "respuesta": "lo que le vas a decir al dueño confirmando la acción"
}

Ejemplos:
- "necesito liquidez, vendé todo" → {"accion":"bajar_precios_minimo","producto":null,"precio_min":null,"precio_max":null,"respuesta":"Bajando todos los precios al mínimo para generar liquidez."}
- "el hub está volando, subí el precio" → {"accion":"subir_precios_maximo","producto":"hub","precio_min":null,"precio_max":null,"respuesta":"Subiendo el hub al precio máximo."}
- "me voy de viaje una semana" → {"accion":"pausar_todo","producto":null,"precio_min":null,"precio_max":null,"respuesta":"Pausando todas las publicaciones. Avisame cuando volvés para reactivarlas."}
- "cómo vamos?" → {"accion":"reporte","producto":null,"precio_min":null,"precio_max":null,"respuesta":"Generando el reporte ahora."}
"""

def interpretar(mensaje):
    headers = {
        "Content-Type": "application/json",
        "x-api-key": os.getenv("ANTHROPIC_API_KEY", ""),
        "anthropic-version": "2023-06-01"
    }
    body = {
        "model": CLAUDE_MODEL,
        "max_tokens": 300,
        "system": SISTEMA,
        "messages": [{"role": "user", "content": mensaje}]
    }
    try:
        r = requests.post(CLAUDE_API_URL, headers=headers, json=body, timeout=30)
        texto = r.json()["content"][0]["text"].strip()
        texto = texto.replace("```json", "").replace("```", "").strip()
        return json.loads(texto)
    except Exception as e:
        print(f"Error interpretando mensaje: {e}")
        return None

def ejecutar(interpretacion, sheets_service=None):
    if not interpretacion:
        return "No entendí el mensaje. Podés intentar de nuevo o usar /ayuda para ver los comandos."

    accion = interpretacion.get("accion")
    producto = interpretacion.get("producto")
    respuesta_base = interpretacion.get("respuesta", "")

    try:
        if accion == "bajar_precios_minimo":
            from config import PRODUCTOS
            from ml_api import actualizar_precio
            for p in PRODUCTOS:
                actualizar_precio(p["id"], p["precio_min"])
            from modulo_decisiones import registrar
            registrar("LENGUAJE_NATURAL", "todos", "Precios bajados al mínimo por orden del dueño")

        elif accion == "subir_precios_maximo":
            from config import PRODUCTOS
            from ml_api import actualizar_precio
            productos_target = [p for p in PRODUCTOS if not producto or producto.lower() in p["nombre"].lower()]
            for p in productos_target:
                actualizar_precio(p["id"], p["precio_max"])
            from modulo_decisiones import registrar
            registrar("LENGUAJE_NATURAL", producto or "todos", "Precios subidos al máximo por orden del dueño")

        elif accion == "pausar_todo":
            from config import PRODUCTOS
            from ml_api import get_headers
            import requests as req
            for p in PRODUCTOS:
                req.put(f"https://api.mercadolibre.com/items/{p['id']}", 
                       headers=get_headers(), json={"status": "paused"})
            from modulo_decisiones import registrar
            registrar("LENGUAJE_NATURAL", "todos", "Todas las publicaciones pausadas por orden del dueño")

        elif accion == "activar_todo":
            from config import PRODUCTOS
            from ml_api import get_headers
            import requests as req
            for p in PRODUCTOS:
                req.put(f"https://api.mercadolibre.com/items/{p['id']}", 
                       headers=get_headers(), json={"status": "active"})
            from modulo_decisiones import registrar
            registrar("LENGUAJE_NATURAL", "todos", "Todas las publicaciones activadas por orden del dueño")

        elif accion == "ver_stock":
            from modulo_stock import verificar_stock
            verificar_stock()

        elif accion == "ver_ventas":
            from modulo_reporte import generar_reporte
            generar_reporte()

        elif accion == "reporte":
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
        return f"Entendí lo que querés hacer pero hubo un error al ejecutarlo: {e}"

    return f"✅ {respuesta_base}"
