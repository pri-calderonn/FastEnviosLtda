"""
agent.py — Agente Funcional FastEnvios Ltda.
Evaluación Parcial N°2 — ISY0101 Ingeniería de Soluciones con IA
Autores: Priscila Calderón / Gustavo Soto — DuocUC 2026

Versiones requeridas (ver requirements.txt):
    langchain==1.3.4
    langchain-community==0.4.2
    langchain-core==1.4.1
    langchain-openai==1.2.2
    langgraph==1.2.4
    langgraph-prebuilt==1.1.0
    langgraph-checkpoint==4.1.1
    chromadb==1.5.9
    openai==2.41.0

Arquitectura del agente:
    Usuario
       │
       
  [Nodo: clasificador]  - detecta intención + recupera memoria largo plazo
       │
       
  [Nodo: agente]        - LLM GPT-4.1 con herramientas enlazadas
       │
       ├─── ¿usa herramienta? - [Nodo: herramientas] - vuelve al agente
       │
       └─── ¿respuesta final? - [Nodo: guardar] - END
                                       │
                                       
                                  ChromaDB historial
                                  (memoria largo plazo)
"""

import os
import sys
import json
import warnings
import time
from datetime import datetime
from typing import Annotated
from dotenv import load_dotenv
from typing_extensions import TypedDict
from observabilidad import registrar_evento
from seguridad import procesar_con_seguridad, validar_respuesta
warnings.filterwarnings("ignore", category=DeprecationWarning)

load_dotenv()


from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode


from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter



GITHUB_TOKEN   = os.getenv("GITHUB_TOKEN")
BASE_URL       = os.getenv("OPENAI_BASE_URL")
EMBEDDINGS_URL = os.getenv("OPENAI_EMBEDDINGS_URL")
CHROMA_DIR     = "./chroma_db"
HISTORIAL_DIR  = "./chroma_historial"
RECLAMOS_FILE  = "./reclamos_registrados.json"

if not GITHUB_TOKEN:
    print("Error: No se encontró GITHUB_TOKEN en el archivo .env")
    sys.exit(1)


embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    api_key=GITHUB_TOKEN,
    base_url=EMBEDDINGS_URL
)


print("Cargando base de conocimiento...")

if not os.path.exists(CHROMA_DIR):
    print("  Primera vez: indexando documentos...")
    loader = DirectoryLoader(
        "documentos/",
        glob="*.txt",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"}
    )
    documentos = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    fragmentos = splitter.split_documents(documentos)
    vectorstore = Chroma.from_documents(
        documents=fragmentos,
        embedding=embeddings,
        persist_directory=CHROMA_DIR
    )
    print(f"  {len(fragmentos)} fragmentos indexados.")
else:
    vectorstore = Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=embeddings
    )
    print("  Base de conocimiento cargada.")

retriever = vectorstore.as_retriever(search_kwargs={"k": 3})


historial_store = Chroma(
    persist_directory=HISTORIAL_DIR,
    embedding_function=embeddings,
    collection_name="historial_conversaciones"
)


def guardar_en_historial(session_id: str, rol: str, contenido: str) -> None:
    """Persiste cada turno de conversación en ChromaDB."""
    doc_id = f"{session_id}_{rol}_{datetime.now().isoformat()}"
    historial_store.add_texts(
        texts=[contenido],
        metadatas=[{
            "session_id": session_id,
            "rol": rol,
            "timestamp": datetime.now().isoformat()
        }],
        ids=[doc_id]
    )


def recuperar_contexto_historico(session_id: str, consulta: str, k: int = 3) -> str:
    """
    Recupera mensajes anteriores semánticamente relevantes para la consulta.
    Implementa recuperación de contexto semántico (IE4).
    """
    try:
        resultados = historial_store.similarity_search_with_score(
            consulta,
            k=k,
            filter={"session_id": session_id}
        )
        if not resultados:
            return ""
        #filtrar
        relevantes = [
            f"[{doc.metadata['rol']}]: {doc.page_content}"
            for doc, score in resultados
            if score < 1.2
        ]
        return "\n".join(relevantes)
    except Exception:
        return ""


