import requests


URL_JUEGO = "https://statsapi.mlb.com/api/v1.1/game/{}/feed/live"

ESTADOS_FINALES = {
    "Final",
    "Game Over",
    "Completed Early",
}


def obtener_resultado(juego_id):
    url = URL_JUEGO.format(juego_id)

    respuesta = requests.get(
        url,
        timeout=20,
    )
    respuesta.raise_for_status()

    datos = respuesta.json()

    estado = (
        datos.get("gameData", {})
        .get("status", {})
        .get("detailedState", "Desconocido")
    )

    if estado not in ESTADOS_FINALES:
        return {
            "terminado": False,
            "estado": estado,
        }

    lineas = datos.get("liveData", {}).get("linescore", {})
    equipos = lineas.get("teams", {})

    carreras_visitante = equipos.get("away", {}).get("runs")
    carreras_local = equipos.get("home", {}).get("runs")

    nombres = datos.get("gameData", {}).get("teams", {})
    visitante = nombres.get("away", {}).get("name", "Visitante")
    local = nombres.get("home", {}).get("name", "Local")

    if carreras_visitante > carreras_local:
        ganador = visitante
    else:
        ganador = local

    return {
        "terminado": True,
        "estado": estado,
        "visitante": visitante,
        "local": local,
        "carreras_visitante": carreras_visitante,
        "carreras_local": carreras_local,
        "ganador_real": ganador,
    }