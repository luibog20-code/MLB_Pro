import requests
from datetime import date


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
