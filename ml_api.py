import requests
from modulo_auth import get_access_token

BASE = "https://api.mercadolibre.com"

def get_headers():
    return {"Authorization": f"Bearer {get_access_token()}"}

HEADERS = get_headers()

def get_mis_publicaciones():
    r = requests.get(f"{BASE}/users/me/items/search", headers=get_headers())
    return r.json().get("results", [])

def get_publicacion(item_id):
    r = requests.get(f"{BASE}/items/{item_id}", headers=get_headers())
    return r.json()

def get_preguntas_sin_responder(item_id):
    r = requests.get(
        f"{BASE}/questions/search?item={item_id}&status=UNANSWERED",
        headers=HEADERS
    )
    return r.json().get("questions", [])

def responder_pregunta(question_id, texto):
    r = requests.post(
        f"{BASE}/answers",
        headers=HEADERS,
        json={"question_id": question_id, "text": texto}
    )
    return r.json()

def actualizar_precio(item_id, precio_nuevo):
    r = requests.put(
        f"{BASE}/items/{item_id}",
        headers=HEADERS,
        json={"price": precio_nuevo}
    )
    return r.json()

def get_ventas_recientes():
    r = requests.get(
        f"{BASE}/orders/search?seller=me&sort=date_desc",
        headers=HEADERS
    )
    return r.json().get("results", [])

def get_competidores(query, limite=10):
    r = requests.get(
        f"{BASE}/sites/MLA/search?q={query}&limit={limite}",
        headers=HEADERS
    )
    return r.json().get("results", [])

def get_reputacion():
    r = requests.get(f"{BASE}/users/me", headers=get_headers())
    data = r.json()
    rep = data.get("seller_reputation", {})
    return {
        "nivel": rep.get("level_id", "N/A"),
        "transacciones": rep.get("transactions", {}).get("total", 0),
        "calificacion": rep.get("transactions", {}).get("ratings", {}).get("positive", 0)
    }
