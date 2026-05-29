import re
from ml_api import get_preguntas_sin_responder, responder_pregunta, get_mis_publicaciones, get_publicacion
from telegram_utils import enviar_mensaje
from config import REGLAS_RESPUESTA, CONTEXTO_NEGOCIO, PRODUCTOS
from modulo_ia import consultar_claude

KEYWORDS = {
    "envio":           ["envio", "envío", "llega", "despacho", "correo", "manda", "cuando llega"],
    "stock":           ["stock", "disponible", "hay", "tienen", "queda"],
    "garantia":        ["garantia", "garantía", "falla", "roto", "defecto", "problema"],
    "factura":         ["factura", "factur", "comprobante", "ticket"],
    "mayor":           ["mayor", "mayorista", "por mayor", "cantidad", "varios"],
    "original":        ["original", "genuino", "legitimo", "legítimo", "trucho", "falso"],
    "demora":          ["demora", "tarda", "dias", "días", "tiempo"],
    "retiro":          ["retiro", "buscar", "paso a buscar", "pickup"],
    "precio_especial": ["descuento", "rebaja", "más barato", "oferta", "precio especial"],
    "reclamo":         ["reclamo", "queja", "mal", "no funciona", "no sirve"],
    "cambio":          ["cambio", "cambiar", "cambié"],
    "devolucion":      ["devolucion", "devolución", "devolver", "reembolso"],
}

def normalizar(texto):
    texto = texto.lower()
    texto = re.sub(r'[áàä]', 'a', texto)
    texto = re.sub(r'[éèë]', 'e', texto)
    texto = re.sub(r'[íìï]', 'i', texto)
    texto = re.sub(r'[óòö]', 'o', texto)
    texto = re.sub(r'[úùü]', 'u', texto)
    return texto

def detectar_categoria(texto):
    texto_norm = normalizar(texto)
    for categoria, keywords in KEYWORDS.items():
        if any(kw in texto_norm for kw in keywords):
            return categoria
    return None

def get_info_producto_real(item_id):
    try:
        pub = get_publicacion(item_id)
        return {
            "nombre": pub.get("title", item_id),
            "precio": pub.get("price", 0),
            "stock": pub.get("available_quantity", 0),
            "estado": pub.get("status", ""),
        }
    except Exception as e:
        print(f"⚠️ No se pudo obtener info de ML: {e}")
        for p in PRODUCTOS:
            if p.get("id") == item_id:
                return {
                    "nombre": p.get("nombre", item_id),
                    "precio": p.get("precio_min", 0),
                    "stock": p.get("stock_alerta", 0),
                    "estado": "active",
                }
        return {"nombre": item_id, "precio": 0, "stock": 0, "estado": ""}

def generar_respuesta_con_ia(pregunta, info_producto):
    nombre = info_producto.get("nombre", "")
    precio = info_producto.get("precio", 0)
    stock = info_producto.get("stock", 0)

    prompt = f"""
{CONTEXTO_NEGOCIO}

Un comprador hizo esta pregunta en MercadoLibre sobre el producto "{nombre}":
"{pregunta}"

Datos actuales:
- Precio: ${precio:,}
- Stock: {stock} unidades {"(disponible)" if stock > 0 else "(sin stock)"}

Respondé usando SOLO la información del contexto de arriba.
Si no sabés algo con certeza, decí "Te consulto y te confirmo enseguida."
Máximo 3 oraciones. Empezá con "¡Hola!"
"""
    return consultar_claude(prompt, max_tokens=200)

def consultar_al_dueno(pregunta_id, texto, producto_nombre):
    enviar_mensaje(
        f"❓ <b>PREGUNTA REQUIERE TU RESPUESTA</b>\n\n"
        f"Producto: {producto_nombre}\n"
        f"Pregunta: {texto}\n\n"
        f"Respondé directamente en ML."
    )
    print(f"📤 Escalada al dueño: '{texto[:50]}'")

def procesar_preguntas():
    publicaciones = get_mis_publicaciones()
    total_respondidas = 0
    total_escaladas = 0

    for item_id in publicaciones:
        preguntas = get_preguntas_sin_responder(item_id)
        if not preguntas:
            continue

        info = get_info_producto_real(item_id)
        nombre = info.get("nombre", item_id)

        for pregunta in preguntas:
            texto = pregunta.get("text", "")
            pregunta_id = pregunta["id"]
            categoria = detectar_categoria(texto)

            if categoria:
                regla = REGLAS_RESPUESTA.get(categoria, "AUTOMATICO")
                if regla == "CONSULTAR_DUEÑO":
                    consultar_al_dueno(pregunta_id, texto, nombre)
                    total_escaladas += 1
                else:
                    respuesta = generar_respuesta_con_ia(texto, info)
                    if respuesta:
                        responder_pregunta(pregunta_id, respuesta)
                        total_respondidas += 1
                        enviar_mensaje(
                            f"🤖 <b>Pregunta respondida</b>\n\n"
                            f"Producto: {nombre}\n"
                            f"Pregunta: {texto}\n"
                            f"Respuesta: {respuesta}"
                        )
                    else:
                        consultar_al_dueno(pregunta_id, texto, nombre)
                        total_escaladas += 1
            else:
                # Cualquier pregunta que no tenga keyword — Claude igual responde
                respuesta = generar_respuesta_con_ia(texto, info)
                if respuesta:
                    responder_pregunta(pregunta_id, respuesta)
                    total_respondidas += 1
                    enviar_mensaje(
                        f"🤖 <b>Pregunta respondida</b>\n\n"
                        f"Producto: {nombre}\n"
                        f"Pregunta: {texto}\n"
                        f"Respuesta: {respuesta}"
                    )
                else:
                    consultar_al_dueno(pregunta_id, texto, nombre)
                    total_escaladas += 1

    if total_respondidas > 0 or total_escaladas > 0:
        print(f"✅ Respondidas: {total_respondidas} | 📤 Escaladas: {total_escaladas}")
