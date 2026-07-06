import time
from difflib import SequenceMatcher
from agent import ejecutar_agente

# Consultas variadas: cubren las 4 intenciones mas los casos ambiguos
CONSULTAS_PRUEBA = [
    # politica_envio
    "¿Cuánto demora un envío a Valparaíso?",
    "¿Cuál es el costo de despacho a regiones?",
    "¿Qué días hacen despachos?",
    # seguimiento
    "¿Dónde está mi pedido con tracking FE12345?",
    "Mi pedido no ha llegado, ¿pueden revisar el seguimiento?",
    # reclamo
    "Mi paquete llegó dañado, quiero hacer un reclamo",
    "El pedido nunca llegó y ya pasaron 15 días",
    "Recibí un producto equivocado, es un reclamo",
    # escalada
    "Quiero hablar con un ejecutivo humano",
    "Necesito hablar con una persona, esto no me sirve",
    # ambiguas / fuera de contexto (para medir precisión y manejo de error)
    "¿Cuál es la capital de Francia?",
    "Cuéntame un chiste",
    "¿Tienen envíos a la Antártica?",
    "asdkjaslkdj",
]

# Consultas que se repiten para medir CONSISTENCIA (misma pregunta, 3 veces)
CONSULTAS_CONSISTENCIA = [
    "¿Cuánto demora un envío a Valparaíso?",
    "Mi paquete llegó dañado, quiero hacer un reclamo",
]


def similitud(a: str, b: str) -> float:
    """Similitud simple entre dos textos (0 a 1). Proxy de consistencia semántica."""
    return SequenceMatcher(None, a, b).ratio()


def ejecutar_lote(consultas: list, session_prefix: str = "prueba") -> None:
    for i, consulta in enumerate(consultas):
        session_id = f"{session_prefix}_{i}"
        print(f"[{i+1}/{len(consultas)}] Enviando: {consulta[:50]}...")
        try:
            respuesta = ejecutar_agente(consulta, session_id)
            print(f"   → Respondido ({len(respuesta)} caracteres)")
        except Exception as e:
            print(f"   → Error: {e}")
        time.sleep(0.5)  #pa no saturar


def ejecutar_pruebas_consistencia() -> None:
    """
    Ejecuta cada consulta de CONSULTAS_CONSISTENCIA 3 veces (en sesiones
    distintas, para que no haya memoria de por medio) y calcula la
    similitud promedio entre las respuestas. Resultado -> hallazgo de
    consistencia para el informe (IE1).
    """
    print("\n" + "=" * 60)
    print("  PRUEBA DE CONSISTENCIA")
    print("=" * 60)
    for consulta in CONSULTAS_CONSISTENCIA:
        respuestas = []
        for rep in range(3):
            session_id = f"consistencia_{abs(hash(consulta)) % 1000}_{rep}"
            respuesta = ejecutar_agente(consulta, session_id)
            respuestas.append(respuesta)
            time.sleep(0.5)

        similitudes = [
            similitud(respuestas[i], respuestas[j])
            for i in range(len(respuestas))
            for j in range(i + 1, len(respuestas))
        ]
        promedio = sum(similitudes) / len(similitudes) if similitudes else 0

        print(f"\nConsulta: {consulta}")
        print(f"  Similitud promedio entre 3 respuestas: {promedio:.2%}")
        if promedio < 0.5:
            print("  ⚠ Baja consistencia detectada")


if __name__ == "__main__":
    print("Iniciando generación de tráfico de prueba para Fasty...\n")
    ejecutar_lote(CONSULTAS_PRUEBA)
    ejecutar_pruebas_consistencia()
    print("\nListo. Revisa logs/observabilidad.jsonl para ver los eventos registrados.")