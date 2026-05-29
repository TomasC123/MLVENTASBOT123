from ml_api import get_competidores, actualizar_precio, get_publicacion
from modulo_ia import consultar_claude
from telegram_utils import enviar_mensaje
from config import PRODUCTOS
from modulo_decisiones import registrar

# Queries optimizadas para buscar competidores reales en ML
QUERIES_COMPETENCIA = {
    "AUCATCAC": "cable usb c carga rapida 3a",
    "AUHUB271": "hub usb c 7 en 1",
    "AUCHDMI2": "cable usb c hdmi 4k",
    "AUMICOK8": "microfono corbatero inalambrico",
    "AUIMPTMI": "mini impresora termica portatil",
}

def analizar_precio_con_ia(producto, precio_actual, precio_min, precio_max, precio_competidor_min, precio_competidor_promedio, dias_sin_vender=0):
    prompt = f"""
Sos el sistema de pricing de una tienda en MercadoLibre Argentina.
Tenés que decidir el precio óptimo para maximizar ventas manteniendo margen.

PRODUCTO: {producto}
Precio actual: ${precio_actual:,}
Precio mínimo permitido: ${precio_min:,}
Precio máximo permitido: ${precio_max:,}
Competidor más barato: ${precio_competidor_min:,}
Precio promedio competencia: ${precio_competidor_promedio:,}
Días sin vender: {dias_sin_vender}

REGLAS:
- Nunca bajés del precio mínimo
- Nunca subás del precio máximo
- Si llevás más de 3 días sin vender, sé más agresivo
- No seas el más barato si el margen lo permite
- Pensá en reputación — vender barato al principio construye historial

Respondé EXACTAMENTE así:
PRECIO: [número]
RAZON: [una línea explicando la decisión]
"""
    respuesta = consultar_claude(prompt, max_tokens=150)
    if not respuesta:
        return None
    try:
        lineas = respuesta.strip().split("\n")
        precio = int([l for l in lineas if l.startswith("PRECIO:")][0].split(":")[1].strip())
        razon = [l for l in lineas if l.startswith("RAZON:")][0].split(":")[1].strip()
        precio = max(precio_min, min(precio_max, precio))
        return {"precio": precio, "razon": razon}
    except:
        return None

def ajustar_precio(producto):
    if not producto.get("activo"):
        return
    if not producto.get("id"):
        return

    item_id = producto["id"]
    nombre = producto["nombre"]
    codigo_uli = producto["codigo_uli"]
    precio_min = producto["precio_min"]
    precio_max = producto["precio_max"]

    # Precio actual desde ML
    pub = get_publicacion(item_id)
    precio_actual = pub.get("price", 0)
    if not precio_actual:
        print(f"⚠️ No se pudo obtener precio actual de {nombre}")
        return

    # Buscar competidores con query optimizada
    query = QUERIES_COMPETENCIA.get(codigo_uli, nombre)
    competidores = get_competidores(query, limite=20)
    precios_competencia = [
        c["price"] for c in competidores
        if c.get("id") != item_id and c.get("price", 0) > precio_min * 0.5
    ]

    if not precios_competencia:
        print(f"⚠️ Sin competidores encontrados para {nombre}")
        return

    precio_min_comp = min(precios_competencia)
    precio_prom_comp = round(sum(precios_competencia) / len(precios_competencia))

    print(f"📊 {nombre}: competidor min=${precio_min_comp:,} prom=${precio_prom_comp:,}")

    # Claude decide el precio
    decision = analizar_precio_con_ia(
        nombre, precio_actual, precio_min, precio_max,
        precio_min_comp, precio_prom_comp
    )

    if not decision:
        print(f"⚠️ Claude no pudo decidir precio para {nombre}")
        return

    precio_nuevo = decision["precio"]
    razon = decision["razon"]

    # Solo actualizar si cambió más del 1%
    if abs(precio_nuevo - precio_actual) / precio_actual > 0.01:
        actualizar_precio(item_id, precio_nuevo)
        registrar("PRICING", nombre, f"${precio_actual:,} → ${precio_nuevo:,} | {razon}")
        enviar_mensaje(
            f"💰 <b>Precio ajustado</b>\n\n"
            f"Producto: {nombre}\n"
            f"Precio anterior: ${precio_actual:,}\n"
            f"Precio nuevo: ${precio_nuevo:,}\n"
            f"Competidor más barato: ${precio_min_comp:,}\n\n"
            f"🧠 Razonamiento: {razon}"
        )
        print(f"💰 {nombre}: ${precio_actual:,} → ${precio_nuevo:,}")
    else:
        print(f"✅ {nombre}: precio OK (${precio_actual:,}) — {razon}")

def procesar_precios():
    from config import sincronizar_desde_sheets
    sincronizar_desde_sheets()
    for producto in PRODUCTOS:
        try:
            ajustar_precio(producto)
        except Exception as e:
            print(f"❌ Error en {producto['nombre']}: {e}")
