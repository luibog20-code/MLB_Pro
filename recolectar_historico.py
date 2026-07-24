import csv
from datetime import date, timedelta
from pathlib import Path

import requests


URL_CALENDARIO = "https://statsapi.mlb.com/api/v1/schedule"
ARCHIVO_HISTORICO = Path("data") / "juegos_historicos.csv"


def consultar_juegos_historicos(fecha_inicial, fecha_final):
    parametros = {
        "sportId": 1,
        "startDate": fecha_inicial,
        "endDate": fecha_final,
        "gameType": "R",
    }

    respuesta = requests.get(
        URL_CALENDARIO,
        params=parametros,
        timeout=30,
    )
    respuesta.raise_for_status()

    return respuesta.json()

def extraer_juegos_finalizados(datos):
    filas = []

    for grupo_fecha in datos.get("dates", []):
        fecha_juego = grupo_fecha["date"]

        for juego in grupo_fecha.get("games", []):
            estado = juego["status"]["detailedState"]

            if estado not in {
                "Final",
                "Game Over",
                "Completed Early",
            }:
                continue

            visitante = juego["teams"]["away"]
            local = juego["teams"]["home"]

            carreras_visitante = visitante.get("score")
            carreras_local = local.get("score")

            if (
                carreras_visitante is None
                or carreras_local is None
            ):
                continue
            gano_local = int(
                carreras_local > carreras_visitante
        )

            filas.append({
                "juego_id": juego["gamePk"],
                "fecha": fecha_juego,
                "visitante": visitante["team"]["name"],
                "local": local["team"]["name"],
                "id_visitante": visitante["team"]["id"],
                "id_local": local["team"]["id"],
                "carreras_visitante": carreras_visitante,
                "carreras_local": carreras_local,
                "gano_local": gano_local,
            })

    return filas


def guardar_juegos_historicos(filas):
    ARCHIVO_HISTORICO.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    juegos_existentes = set()

    if ARCHIVO_HISTORICO.exists():
        with ARCHIVO_HISTORICO.open(
            "r",
            newline="",
            encoding="utf-8-sig",
        ) as archivo:
            lector = csv.DictReader(archivo)

            for fila in lector:
                juegos_existentes.add(
                    fila["juego_id"]
                )
    filas_nuevas = [
        fila
        for fila in filas
        if str(fila["juego_id"])
        not in juegos_existentes
    ]

    if not filas_nuevas:
        return 0

    archivo_nuevo = not ARCHIVO_HISTORICO.exists()

    with ARCHIVO_HISTORICO.open(
        "a",
        newline="",
        encoding="utf-8-sig",
    ) as archivo:
        escritor = csv.DictWriter(
            archivo,
            fieldnames=filas_nuevas[0].keys(),
        )

        if archivo_nuevo:
            escritor.writeheader()

        escritor.writerows(filas_nuevas)

    return len(filas_nuevas)

def main():
    fecha_final = date.today() - timedelta(days=1)
    fecha_inicial = fecha_final - timedelta(days=30)

    print(
        f"Consultando desde {fecha_inicial} "
        f"hasta {fecha_final}..."
    )

    datos = consultar_juegos_historicos(
        fecha_inicial.isoformat(),
        fecha_final.isoformat(),
    )

    filas = extraer_juegos_finalizados(datos)
    cantidad_guardada = guardar_juegos_historicos(
        filas
    )

    print(f"Juegos encontrados: {len(filas)}")
    print(f"Juegos nuevos guardados: {cantidad_guardada}")
    print(f"Archivo: {ARCHIVO_HISTORICO}")


if __name__ == "__main__":
    main()