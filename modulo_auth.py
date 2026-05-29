import requests
import json
import os
from datetime import datetime, timedelta
from telegram_utils import enviar_mensaje

BASE = "https://api.mercadolibre.com"
TOKEN_FILE = "ml_tokens.json"

def actualizar_variables_railway(access_token, refresh_token):
    """Guarda los tokens como variables de entorno en Railway para que persistan."""
    railway_token = os.getenv("RAILWAY_TOKEN")
    service_id = os.getenv("RAILWAY_SERVICE_ID")
    
    if not railway_token or not service_id:
        print("⚠️ RAILWAY_TOKEN o RAILWAY_SERVICE_ID no configurados")
        return False

    query = """
    mutation upsertVariables($serviceId: String!, $environmentId: String, $variables: VariableInput!) {
        variableCollectionUpsert(input: {
            serviceId: $serviceId,
            environmentId: $environmentId,
            variables: $variables
        })
    }
    """
    
    try:
        r = requests.post(
            "https://backboard.railway.app/graphql/v2",
            headers={
                "Authorization": f"Bearer {railway_token}",
                "Content-Type": "application/json"
            },
            json={
                "query": query,
                "variables": {
                    "serviceId": service_id,
                    "variables": {
                        "ML_ACCESS_TOKEN": access_token,
                        "ML_REFRESH_TOKEN": refresh_token
                    }
                }
            },
            timeout=15
        )
        data = r.json()
        if "errors" not in data:
            print("✅ Tokens actualizados en Railway")
            return True
        else:
            print(f"⚠️ Error actualizando Railway: {data['errors']}")
            return False
    except Exception as e:
        print(f"⚠️ No se pudo actualizar Railway: {e}")
        return False

def guardar_tokens(access_token, refresh_token, expires_in=21600):
    data = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_at": (datetime.now() + timedelta(seconds=expires_in)).isoformat()
    }
    with open(TOKEN_FILE, "w") as f:
        json.dump(data, f)
    print(f"✅ Tokens guardados. Vencen: {data['expires_at']}")
    # También guardar en Railway para que persistan ante reinicios
    actualizar_variables_railway(access_token, refresh_token)

def cargar_tokens():
    try:
        with open(TOKEN_FILE, "r") as f:
            return json.load(f)
    except:
        pass
    access_token = os.getenv("ML_ACCESS_TOKEN", "")
    refresh_token = os.getenv("ML_REFRESH_TOKEN", "")
    if access_token and refresh_token:
        print("📦 Tokens cargados desde variables de entorno")
        guardar_tokens(access_token, refresh_token, expires_in=21600)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_at": (datetime.now() + timedelta(seconds=21600)).isoformat()
        }
    return None

def token_por_vencer(margen_minutos=30):
    tokens = cargar_tokens()
    if not tokens:
        return True
    expires_at = datetime.fromisoformat(tokens["expires_at"])
    return datetime.now() >= expires_at - timedelta(minutes=margen_minutos)

def get_access_token():
    tokens = cargar_tokens()
    if tokens:
        return tokens["access_token"]
    return os.getenv("ML_ACCESS_TOKEN", "")

def renovar_token():
    tokens = cargar_tokens()
    if not tokens or not tokens.get("refresh_token"):
        print("⚠️ Sin refresh token disponible")
        enviar_mensaje(
            "⚠️ <b>Token ML vencido</b>\n\n"
            "El Access Token venció y no hay refresh token.\n"
            "Escribí /reautenticar para reconectar."
        )
        return False

    client_id = os.getenv("ML_CLIENT_ID")
    client_secret = os.getenv("ML_CLIENT_SECRET")
    refresh_token = tokens["refresh_token"]

    try:
        r = requests.post(
            f"{BASE}/oauth/token",
            data={
                "grant_type": "refresh_token",
                "client_id": client_id,
                "client_secret": client_secret,
                "refresh_token": refresh_token
            },
            timeout=15
        )
        data = r.json()

        if "access_token" in data:
            guardar_tokens(
                data["access_token"],
                data.get("refresh_token", refresh_token),
                data.get("expires_in", 21600)
            )
            print("✅ Token renovado exitosamente")
            enviar_mensaje("🔄 <b>Token ML renovado automáticamente</b>")
            return True
        else:
            print(f"❌ Error renovando token: {data}")
            enviar_mensaje(
                f"❌ <b>Error renovando token ML</b>\n\n"
                f"Error: {data.get('message', 'desconocido')}\n"
                f"Escribí /reautenticar para reconectar."
            )
            return False

    except Exception as e:
        print(f"❌ Excepción renovando token: {e}")
        enviar_mensaje(f"❌ <b>Error de conexión renovando token</b>\n{str(e)}")
        return False

def verificar_y_renovar():
    if token_por_vencer(margen_minutos=30):
        print("🔄 Token por vencer — renovando...")
        return renovar_token()
    print("✅ Token ML verificado")
    return True

def get_url_autenticacion():
    client_id = os.getenv("ML_CLIENT_ID")
    redirect_uri = os.getenv("ML_REDIRECT_URI", "https://mlventasbot.up.railway.app/callback")
    return (
        f"https://auth.mercadolibre.com.ar/authorization"
        f"?response_type=code"
        f"&client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
    )

def autenticar_con_codigo(codigo):
    client_id = os.getenv("ML_CLIENT_ID")
    client_secret = os.getenv("ML_CLIENT_SECRET")
    redirect_uri = os.getenv("ML_REDIRECT_URI", "https://mlventasbot.up.railway.app/callback")

    print(f"🔑 Autenticando con código: {codigo[:20]}...")

    try:
        r = requests.post(
            f"{BASE}/oauth/token",
            data={
                "grant_type": "authorization_code",
                "client_id": client_id,
                "client_secret": client_secret,
                "code": codigo,
                "redirect_uri": redirect_uri
            },
            timeout=15
        )
        data = r.json()

        if "access_token" in data:
            guardar_tokens(
                data["access_token"],
                data.get("refresh_token", ""),
                data.get("expires_in", 21600)
            )
            print("✅ Access Token guardado exitosamente")
            enviar_mensaje("✅ <b>Autenticación exitosa</b>\n\nEl sistema está conectado a tu cuenta de ML.")
            return True
        else:
            print(f"❌ Error OAuth: {data}")
            enviar_mensaje(f"❌ Error de autenticación ML: {data}")
            return False

    except Exception as e:
        print(f"❌ Excepción OAuth: {e}")
        enviar_mensaje(f"❌ Error de conexión: {str(e)}")
        return False

def autenticar_si_hay_codigo():
    codigo = os.getenv("ML_AUTH_CODE", "")
    if not codigo:
        return False
    print("🔑 Código de autorización detectado, obteniendo Access Token...")
    return autenticar_con_codigo(codigo)
