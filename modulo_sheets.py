import gspread
from google.oauth2.service_account import Credentials
import json
import os

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "TU_SHEET_ID_AQUI")

class SheetsManager:
    def __init__(self):
        creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
        if creds_json:
            creds_dict = json.loads(creds_json)
            creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        else:
            creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)

        self.client = gspread.authorize(creds)
        self.sheet = self.client.open_by_key(SHEET_ID)

    def leer_productos(self):
        ws = self.sheet.worksheet("⚙️ Productos")
        rows = ws.get_all_records()
        productos = []
        for r in rows:
            if r.get("Activo") == "SI":
                productos.append({
                    "id": r.get("ID MercadoLibre", ""),
                    "codigo_uli": r.get("Código ULI", ""),
                    "nombre": r.get("Producto", ""),
                    "costo": int(r.get("Costo ($)", 0)),
                    "precio_min": int(r.get("Precio Mín ($)", 0)),
                    "precio_max": int(r.get("Precio Máx ($)", 0)),
                    "stock_alerta": int(r.get("Stock Alerta", 3)),
                })
        return productos

    def actualizar_rango(self, codigo_uli, precio_min, precio_max):
        ws = self.sheet.worksheet("⚙️ Productos")
        records = ws.get_all_records()
        for i, r in enumerate(records, 2):
            if r.get("Código ULI") == codigo_uli:
                ws.update_cell(i, 5, precio_min)
                ws.update_cell(i, 6, precio_max)
                break

    def actualizar_estado(self, codigo_uli, estado):
        ws = self.sheet.worksheet("⚙️ Productos")
        records = ws.get_all_records()
        for i, r in enumerate(records, 2):
            if r.get("Código ULI") == codigo_uli:
                ws.update_cell(i, 1, estado)
                break

    def registrar_venta(self, fecha, producto, unidades, precio_venta, costo, id_orden):
        ws = self.sheet.worksheet("📦 Ventas")
        margen = (precio_venta - costo) * unidades
        margen_pct = (precio_venta - costo) / precio_venta if precio_venta > 0 else 0
        ws.append_row([
            fecha, producto, unidades,
            precio_venta, costo, margen,
            f"{margen_pct:.1%}", id_orden
        ])

    def actualizar_reporte(self, datos):
        ws = self.sheet.worksheet("📊 Reporte")
        campos = [
            ("B4", datos.get("semana", "")),
            ("B5", datos.get("ventas", 0)),
            ("B6", datos.get("ingresos", 0)),
            ("B7", datos.get("margen", 0)),
            ("B8", datos.get("mejor_producto", "")),
            ("B9", datos.get("reputacion", "")),
            ("B10", datos.get("preguntas_auto", 0)),
            ("B11", datos.get("ajustes_precio", 0)),
            ("B12", datos.get("alertas_stock", 0)),
        ]
        for celda, valor in campos:
            ws.update_acell(celda, valor)

    def leer_config(self):
        ws = self.sheet.worksheet("🔧 Configuración")
        records = ws.get_all_records()
        config = {}
        for r in records:
            if r.get("Unnamed: 0") and r.get("Unnamed: 1"):
                config[r["Unnamed: 0"]] = r["Unnamed: 1"]
        return config
