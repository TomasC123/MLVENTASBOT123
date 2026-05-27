import requests
import os
from telegram_utils import enviar_mensaje
from modulo_decisiones import registrar

def verificar_sistema():
    errores = []

    # 1. Verificar token ML
    try:
        from modulo_auth import verificar_y_renovar, get_access_token
        token_ok = verificar_y_renovar()
        if not token_ok:
            errores.append("Token ML vencido o inválido")
    except Exception as e:
        errores.append(f"Error de autenticación ML: {e}")

    # 2. Verificar API ML
    try:
        token = get_access_token()
        r = requests.get(
            "https://api.mercadolibre.com/users/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        if r.status_code != 200:
            errores.append(f"API ML respondió {r.status_code}")
    except Exception as e:
        errores.append(f"API ML no responde: {e}")

    # 3. Verificar Claude API
    try:
        from modulo_ia import consultar_claude
        test = consultar_claude("Responde solo: OK", max_tokens=10)
        if not test or "OK" not in test.upper():
            errores.append("Claude API no responde correctamente")
    except Exception as e:
        errores.append(f"Claude API error: {e}")

    # 4. Verificar Google Sheets
    try:
        from modulo_sheets import SheetsManager
        sheets = SheetsManager()
        sheets.leer_productos()
    except Exception as e:
        errores.append(f"Google Sheets error: {e}")

    if errores:
        msg = "🚨 <b>ALERTA DEL SISTEMA</b>\n\n"
        for err in errores:
            msg += f"❌ {err}\n"
        msg += "\nAlgunos módulos pueden no estar funcionando correctamente."
        enviar_mensaje(msg)
        registrar("SISTEMA", "monitor", f"{len(errores)} errores detectados")
    else:
        print("✅ Sistema OK — todos los servicios responden")
