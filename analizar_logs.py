"""
analizar_logs.py — Análisis de logs y trazabilidad
Evaluación Parcial N°3 — ISY0101 Ingeniería de Soluciones con IA
Autores: Priscila Calderón / Gustavo Soto — DuocUC 2026

Basado en el patrón de "analyze_logs()" enseñado en IL3.2: procesa
logs/observabilidad.jsonl para detectar:
- Latencia promedio y percentiles (p50, p90) → cuellos de botella
- Tasa de errores y tipos de error
- Consultas/intenciones más frecuentes (patrones de uso)
- Casos de "posible_falla_precision" (cuellos de botella de calidad,
  no solo de rendimiento) → puntos críticos de mejora (IE3, IE4)

Al ejecutarse, imprime un resumen en consola Y genera un archivo
hallazgos_trazabilidad.md con los mismos resultados en formato
markdown, listo para pegar en el apartado B del informe.
"""

import statistics
from collections import Counter
from observabilidad import leer_eventos


def percentil(valores: list, p: float) -> float:
    if not valores:
        return 0.0
    valores_ordenados = sorted(valores)
    k = (len(valores_ordenados) - 1) * p
    f = int(k)
    c = min(f + 1, len(valores_ordenados) - 1)
    if f == c:
        return valores_ordenados[f]
    return valores_ordenados[f] + (valores_ordenados[c] - valores_ordenados[f]) * (k - f)


def analizar(eventos: list) -> dict:
    if not eventos:
        return {"total": 0}

    total = len(eventos)
    latencias = [e["latencia_total_seg"] for e in eventos]
    errores = [e for e in eventos if e.get("error")]
    fallas_precision = [e for e in eventos if e.get("posible_falla_precision")]
    intenciones = Counter(e["intencion"] for e in eventos)
    tipos_error = Counter(e["tipo_error"] for e in errores if e.get("tipo_error"))
    tokens_totales = sum(e.get("tokens_entrada", 0) + e.get("tokens_salida", 0) for e in eventos)

    # Cuello de botella: eventos con latencia sobre el percentil 90
    p90 = percentil(latencias, 0.90)
    cuellos_de_botella = [e for e in eventos if e["latencia_total_seg"] >= p90]

    return {
        "total": total,
        "latencia_promedio": statistics.mean(latencias),
        "latencia_p50": percentil(latencias, 0.50),
        "latencia_p90": p90,
        "latencia_max": max(latencias),
        "tasa_error": len(errores) / total,
        "tipos_error": tipos_error,
        "tasa_falla_precision": len(fallas_precision) / total,
        "intenciones_frecuentes": intenciones.most_common(),
        "tokens_totales": tokens_totales,
        "tokens_promedio_por_consulta": tokens_totales / total,
        "cuellos_de_botella": cuellos_de_botella[:5],  # top 5 peores casos
        "casos_falla_precision": fallas_precision[:5],
    }


def generar_reporte_markdown(resultados: dict) -> str:
    lineas = []
    lineas.append("# Hallazgos de Trazabilidad — Agente Fasty\n")
    lineas.append(f"**Total de interacciones analizadas:** {resultados['total']}\n")

    lineas.append("## Métricas de latencia\n")
    lineas.append(f"- Promedio: {resultados['latencia_promedio']:.2f} s")
    lineas.append(f"- Mediana (p50): {resultados['latencia_p50']:.2f} s")
    lineas.append(f"- Percentil 90 (p90): {resultados['latencia_p90']:.2f} s")
    lineas.append(f"- Máxima: {resultados['latencia_max']:.2f} s\n")

    lineas.append("## Errores\n")
    lineas.append(f"- Tasa de errores: {resultados['tasa_error']:.1%}")
    if resultados["tipos_error"]:
        for tipo, cantidad in resultados["tipos_error"].items():
            lineas.append(f"  - {tipo}: {cantidad} caso(s)")
    else:
        lineas.append("  - No se registraron errores en esta muestra.")
    lineas.append("")

    lineas.append("## Distribución de intenciones (patrones de uso)\n")
    for intencion, cantidad in resultados["intenciones_frecuentes"]:
        porcentaje = cantidad / resultados["total"]
        lineas.append(f"- {intencion}: {cantidad} ({porcentaje:.1%})")
    lineas.append("")

    lineas.append("## Uso de recursos (tokens)\n")
    lineas.append(f"- Tokens totales consumidos: {resultados['tokens_totales']}")
    lineas.append(f"- Promedio por consulta: {resultados['tokens_promedio_por_consulta']:.0f}\n")

    lineas.append("## Posibles fallas de precisión\n")
    lineas.append(
        f"- {resultados['tasa_falla_precision']:.1%} de las consultas que requerían "
        f"documentos no citaron ninguna fuente ni usaron `consultar_documentos`."
    )
    if resultados["casos_falla_precision"]:
        lineas.append("\n**Ejemplos (trace_id):**")
        for caso in resultados["casos_falla_precision"]:
            lineas.append(f"- `{caso['trace_id']}` — \"{caso['consulta'][:60]}\"")
    lineas.append("")

    lineas.append("## Cuellos de botella de latencia (top 5, sobre p90)\n")
    for caso in resultados["cuellos_de_botella"]:
        lineas.append(
            f"- `{caso['trace_id']}` — {caso['latencia_total_seg']:.2f}s — "
            f"\"{caso['consulta'][:60]}\""
        )

    return "\n".join(lineas)


if __name__ == "__main__":
    eventos = leer_eventos()

    if not eventos:
        print("No hay eventos registrados aún en logs/observabilidad.jsonl.")
        print("Corre primero generar_trafico_prueba.py")
    else:
        resultados = analizar(eventos)

        print("\n" + "=" * 60)
        print("  ANÁLISIS DE TRAZABILIDAD — Fasty")
        print("=" * 60)
        print(f"Total de interacciones: {resultados['total']}")
        print(f"Latencia promedio: {resultados['latencia_promedio']:.2f}s "
              f"(p90: {resultados['latencia_p90']:.2f}s)")
        print(f"Tasa de error: {resultados['tasa_error']:.1%}")
        print(f"Posibles fallas de precisión: {resultados['tasa_falla_precision']:.1%}")
        print("=" * 60)

        reporte = generar_reporte_markdown(resultados)
        with open("hallazgos_trazabilidad.md", "w", encoding="utf-8") as f:
            f.write(reporte)
        print("\nReporte guardado en hallazgos_trazabilidad.md")