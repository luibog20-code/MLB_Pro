from pathlib import Path

import pandas as pd
import streamlit as st


ARCHIVO_PRONOSTICOS = Path("data") / "pronosticos.csv"
ARCHIVO_RESULTADOS = Path("data") / "resultados.csv"

st.set_page_config(
    page_title="MLB Pro AI",
    page_icon="⚾",
    layout="wide",
)

st.title("⚾ MLB Pro AI")
st.caption("Pronósticos y seguimiento de juegos MLB")

pestana_pronosticos, pestana_resultados = st.tabs(
    ["Pronósticos", "Resultados"]
)

with pestana_pronosticos:
    st.subheader("Pronósticos registrados")

    if ARCHIVO_PRONOSTICOS.exists():
        pronosticos = pd.read_csv(ARCHIVO_PRONOSTICOS)

        st.metric(
            "Pronósticos guardados",
            len(pronosticos),
        )

        st.dataframe(
            pronosticos,
            width="stretch",
            hide_index=True,
        )
    else:
        st.info("Todavía no existen pronósticos guardados.")

with pestana_resultados:
    st.subheader("Resultados finales")

    if ARCHIVO_RESULTADOS.exists():
        resultados = pd.read_csv(ARCHIVO_RESULTADOS)

        st.metric(
            "Resultados registrados",
            len(resultados),
        )

        st.dataframe(
            resultados,
            width="stretch",
            hide_index=True,
        )
    else:
        st.info(
            "Los resultados aparecerán cuando terminen "
            "los juegos pronosticados."
        )

st.caption(
    "Modelo preliminar en desarrollo. "
    "No garantiza resultados ni ganancias."
)