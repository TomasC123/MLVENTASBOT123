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
        "id": os.getenv("ML_ID_CABLE", ""),
        "codigo_uli": "AUCATCAC",
        "nombre": "Cable USB-C a USB-C carga rápida",
        "costo": 3333,
        "precio_min": 5500,
        "precio_max": 8500,
        "stock_alerta": 5,
        "activo": True,
    },
    {
        "id": os.getenv("ML_ID_MIC", ""),
        "codigo_uli": "AUMICOK8",
        "nombre": "Micrófono Corbatero Inalámbrico K8",
        "costo": 5115,
        "precio_min": 10000,
        "precio_max": 15000,
        "stock_alerta": 2,
        "activo": True,
    },
    {
        "id": os.getenv("ML_ID_HUB", ""),
        "codigo_uli": "AUHUB271",
        "nombre": "Hub USB-C 7 en 1 aluminio",
        "costo": 6200,
        "precio_min": 12000,
        "precio_max": 18000,
        "stock_alerta": 3,
        "activo": False,
    },
    {
        "id": os.getenv("ML_ID_HDMI", ""),
        "codigo_uli": "AUCHDMI2",
        "nombre": "Cable USB-C a HDMI 4K 2m",
        "costo": 7285,
        "precio_min": 14000,
        "precio_max": 20000,
        "stock_alerta": 2,
        "activo": False,
    },
    {
        "id": os.getenv("ML_ID_IMP", ""),
        "codigo_uli": "AUIMPTMI",
        "nombre": "Mini impresora térmica portátil",
        "costo": 15190,
        "precio_min": 29000,
        "precio_max": 40000,
        "stock_alerta": 1,
        "activo": False,
    },
]

CONTEXTO_NEGOCIO = """
Sos el asistente de ventas de una tienda en MercadoLibre Argentina.
Respondés preguntas de compradores con información real y precisa.
Nunca inventés datos. Si no sabés algo con certeza, decí que lo vas a consultar.

═══════════════════════════════════
PRODUCTO 1: Cable USB-C a USB-C carga rápida
═══════════════════════════════════
Marca: Samsung (diseño Samsung, fabricado en China)
Modelo: USB Type-C to Type-C 3A
Color: Negro
Largo: 1 metro
Carga rápida: Sí, 3A — carga más rápido que el cable original de la caja
Transferencia de datos: Sí, alta velocidad

Compatibilidad:
- Samsung Galaxy serie S, A y Note
- Motorola Edge y serie G
- Xiaomi, Redmi, OPPO y cualquier celular con USB-C
- iPad Pro y MacBook Air/Pro
- Nintendo Switch
- Cualquier dispositivo con entrada USB-C

Preguntas frecuentes:
- ¿Es compatible con iPhone? Solo iPhone 15 en adelante (USB-C). iPhone 14 y anteriores NO porque usan Lightning.
- ¿Carga rápido? Sí, soporta carga rápida 3A.
- ¿Sirve para Samsung? Sí, compatible con toda la línea Galaxy.
- ¿Qué largo tiene? 1 metro.
- ¿De qué color es? Negro.
- ¿Se puede usar para transferir datos? Sí.

Garantía: 30 días. Si falla, lo resolvemos.

═══════════════════════════════════
PRODUCTO 2: Micrófono Corbatero Inalámbrico K8
═══════════════════════════════════
Marca: Lambo Tech
Modelo: K8
Color: Negro
Tipo: Corbatero inalámbrico — se prende en la ropa

Conexión: Plug & play — enchufás al celular y grabás. Sin Bluetooth, sin apps, sin configuración.
- Para Android (USB-C): cualquier celular Samsung, Motorola, Xiaomi, OPPO con USB-C
- Para iPhone hasta 14: conector Lightning incluido
- Para iPhone 15 en adelante: conector USB-C incluido
- Para iPad y tablets con USB-C

Alcance inalámbrico: 20 metros
Frecuencia: 50Hz a 16kHz
Reducción de ruido ambiental: Sí
Delay: Sin delay perceptible

Ideal para:
- Lives en Instagram, TikTok y YouTube
- Videos cortos, vlogs y reels
- Entrevistas y grabaciones en movimiento
- Clases online y reuniones

Preguntas frecuentes:
- ¿Tiene Bluetooth? NO. Se conecta directo al puerto del celular, sin Bluetooth.
- ¿Es compatible con iPhone? Sí, con todos los iPhone. Incluye adaptador Lightning (hasta iPhone 14) y USB-C (iPhone 15+).
- ¿Necesita app? No, es plug & play — enchufás y funciona.
- ¿Qué alcance tiene? 20 metros.
- ¿Graba bien en exteriores? Sí, reduce el ruido ambiental.
- ¿Se nota en la ropa? Es pequeño y discreto, apenas se nota.
- ¿Sirve para Samsung? Sí, cualquier Samsung con USB-C.

Garantía: 30 días. Si falla, lo resolvemos.

═══════════════════════════════════
POLÍTICAS DE LA TIENDA
═══════════════════════════════════
- Envíos a todo el país por Mercado Envíos, 2 a 5 días hábiles
- No hacemos retiro en persona
- No damos descuentos ni precios especiales sin autorización
- Garantía 30 días en todos los productos
- Tono: amigable, profesional, directo. Máximo 3 oraciones por respuesta.
- Empezá siempre con "¡Hola!"
"""

REGLAS_RESPUESTA = {
    "envio":           "AUTOMATICO",
    "stock":           "AUTOMATICO",
    "garantia":        "AUTOMATICO",
    "original":        "AUTOMATICO",
    "demora":          "AUTOMATICO",
    "retiro":          "AUTOMATICO",
    "factura":         "CONSULTAR_DUEÑO",
    "mayor":           "CONSULTAR_DUEÑO",
    "precio_especial": "CONSULTAR_DUEÑO",
    "reclamo":         "CONSULTAR_DUEÑO",
    "cambio":          "CONSULTAR_DUEÑO",
    "devolucion":      "CONSULTAR_DUEÑO",
}

REPORTE_DIA = "monday"
REPORTE_HORA = 9

def sincronizar_desde_sheets():
    try:
        from modulo_sheets import SheetsManager
        sheets = SheetsManager()
        productos_sheets = sheets.leer_productos()
        for ps in productos_sheets:
            for p in PRODUCTOS:
                if p["codigo_uli"] == ps["codigo_uli"]:
                    p["costo"] = ps["costo"]
                    p["precio_min"] = ps["precio_min"]
                    p["precio_max"] = ps["precio_max"]
                    p["stock_alerta"] = ps["stock_alerta"]
                    if ps.get("id"):
                        p["id"] = ps["id"]
                    if ps.get("activo") is not None:
                        p["activo"] = ps["activo"]
                    break
        print("✅ Productos sincronizados desde Sheets")
    except Exception as e:
        print(f"⚠️ No se pudo sincronizar desde Sheets: {e}")
