import csv
from pathlib import Path


ARCHIVO_PRONOSTICOS = Path("data") / "pronosticos.csv"

CAMPOS = [
    "juego_id",
    "fecha",
    "visitante",
    "local",
    "ganador_pronosticado",
    "probabilidad",
    "recomendacion",
]


def guardar_pronostico(fila):
    ARCHIVO_PRONOSTICOS.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if ARCHIVO_PRONOSTICOS.exists():
        with ARCHIVO_PRONOSTICOS.open(
            "r",
            newline="",
            encoding="utf-8-sig",
        ) as archivo:
            lector = csv.DictReader(archivo)

            for fila_existente in lector:
                if fila_existente.get("juego_id") == str(
                    fila.get("juego_id")
                ):
                    return False

    archivo_nuevo = not ARCHIVO_PRONOSTICOS.exists()

    with ARCHIVO_PRONOSTICOS.open(
        "a",
        newline="",
        encoding="utf-8-sig",
    ) as archivo:
        escritor = csv.DictWriter(
            archivo,
            fieldnames=CAMPOS,
            extrasaction="ignore",
        )

        if archivo_nuevo:
            escritor.writeheader()

        escritor.writerow(fila)

    return True