@tool
def consultar_documentos(pregunta: str) -> str:
    """
    Consulta la base de conocimiento interna de FastEnvios.
    Usala para responder preguntas sobre políticas de envío, tarifas,
    plazos de entrega,seguimiento de pedidos y preguntas frecuentes.
    Siempre cita la fuente documental en tu respuesta.
    """
    docs = retriever.invoke(pregunta)
    if not docs:
        return "No se encontró información relevante en los documentos internos."
    fragmentos = []
    for doc in docs:
        fuente = os.path.basename(doc.metadata.get("source", "documento_interno"))
        fragmentos.append(f"[Fuente: {fuente}]\n{doc.page_content}")
    return "\n\n---\n\n".join(fragmentos)


@tool
def registrar_reclamo(numero_tracking: str, tipo_reclamo: str, descripcion: str) -> str:
    """
    Registra un reclamo formal del cliente en el sistema de FastEnvios.
    Úsala cuando el cliente reporte: paquete dañado, no entregado,
    extraviado o demora excesiva. Requiere número de tracking y descripción.
    Los tipos válidos son: DAÑO, NO_ENTREGADO, EXTRAVIADO, DEMORA.
    """
    reclamos = []
    if os.path.exists(RECLAMOS_FILE):
        with open(RECLAMOS_FILE, "r", encoding="utf-8") as f:
            reclamos = json.load(f)

    numero_caso = f"RC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    nuevo = {
        "numero_caso":      numero_caso,
        "numero_tracking":  numero_tracking,
        "tipo":             tipo_reclamo,
        "descripcion":      descripcion,
        "fecha":            datetime.now().isoformat(),
        "estado":           "RECIBIDO"
    }
    reclamos.append(nuevo)

    with open(RECLAMOS_FILE, "w", encoding="utf-8") as f:
        json.dump(reclamos, f, ensure_ascii=False, indent=2)

    return (
        f"Reclamo registrado exitosamente.\n"
        f"  Número de caso:  {numero_caso}\n"
        f"  Tipo de reclamo: {tipo_reclamo}\n"
        f"  Estado actual:   RECIBIDO\n"
        f"  Recibirás una resolución en máximo 10 días hábiles por correo electrónico."
    )


@tool
def escalar_a_ejecutivo(motivo: str) -> str:
    """
    Escala la consulta a un ejecutivo humano de FastEnvios.
    Úsala cuando la consulta sea demasiado compleja para resolverse
    con los documentos disponibles, o cuando el cliente pida
    hablar con una persona.
    """
    return (
        f"Tu consulta ha sido escalada a un ejecutivo.\n"
        f"  Motivo registrado: {motivo}\n"
        f"  Tiempo de espera estimado: 5 a 10 minutos.\n\n"
        f"También puedes contactarnos directamente:\n"
        f"  WhatsApp:  +56 9 8765 4321\n"
        f"  Email:     atencion@fastenvios.cl\n"
        f"  Horario:   Lunes a viernes, 9:00 a 18:00 hrs."
    )


HERRAMIENTAS = [consultar_documentos, registrar_reclamo, escalar_a_ejecutivo]



#MODELO LLM

llm = ChatOpenAI(
    model="gpt-4.1",
    api_key=GITHUB_TOKEN,
    base_url=BASE_URL,
    temperature=0.2,
    max_tokens=600
)

llm_con_herramientas = llm.bind_tools(HERRAMIENTAS)

SYSTEM_PROMPT = """Eres Fasty, el agente virtual oficial de FastEnvios Ltda.,
una empresa chilena de despacho a domicilio.

REGLAS OBLIGATORIAS:
- Responde SIEMPRE en español, con tono amable, formal y cercano.
- Para consultas sobre envíos, tarifas o plazos: usa 'consultar_documentos'.
- Para reclamos formales (daño, extravío, no entrega, demora): usa 'registrar_reclamo'.
- Si la consulta supera tu capacidad o el cliente pide un humano: usa 'escalar_a_ejecutivo'.
- Cita siempre la fuente documental cuando uses información de documentos.
- NUNCA inventes datos que no provengan de las herramientas o documentos."""


class EstadoAgente(TypedDict):
    messages:   Annotated[list, add_messages]
    session_id: str
    intencion:  str
    metricas_llm: list

