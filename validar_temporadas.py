from pathlib import Path

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


ARCHIVO_DATOS = Path("data") / "dataset_entrenamiento.csv"

VARIABLES = [
    "porcentaje_visitante",
    "porcentaje_local",
    "forma_visitante",
    "forma_local",
    "carreras_anotadas_visitante",
    "carreras_anotadas_local",
    "carreras_permitidas_visitante",
    "carreras_permitidas_local",
]


def crear_modelo():
    return Pipeline(
        [
            ("escalador", StandardScaler()),
            (
                "modelo",
                LogisticRegression(
                    max_iter=2000,
                    random_state=42,
                ),
            ),
        ]
    )


datos = pd.read_csv(ARCHIVO_DATOS)

temporadas_prueba = [2024, 2025, 2026]
resultados = []

for temporada in temporadas_prueba:
    entrenamiento = datos[datos["temporada"] < temporada]
    prueba = datos[datos["temporada"] == temporada]

    if entrenamiento.empty or prueba.empty:
        continue

    x_entrenamiento = entrenamiento[VARIABLES]
    y_entrenamiento = entrenamiento["gano_local"]

    x_prueba = prueba[VARIABLES]
    y_prueba = prueba["gano_local"]

    modelo = crear_modelo()
    modelo.fit(x_entrenamiento, y_entrenamiento)

    probabilidades = modelo.predict_proba(x_prueba)[:, 1]
    predicciones = (probabilidades >= 0.5).astype(int)

    exactitud = accuracy_score(y_prueba, predicciones)
    base_local = y_prueba.mean()
    perdida = log_loss(y_prueba, probabilidades)
    brier = brier_score_loss(y_prueba, probabilidades)

    resultados.append(
        {
            "temporada": temporada,
            "juegos": len(prueba),
            "base_local": base_local,
            "exactitud": exactitud,
            "mejora": exactitud - base_local,
            "log_loss": perdida,
            "brier": brier,
        }
    )

    print("=" * 50)
    print(f"Temporada probada: {temporada}")
    print(f"Juegos de prueba: {len(prueba)}")
    print(f"Base siempre local: {base_local * 100:.2f}%")
    print(f"Exactitud del modelo: {exactitud * 100:.2f}%")
    print(f"Mejora sobre la base: {(exactitud - base_local) * 100:+.2f}%")
    print(f"Pérdida logarítmica: {perdida:.4f}")
    print(f"Puntuación Brier: {brier:.4f}")

tabla = pd.DataFrame(resultados)

print("=" * 50)
print("RESUMEN")
print(f"Exactitud promedio: {tabla['exactitud'].mean() * 100:.2f}%")
print(f"Base local promedio: {tabla['base_local'].mean() * 100:.2f}%")
print(f"Mejora promedio: {tabla['mejora'].mean() * 100:+.2f}%")