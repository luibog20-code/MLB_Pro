from pathlib import Path

import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    log_loss,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


ARCHIVO_DATASET = Path("data") / "dataset_entrenamiento.csv"
ARCHIVO_MODELO = Path("models") / "modelo_mlb.joblib"

VARIABLES = [
    "descanso_visitante",
    "descanso_local",
    "porcentaje_visitante",
    "porcentaje_local",
    "forma_visitante",
    "forma_local",
    "carreras_anotadas_visitante",
    "carreras_anotadas_local",
    "carreras_permitidas_visitante",
    "carreras_permitidas_local",
]

OBJETIVO = "gano_local"
TEMPORADA_PRUEBA = 2026

def entrenar():
    if not ARCHIVO_DATASET.exists():
        print("No existe el dataset de entrenamiento.")
        return

    datos = pd.read_csv(ARCHIVO_DATASET)

    entrenamiento = datos[
        datos["temporada"] < TEMPORADA_PRUEBA
    ].copy()

    prueba = datos[
        datos["temporada"] == TEMPORADA_PRUEBA
    ].copy()

    if entrenamiento.empty or prueba.empty:
        print("No hay suficientes datos para entrenar y probar.")
        return

    x_entrenamiento = entrenamiento[VARIABLES]
    y_entrenamiento = entrenamiento[OBJETIVO]

    x_prueba = prueba[VARIABLES]
    y_prueba = prueba[OBJETIVO]
    modelo = Pipeline([
        ("escalador", StandardScaler()),
        (
            "clasificador",
            LogisticRegression(
                max_iter=2000,
                random_state=42,
            ),
        ),
    ])

    modelo.fit(
        x_entrenamiento,
        y_entrenamiento,
    )

    probabilidades = modelo.predict_proba(
        x_prueba
    )[:, 1]

    predicciones = (
        probabilidades >= 0.5
    ).astype(int)

    exactitud = accuracy_score(
        y_prueba,
        predicciones,
    )
    perdida_logaritmica = log_loss(
        y_prueba,
        probabilidades,
    )
    brier = brier_score_loss(
        y_prueba,
        probabilidades,
    )
    ARCHIVO_MODELO.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    paquete_modelo = {
        "modelo": modelo,
        "variables": VARIABLES,
        "temporada_prueba": TEMPORADA_PRUEBA,
    }

    joblib.dump(
        paquete_modelo,
        ARCHIVO_MODELO,
    )

    print(f"Juegos de entrenamiento: {len(entrenamiento)}")
    print(f"Juegos de prueba: {len(prueba)}")
    print(f"Exactitud: {exactitud:.2%}")
    print(
        "Pérdida logarítmica: "
        f"{perdida_logaritmica:.4f}"
    )
    print(f"Puntuación Brier: {brier:.4f}")
    print(f"Modelo guardado: {ARCHIVO_MODELO}")


if __name__ == "__main__":
    entrenar()   