import json
import os
import requests
from collections import deque

CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
CLAUDE_MODEL = "claude-sonnet-4-20250514"

# Historial de conversación — últimos 10 mensajes
historial = deque(maxlen=10)

SISTEMA = """
Sos el asistente de gestión de una tienda en MercadoLibre Argentina llamada MLVentasBot.
El dueño te manda mensajes en lenguaje natural y vos tenés que interpretarlos,
mantener el hilo de la conversación, y devolver UNA acción concreta en formato JSON.

PRODUCTOS DE LA TIENDA:
- cable: Cable USB-C a USB-C carga rápida (costo $3.333, min $6.500, max $8.500)
- hub: Hub USB-C 7 en 1 aluminio (costo $6.200, min $12.000, max $18.000)
- hdmi: Cable USB-C a HDMI 4K 2m (costo $7.285, min $14.000, max $20.000)
- microfono: Micrófono corbatero inalámbrico (costo $5.115, min $10.000, max $15.000)
- impresora: Mini impresora térmica portátil (costo $15.190, min $29.000, max $40.000)

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
- reporte: genera el reporte semanal ahora
- analizar_campanas: analiza campañas con IA
- proponer_restock: analiza si hay que reponer stock
- mensaje_libre: cuando el dueño hace una pregunta, pide info o charla

REGLAS IMPORTANTES:
- Mantené el hilo de la conversación — si te preguntaron algo antes, recordalo
- Si el dueño dice "dale" o "sí" después de que vos propusiste algo, ejecutá esa acción
- Si no está claro qué quiere, preguntá antes de ejecutar
- Respondé siempre en español, tono directo y amigable
- Para acciones de dinero importantes, confirmá antes de ejecutar

Respondé SOLO con JSON sin texto adicional ni markdown:
{
  "accion": "nombre_accion",
  "producto": "nombre_producto_o_null",
  "precio_nuevo": numero_o_null,
  "respuesta": "lo que le vas a decir al dueño"
}
"""

def interpretar(mensaje):
    # Agregar mensaje del usuario al historial
    historial.append({"role": "user", "content": mensaje})
    
    headers = {
        "Content-Type": "application/json",
        "x-api-key": os.getenv("ANTHROPIC_API_KEY", ""),
        "anthropic-version": "2023-06-01"
    }
    body = {
        "model": CLAUDE_MODEL,
        "max_tokens": 400,
        "system": SISTEMA,
        "messages": list(historial)
    }
    try:
        r = requests.post(CLAUDE_API_URL, headers=headers, json=body, timeout=30)
        texto = r.json()["content"][0]["text"].strip()
        texto = texto.replace("```json", "").replace("```", "").strip()
        resultado = json.loads(texto)
        
        # Agregar respuesta del asistente al historial
        historial.append({"role": "assistant", "content": texto})
        
        return resultado
    except Exception as e:
        print(f"Error interpretando mensaje: {e}")
        historial.append({"role": "assistant", "content": '{"accion":"mensaje_libre","producto":null,"precio_nuevo":null,"respuesta":"Hubo un error procesando tu mensaje. Podés intentar de nuevo."}'})
        return {"accion": "mensaje_libre", "respuesta": "Hubo un error procesando tu mensaje. Podés intentar de nuevo."}

def ejecutar(interpretacion, sheets_service=None):
    if not interpretacion:
        return "No entendí el mensaje. Podés intentar de nuevo o usar /ayuda."

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
            registrar("LENGUAJE_NATURAL", "todos", "Precios bajados al mínimo")

        elif accion == "subir_precios_maximo":
            from config import PRODUCTOS
            from ml_api import actualizar_precio
            productos_target = [p for p in PRODUCTOS if not producto or producto.lower() in p["nombre"].lower()]
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
                    if producto.lower() in p["nombre"].lower():
                        actualizar_precio(p["id"], precio_nuevo)
                        from modulo_decisiones import registrar
                        registrar("LENGUAJE_NATURAL", p["nombre"], f"Precio cambiado a ${precio_nuevo:,}")
                        break

        elif accion == "pausar_todo":
            from config import PRODUCTOS
            from modulo_auth import get_access_token
            token = get_access_token()
            headers_ml = {"Authorization": f"Bearer {token}"}
            for p in PRODUCTOS:
                requests.put(f"https://api.mercadolibre.com/items/{p['id']}", 
                           headers=headers_ml, json={"status": "paused"})
            from modulo_decisiones import registrar
            registrar("LENGUAJE_NATURAL", "todos", "Publicaciones pausadas")

        elif accion == "activar_todo":
            from config import PRODUCTOS
            from modulo_auth import get_access_token
            token = get_access_token()
            headers_ml = {"Authorization": f"Bearer {token}"}
            for p in PRODUCTOS:
                requests.put(f"https://api.mercadolibre.com/items/{p['id']}", 
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
        return f"Entendí lo que querés pero hubo un error: {e}"

    return f"✅ {respuesta_base}"

def limpiar_historial():
    historial.clear()
