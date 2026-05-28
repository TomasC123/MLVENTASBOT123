import re
from ml_api import get_preguntas_sin_responder, responder_pregunta, get_mis_publicaciones
from telegram_utils import enviar_mensaje
from config import REGLAS_RESPUESTA, CONTEXTO_NEGOCIO, PRODUCTOS
from modulo_ia import consultar_claude

KEYWORDS = {
    "envio":          ["envio", "envío", "llega", "despacho", "correo", "manda", "cuando llega"],
    "stock":          ["stock", "disponible", "hay", "tienen", "queda"],
    "garantia":       ["garantia", "garantía", "falla", "roto", "defecto", "problema"],
    "factura":        ["factura", "factur", "comprobante", "ticket"],
    "mayor":          ["mayor", "mayorista", "por mayor", "cantidad", "varios"],
    "original":       ["original", "genuino", "legitimo", "legítimo", "trucho", "falso"],
    "demora":         ["demora", "tarda", "dias", "días", "tiempo"],
    "retiro":         ["retiro", "buscar", "paso a buscar", "pickup"],
    "precio_especial":["descuento", "rebaja", "más barato", "oferta", "precio especial"],
    "reclamo":        ["reclamo", "queja", "mal", "no funciona", "no sirve"],
    "cambio":         ["cambio", "cambiar", "cambié"],
    "devolucion":     ["devolucion", "devolución", "devolver", "reembolso"],
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

def generar_respuesta_con_ia(pregunta, producto_nombre, precio, stock):
    prompt = f"""
Contexto del negocio:
{CONTEXTO_NEGOCIO}

Un comprador hizo esta pregunta en MercadoLibre sobre el producto "{producto_nombre}":
"{pregunta}"

Precio actual: ${precio:,}
Stock disponible: {stock} unidades

Escribí una respuesta natural, amigable y profesional.
- Máximo 3 oraciones
- No uses emojis en exceso
- No ofrezcas descuentos ni condiciones especiales
- Si no tenés certeza de algo, decí que lo vas a consultar
- Empezá con "¡Hola!" 
"""
    return consultar_claude(prompt, max_tokens=200)

def consultar_al_dueno(pregunta_id, texto, item_id, producto_nombre):
    enviar_mensaje(
        f"❓ <b>PREGUNTA REQUIERE TU RESPUESTA</b>\n\n"
        f"Producto: {producto_nombre}\n"
        f"Pregunta: {texto}\n\n"
        f"Respondé en ML y después confirmame acá con:\n"
        f"/respondida {pregunta_id}"
    )
    print(f"📤 Escalada al dueño: '{texto[:50]}'")

def escalar_sin_categoria(pregunta_id, texto, item_id, producto_nombre):
    # Claude intenta igual, pero avisa al dueño también
    respuesta_ia = generar_respuesta_con_ia(
        texto, producto_nombre,
        precio=0, stock=0
    )
    if respuesta_ia:
        enviar_mensaje(
            f"🤖 <b>PREGUNTA RESPONDIDA CON IA</b>\n\n"
            f"Producto: {producto_nombre}\n"
            f"Pregunta: {texto}\n\n"
            f"Respuesta enviada:\n{respuesta_ia}\n\n"
            f"Si querés corregirla, respondé manualmente en ML."
        )
        return respuesta_ia
    else:
        enviar_mensaje(
            f"❓ <b>PREGUNTA SIN RESPONDER</b>\n\n"
            f"Producto: {producto_nombre}\n"
            f"Pregunta: {texto}\n\n"
            f"👉 Respondé manualmente en ML"
        )
        return None

def get_info_producto(item_id):
    for p in PRODUCTOS:
        if p.get("id") == item_id:
            return p
    return {"nombre": item_id, "precio_min": 0, "precio_max": 0}

def procesar_preguntas():
    publicaciones = get_mis_publicaciones()
    total_respondidas = 0
    total_escaladas = 0

    for item_id in publicaciones:
        preguntas = get_preguntas_sin_responder(item_id)
        producto = get_info_producto(item_id)
        nombre = producto.get("nombre", item_id)
        precio = producto.get("precio_min", 0)
        stock = producto.get("stock_alerta", 0)

        for pregunta in preguntas:
            texto = pregunta.get("text", "")
            pregunta_id = pregunta["id"]
            categoria = detectar_categoria(texto)

            if categoria:
                regla = REGLAS_RESPUESTA.get(categoria, "AUTOMATICO")

                if regla == "CONSULTAR_DUEÑO":
                    # Le pregunta al dueño antes de responder
                    consultar_al_dueno(pregunta_id, texto, item_id, nombre)
                    total_escaladas += 1

                else:
                    # Claude genera la respuesta pensando
                    respuesta = generar_respuesta_con_ia(texto, nombre, precio, stock)
                    if respuesta:
                        responder_pregunta(pregunta_id, respuesta)
                        total_respondidas += 1
                        print(f"✅ Respondida con IA: '{texto[:50]}'")
                    else:
                        consultar_al_dueno(pregunta_id, texto, item_id, nombre)
                        total_escaladas += 1
            else:
                # Categoría desconocida — Claude intenta y avisa
                respuesta = escalar_sin_categoria(pregunta_id, texto, item_id, nombre)
                if respuesta:
                    responder_pregunta(pregunta_id, respuesta)
                    total_respondidas += 1
                else:
                    total_escaladas += 1

    if total_respondidas > 0 or total_escaladas > 0:
        print(f"✅ Respondidas: {total_respondidas} | 📤 Escaladas: {total_escaladas}")
