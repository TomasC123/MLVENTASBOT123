import requests
from modulo_auth import get_access_token

BASE = "https://api.mercadolibre.com"

def get_headers():
    return {"Authorization": f"Bearer {get_access_token()}"}

def get_mis_publicaciones():
    try:
        r = requests.get(f"{BASE}/users/me/items/search", headers=get_headers(), timeout=15)
        data = r.json()
        if "results" not in data:
            print(f"⚠️ get_mis_publicaciones error: {data}")
            return []
        return data["results"]
    except Exception as e:
        print(f"❌ get_mis_publicaciones excepción: {e}")
        return []

def get_publicacion(item_id):
    try:
        r = requests.get(f"{BASE}/items/{item_id}", headers=get_headers(), timeout=15)
        return r.json()
    except Exception as e:
        print(f"❌ get_publicacion excepción: {e}")
        return {}

def get_preguntas_sin_responder(item_id):
    try:
        r = requests.get(
            f"{BASE}/questions/search?item={item_id}&status=UNANSWERED",
            headers=get_headers(),
            timeout=15
        )
        data = r.json()
        if "questions" not in data:
            print(f"⚠️ get_preguntas error: {data}")
            return []
        return data["questions"]
    except Exception as e:
        print(f"❌ get_preguntas excepción: {e}")
        return []

def responder_pregunta(question_id, texto):
    try:
        r = requests.post(
            f"{BASE}/answers",
            headers=get_headers(),
            json={"question_id": question_id, "text": texto},
            timeout=15
        )
        return r.json()
    except Exception as e:
        print(f"❌ responder_pregunta excepción: {e}")
        return {}

def actualizar_precio(item_id, precio_nuevo):
    try:
        r = requests.put(
            f"{BASE}/items/{item_id}",
            headers=get_headers(),
            json={"price": precio_nuevo},
            timeout=15
        )
        data = r.json()
        if "id" not in data:
            print(f"⚠️ actualizar_precio error: {data}")
        return data
    except Exception as e:
        print(f"❌ actualizar_precio excepción: {e}")
        return {}

def get_ventas_recientes():
    try:
        r = requests.get(
            f"{BASE}/orders/search?seller=me&sort=date_desc",
            headers=get_headers(),
            timeout=15
        )
        data = r.json()
        if "results" not in data:
            print(f"⚠️ get_ventas error: {data}")
            return []
        return data["results"]
    except Exception as e:
        print(f"❌ get_ventas excepción: {e}")
        return []

def get_competidores(query, limite=10):
    try:
        r = requests.get(
            f"{BASE}/sites/MLA/search?q={query}&limit={limite}",
            headers=get_headers(),
            timeout=15
        )
        data = r.json()
        return data.get("results", [])
    except Exception as e:
        print(f"❌ get_competidores excepción: {e}")
        return []

def get_reputacion():
    try:
        r = requests.get(f"{BASE}/users/me", headers=get_headers(), timeout=15)
        data = r.json()
        rep = data.get("seller_reputation", {})
        return {
            "nivel": rep.get("level_id", "N/A"),
            "transacciones": rep.get("transactions", {}).get("total", 0),
            "calificacion": rep.get("transactions", {}).get("ratings", {}).get("positive", 0)
        }
    except Exception as e:
        print(f"❌ get_reputacion excepción: {e}")
        return {"nivel": "N/A", "transacciones": 0, "calificacion": 0}
