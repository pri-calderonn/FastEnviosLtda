import os
import json
import uuid
from datetime import datetime

LOG_DIR = "./logs"
LOG_FILE = os.path.join(LOG_DIR, "observabilidad.jsonl")

os.makedirs(LOG_DIR, exist_ok=True)

# Intenciones que, si la respuesta NO usó consultar_documentos,
# se consideran una posible falla de precisión (el agente debió
# haber buscado en la base de conocimiento y no lo hizo).
INTENCIONES_QUE_REQUIEREN_DOCUMENTOS = {"politica_envio", "seguimiento"}


def registrar_evento(
    session_id: str,
    consulta: str,
    intencion: str,
    herramientas_usadas: list,
    latencia_total_seg: float,
    latencia_llm_seg: float,
    tokens_entrada: int,
    tokens_salida: int,
    respuesta: str,
    error: bool = False,
    tipo_error: str = None,
) -> dict:
    """
    Construye y persiste un evento de observabilidad en logs/observabilidad.jsonl.
    Retorna el evento (útil para debug o tests).
    """
    uso_fuente = "[Fuente:" in (respuesta or "") or "consultar_documentos" in herramientas_usadas
    requiere_documentos = intencion in INTENCIONES_QUE_REQUIEREN_DOCUMENTOS
    posible_falla_precision = requiere_documentos and not uso_fuente and not error

    # trace_id: identificación única por interacción
    # Permite correlacionar este evento en logs, dashboard y auditoría.
    trace_id = str(uuid.uuid4())

    evento = {
        "trace_id": trace_id,
        "timestamp": datetime.now().isoformat(),
        "session_id": session_id,
        "consulta": consulta,
        "intencion": intencion,
        "herramientas_usadas": herramientas_usadas,
        "latencia_total_seg": round(latencia_total_seg, 3),
        "latencia_llm_seg": round(latencia_llm_seg, 3),
        "tokens_entrada": tokens_entrada,
        "tokens_salida": tokens_salida,
        "tokens_totales": tokens_entrada + tokens_salida,
        "longitud_respuesta_caracteres": len(respuesta) if respuesta else 0,
        "uso_fuente_documental": uso_fuente,
        "posible_falla_precision": posible_falla_precision,
        "error": error,
        "tipo_error": tipo_error,
    }

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(evento, ensure_ascii=False) + "\n")

    return evento


def leer_eventos() -> list:
    """Lee todos los eventos registrados. Usado por el dashboard (paso 3)."""
    if not os.path.exists(LOG_FILE):
        return []
    eventos = []
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()
            if linea:
                eventos.append(json.loads(linea))
    return eventos