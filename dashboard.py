
import pandas as pd
import streamlit as st
from observabilidad import leer_eventos

st.set_page_config(page_title="Fasty — Dashboard de Observabilidad", layout="wide")

st.title("Fasty — Dashboard de Observabilidad")
st.caption("FastEnvios Ltda. · Evaluación Parcial N°3 · ISY0101")

eventos = leer_eventos()

if not eventos:
    st.warning(
        "No hay datos en `logs/observabilidad.jsonl` todavía. "
        "Corre primero `python generar_trafico_prueba.py`."
    )
    st.stop()

df = pd.DataFrame(eventos)
df["timestamp"] = pd.to_datetime(df["timestamp"], format="mixed")


#Filtros
with st.sidebar:
    st.header("Filtros")
    intenciones_disponibles = sorted(df["intencion"].unique())
    intenciones_sel = st.multiselect(
        "Intención", intenciones_disponibles, default=intenciones_disponibles
    )

df_filtrado = df[df["intencion"].isin(intenciones_sel)]

#Métricas principales (KPIs)
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total de interacciones", len(df_filtrado))
col2.metric("Latencia promedio", f"{df_filtrado['latencia_total_seg'].mean():.2f} s")
col3.metric("Tasa de error", f"{df_filtrado['error'].mean():.1%}")
col4.metric(
    "Tokens totales",
    f"{int(df_filtrado['tokens_entrada'].sum() + df_filtrado['tokens_salida'].sum()):,}",
)

st.divider()

#Latencia en el tiempo
st.subheader("Latencia por interacción")
st.line_chart(df_filtrado.set_index("timestamp")["latencia_total_seg"])

col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Distribución de intenciones")
    conteo_intenciones = df_filtrado["intencion"].value_counts()
    st.bar_chart(conteo_intenciones)

with col_b:
    st.subheader("Herramientas utilizadas")
    herramientas_planas = df_filtrado["herramientas_usadas"].explode().dropna()
    if not herramientas_planas.empty:
        st.bar_chart(herramientas_planas.value_counts())
    else:
        st.info("Sin herramientas registradas en la selección actual.")

st.divider()

#Calidad: precisión y errores
col_c, col_d = st.columns(2)

with col_c:
    st.subheader("Uso de fuentes documentales")
    st.bar_chart(df_filtrado["uso_fuente_documental"].value_counts())

with col_d:
    st.subheader("Posibles fallas de precisión")
    tasa_falla = df_filtrado["posible_falla_precision"].mean()
    st.metric("Tasa de posible falla de precisión", f"{tasa_falla:.1%}")
    if tasa_falla > 0:
        st.dataframe(
            df_filtrado[df_filtrado["posible_falla_precision"]][
                ["trace_id", "consulta", "intencion"]
            ],
            use_container_width=True,
        )

st.divider()

#Tabla de eventos con trazabilidad completa
st.subheader("Trazabilidad completa (logs)")
st.dataframe(
    df_filtrado[
        [
            "trace_id", "timestamp", "session_id", "consulta", "intencion",
            "herramientas_usadas", "latencia_total_seg", "tokens_totales",
            "uso_fuente_documental", "error", "tipo_error",
        ]
    ].sort_values("timestamp", ascending=False),
    use_container_width=True,
)