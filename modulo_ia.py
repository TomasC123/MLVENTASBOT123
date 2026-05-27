import requests
import json

CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
CLAUDE_MODEL = "claude-sonnet-4-20250514"

CONTEXTO_NEGOCIO = """
Sos el sistema de gestión autónomo de una tienda en MercadoLibre Argentina.
Vendés accesorios tecnológicos: cables USB-C, hubs, cables HDMI, micrófonos y mini impresoras.
Tu objetivo es maximizar ventas y margen dentro de los límites configurados por el dueño.

REGLAS ABSOLUTAS:
- Nunca bajar precio por debajo de costo + 10%
- Nunca aprobar restock sin consultar al dueño
- En reclamos, solo podés disculparte — nada más
- Siempre responder en español, tono profesional y amigable
- Respuestas concisas y accionables
"""

def consultar_claude(prompt, max_tokens=500):
    headers = {
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01"
    }
    body = {
        "model": CLAUDE_MODEL,
        "max_tokens": max_tokens,
        "system": CONTEXTO_NEGOCIO,
        "messages": [{"role": "user", "content": prompt}]
    }
    try:
        r = requests.post(CLAUDE_API_URL, headers=headers, json=body, timeout=30)
        data = r.json()
        return data["content"][0]["text"]
    except Exception as e:
        print(f"Error Claude API: {e}")
        return None

# ── DECISIÓN DE PRICING ──────────────────────────────────
def decidir_precio(producto, costo, precio_actual, precio_min, precio_competidor, dias_sin_vender, reputacion, stock):
    precio_absoluto_min = round(costo * 1.10)

    prompt = f"""
Tomá una decisión de pricing para este producto:

- Producto: {producto}
- Costo unitario: ${costo:,}
- Precio mínimo absoluto (costo +10%): ${precio_absoluto_min:,}
- Precio mínimo configurado: ${precio_min:,}
- Precio actual: ${precio_actual:,}
- Competidor más barato: ${precio_competidor:,}
- Días sin vender: {dias_sin_vender}
- Reputación ML: {reputacion}
- Stock disponible: {stock} unidades

Respondé EXACTAMENTE en este formato:
PRECIO: [número sin puntos ni comas]
RAZON: [una línea explicando la decisión]
URGENCIA: [NORMAL / ATENCIÓN / CRITICO]
"""
    respuesta = consultar_claude(prompt)
    if not respuesta:
        return None

    try:
        lineas = respuesta.strip().split("\n")
        precio = int([l for l in lineas if l.startswith("PRECIO:")][0].split(":")[1].strip())
        razon = [l for l in lineas if l.startswith("RAZON:")][0].split(":")[1].strip()
        urgencia = [l for l in lineas if l.startswith("URGENCIA:")][0].split(":")[1].strip()
        precio = max(precio, precio_absoluto_min)
        return {"precio": precio, "razon": razon, "urgencia": urgencia}
    except:
        return None

# ── RESPUESTA INTELIGENTE A PREGUNTAS ────────────────────
def responder_pregunta_inteligente(pregunta, producto, precio, stock):
    prompt = f"""
Un comprador hizo esta pregunta en MercadoLibre:
"{pregunta}"

Sobre el producto: {producto}
Precio actual: ${precio:,}
Stock disponible: {stock} unidades

Escribí una respuesta corta, amigable y profesional.
Máximo 3 oraciones. No uses emojis en exceso.
No ofrezcas descuentos ni condiciones especiales.
Si pregunta algo que no podés responder con certeza, decí que lo vas a consultar.
"""
    return consultar_claude(prompt, max_tokens=200)

# ── GESTIÓN DE RECLAMOS ──────────────────────────────────
def gestionar_reclamo(reclamo, producto, precio_pagado):
    prompt = f"""
Un comprador hizo este reclamo en MercadoLibre:
"{reclamo}"

Producto: {producto}
Precio pagado: ${precio_pagado:,}

IMPORTANTE: Solo podés disculparte y decirle que vas a revisar el caso.
No ofrezcas reembolsos, reenvíos ni soluciones concretas.
Escribí una respuesta empática, breve y profesional.
Máximo 2 oraciones.
"""
    respuesta = consultar_claude(prompt, max_tokens=150)

    # Siempre escalar al dueño
    return {
        "respuesta_comprador": respuesta,
        "escalar": True,
        "motivo": reclamo[:100]
    }

# ── ANÁLISIS DE OPORTUNIDADES ────────────────────────────
def analizar_oportunidades(ventas_semana, stock_actual, tendencias_ml):
    prompt = f"""
Analizá esta situación del negocio y sugerí una acción concreta:

Ventas esta semana por producto:
{json.dumps(ventas_semana, ensure_ascii=False, indent=2)}

Stock actual:
{json.dumps(stock_actual, ensure_ascii=False, indent=2)}

Tendencias detectadas en ML esta semana:
{tendencias_ml}

Respondé con UNA sola sugerencia accionable.
Formato:
SUGERENCIA: [qué hacer]
IMPACTO: [por qué conviene]
URGENCIA: [BAJA / MEDIA / ALTA]
"""
    return consultar_claude(prompt, max_tokens=300)

# ── REPORTE SEMANAL INTELIGENTE ──────────────────────────
def generar_resumen_ejecutivo(datos_semana):
    prompt = f"""
Generá un resumen ejecutivo semanal del negocio basado en estos datos:

{json.dumps(datos_semana, ensure_ascii=False, indent=2)}

Incluí:
1. Performance general (2 líneas)
2. Lo que funcionó bien (1 línea)
3. Lo que hay que mejorar (1 línea)
4. Recomendación para la próxima semana (1 línea)

Tono directo, como un socio de negocio. Sin paja.
"""
    return consultar_claude(prompt, max_tokens=400)


# ── RESUMEN DIARIO DE DECISIONES ─────────────────────────
def generar_resumen_diario(decisiones_del_dia):
    prompt = f"""
Resumí las decisiones que tomó el sistema hoy de forma clara y directa.

Decisiones registradas:
{json.dumps(decisiones_del_dia, ensure_ascii=False, indent=2)}

Formato del resumen:
📋 RESUMEN DEL DÍA [fecha]

💰 PRECIOS ([N] cambios)
- [producto]: $X → $Y (motivo breve)

❓ PREGUNTAS ([N] respondidas, [N] escaladas)
- [resumen breve]

📦 STOCK
- [estado general]

⚠️ ALERTAS
- [si hubo algo importante]

🔍 OBSERVACIÓN DEL DÍA
- [una línea con algo relevante que notó el sistema]

Sé conciso. Si no hubo actividad en alguna categoría, omitila.
"""
    return consultar_claude(prompt, max_tokens=500)
