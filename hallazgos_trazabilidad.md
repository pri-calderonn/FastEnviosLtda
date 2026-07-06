# Hallazgos de Trazabilidad — Agente Fasty

**Total de interacciones analizadas:** 70

## Métricas de latencia

- Promedio: 14.52 s
- Mediana (p50): 4.72 s
- Percentil 90 (p90): 50.90 s
- Máxima: 53.36 s

## Errores

- Tasa de errores: 54.3%
  - RateLimitError: 38 caso(s)


cls## Distribución de intenciones (patrones de uso)

- : 38 (54.3%)
- politica_envio: 12 (17.1%)
- seguimiento: 12 (17.1%)
- general: 4 (5.7%)
- reclamo: 2 (2.9%)
- escalada: 2 (2.9%)

## Uso de recursos (tokens)

- Tokens totales consumidos: 29565
- Promedio por consulta: 422

## Posibles fallas de precisión

- 18.6% de las consultas que requerían documentos no citaron ninguna fuente ni usaron `consultar_documentos`.

**Ejemplos (trace_id):**
- `93ad0f77-7764-4c89-a8e8-874e11b5e530` — "Mi pedido no ha llegado, ¿pueden revisar el seguimiento?"
- `bd2c75af-dcf6-45ee-bd6e-ce634c92b608` — "Mi paquete llegó dañado, quiero hacer un reclamo"
- `b7a3ddc2-0f0e-4548-9267-6a22e3d47c93` — "¿Cuánto demora un envío a Valparaíso?"
- `1476a2e0-5825-4d40-aa01-2bbaafdedfb5` — "¿Qué días hacen despachos?"
- `5a4d2807-943c-413e-9d89-8a50e0a62172` — "¿Dónde está mi pedido con tracking FE12345?"

## Cuellos de botella de latencia (top 5, sobre p90)

- `72b7d301-9725-4bda-a2b0-9fb5a1c624cc` — 52.15s — "¿Dónde está mi pedido con tracking FE12345?"
- `c6ae8339-1a2f-4654-ac01-fa0ac9d40beb` — 52.30s — "¿Cuál es la capital de Francia?"
- `ec0f520b-434b-4c2f-ac48-39a3273ab0aa` — 53.36s — "¿Qué días hacen despachos?"
- `a837ec9a-1a07-447a-a817-5baa5f76efb6` — 52.04s — "Mi paquete llegó dañado, quiero hacer un reclamo"
- `7bb22ae3-1c9b-4845-80d4-3417deb885ab` — 52.18s — "Quiero hablar con un ejecutivo humano"