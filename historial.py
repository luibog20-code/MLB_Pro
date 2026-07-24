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

    filas_existentes = []
    campos_existentes = []

    if ARCHIVO_PRONOSTICOS.exists():
        with ARCHIVO_PRONOSTICOS.open(
            "r",
            newline="",
            encoding="utf-8-sig",
        ) as archivo:
            lector = csv.DictReader(archivo)
            campos_existentes = lector.fieldnames or []
            filas_existentes = list(lector)

    juego_id = str(fila.get("juego_id"))

    fila_actualizada = {
        clave: "" if valor is None else str(valor)
        for clave, valor in fila.items()
    }

    encontrado = False

    for indice, fila_existente in enumerate(
        filas_existentes
    ):
        if fila_existente.get("juego_id") == juego_id:
            fila_existente.update(fila_actualizada)
            filas_existentes[indice] = fila_existente
            encontrado = True
            break

    if not encontrado:
        filas_existentes.append(fila_actualizada)

    campos = list(
        dict.fromkeys(
            [
                *campos_existentes,
                *fila_actualizada.keys(),
            ]
        )
    )

    with ARCHIVO_PRONOSTICOS.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as archivo:
        escritor = csv.DictWriter(
            archivo,
            fieldnames=campos,
            extrasaction="ignore",
        )
        escritor.writeheader()
        escritor.writerows(filas_existentes)

    return True