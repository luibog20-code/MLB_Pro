from pathlib import Path

import joblib
import pandas as pd


ARCHIVO_MODELO = Path("models") / "modelo_mlb.joblib"


def cargar_modelo():
    if not ARCHIVO_MODELO.exists():
        raise FileNotFoundError(
            f"No existe el modelo: {ARCHIVO_MODELO}"
        )

    return joblib.load(ARCHIVO_MODELO)


def predecir_juego(
    visitante,
    local,
    datos_juego,
):
    paquete = cargar_modelo()
    modelo = paquete["modelo"]
    variables = paquete["variables"]

    faltantes = [
        variable
        for variable in variables
        if variable not in datos_juego
    ]

    if faltantes:
        raise ValueError(
            "Faltan variables para la predicción: "
            + ", ".join(faltantes)
        )

    fila = pd.DataFrame(
        [
            {
                variable: datos_juego[variable]
                for variable in variables
            }
        ]
    )

    probabilidad_local = float(
        modelo.predict_proba(fila)[0][1]
    )
    probabilidad_visitante = 1 - probabilidad_local

    if probabilidad_local >= probabilidad_visitante:
        ganador = local
        probabilidad_ganador = probabilidad_local
    else:
        ganador = visitante
        probabilidad_ganador = probabilidad_visitante

    if probabilidad_ganador < 0.55:
        recomendacion = "No apostar"
    elif probabilidad_ganador < 0.60:
        recomendacion = "Confianza baja"
    else:
        recomendacion = "Confianza moderada"

    return {
        "ganador": ganador,
        "probabilidad": round(
            probabilidad_ganador * 100,
            1,
        ),
        "probabilidad_visitante": round(
            probabilidad_visitante * 100,
            1,
        ),
        "probabilidad_local": round(
            probabilidad_local * 100,
            1,
        ),
        "recomendacion": recomendacion,
    }