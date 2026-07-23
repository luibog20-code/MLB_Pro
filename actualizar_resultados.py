import csv
from pathlib import Path

from resultados import obtener_resultado


ARCHIVO_PRONOSTICOS = Path("data") / "pronosticos.csv"
ARCHIVO_RESULTADOS = Path("data") / "resultados.csv"

CAMPOS_RESULTADOS = [
    "juego_id",
    "fecha",
    "visitante",
    "local",
    "ganador_pronosticado",
    "probabilidad",
    "recomendacion",
    "carreras_visitante",
    "carreras_local",
    "ganador_real",
    "acertado",
]

def actualizar_resultados():
    if not ARCHIVO_PRONOSTICOS.exists():
        print("No existe el archivo de pronósticos.")
        return

    with ARCHIVO_PRONOSTICOS.open(
        "r",
        newline="",
        encoding="utf-8-sig",
    ) as archivo:
        pronosticos = list(csv.DictReader(archivo))

    resultados_finales = []

    for pronostico in pronosticos:
        juego_id = pronostico["juego_id"]
        resultado = obtener_resultado(juego_id)

        if not resultado["terminado"]:
            print(
                f"Juego {juego_id}: "
                f"{resultado['estado']} - pendiente."
            )
            continue

        acertado = (
            pronostico["ganador_pronosticado"]
            == resultado["ganador_real"]
        )

        resultados_finales.append({
            **pronostico,
            "carreras_visitante": resultado["carreras_visitante"],
            "carreras_local": resultado["carreras_local"],
            "ganador_real": resultado["ganador_real"],
            "acertado": "Sí" if acertado else "No",
        })

    if not resultados_finales:
        print("Todavia no hay resultados finales para guardar.")
        return

    with ARCHIVO_RESULTADOS.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as archivo:
        escritor = csv.DictWriter(
            archivo,
            fieldnames=CAMPOS_RESULTADOS,
            extrasaction="ignore",
        )
        escritor.writeheader()
        escritor.writerows(resultados_finales)

    print(
        f"Resultados actualizados: "
        f"{len(resultados_finales)}"
    )


if __name__ == "__main__":
    actualizar_resultados()