def nodo_clasificador(estado: EstadoAgente) -> dict:
    """
    Nodo de planificación y enrutamiento (IE5).
    - Clasifica la intención del usuario por palabras clave.
    - Recupera contexto histórico semántico de sesiones previas (IE4).
    - Inyecta el SystemMessage con contexto enriquecido.
    - Persiste el mensaje del usuario en memoria largo plazo (IE3).
    """
    ultimo_mensaje = estado["messages"][-1].content
    session_id     = estado.get("session_id", "default")

    consulta_lower = ultimo_mensaje.lower()
    if any(p in consulta_lower for p in
           ["seguimiento", "dónde está", "donde esta", "mi pedido", "tracking", "llegó", "llego"]):
        intencion = "seguimiento"
    elif any(p in consulta_lower for p in
             ["reclamo", "problema", "queja", "dañado", "dañada", "perdido", "no llegó", "no llego"]):
        intencion = "reclamo"
    elif any(p in consulta_lower for p in
             ["cuánto demora", "cuanto demora", "plazo", "costo", "precio", "tarifa", "despacho", "días"]):
        intencion = "politica_envio"
    elif any(p in consulta_lower for p in
             ["ejecutivo", "hablar con", "persona", "humano", "agente humano"]):
        intencion = "escalada"
    else:
        intencion = "general"

    print(f"   [Intención detectada: {intencion}]")

    contexto_historico = recuperar_contexto_historico(session_id, ultimo_mensaje)

    system_content = SYSTEM_PROMPT
    if contexto_historico:
        system_content += (
            f"\n\nCONTEXTO HISTÓRICO DE ESTE CLIENTE (sesión {session_id}):\n"
            f"{contexto_historico}"
        )

    guardar_en_historial(session_id, "usuario", ultimo_mensaje)

    mensajes = list(estado["messages"])
    if not any(isinstance(m, SystemMessage) for m in mensajes):
        mensajes = [SystemMessage(content=system_content)] + mensajes

    return {
        "messages":   mensajes,
        "intencion":  intencion,
        "session_id": session_id
    }


def nodo_agente(estado: EstadoAgente) -> dict:
    """
    Nodo principal de razonamiento (IE6).
    Instrumentado (EP3): mide latencia y tokens de esta llamada al LLM.
    """
    inicio = time.perf_counter()
    respuesta = llm_con_herramientas.invoke(estado["messages"])
    latencia_llm = time.perf_counter() - inicio

    usage = getattr(respuesta, "usage_metadata", None) or {}
    tokens_entrada = usage.get("input_tokens", 0)
    tokens_salida = usage.get("output_tokens", 0)

    metricas_previas = estado.get("metricas_llm", [])
    metricas_previas.append({
        "latencia": latencia_llm,
        "tokens_entrada": tokens_entrada,
        "tokens_salida": tokens_salida,
    })

    return {"messages": [respuesta], "metricas_llm": metricas_previas}


def nodo_guardar_respuesta(estado: EstadoAgente) -> dict:
    """
    Nodo de escritura: persiste la respuesta del agente en ChromaDB (IE3).
    Garantiza continuidad semántica en sesiones futuras.
    """
    session_id = estado.get("session_id", "default")
    ultimo = estado["messages"][-1]
    if isinstance(ultimo, AIMessage) and isinstance(ultimo.content, str) and ultimo.content.strip():
        guardar_en_historial(session_id, "agente", ultimo.content)
    return {}


def debe_usar_herramienta(estado: EstadoAgente) -> str:
    """
    Decide el siguiente nodo según si el LLM solicitó una herramienta.
    Si hay tool_calls pendientes  ejecutar herramientas y volver al agente.
    Si no hay tool_calls    persistir respuesta y terminar.
    """
    ultimo = estado["messages"][-1]
    if hasattr(ultimo, "tool_calls") and ultimo.tool_calls:
        return "herramientas"
    return "guardar"


nodo_herramientas = ToolNode(HERRAMIENTAS)

grafo = StateGraph(EstadoAgente)

grafo.add_node("clasificador", nodo_clasificador)
grafo.add_node("agente",       nodo_agente)
grafo.add_node("herramientas", nodo_herramientas)
grafo.add_node("guardar",      nodo_guardar_respuesta)

grafo.set_entry_point("clasificador")
grafo.add_edge("clasificador", "agente")

grafo.add_conditional_edges(
    "agente",
    debe_usar_herramienta,
    {
        "herramientas": "herramientas",
        "guardar":      "guardar"
    }
)

