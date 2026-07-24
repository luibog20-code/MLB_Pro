from collections import defaultdict, deque
from pathlib import Path

import pandas as pd


ARCHIVO_JUEGOS = Path("data") / "juegos_historicos.csv"
ARCHIVO_DATASET = Path("data") / "dataset_entrenamiento.csv"
VENTANA_RECIENTE = 10

def crear_estado_equipo():
    return {
        "juegos": 0,
        "victorias": 0,
        "carreras_anotadas": 0,
        "carreras_permitidas": 0,
        "ultimos_resultados": deque(
            maxlen=VENTANA_RECIENTE
        ),
    }

def resumir_estado(estado):
    juegos = estado["juegos"]

    if juegos == 0:
        return {
            "porcentaje_victorias": 0.5,
            "forma_reciente": 0.5,
            "carreras_anotadas_promedio": 0.0,
            "carreras_permitidas_promedio": 0.0,
        }

    resultados = estado["ultimos_resultados"]

    if resultados:
        forma_reciente = (
            sum(resultados) / len(resultados)
        )
    else:
        forma_reciente = 0.5

    return {
        "porcentaje_victorias": (
            estado["victorias"] / juegos
        ),
        "forma_reciente": forma_reciente,
        "carreras_anotadas_promedio": (
            estado["carreras_anotadas"] / juegos
        ),
        "carreras_permitidas_promedio": (
            estado["carreras_permitidas"] / juegos
        ),
    }

def actualizar_estado(
    estado,
    carreras_anotadas,
    carreras_permitidas,
    gano,
):
    estado["juegos"] += 1
    estado["victorias"] += int(gano)
    estado["carreras_anotadas"] += carreras_anotadas
    estado["carreras_permitidas"] += carreras_permitidas
    estado["ultimos_resultados"].append(
        int(gano)
    )

def preparar_dataset():
        if not ARCHIVO_JUEGOS.exists():
            print("No existe el archivo de juegos históricos.")
            return

        juegos = pd.read_csv(ARCHIVO_JUEGOS)
        juegos = juegos.sort_values(
            ["fecha", "juego_id"]
        )

        estados = defaultdict(crear_estado_equipo)
        temporada_actual = None
        filas_dataset = []

        for _, juego in juegos.iterrows():
            temporada = int(
                str(juego["fecha"])[:4]
            )

            if temporada != temporada_actual:
                estados = defaultdict(
                    crear_estado_equipo
                )
                temporada_actual = temporada

            id_visitante = int(juego["id_visitante"])
            id_local = int(juego["id_local"])

            estado_visitante = estados[id_visitante]
            estado_local = estados[id_local]

            previo_visitante = resumir_estado(
                    estado_visitante
                )
            previo_local = resumir_estado(
                    estado_local
                )
            fila_dataset = {
                    "juego_id": int(juego["juego_id"]),
                    "fecha": juego["fecha"],
                    "temporada": temporada,
                    "juegos_previos_visitante": (
                        estado_visitante["juegos"]
                    ),
                    "juegos_previos_local": (
                        estado_local["juegos"]
                    ),
                    "porcentaje_visitante": (
                        previo_visitante["porcentaje_victorias"]
                    ),
                    "porcentaje_local": (
                        previo_local["porcentaje_victorias"]
                    ),
                    "forma_visitante": (
                        previo_visitante["forma_reciente"]
                    ),
                    "forma_local": (
                        previo_local["forma_reciente"]
                    ),
                    "gano_local": int(juego["gano_local"]),
                }

            filas_dataset.append(fila_dataset)
            carreras_visitante = int(
                    juego["carreras_visitante"]
                )
            carreras_local = int(
                    juego["carreras_local"]
                )
            gano_local = int(juego["gano_local"])
            gano_visitante = 1 - gano_local

            actualizar_estado(
                    estado_visitante,
                    carreras_visitante,
                    carreras_local,
                    gano_visitante,
                )

            actualizar_estado(
                    estado_local,
                    carreras_local,
                    carreras_visitante,
                    gano_local,
                )

        dataset = pd.DataFrame(filas_dataset)

        dataset = dataset[
            (
                dataset["juegos_previos_visitante"]
                >= VENTANA_RECIENTE
            )
            & (
                dataset["juegos_previos_local"]
                >= VENTANA_RECIENTE
            )
        ].copy()

        dataset.to_csv(
            ARCHIVO_DATASET,
            index=False,
            encoding="utf-8-sig",
        )

        print(f"Juegos originales: {len(juegos)}")
        print(f"Filas para entrenar: {len(dataset)}")
        print(f"Archivo creado: {ARCHIVO_DATASET}")
if __name__ == "__main__":
    preparar_dataset()
    