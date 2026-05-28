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
        "id": os.getenv("ML_ID_MIC", ""),
        "codigo_uli": "AUMICOK8",
        "nombre": "Micrófono corbatero inalámbrico",
        "costo": 5115,
        "precio_min": 10000,
        "precio_max": 15000,
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

# Reglas de comportamiento para Claude
# En lugar de respuestas fijas, Claude usa estas reglas para pensar cada respuesta
REGLAS_RESPUESTA = {
    "envio": "AUTOMATICO",        # Claude responde solo
    "stock": "AUTOMATICO",        # Claude responde solo
    "garantia": "AUTOMATICO",     # Claude responde solo
    "original": "AUTOMATICO",     # Claude responde solo
    "demora": "AUTOMATICO",       # Claude responde solo
    "retiro": "AUTOMATICO",       # Claude responde solo
    "factura": "CONSULTAR_DUEÑO", # Le pregunta al dueño antes de responder
    "mayor": "CONSULTAR_DUEÑO",   # Le pregunta al dueño antes de responder
    "precio_especial": "CONSULTAR_DUEÑO",
    "reclamo": "CONSULTAR_DUEÑO",
    "cambio": "CONSULTAR_DUEÑO",
    "devolucion": "CONSULTAR_DUEÑO",
}

# Contexto del negocio que Claude usa para pensar cada respuesta
CONTEXTO_NEGOCIO = """
Vendés accesorios tecnológicos en MercadoLibre Argentina.
Productos: cables USB-C, hubs, cables HDMI, micrófonos y mini impresoras.
Trabajás con Mercado Envíos — entregas en 2 a 5 días hábiles según la zona.
Garantía de 90 días en todos los productos.
No hacés retiro en persona — solo envíos.
No des descuentos ni precios especiales sin consultar al dueño.
Tono: profesional, amigable, directo. Máximo 3 oraciones por respuesta.
"""

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
                    p["activo"] = True
                    if ps.get("id"):
                        p["id"] = ps["id"]
                    break
        print("✅ Productos sincronizados desde Sheets")
    except Exception as e:
        print(f"⚠️ No se pudo sincronizar desde Sheets: {e}")
