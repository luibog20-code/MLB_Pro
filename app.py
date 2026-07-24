import subprocess
import sys
from pathlib import Path
from PIL import Image

import pandas as pd
import streamlit as st


ARCHIVO_PRONOSTICOS = Path("data") / "pronosticos.csv"
ARCHIVO_RESULTADOS = Path("data") / "resultados.csv"
def mostrar_mercado_y_valor(ultimo, pronosticos):
    if "cuota" not in pronosticos.columns:
        return

    cuota = ultimo.get("cuota")

    if pd.isna(cuota) or str(cuota).strip() == "":
        return

    st.markdown("### Mercado y valor")

    columna_1, columna_2, columna_3, columna_4 = (
        st.columns(4)
    )

    with columna_1:
        st.metric(
            "Selección de valor",
            ultimo.get("seleccion_valor", "N/D"),
        )

    with columna_2:
        st.metric(
            "Mejor cuota",
            f"{float(cuota):+.0f}",
        )

    with columna_3:
        st.metric(
            "Casa",
            ultimo.get("casa", "N/D"),
        )

    with columna_4:
        st.metric(
            "Valor esperado",
            (
                f"{float(ultimo['valor_esperado']):+.1f}%"
            ),
        )

    st.write(
        f"**Mercado sin margen:** "
        f"{ultimo['visitante']} "
        f"{float(ultimo['mercado_visitante']):.1f}% | "
        f"{ultimo['local']} "
        f"{float(ultimo['mercado_local']):.1f}%"
    )

    st.write(
        f"**Ventaja IA frente al mercado:** "
        f"{float(ultimo['ventaja_mercado']):+.1f} puntos"
    )

    st.warning(
        f"Decisión: "
        f"{ultimo.get('decision_valor', 'N/D')}. "
        "Esta señal todavía es experimental."
    )
ICONO_APP = Image.open(Path("assets") / "mlb-pro-ai-icon.png")
st.set_page_config(
    page_title="MLB Pro AI",
    page_icon=ICONO_APP,
    layout="wide",
)

st.title("⚾ MLB Pro AI")
st.caption("Pronósticos y seguimiento de juegos MLB")
columna_generar, columna_resultados, columna_refrescar = st.columns(3)

with columna_generar:
    if st.button(
        "Generar pronósticos",
        use_container_width=True,
    ):
        with st.spinner("Analizando juegos..."):
            proceso = subprocess.run(
                [sys.executable, "juegos_hoy.py"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )

        if proceso.returncode == 0:
            st.success("Pronósticos actualizados.")
        else:
            st.error("No se pudieron generar los pronósticos.")
            st.code(proceso.stderr)

with columna_resultados:
    if st.button(
        "Actualizar resultados",
        use_container_width=True,
    ):
        with st.spinner("Consultando resultados..."):
            proceso = subprocess.run(
                [sys.executable, "actualizar_resultados.py"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )

        if proceso.returncode == 0:
            st.success("Resultados consultados.")
            st.code(proceso.stdout)
        else:
            st.error("No se pudieron actualizar los resultados.")
            st.code(proceso.stderr)

with columna_refrescar:
    if st.button(
        "Refrescar pantalla",
        use_container_width=True,
    ):
        st.rerun()

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
        ultimo = pronosticos.iloc[-1]

        st.markdown("#### Último pronóstico de IA")

        columna_1, columna_2, columna_3 = st.columns(3)

        with columna_1:
            st.metric(
                "Ganador previsto",
                ultimo["ganador_pronosticado"],
            )

        with columna_2:
            st.metric(
                "Probabilidad",
                f"{ultimo['probabilidad']}%",
            )

        with columna_3:
            st.metric(
                "Recomendación",
                ultimo["recomendacion"],
            )

        juego = (
            f"{ultimo['visitante']} vs. "
            f"{ultimo['local']}"
        )
        st.write(f"**Juego:** {juego}")

        if ultimo["recomendacion"] == "No apostar":
            st.warning(
                "La ventaja calculada no es suficiente "
                "para recomendar una selección."
            )
        else:
            st.success(
                "La IA detectó una ventaja estadística suficiente."
            )
        mostrar_mercado_y_valor(ultimo, pronosticos)
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