grafo.add_edge("herramientas", "agente")
grafo.add_edge("guardar", END)

memoria_corto_plazo = MemorySaver()
agente_compilado = grafo.compile(checkpointer=memoria_corto_plazo)



def ejecutar_agente(consulta: str, session_id: str) -> str:
    """Invoca el agente con la consulta del usuario y retorna la respuesta."""
    #Capa de seguridad

    consulta_segura, bloqueo = procesar_con_seguridad (consulta , session_id)
    if bloqueo:
        registrar_evento(
            session_id= session_id,consulta=consulta, intencion = "bloqueada_seguridad",
            herramientas_usadas=[], latencia_total_seg=0, latencia_llm_seg=0,
            tokens_entrada=0, tokens_salida= 0, respuesta= bloqueo,
            error= False, tipo_error= None,
        )
        return bloqueo
    consulta = consulta_segura

    config = {"configurable": {"thread_id": session_id}}
    estado_inicial = {
        "messages":   [HumanMessage(content=consulta)],
        "session_id": session_id,
        "intencion":  "",
        "metricas_llm" : []
    }

    inicio_total= time.perf_counter()
    error_ocurrido = False
    tipo_error = None
    respuesta_final = "No se puedo generar una respuesta, intente nuevamente"
    herramientas_usadas=[]
    intencion_detectada = ""

    try:
        resultado = agente_compilado.invoke(estado_inicial, config=config)

        for msg in resultado ["messages"]:
            if hasattr (msg, "tool_calls") and msg.tool_calls:
                herramientas_usadas.extend([tc["name"] for tc in msg.tool_calls])

        intencion_detectada = resultado.get ("intencion","")

        for msg in reversed(resultado["messages"]):
            if isinstance(msg, AIMessage) and isinstance(msg.content, str) and msg.content.strip():
                respuesta_final = msg.content
                break
        respuesta_final = validar_respuesta(respuesta_final)
        metricas = resultado.get("metricas_llm", [])
        latencia_llm_total = sum(m["latencia"] for m in metricas)
        tokens_entrada = sum(m["tokens_entrada"] for m in metricas)
        tokens_salida = sum(m["tokens_salida"] for m in metricas)

    except Exception as e:
        error_ocurrido = True
        tipo_error = type(e).__name__
        latencia_llm_total = 0
        tokens_entrada = 0
        tokens_salida = 0
        raise

    finally:
        latencia_total = time.perf_counter() - inicio_total
        registrar_evento(
            session_id=session_id,
            consulta=consulta,
            intencion=intencion_detectada,
            herramientas_usadas=herramientas_usadas,
            latencia_total_seg=latencia_total,
            latencia_llm_seg=latencia_llm_total,
            tokens_entrada=tokens_entrada,
            tokens_salida=tokens_salida,
            respuesta=respuesta_final,
            error=error_ocurrido,
            tipo_error=tipo_error,
        )

    return respuesta_final



def main():
    print("\n" + "=" * 60)
    print("  FASTY — Agente Virtual de FastEnvios Ltda. (v2.0)")
    print("  Framework: LangGraph 1.2.4 + GPT-4.1 + ChromaDB")
    print("=" * 60)
    print("  Comandos disponibles:")
    print("    'nueva sesion' → inicia una sesión nueva")
    print("    'salir'        → termina el programa")
    print("=" * 60 + "\n")

    session_id = f"sesion_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"  Sesión activa: {session_id}\n")

    while True:
        try:
            consulta = input("Cliente: ").strip()
        except KeyboardInterrupt:
            print("\n\n¡Hasta pronto!")
            break

        if not consulta:
            continue

        if consulta.lower() == "salir":
            print("¡Hasta pronto! Que tengas un excelente día.")
            break

        if consulta.lower() == "nueva sesion":
            session_id = f"sesion_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            print(f"\n  Nueva sesión iniciada: {session_id}\n")
            continue

        print("\nFasty: ", end="", flush=True)
        try:
            respuesta = ejecutar_agente(consulta, session_id)
            print(respuesta)
        except Exception as e:
            print(f"Error: {e}")
            print("  Verifica tu conexión y que el GITHUB_TOKEN sea válido.")

        print("-" * 60 + "\n")


if __name__ == "__main__":
    main()


