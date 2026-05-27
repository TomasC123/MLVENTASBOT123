from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import threading
from modulo_preguntas import procesar_preguntas
from modulo_decisiones import registrar
from telegram_utils import enviar_mensaje, alerta_venta

class WebhookHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        # Callback OAuth de ML
        if "/callback" in self.path:
            from urllib.parse import urlparse, parse_qs
            from modulo_auth import autenticar_con_codigo
            query = parse_qs(urlparse(self.path).query)
            codigo = query.get("code", [None])[0]
            if codigo:
                autenticar_con_codigo(codigo)
                self._responder(200, "Autenticacion exitosa. Podes cerrar esta ventana.")
            else:
                self._responder(400, "Sin codigo de autorizacion.")
        else:
            self._responder(200, "MLVentasBot activo")

    def do_POST(self):
        # Notificaciones en tiempo real de ML
        if "/notifications" in self.path:
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length)
                data = json.loads(body)
                self._responder(200, "OK")
                threading.Thread(
                    target=procesar_notificacion,
                    args=(data,),
                    daemon=True
                ).start()
            except Exception as e:
                print(f"Error webhook: {e}")
                self._responder(500, "Error")
        else:
            self._responder(404, "Not found")

    def _responder(self, code, msg):
        self.send_response(code)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(msg.encode())

    def log_message(self, format, *args):
        pass  # Silenciar logs HTTP

def procesar_notificacion(data):
    topic = data.get("topic", "")
    resource = data.get("resource", "")

    print(f"📨 Notificación: {topic} — {resource}")

    if topic == "questions":
        procesar_preguntas()

    elif topic == "orders_v2":
        from ml_api import get_ventas_recientes
        ventas = get_ventas_recientes()
        if ventas:
            v = ventas[0]
            items = v.get("order_items", [])
            if items:
                producto = items[0].get("item", {}).get("title", "Producto")
                precio = v.get("total_amount", 0)
                comprador = v.get("buyer", {}).get("nickname", "Comprador")
                alerta_venta(producto, precio, comprador)
                registrar("VENTA", producto, f"${precio:,} — {comprador}")

    elif topic == "claims":
        enviar_mensaje(
            f"⚠️ <b>RECLAMO NUEVO</b>\n\n"
            f"Recurso: {resource}\n\n"
            f"Revisalo en ML y respondé. El sistema solo puede disculparse."
        )

    elif topic in ["shipments", "orders_feedback"]:
        pass

def iniciar_servidor(puerto=8080):
    servidor = HTTPServer(("0.0.0.0", puerto), WebhookHandler)
    print(f"🌐 Servidor webhook activo en puerto {puerto}")
    hilo = threading.Thread(target=servidor.serve_forever, daemon=True)
    hilo.start()
    return servidor
