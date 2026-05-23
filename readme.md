FastEnvios RAG — Asistente Virtual con IA

Sistema de atención al cliente basado en LLMs y pipeline RAG, desarrollado para FastEnvios Ltda.  
Utiliza LangChain + GitHub Models (GPT-4.1) + ChromaDB para responder consultas basándose en documentación interna de la empresa.

Descripción del proyecto

Fasty es el asistente virtual de FastEnvios Ltda., una empresa chilena de despacho a domicilio. El sistema:

-Clasifica la intención del cliente (seguimiento, reclamo, política de envío)
-Recupera información relevante desde documentos internos usando búsqueda semántica
-Genera respuestas precisas citando siempre la fuente documental
-Deriva a un ejecutivo humano cuando la consulta supera su conocimiento



Tecnologías utilizadas

| Componente | Tecnología |
|---|---|
| Framework RAG | LangChain |
| Modelo LLM | GPT-4.1 (via GitHub Models) |
| Embeddings | text-embedding-3-small |
| Base de datos vectorial | ChromaDB |
| API Backend | FastAPI |
| Lenguaje | Python 3.12+ |

Estructura del proyecto

```
fastenvios-rag/
│
├── app.py                  Sistema RAG principal
├── .env                    Variables de entorno (NO subir a GitHub)
├── .gitignore              Archivos excluidos del repositorio
├── README.md               Este archivo
│
├── documentos/             Base documental interna de FastEnvios
│   ├── politicas_envio.txt
│   ├── preguntas_frecuentes.txt
│   └── reglamento_reclamos.txt
│
└── chroma_db/              Base de datos vectorial (se genera automáticamente)
```

Requisitos previos
-Python 3.12 o superior
-Cuenta en GitHub con acceso a [GitHub Models](https://github.com/marketplace/models)
-Token de GitHub (`ghp_...`)

Instalación y ejecución

1. Clonar el repositorio

```bash
git clone https://github.com/pri-calderonn/FastEnviosLtda.git
cd fastenvios-rag
```

2. Crear y activar el entorno virtual

```bash
# Crear entorno virtual
python -m venv venv

# Activar en Windows
venv\Scripts\activate

# Activar en Mac/Linux
source venv/bin/activate
```

3. Instalar dependencias

pip install langchain langchain-openai langchain-community chromadb openai fastapi uvicorn python-dotenv


4. Configurar variables de entorno

Crea un archivo `.env` en la raíz del proyecto con el siguiente contenido:

```dotenv
GITHUB_TOKEN=ghp_tuTokenAqui
GITHUB_BASE_URL=https://models.inference.ai.azure.com
OPENAI_BASE_URL=https://models.inference.ai.azure.com
OPENAI_EMBEDDINGS_URL=https://models.inference.ai.azure.com
```

5. Ejecutar el sistema

python app.py


La primera vez generará los embeddings y creará la base de datos vectorial (tarda ~30 segundos).  
Las ejecuciones siguientes cargan la base existente y arrancan de inmediato.

Uso del asistente

Al ejecutar `app.py` se abre una interfaz de conversación en la terminal:

```
=======================================================
  FASTY — Asistente Virtual de FastEnvios Ltda.
=======================================================
  Escribe tu consulta y presiona Enter.
  Escribe 'salir' para terminar.

Cliente: ¿Cuánto demora un envío a regiones?
   [Intención detectada: politica_envio]

Fasty: Los envíos a regiones tienen un plazo de 3 a 5 días hábiles...
         [Manual de Políticas de Envío, Sección 2]

Fuentes consultadas:
   • politicas_envio.txt
-------------------------------------------------------
```

Para salir escribe `salir` o presiona `Ctrl+C`.

---

Clasificador de intención

El sistema detecta automáticamente el tipo de consulta:

| Intención | Palabras clave detectadas |
|---|---|
| `seguimiento` | seguimiento, dónde está, mi pedido, tracking |
| `reclamo` | reclamo, problema, queja, dañado, perdido |
| `politica_envio` | cuánto demora, días, plazo, costo, despacho |
| `general` | cualquier otra consulta |

---

Arquitectura del sistema

```
Usuario → Frontend/chat
    ↓
API FastAPI → recibe la consulta
    ↓              ↓
Clasificador    Base documental
de intención    (políticas, FAQs, contratos)
    ↓              ↓
        Embeddings (text-embedding-3-small)
              ↓
           ChromaDB (recuperación semántica)
              ↓
           GPT-4.1 (generación de respuesta)
              ↓                    ↓
        Respuesta con         Ejecutivo
        cita documental    (caso complejo)
```



Evidencia de pruebas

El sistema fue probado con las siguientes consultas:

- Consultas sobre políticas de envío
- Consultas sobre estado de pedidos
- Consultas sobre reclamos y devoluciones
- Consultas sin información disponible (deriva a ejecutivo)



Autores

- Priscila Calderón
- Gustavo Soto

Asignatura: Ingeniería de Soluciones con IA  
Instituto: DuocUC — 2026