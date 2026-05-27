import schedule
import time
import os
from telegram_utils import enviar_mensaje

print("🤖 Iniciando MLVentasBot...")

# Conectar Sheets
try:
    from modulo_sheets import SheetsManager
    sheets = SheetsManager()
    print("✅ Google Sheets conectado")
except Exception as e:
    print(f"⚠️ Sheets no disponible: {e}")
    sheets = None

# Iniciar servidor webhook
try:
    from modulo_webhook import iniciar_servidor
    iniciar_servidor(puerto=int(os.getenv("PORT", 8080)))
    print("✅ Servidor webhook activo")
except Exception as e:
    print(f"⚠️ Webhook no disponible: {e}")

# Verificar token al arrancar
try:
    from modulo_auth import verificar_y_renovar
    verificar_y_renovar()
    print("✅ Token ML verificado")
except Exception as e:
    print(f"⚠️ Error verificando token: {e}")

enviar_mensaje(
    "🤖 <b>MLVentasBot activo</b>\n\n"
    "✅ Preguntas automáticas (IA)\n"
    "✅ Pricing dinámico (IA)\n"
    "✅ Monitor de stock\n"
    "✅ Campañas Product Ads (IA)\n"
    "✅ Post-venta automático (IA)\n"
    "✅ Propuestas de restock (IA)\n"
    "✅ Reportes semanales\n"
    "✅ Resumen diario de decisiones\n"
    "✅ OAuth y renovación de tokens\n"
    "✅ Monitor de salud del sistema\n"
    f"{'✅' if sheets else '⚠️'} Google Sheets\n\n"
    "Escribí /ayuda para ver todos los comandos."
)

# ── FUNCIÓN RESUMEN DIARIO ────────────────────────────────
def enviar_resumen_diario():
    from modulo_decisiones import get_decisiones, limpiar
    from modulo_ia import generar_resumen_diario
    decisiones = get_decisiones()
    if decisiones:
        resumen = generar_resumen_diario(decisiones)
        if resumen:
            enviar_mensaje(resumen)
    else:
        enviar_mensaje("📋 <b>Resumen del día</b>\n\nSin actividad registrada hoy.")
    limpiar()

# ── IMPORTS DE MÓDULOS ────────────────────────────────────
from modulo_preguntas import procesar_preguntas
from modulo_pricing import procesar_precios
from modulo_stock import verificar_stock
from modulo_reporte import generar_reporte
from modulo_campanas import analizar_campanas
from modulo_postventa import procesar_postventa
from modulo_restock import proponer_restock
from modulo_monitor import verificar_sistema
from modulo_auth import verificar_y_renovar

# ── SCHEDULES ─────────────────────────────────────────────
schedule.every(5).minutes.do(procesar_preguntas)
schedule.every(5).minutes.do(procesar_postventa)
schedule.every(2).hours.do(verificar_stock)
schedule.every(2).hours.do(verificar_y_renovar)
schedule.every(4).hours.do(procesar_precios)
schedule.every(6).hours.do(verificar_sistema)
schedule.every().day.at("11:00").do(analizar_campanas)
schedule.every().day.at("14:00").do(proponer_restock)
schedule.every().day.at("00:00").do(enviar_resumen_diario)
schedule.every().monday.at("12:00").do(generar_reporte)

print("\n📅 Schedules activos:")
print("   c/5 min  → preguntas + post-venta")
print("   c/2 hs   → stock + token renewal")
print("   c/4 hs   → pricing")
print("   c/6 hs   → monitor sistema")
print("   8am ARG  → campañas")
print("   11am ARG → restock")
print("   9pm ARG  → resumen del día")
print("   Lunes 9am → reporte semanal\n")

# ── LOOP PRINCIPAL ────────────────────────────────────────
while True:
    schedule.run_pending()
    from modulo_telegram_bot import escuchar_comandos
    escuchar_comandos(sheets_service=sheets)
    time.sleep(3)
