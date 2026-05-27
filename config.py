import os

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

ML_CLIENT_ID = os.getenv("ML_CLIENT_ID", "")
ML_CLIENT_SECRET = os.getenv("ML_CLIENT_SECRET", "")
ML_ACCESS_TOKEN = os.getenv("ML_ACCESS_TOKEN", "")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "")

PRODUCTOS = [
    {
        "id": os.getenv("ML_ID_CABLE", "MLA_CABLE_USBC"),
        "codigo_uli": "AUCATCAC",
        "nombre": "Cable USB-C a USB-C carga rápida",
        "costo": 3333,
        "precio_min": 6500,
        "precio_max": 8500,
        "stock_alerta": 5,
    },
    {
        "id": os.getenv("ML_ID_HUB", "MLA_HUB_7EN1"),
        "codigo_uli": "AUHUB271",
        "nombre": "Hub USB-C 7 en 1 aluminio",
        "costo": 6200,
        "precio_min": 12000,
        "precio_max": 18000,
        "stock_alerta": 3,
    },
    {
        "id": os.getenv("ML_ID_HDMI", "MLA_CABLE_HDMI"),
        "codigo_uli": "AUCHDMI2",
        "nombre": "Cable USB-C a HDMI 4K 2m",
        "costo": 7285,
        "precio_min": 14000,
        "precio_max": 20000,
        "stock_alerta": 2,
    },
    {
        "id": os.getenv("ML_ID_MIC", "MLA_MICROFONO"),
        "codigo_uli": "AUMICOK8",
        "nombre": "Micrófono corbatero inalámbrico",
        "costo": 5115,
        "precio_min": 10000,
        "precio_max": 15000,
        "stock_alerta": 2,
    },
    {
        "id": os.getenv("ML_ID_IMP", "MLA_IMPRESORA"),
        "codigo_uli": "AUIMPTMI",
        "nombre": "Mini impresora térmica portátil",
        "costo": 15190,
        "precio_min": 29000,
        "precio_max": 40000,
        "stock_alerta": 1,
    },
]

RESPUESTAS = {
    "envio": "¡Hola! Sí, hacemos envíos a todo el país a través de Mercado Envíos. El tiempo estimado es de 2 a 5 días hábiles según tu zona. ¡Cualquier consulta estamos a disposición!",
    "stock": "¡Hola! Sí, tenemos stock disponible. Podés comprarlo ahora mismo. ¡Saludos!",
    "garantia": "¡Hola! El producto tiene garantía de 90 días. Ante cualquier problema nos contactás y lo resolvemos. ¡Saludos!",
    "factura": "¡Hola! Sí, emitimos factura electrónica con cada compra. ¡Saludos!",
    "mayor": "¡Hola! Por compras mayoristas escribinos por mensaje privado para coordinar precio especial. ¡Saludos!",
    "original": "¡Hola! Todos nuestros productos son originales y de calidad garantizada. ¡Saludos!",
    "demora": "¡Hola! El tiempo de envío es de 2 a 5 días hábiles según tu zona. ¡Saludos!",
    "retiro": "¡Hola! Por el momento solo trabajamos con envíos a domicilio via Mercado Envíos. ¡Saludos!",
}

REPORTE_DIA = "monday"
REPORTE_HORA = 9
