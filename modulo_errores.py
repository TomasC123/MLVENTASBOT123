import traceback
import time
from functools import wraps
from telegram_utils import enviar_mensaje

# Contador de errores por módulo para no spamear
_errores = {}
_MAX_ALERTAS = 3
_COOLDOWN = 3600  # 1 hora entre alertas del mismo error

def alerta_error(modulo, error, critico=False):
    ahora = time.time()
    key = f"{modulo}:{str(error)[:50]}"

    if key in _errores:
        ultimo, count = _errores[key]
        if ahora - ultimo < _COOLDOWN and count >= _MAX_ALERTAS:
            print(f"⚠️ Error silenciado (ya avisé {count}x): {key}")
            return
        _errores[key] = (ahora, count + 1)
    else:
        _errores[key] = (ahora, 1)

    nivel = "🔴 CRÍTICO" if critico else "⚠️ Error"
    enviar_mensaje(
        f"{nivel} — <b>{modulo}</b>\n\n"
        f"<code>{str(error)[:200]}</code>\n\n"
        f"El sistema continúa operando."
    )

def con_manejo_errores(modulo, critico=False):
    """Decorator que captura errores y avisa por Telegram sin tirar el sistema."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                tb = traceback.format_exc()
                print(f"❌ Error en {modulo}: {e}\n{tb}")
                alerta_error(modulo, e, critico)
                return None
        return wrapper
    return decorator

def monitorear_sistema():
    """Chequeo de salud del sistema — corre cada hora."""
    from modulo_auth import verificar_token
    import requests

    problemas = []

    # 1. Verificar token ML
    try:
        if not verificar_token():
            problemas.append("Token ML inválido o vencido")
    except Exception as e:
        problemas.append(f"No se pudo verificar token ML: {e}")

    # 2. Verificar conexión a internet
    try:
        r = requests.get("https://api.mercadolibre.com/sites/MLA", timeout=5)
        if r.status_code != 200:
            problemas.append(f"API ML devuelve status {r.status_code}")
    except:
        problemas.append("Sin conexión a API ML")

    # 3. Verificar Anthropic API
    try:
        r = requests.get("https://api.anthropic.com", timeout=5)
        # Solo chequea que responda, no importa el status
    except:
        problemas.append("Sin conexión a Anthropic API")

    if problemas:
        msg = "⚠️ <b>Alerta del sistema</b>\n\n"
        for p in problemas:
            msg += f"• {p}\n"
        enviar_mensaje(msg)
        print(f"⚠️ Problemas detectados: {problemas}")
    else:
        print("✅ Sistema saludable")
