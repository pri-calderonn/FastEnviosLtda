import os
import sys
from dotenv import load_dotenv
load_dotenv()

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough



GITHUB_TOKEN   = os.getenv("GITHUB_TOKEN")
BASE_URL       = os.getenv("OPENAI_BASE_URL")
EMBEDDINGS_URL = os.getenv("OPENAI_EMBEDDINGS_URL")

if not GITHUB_TOKEN:
    print("Error: No se encontró GITHUB_TOKEN en el archivo .env")
    sys.exit(1)

# Embeddings

embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    openai_api_key=GITHUB_TOKEN,
    openai_api_base=EMBEDDINGS_URL
)

#Cargar documentos y fragmentar

CHROMA_DIR = "./chroma_db"

if not os.path.exists(CHROMA_DIR):
    print("Primera vez: cargando y procesando documentos...")

    loader = DirectoryLoader(
        "documentos/",
        glob="*.txt",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"}
    )
    documentos = loader.load()
    print(f"{len(documentos)} documentos cargados")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    fragmentos = splitter.split_documents(documentos)
    print(f" {len(fragmentos)} fragmentos (chunks) creados")

    print("Generando embeddings (puede tardar 30 segundos)...")
    vectorstore = Chroma.from_documents(
        documents=fragmentos,
        embedding=embeddings,
        persist_directory=CHROMA_DIR
    )
    print("Base de conocimientos creada y guardada")

else:
    print("Base de conocimientos existente, cargando...")
    vectorstore = Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=embeddings
    )
    print(" Lista")


#Recuperador semántico

retriever = vectorstore.as_retriever(search_kwargs={"k": 3})


#Clasificador de intención

def clasificar_intencion(consulta: str) -> str:
    consulta = consulta.lower()
    if any(p in consulta for p in ["seguimiento", "dónde está", "donde esta", "mi pedido", "tracking", "llegó", "llego"]):
        return "seguimiento"
    if any(p in consulta for p in ["reclamo", "problema", "queja", "dañado", "dañada", "perdido", "no llegó"]):
        return "reclamo"
    if any(p in consulta for p in ["cuánto demora", "cuanto demora", "días", "plazo", "tiempo", "despacho", "envío", "costo", "precio"]):
        return "politica_envio"
    return "general"

#Prompt principal

PROMPT_TEMPLATE = """Eres Fasty, el asistente virtual oficial de FastEnvios Ltda., \
una empresa chilena de despacho a domicilio.

INSTRUCCIONES OBLIGATORIAS:
- Responde ÚNICAMENTE basándote en el contexto de documentos entregado.
- NO inventes información que no esté en el contexto.
- Siempre cita el documento fuente entre corchetes. Ejemplo: [Manual de Políticas de Envío, Sección 2]
- Usa un tono amable, formal y cercano. Habla en español latino.
- Si la información NO está en el contexto, responde exactamente: \
"Lo siento, esta consulta requiere atención de un ejecutivo. Te derivaré en un momento."
- Primero da la respuesta directa, luego los detalles si corresponde.

CONTEXTO DE DOCUMENTOS INTERNOS:
{context}

CONSULTA DEL CLIENTE:
{question}

RESPUESTA DE FASTY:"""

prompt = PromptTemplate(
    template=PROMPT_TEMPLATE,
    input_variables=["context", "question"]
)


#Modelo LLM — GPT-4o via GitHub Models

llm = ChatOpenAI(
    model="gpt-4.1",
    openai_api_key=GITHUB_TOKEN,
    openai_api_base=BASE_URL,
    temperature=0.2,
    max_tokens=500
)

#Cadena RAG completa

def formatear_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

cadena_rag = (
    {"context": retriever | formatear_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

#Interfaz de conversación en terminal

print("\n" + "="*55)
print("  FASTY — Asistente Virtual de FastEnvios Ltda.")
print("="*55)
print("  Escribe tu consulta y presiona Enter.")
print("  Escribe 'salir' para terminar.\n")

while True:
    try:
        consulta = input("Cliente: ").strip()
    except KeyboardInterrupt:
        print("\n\nHasta pronto!")
        break

    if not consulta:
        continue

    if consulta.lower() == "salir":
        print("¡Hasta pronto!")
        break

    # Clasificar intención
    intencion = clasificar_intencion(consulta)
    print(f"   [Intención detectada: {intencion}]")

    print("\nFasty: ", end="", flush=True)

    try:
        docs_relevantes = retriever.invoke(consulta)
        respuesta = cadena_rag.invoke(consulta)
        print(respuesta)

        print("\nFuentes consultadas:")
        fuentes_vistas = set()
        for doc in docs_relevantes:
            fuente = os.path.basename(doc.metadata.get("source", "Documento interno"))
            if fuente not in fuentes_vistas:
                print(f"    {fuente}")
                fuentes_vistas.add(fuente)

    except Exception as e:
        print(f"\nError al consultar: {e}")
        print("   Verifica tu conexión y que el GITHUB_TOKEN sea válido.")

    print("-"*55 + "\n")