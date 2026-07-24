import os
import subprocess
import sys
import json
from pathlib import Path
from dotenv import load_dotenv
from PIL import Image

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
load_dotenv()


ARCHIVO_PRONOSTICOS = Path("data") / "pronosticos.csv"
ARCHIVO_RESULTADOS = Path("data") / "resultados.csv"


def configurar_instalacion_movil():
    manifiesto = {
        "name": "MLB Pro AI",
        "short_name": "MLB Pro AI",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#071a3d",
        "theme_color": "#071a3d",
        "icons": [
            {
                "src": "/app/static/mlb-pro-ai-192.png",
                "sizes": "192x192",
                "type": "image/png",
            },
            {
                "src": "/app/static/mlb-pro-ai-512.png",
                "sizes": "512x512",
                "type": "image/png",
            },
        ],
    }
    manifiesto_json = json.dumps(
        manifiesto,
        ensure_ascii=False,
    )

    components.html(
        f"""
        <script>
        const head = window.parent.document.head;

        function agregarEnlace(rel, href, sizes = "") {{
            let enlace = head.querySelector(
                `link[rel="${{rel}}"]`
            );
            if (!enlace) {{
                enlace = window.parent.document.createElement("link");
                enlace.rel = rel;
                head.appendChild(enlace);
            }}
            enlace.href = href;
            if (sizes) enlace.sizes = sizes;
        }}

        agregarEnlace(
            "apple-touch-icon",
            "/app/static/mlb-pro-ai-180.png",
            "180x180"
        );

        const manifiesto = {manifiesto_json};
        const manifiestoUrl =
            "data:application/manifest+json;charset=utf-8,"
            + encodeURIComponent(JSON.stringify(manifiesto));
        agregarEnlace("manifest", manifiestoUrl);

        let tema = head.querySelector('meta[name="theme-color"]');
        if (!tema) {{
            tema = window.parent.document.createElement("meta");
            tema.name = "theme-color";
            head.appendChild(tema);
        }}
        tema.content = "#071a3d";
        </script>
        """,
        height=0,
        width=0,
    )


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
configurar_instalacion_movil()

st.title("⚾ MLB Pro AI")
st.caption("Pronósticos y seguimiento de juegos MLB")
pin_guardado = os.getenv("APP_ADMIN_PIN", "")

pin_ingresado = st.text_input(
    "Código privado para actualizar datos",
    type="password",
    placeholder="Escribe tu código privado",
)

acceso_admin = (
    bool(pin_guardado)
    and pin_ingresado == pin_guardado
)

if pin_ingresado and not acceso_admin:
    st.error("Código privado incorrecto.")
columna_generar, columna_resultados, columna_refrescar = st.columns(3)

with columna_generar:
    if st.button(
        "Generar pronósticos",
        use_container_width=True,
        disabled=not acceso_admin,
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
        disabled=not acceso_admin,
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
