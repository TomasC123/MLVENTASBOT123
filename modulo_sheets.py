import gspread
from google.oauth2.service_account import Credentials
import json
import os

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "TU_SHEET_ID_AQUI")

# Columnas por posición (1-indexed)
COL_ACTIVO = 1
COL_CODIGO_ULI = 2
COL_PRODUCTO = 3
COL_COSTO = 4
COL_PRECIO_MIN = 5
COL_PRECIO_MAX = 6
COL_STOCK_ALERTA = 7
COL_ID_ML = 8
COL_PRECIO_ACTUAL = 9
COL_MARGEN_MIN = 10

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
        try:
            ws = self.sheet.worksheet("⚙️ Productos")
            rows = ws.get_all_values()
            productos = []
            for r in rows[1:]:  # Saltamos la fila de headers
                if len(r) < 8:
                    continue
                try:
                    productos.append({
                        "activo": r[COL_ACTIVO-1].strip().upper() == "SI",
                        "codigo_uli": r[COL_CODIGO_ULI-1].strip(),
                        "nombre": r[COL_PRODUCTO-1].strip(),
                        "costo": int(str(r[COL_COSTO-1]).replace("$","").replace(".","").replace(",","").strip() or 0),
                        "precio_min": int(str(r[COL_PRECIO_MIN-1]).replace("$","").replace(".","").replace(",","").strip() or 0),
                        "precio_max": int(str(r[COL_PRECIO_MAX-1]).replace("$","").replace(".","").replace(",","").strip() or 0),
                        "stock_alerta": int(str(r[COL_STOCK_ALERTA-1]).strip() or 3),
                        "id": r[COL_ID_ML-1].strip(),
                    })
                except Exception as e:
                    print(f"⚠️ Error leyendo fila: {r} — {e}")
                    continue
            return productos
        except Exception as e:
            print(f"❌ leer_productos error: {e}")
            return []

    def actualizar_rango(self, codigo_uli, precio_min, precio_max):
        try:
            ws = self.sheet.worksheet("⚙️ Productos")
            rows = ws.get_all_values()
            for i, r in enumerate(rows[1:], 2):
                if len(r) >= 2 and r[COL_CODIGO_ULI-1].strip() == codigo_uli:
                    ws.update_cell(i, COL_PRECIO_MIN, precio_min)
                    ws.update_cell(i, COL_PRECIO_MAX, precio_max)
                    print(f"✅ Rango actualizado en Sheets: {codigo_uli} min={precio_min} max={precio_max}")
                    break
        except Exception as e:
            print(f"❌ actualizar_rango error: {e}")

    def actualizar_estado(self, codigo_uli, estado):
        try:
            ws = self.sheet.worksheet("⚙️ Productos")
            rows = ws.get_all_values()
            for i, r in enumerate(rows[1:], 2):
                if len(r) >= 2 and r[COL_CODIGO_ULI-1].strip() == codigo_uli:
                    ws.update_cell(i, COL_ACTIVO, estado)
                    print(f"✅ Estado actualizado en Sheets: {codigo_uli} = {estado}")
                    break
        except Exception as e:
            print(f"❌ actualizar_estado error: {e}")

    def actualizar_precio_actual(self, codigo_uli, precio_actual):
        try:
            ws = self.sheet.worksheet("⚙️ Productos")
            rows = ws.get_all_values()
            for i, r in enumerate(rows[1:], 2):
                if len(r) >= 2 and r[COL_CODIGO_ULI-1].strip() == codigo_uli:
                    ws.update_cell(i, COL_PRECIO_ACTUAL, precio_actual)
                    break
        except Exception as e:
            print(f"❌ actualizar_precio_actual error: {e}")

    def registrar_venta(self, fecha, producto, unidades, precio_venta, costo, id_orden):
        try:
            ws = self.sheet.worksheet("📦 Ventas")
            margen = (precio_venta - costo) * unidades
            margen_pct = (precio_venta - costo) / precio_venta if precio_venta > 0 else 0
            ws.append_row([
                fecha, producto, unidades,
                precio_venta, costo, margen,
                f"{margen_pct:.1%}", id_orden
            ])
        except Exception as e:
            print(f"❌ registrar_venta error: {e}")

    def actualizar_reporte(self, datos):
        try:
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
        except Exception as e:
            print(f"❌ actualizar_reporte error: {e}")

    def leer_config(self):
        try:
            ws = self.sheet.worksheet("🔧 Configuración")
            records = ws.get_all_values()
            config = {}
            for r in records[1:]:
                if len(r) >= 2 and r[0] and r[1]:
                    config[r[0]] = r[1]
            return config
        except Exception as e:
            print(f"❌ leer_config error: {e}")
            return {}
