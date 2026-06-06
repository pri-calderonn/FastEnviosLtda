#FastEnvios — Agente Virtual con IA
Sistema de atención al cliente basado en un agente funcional con LangGraph, pipeline RAG y la memoria semántica, desarrollado para FastEnvios Ltda.  
Implementa un agente capaz de consultar documentos internos, registrar reclamos y escalar casos a ejecutivos humanos de forma autónoma.

#Descripción del proyecto

"Fasty" es el agente virtual de FastEnvios Ltda., empresa chilena de despacho a domicilio.
El sistema evolucionó desde un pipeline RAG simple (EVALUACION 1) hacia un agente funcional completo (EVALUACION 2) con las siguientes capacidades:

-Clasifica la intención del cliente antes de responder (seguimiento, reclamo, política de envío, escalada)
-Recupera información relevante desde documentos internos usando búsqueda semántica (RAG)
-Registra reclamos formales con número de caso automático
-Deriva a ejecutivo humano cuando la consulta supera su capacidad
-Mantiene memoria de corto plazo (hilo de conversación por sesión)
-Mantiene memoria de largo plazo (historial semántico persistente entre sesiones)

#Tecnologías utilizadas

| Componente | Tecnología |
|---|---|
| Framework de agente | LangGraph 1.2.4 |
| Modelo LLM | GPT-4.1 (vía GitHub Models) |
| Embeddings | text-embedding-3-small |
| Base de datos vectorial | ChromaDB (langchain-chroma) |
| Memoria corto plazo | LangGraph MemorySaver |
| Memoria largo plazo | ChromaDB colección historial |
| Lenguaje | Python 3.14 |

#Arquitectura del agente

Usuario (terminal)
       │
       ▼
┌─────────────────────────────────────────────────────┐
│                   AGENTE FASTY                      │
│                                                     │
│  [1. Nodo Clasificador]                             │
│      ├── Detecta intención por palabras clave       │
│      ├── Recupera historial semántico (ChromaDB)    │
│      └── Enriquece el contexto del LLM              │
│                   │                                 │
│  [2. Nodo Agente — GPT-4.1]                        │
│      ├── Razona sobre la consulta                   │
│      └── Decide qué herramienta usar               │
│                   │                                 │
│      ┌────────────┴────────────┐                   │
│      ▼                         ▼                   │
│  ¿Usa herramienta?        ¿Respuesta lista?        │
│      │                         │                   │
│  [3. Nodo Herramientas]   [4. Nodo Guardar]        │
│      ├── consultar_documentos  └── Persiste en     │
│      ├── registrar_reclamo         ChromaDB        │
│      └── escalar_a_ejecutivo       historial       │
│           │                        │               │
│           └────── vuelve ──────────┘               │
│                  al agente         │               │
└────────────────────────────────────┼───────────────┘
                                     ▼
                                  Usuario
```

#Memoria del agente

| Tipo | Implementación | Alcance |
|---|---|---|
| Corto plazo | LangGraph MemorySaver | Hilo completo de la sesión activa |
| Largo plazo | ChromaDB `chroma_historial/` | Persiste entre sesiones, recuperación semántica |

#Herramientas disponibles

| Herramienta | Función | Cuándo se activa |
|---|---|---|
| `consultar_documentos` | Busca en políticas, FAQ y reglamento de reclamos | Preguntas sobre envíos, tarifas, plazos |
| `registrar_reclamo` | Crea caso con número RC-XXXXXXXXXX | Cliente reporta daño, extravío o demora |
| `escalar_a_ejecutivo` | Deriva a atención humana | Consulta compleja o solicitud explícita |


#Estructura del proyecto

```
FastEnviosLtda/
│
├── app.py                  Pipeline RAG original (EvA1)
├── agent.py                Agente funcional con LangGraph (EVA2)
├── requirements.txt        Dependencias del proyecto
├── .env                    Variables de entorno
├── .gitignore              Archivos excluidos del repositorio
├── README.md               Este archivo
│
├── documentos/             Base documental interna de FastEnvios
│   ├── politicas_envio.txt
│   ├── preguntas_frecuentes.txt
│   └── reglamento_reclamos.txt
│
├── chroma_db/              Base vectorial de documentos
└── chroma_historial/       Historial semántico de conversaciones

