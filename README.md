# MLVentasBot — Sistema completo de automatización MercadoLibre

## Módulos (14 archivos)
- main.py              — orquestador + schedules
- ml_api.py            — API MercadoLibre
- modulo_auth.py       — OAuth + refresh token automático
- modulo_ia.py         — cerebro Claude IA
- modulo_preguntas.py  — respuestas automáticas
- modulo_pricing.py    — precios dinámicos
- modulo_stock.py      — alertas de stock
- modulo_campanas.py   — gestión campañas Product Ads
- modulo_postventa.py  — mensajes post-compra + calificaciones
- modulo_restock.py    — propuestas de restock con IA
- modulo_reporte.py    — reportes semanales
- modulo_decisiones.py — log diario de decisiones
- modulo_telegram_bot.py — comandos por Telegram
- modulo_sheets.py     — Google Sheets bidireccional
- modulo_webhook.py    — servidor HTTP tiempo real
- modulo_monitor.py    — monitor de salud del sistema
- telegram_utils.py    — notificaciones
- config.py            — configuración central

## Schedules
c/5 min  → preguntas automáticas + post-venta
c/2 hs   → stock + renovación token ML
c/4 hs   → pricing dinámico
c/6 hs   → monitor salud del sistema
8am ARG  → análisis campañas (te consulta)
11am ARG → propuesta de restock (te consulta)
9pm ARG  → resumen decisiones del día
Lunes 9am → reporte semanal

## Comandos Telegram
/precio cable min 6000 max 9000
/activar [producto] / /desactivar [producto]
/stock / /ventas / /reporte / /precios
/campanas / /analizar_campanas
/aprobar_campana [n] / /rechazar_campana [n]
/aprobar_campanas_todas
/pausar_campana [id] / /activar_campana [id]
/aprobar_restock / /rechazar_restock
/estado / /reautenticar
/ayuda

## Lo que SIEMPRE te consulta antes de ejecutar
- Cambios en campañas (presupuesto, pausar)
- Órdenes de restock a ULI
- Cualquier acción con gasto de dinero

## Variables de entorno en Railway
Ver .env.example — cargar todas antes de deployar

## Deploy
1. Subir a repo privado GitHub
2. Railway → New Project → GitHub Repository
3. Cargar variables de entorno
4. Deploy automático
5. Primera autenticación: /reautenticar en Telegram
