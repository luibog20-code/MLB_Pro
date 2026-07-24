from pathlib import Path

import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


ARCHIVO_DATOS = Path("data") / "dataset_entrenamiento.csv"
TEMPORADA_PRUEBA = 2026

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


def evaluar(nombre, modelo, x_entrenamiento, y_entrenamiento, x_prueba, y_prueba):
    modelo.fit(x_entrenamiento, y_entrenamiento)

    probabilidades = modelo.predict_proba(x_prueba)[:, 1]
    predicciones = (probabilidades >= 0.5).astype(int)

    print("=" * 45)
    print(nombre)
    print(f"Exactitud: {accuracy_score(y_prueba, predicciones) * 100:.2f}%")
    print(f"Pérdida logarítmica: {log_loss(y_prueba, probabilidades):.4f}")
    print(f"Puntuación Brier: {brier_score_loss(y_prueba, probabilidades):.4f}")


datos = pd.read_csv(ARCHIVO_DATOS)

entrenamiento = datos[datos["temporada"] < TEMPORADA_PRUEBA]
prueba = datos[datos["temporada"] == TEMPORADA_PRUEBA]

x_entrenamiento = entrenamiento[VARIABLES]
y_entrenamiento = entrenamiento["gano_local"]

x_prueba = prueba[VARIABLES]
y_prueba = prueba["gano_local"]

modelo_logistico = Pipeline(
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

modelo_gradiente = HistGradientBoostingClassifier(
    learning_rate=0.05,
    max_iter=200,
    max_leaf_nodes=15,
    min_samples_leaf=30,
    random_state=42,
)

print(f"Entrenamiento: {len(entrenamiento)} juegos")
print(f"Prueba: {len(prueba)} juegos")
print(f"Base elegir siempre local: {y_prueba.mean() * 100:.2f}%")

evaluar(
    "Regresión logística",
    modelo_logistico,
    x_entrenamiento,
    y_entrenamiento,
    x_prueba,
    y_prueba,
)

evaluar(
    "Gradiente inteligente",
    modelo_gradiente,
    x_entrenamiento,
    y_entrenamiento,
    x_prueba,
    y_prueba,
)