from ml_api import get_preguntas_sin_responder, responder_pregunta, get_mis_publicaciones
from telegram_utils import enviar_mensaje
from config import RESPUESTAS
import re

KEYWORDS = {
    "envio":    ["envio", "envío", "llega", "despacho", "correo", "manda", "cuando llega"],
    "stock":    ["stock", "disponible", "hay", "tienen", "queda"],
    "garantia": ["garantia", "garantía", "falla", "roto", "defecto", "problema"],
    "factura":  ["factura", "factur", "comprobante", "ticket"],
    "mayor":    ["mayor", "mayorista", "por mayor", "cantidad", "varios"],
    "original": ["original", "genuino", "legitimo", "legítimo", "trucho", "falso"],
    "demora":   ["demora", "tarda", "dias", "días", "tiempo"],
    "retiro":   ["retiro", "buscar", "paso a buscar", "pickup"],
}

def detectar_respuesta(texto):
    texto_lower = texto.lower()
    texto_lower = re.sub(r'[áàä]', 'a', texto_lower)
    texto_lower = re.sub(r'[éèë]', 'e', texto_lower)
    texto_lower = re.sub(r'[íìï]', 'i', texto_lower)
    texto_lower = re.sub(r'[óòö]', 'o', texto_lower)
    texto_lower = re.sub(r'[úùü]', 'u', texto_lower)

    for categoria, keywords in KEYWORDS.items():
        if any(kw in texto_lower for kw in keywords):
            return RESPUESTAS.get(categoria)
    return None

def procesar_preguntas():
    publicaciones = get_mis_publicaciones()
    total_respondidas = 0

    for item_id in publicaciones:
        preguntas = get_preguntas_sin_responder(item_id)
        for pregunta in preguntas:
            texto = pregunta.get("text", "")
            respuesta = detectar_respuesta(texto)

            if respuesta:
                responder_pregunta(pregunta["id"], respuesta)
                total_respondidas += 1
                print(f"✅ Respondida: '{texto[:50]}...'")
            else:
                # No supo responder — te avisa por Telegram
                enviar_mensaje(
                    f"❓ <b>PREGUNTA SIN RESPONDER</b>\n\n"
                    f"Producto: {item_id}\n"
                    f"Pregunta: {texto}\n\n"
                    f"👉 Respondé manualmente en ML"
                )
                print(f"⚠️ Sin respuesta automática: '{texto[:50]}'")

    if total_respondidas > 0:
        print(f"Total respondidas: {total_respondidas}")