#Requisitos previos

-Python 3.12 o superior
-Cuenta en GitHub con acceso a [GitHub Models](https://github.com/marketplace/models)
-Token de GitHub

#Instalación y ejecución

#1.Clonar el repositorio

```
git clone https://github.com/pri-calderonn/FastEnviosLtda.git
cd FastEnviosLtda
```

#Crear y activar el entorno virtual

```
python -m venv venv

#Activar en Windows (CMD)
venv\Scripts\activate

#3.Instalar dependencias

```
pip install -r requirements.txt
```

#4.Configurar variables de entorno

Crea un archivo `.env` en la raíz del proyecto:

```dotenv
GITHUB_TOKEN=ghp_tuTokenAqui
OPENAI_BASE_URL=https://models.inference.ai.azure.com
OPENAI_EMBEDDINGS_URL=https://models.inference.ai.azure.com
```

#5.Ejecutar el agente

```bash
python agent.py
```

La primera vez indexa los documentos y genera la base vectorial (30 segundos).  
Las ejecuciones siguientes cargan la base existente y arrancan de inmediato.

#6.Ejecutar el pipeline RAG

```bash
python app.py
```


#Uso del agente

Al ejecutar `agent.py` se abre una interfaz de conversación en la terminal:

```
============================================================
  FASTY — Agente Virtual de FastEnvios Ltda. (v2.0)
  Framework: LangGraph 1.2.4 + GPT-4.1 + ChromaDB
============================================================
  Comandos disponibles:
    'nueva sesion' → inicia una sesión nueva
    'salir'        → termina el programa
============================================================
  Sesión activa: sesion_20260606_133059

Cliente: ¿Cuánto cuesta enviar a Punta Arenas?
   [Intención detectada: general]

Fasty: El costo base para enviar a Punta Arenas es de $5.990 CLP
       para paquetes de hasta 5 kg. El plazo puede extenderse hasta
       7 días hábiles. [Fuente: politicas_envio.txt]
------------------------------------------------------------

Cliente: Mi paquete llegó dañado, tracking FE-2026-4421
   [Intención detectada: seguimiento]

Fasty: He registrado tu reclamo. Número de caso: RC-20260606133223.
       Recibirás respuesta en máximo 10 días hábiles por correo.
------------------------------------------------------------

Cliente: Necesito hablar con una persona
   [Intención detectada: escalada]

Fasty: Tu consulta fue escalada a un ejecutivo. Tiempo estimado:
       5-10 minutos. WhatsApp: +56 9 8765 4321
------------------------------------------------------------
```

#Clasificador de intención

| Intención | Palabras clave detectadas |
|---|---|
| `seguimiento` | seguimiento, dónde está, mi pedido, tracking, llegó |
| `reclamo` | reclamo, problema, queja, dañado, perdido, no llegó |
| `politica_envio` | cuánto demora, plazo, costo, precio, tarifa, despacho |
| `escalada` | ejecutivo, hablar con, persona, humano |
| `general` | cualquier otra consulta |

---

#Evidencia de pruebas

El agente fue probado exitosamente con las siguientes consultas:

| Consulta | Herramienta usada | Resultado |
|---|---|---|
| ¿Cuánto cuesta enviar a Punta Arenas? | `consultar_documentos` | $5.990 CLP, 7 días hábiles |
| Paquete dañado, tracking FE-2026-4421 | `registrar_reclamo` | Caso RC-20260606133223 creado |
| Necesito hablar con una persona | `escalar_a_ejecutivo` | Derivación exitosa con contactos |


##Autores

- Priscila Calderón
- Gustavo Soto

**Asignatura:** Ingeniería de Soluciones con IA — ISY0101  
**Instituto:** DuocUC — 2026
