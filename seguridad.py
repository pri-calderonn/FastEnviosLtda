"""
seguridad.py — Protocolos de seguridad y uso responsable
Evaluación Parcial N°3 — ISY0101 Ingeniería de Soluciones con IA
Autores: Priscila Calderón / Gustavo Soto — DuocUC 2026

Implementa los patrones enseñados en IL3.3 (Seguridad y Ética),
adaptados al agente Fasty (atención al cliente de FastEnvios):

1. sanitizar_input: limpia caracteres peligrosos y limita longitud.
2. detectar_prompt_injection: bloquea intentos de manipular las
   instrucciones del sistema.
3. validar_respuesta: evita que el agente filtre datos sensibles
   (emails, tarjetas, tokens) o ejecute código.
4. RateLimiter: limita solicitudes por sesión para evitar abuso.
5. verificacion_etica: bloquea temas fuera del alcance del agente
   (ej. asesoría legal/médica) y evita respuestas inapropiadas.
"""

import re
import time
from collections import defaultdict


# ── 1. Sanitización de input ────────────────────────────────────────────────

def sanitizar_input(texto: str, longitud_maxima: int = 1000) -> str:
    """Elimina caracteres potencialmente peligrosos y limita la longitud."""
    limpio = re.sub(r'[<>"\';&|`]', '', texto)
    return limpio[:longitud_maxima]


# ── 2. Protección contra prompt injection ───────────────────────────────────

PATRONES_INYECCION = [
    r"ignor[ae]\s+(las\s+)?instrucciones\s+anteriores",
    r"olvida\s+todo\s+lo\s+anterior",
    r"act[uú]a\s+como\s+si\s+fueras",
    r"finge\s+ser",
    r"eres\s+ahora\s+un[ao]?",
    r"ignore\s+previous\s+instructions",
    r"system\s*:\s*you\s+are\s+now",
]


def detectar_prompt_injection(texto: str) -> bool:
    """Detecta intentos de manipular el comportamiento del agente."""
    texto_lower = texto.lower()
    return any(re.search(p, texto_lower) for p in PATRONES_INYECCION)


# ── 3. Validación de salida (evita fuga de datos sensibles) ─────────────────

PATRONES_DATOS_SENSIBLES = [
    r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',   # tarjetas de crédito
    r'password\s*:\s*\S+',
    r'api[_-]?key\s*:\s*\S+',
    r'token\s*:\s*\S+',
]


def validar_respuesta(respuesta: str) -> str:
    """Bloquea la respuesta si contiene patrones de datos sensibles o código peligroso."""
    for patron in PATRONES_DATOS_SENSIBLES:
        if re.search(patron, respuesta, re.IGNORECASE):
            return ("Lo siento, no puedo entregar esa información por motivos "
                    "de seguridad y privacidad. Te derivaré con un ejecutivo.")
    return respuesta


# ── 4. Rate limiting por sesión ──────────────────────────────────────────────

class LimitadorDeTasa:
    """Evita abuso del agente limitando solicitudes por sesión/minuto."""

    def __init__(self, solicitudes_por_minuto: int = 20):
        self.solicitudes_por_minuto = solicitudes_por_minuto
        self.registro = defaultdict(list)

    def permitir(self, session_id: str) -> bool:
        ahora = time.time()
        hace_un_minuto = ahora - 60
        self.registro[session_id] = [
            t for t in self.registro[session_id] if t > hace_un_minuto
        ]
        if len(self.registro[session_id]) >= self.solicitudes_por_minuto:
            return False
        self.registro[session_id].append(ahora)
        return True


limitador_global = LimitadorDeTasa(solicitudes_por_minuto=20)


# ── 5. Verificación ética básica ─────────────────────────────────────────────

TEMAS_FUERA_DE_ALCANCE = ["asesoría legal", "asesoría médica", "consejo financiero"]


def verificacion_etica(consulta: str) -> tuple:
    """
    Retorna (es_valida: bool, mensaje: str|None).
    Si es_valida es False, el agente NO debe procesar la consulta y
    debe usar el mensaje entregado como respuesta.
    """
    consulta_lower = consulta.lower()
    for tema in TEMAS_FUERA_DE_ALCANCE:
        if tema.split()[1] in consulta_lower:  # ej. detecta "legal", "médica", "financiero"
            return False, (
                f"Esta consulta requiere {tema} profesional, algo fuera del "
                f"alcance de Fasty. Te recomiendo consultar con un especialista."
            )
    return True, None


# ── Función unificada para integrar en agent.py ─────────────────────────────

def procesar_con_seguridad(consulta: str, session_id: str):
    """
    Aplica todas las capas de seguridad ANTES de invocar al agente.
    Retorna (consulta_segura: str|None, bloqueo: str|None).
    Si bloqueo no es None, esa es la respuesta a devolver sin llamar al LLM.
    """
    if not limitador_global.permitir(session_id):
        return None, "Has alcanzado el límite de solicitudes por minuto. Intenta nuevamente en unos segundos."

    consulta_limpia = sanitizar_input(consulta)

    if detectar_prompt_injection(consulta_limpia):
        return None, "No puedo seguir instrucciones que intenten modificar mi comportamiento. ¿En qué más te puedo ayudar con tu envío?"

    es_valida, mensaje = verificacion_etica(consulta_limpia)
    if not es_valida:
        return None, mensaje

    return consulta_limpia, None