from collections import defaultdict, deque
from datetime import date, timedelta

import requests


URL_CALENDARIO = "https://statsapi.mlb.com/api/v1/schedule"
VENTANA_RECIENTE = 10


def crear_estado():
    return {
        "juegos": 0,
        "victorias": 0,
        "carreras_anotadas": 0,
        "carreras_permitidas": 0,
        "ultimos_resultados": deque(
            maxlen=VENTANA_RECIENTE
        ),
        "ultima_fecha": None,
    }


def descargar_juegos_finalizados(fecha_objetivo):
    inicio = date(fecha_objetivo.year, 3, 1)
    fin = fecha_objetivo - timedelta(days=1)

    parametros = {
        "sportId": 1,
        "startDate": inicio.strftime("%Y-%m-%d"),
        "endDate": fin.strftime("%Y-%m-%d"),
        "gameType": "R",
    }

    respuesta = requests.get(
        URL_CALENDARIO,
        params=parametros,
        timeout=30,
    )
    respuesta.raise_for_status()
    datos = respuesta.json()

    juegos = []

    for grupo_fecha in datos.get("dates", []):
        fecha_juego = date.fromisoformat(
            grupo_fecha["date"]
        )

        for juego in grupo_fecha.get("games", []):
            estado = juego["status"]["abstractGameState"]

            if estado != "Final":
                continue

            visitante = juego["teams"]["away"]
            local = juego["teams"]["home"]

            if "score" not in visitante or "score" not in local:
                continue

            juegos.append(
                {
                    "fecha": fecha_juego,
                    "id_visitante": visitante["team"]["id"],
                    "id_local": local["team"]["id"],
                    "carreras_visitante": int(
                        visitante["score"]
                    ),
                    "carreras_local": int(
                        local["score"]
                    ),
                }
            )

    return juegos


def actualizar_equipo(
    estado,
    carreras_anotadas,
    carreras_permitidas,
    gano,
    fecha_juego,
):
    estado["juegos"] += 1
    estado["victorias"] += int(gano)
    estado["carreras_anotadas"] += carreras_anotadas
    estado["carreras_permitidas"] += carreras_permitidas
    estado["ultimos_resultados"].append(int(gano))
    estado["ultima_fecha"] = fecha_juego


def construir_estados(fecha_objetivo=None):
    if fecha_objetivo is None:
        fecha_objetivo = date.today()

    estados = defaultdict(crear_estado)
    juegos = descargar_juegos_finalizados(
        fecha_objetivo
    )

    for juego in juegos:
        estado_visitante = estados[
            juego["id_visitante"]
        ]
        estado_local = estados[juego["id_local"]]

        gano_local = int(
            juego["carreras_local"]
            > juego["carreras_visitante"]
        )
        gano_visitante = 1 - gano_local

        actualizar_equipo(
            estado_visitante,
            juego["carreras_visitante"],
            juego["carreras_local"],
            gano_visitante,
            juego["fecha"],
        )
        actualizar_equipo(
            estado_local,
            juego["carreras_local"],
            juego["carreras_visitante"],
            gano_local,
            juego["fecha"],
        )

    return estados


def resumir_equipo(estado, fecha_objetivo):
    juegos = estado["juegos"]

    if juegos == 0:
        return {
            "porcentaje": 0.5,
            "forma": 0.5,
            "carreras_anotadas": 0.0,
            "carreras_permitidas": 0.0,
            "descanso": 7,
        }

    resultados = estado["ultimos_resultados"]
    forma = sum(resultados) / len(resultados)

    descanso = max(
        (
            fecha_objetivo
            - estado["ultima_fecha"]
        ).days
        - 1,
        0,
    )

    return {
        "porcentaje": estado["victorias"] / juegos,
        "forma": forma,
        "carreras_anotadas": (
            estado["carreras_anotadas"] / juegos
        ),
        "carreras_permitidas": (
            estado["carreras_permitidas"] / juegos
        ),
        "descanso": min(descanso, 7),
    }


def crear_variables_juego(
    estados,
    id_visitante,
    id_local,
    fecha_objetivo=None,
):
    if fecha_objetivo is None:
        fecha_objetivo = date.today()

    visitante = resumir_equipo(
        estados[id_visitante],
        fecha_objetivo,
    )
    local = resumir_equipo(
        estados[id_local],
        fecha_objetivo,
    )

    return {
        "descanso_visitante": visitante["descanso"],
        "descanso_local": local["descanso"],
        "porcentaje_visitante": visitante["porcentaje"],
        "porcentaje_local": local["porcentaje"],
        "forma_visitante": visitante["forma"],
        "forma_local": local["forma"],
        "carreras_anotadas_visitante": (
            visitante["carreras_anotadas"]
        ),
        "carreras_anotadas_local": (
            local["carreras_anotadas"]
        ),
        "carreras_permitidas_visitante": (
            visitante["carreras_permitidas"]
        ),
        "carreras_permitidas_local": (
            local["carreras_permitidas"]
        ),
    }