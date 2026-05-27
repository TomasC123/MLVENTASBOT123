# ============================================
# CONFIGURACIÓN — completar antes de deployar
# ============================================

TELEGRAM_TOKEN = "TU_TOKEN_AQUI"        # El token nuevo de BotFather
TELEGRAM_CHAT_ID = "7412313894"         # Tu Chat ID

ML_CLIENT_ID = "TU_ML_CLIENT_ID"        # De developers.mercadolibre.com
ML_CLIENT_SECRET = "TU_ML_CLIENT_SECRET"
ML_ACCESS_TOKEN = "TU_ML_ACCESS_TOKEN"  # Se genera con OAuth

# ============================================
# PRODUCTOS — completar con tus IDs de ML
# (los obtenés cuando publiques)
# ============================================
PRODUCTOS = [
    {
        "id": "MLA_CABLE_USBC",           # Reemplazar con ID real de ML
        "nombre": "Cable USB-C a USB-C",
        "costo": 3333,
        "precio_min": 6500,               # Nunca bajar de acá
        "precio_max": 9000,               # Nunca subir de acá
        "stock_alerta": 5,                # Alertar cuando queden menos de X
    },
    {
        "id": "MLA_HUB_7EN1",
        "nombre": "Hub USB-C 7 en 1",
        "costo": 6200,
        "precio_min": 13000,
        "precio_max": 20000,
        "stock_alerta": 3,
    },
    {
        "id": "MLA_CABLE_HDMI",
        "nombre": "Cable USB-C a HDMI 4K",
        "costo": 7285,
        "precio_min": 15000,
        "precio_max": 22000,
        "stock_alerta": 2,
    },
    {
        "id": "MLA_MICROFONO",
        "nombre": "Micrófono corbatero",
        "costo": 5115,
        "precio_min": 10000,
        "precio_max": 16000,
        "stock_alerta": 2,
    },
    {
        "id": "MLA_IMPRESORA",
        "nombre": "Mini impresora térmica",
        "costo": 15190,
        "precio_min": 28000,
        "precio_max": 42000,
        "stock_alerta": 1,
    },
]

# ============================================
# RESPUESTAS AUTOMÁTICAS A PREGUNTAS
# ============================================
RESPUESTAS = {
    "envio": "¡Hola! Sí, hacemos envíos a todo el país a través de Mercado Envíos. El tiempo estimado es de 2 a 5 días hábiles según tu zona. ¡Cualquier consulta estamos a disposición!",
    "stock": "¡Hola! Sí, tenemos stock disponible. Podés comprarlo ahora mismo. ¡Saludos!",
    "garantia": "¡Hola! El producto tiene garantía de 90 días por defecto del fabricante. Ante cualquier problema nos contactás y lo resolvemos. ¡Saludos!",
    "factura": "¡Hola! Sí, emitimos factura electrónica con cada compra. ¡Saludos!",
    "mayor": "¡Hola! Por compras mayoristas escribinos por mensaje privado para coordinar precio especial. ¡Saludos!",
    "original": "¡Hola! Todos nuestros productos son originales y de calidad garantizada. ¡Saludos!",
    "demora": "¡Hola! El tiempo de envío es de 2 a 5 días hábiles según tu zona. ¡Saludos!",
    "retiro": "¡Hola! Por el momento solo trabajamos con envíos a domicilio via Mercado Envíos. ¡Saludos!",
}

# Horario del reporte semanal (lunes 9am Argentina = UTC-3)
REPORTE_DIA = "monday"
REPORTE_HORA = 9
