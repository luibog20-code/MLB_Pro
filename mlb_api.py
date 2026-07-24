import requests
from datetime import date, timedelta

URL_CALENDARIO = "https://statsapi.mlb.com/api/v1/schedule"


def obtener_juegos(fecha):
    parametros = {
        "sportId": 1,
        "date": fecha,
        "hydrate": "probablePitcher"
    }

    respuesta = requests.get(
        URL_CALENDARIO,
        params=parametros,
        timeout=20
    )
    respuesta.raise_for_status()

    datos = respuesta.json()

    if not datos.get("dates"):
        return []

    return datos["dates"][0]["games"]
def obtener_estadisticas_temporada(url, grupo):
    parametros = {
        "stats": "season",
        "group": grupo,
        "season": date.today().year
    }

    respuesta = requests.get(
        url,
        params=parametros,
        timeout=20
    )
    respuesta.raise_for_status()

    datos = respuesta.json()

    if not datos.get("stats"):
        return {}

    resultados = datos["stats"][0].get("splits", [])

    if not resultados:
        return {}

    return resultados[0]["stat"]
def obtener_estadisticas_pitcher(pitcher_id):
    if pitcher_id is None:
        return {}

    url = (
        f"https://statsapi.mlb.com/api/v1/people/{pitcher_id}/stats"
    )

    return obtener_estadisticas_temporada(url, "pitching")


def obtener_estadisticas_bateo(equipo_id):
    url = (
        f"https://statsapi.mlb.com/api/v1/teams/{equipo_id}/stats"
    )
    return obtener_estadisticas_temporada(url, "hitting")   
def obtener_estadisticas_bullpen(equipo_id):
    url = (
        f"https://statsapi.mlb.com/api/v1/"
        f"teams/{equipo_id}/stats"
    )

    parametros = {
        "stats": "statSplits",
        "group": "pitching",
        "sitCodes": "rp",
        "season": date.today().year,
    }

    respuesta = requests.get(
        url,
        params=parametros,
        timeout=20,
    )
    respuesta.raise_for_status()

    datos = respuesta.json()

    if not datos.get("stats"):
        return {}

    resultados = datos["stats"][0].get("splits", [])

    if not resultados:
        return {}

    return resultados[0].get("stat", {})

def obtener_forma_reciente(equipo_id, cantidad=10):
    fecha_final = date.today()
    fecha_inicial = fecha_final - timedelta(days=20)

    parametros = {
        "sportId": 1,
        "teamId": equipo_id,
        "startDate": fecha_inicial.strftime("%Y-%m-%d"),
        "endDate": fecha_final.strftime("%Y-%m-%d"),
        "gameType": "R",
    }

    respuesta = requests.get(
        URL_CALENDARIO,
        params=parametros,
        timeout=20,
    )
    respuesta.raise_for_status()

    datos = respuesta.json()
    resultados = []

    for grupo_fecha in datos.get("dates", []):
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

            es_visitante = visitante["team"]["id"] == equipo_id

            if es_visitante:
                gano = carreras_visitante > carreras_local
            else:
                gano = carreras_local > carreras_visitante

            resultados.append(gano)

    resultados = resultados[-cantidad:]

    victorias = sum(resultados)
    derrotas = len(resultados) - victorias

    if resultados:
        porcentaje = victorias / len(resultados)
    else:
        porcentaje = 0

    return {
        "juegos": len(resultados),
        "victorias": victorias,
        "derrotas": derrotas,
        "porcentaje": porcentaje,
    }
