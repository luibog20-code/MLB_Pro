import os
from statistics import mean

import requests
from dotenv import load_dotenv


URL_CUOTAS_MLB = (
    "https://api.the-odds-api.com/v4/"
    "sports/baseball_mlb/odds"
)

load_dotenv()


def obtener_cuotas_mlb():
    api_key = os.getenv("ODDS_API_KEY")

    if not api_key:
        raise RuntimeError(
            "No se encontró ODDS_API_KEY en el archivo .env"
        )

    parametros = {
        "apiKey": api_key,
        "regions": "us",
        "markets": "h2h",
        "oddsFormat": "american",
        "dateFormat": "iso",
    }

    respuesta = requests.get(
        URL_CUOTAS_MLB,
        params=parametros,
        timeout=20,
    )

    if respuesta.status_code != 200:
        try:
            detalle = respuesta.json().get(
                "message",
                "Error desconocido",
            )
        except ValueError:
            detalle = "La API devolvió una respuesta no válida"

        raise RuntimeError(
            f"Error {respuesta.status_code}: {detalle}"
        )

    juegos = respuesta.json()
    creditos = respuesta.headers.get(
        "x-requests-remaining",
        "N/D",
    )

    return juegos, creditos

def cuota_americana_a_decimal(cuota):
    cuota = float(cuota)

    if cuota > 0:
        return 1 + (cuota / 100)

    if cuota < 0:
        return 1 + (100 / abs(cuota))

    return None


def probabilidad_implicita(cuota):
    cuota = float(cuota)

    if cuota > 0:
        return 100 / (cuota + 100)

    if cuota < 0:
        return abs(cuota) / (abs(cuota) + 100)

    return None
def calcular_valor_esperado(
    probabilidad,
    cuota_americana,
):
    cuota_decimal = cuota_americana_a_decimal(
        cuota_americana
    )

    if cuota_decimal is None:
        return None

    return (
        probabilidad * cuota_decimal
    ) - 1
def probabilidades_sin_margen(
    cuota_visitante,
    cuota_local,
):
    prob_visitante = probabilidad_implicita(
        cuota_visitante
    )
    prob_local = probabilidad_implicita(
        cuota_local
    )

    total = prob_visitante + prob_local

    return {
        "visitante": prob_visitante / total,
        "local": prob_local / total,
        "margen": total - 1,
    }
def resumir_cuotas_juego(juego):
    visitante = juego["away_team"]
    local = juego["home_team"]

    probabilidades_visitante = []
    probabilidades_local = []
    margenes = []

    mejor_cuota_visitante = None
    mejor_casa_visitante = None
    mejor_cuota_local = None
    mejor_casa_local = None

    for casa in juego.get("bookmakers", []):
        mercado = next(
            (
                mercado
                for mercado in casa.get("markets", [])
                if mercado.get("key") == "h2h"
            ),
            None,
        )

        if mercado is None:
            continue

        precios = {
            resultado.get("name"): resultado.get("price")
            for resultado in mercado.get("outcomes", [])
        }

        cuota_visitante = precios.get(visitante)
        cuota_local = precios.get(local)

        if not isinstance(
            cuota_visitante,
            (int, float),
        ):
            continue

        if not isinstance(
            cuota_local,
            (int, float),
        ):
            continue

        probabilidades = probabilidades_sin_margen(
            cuota_visitante,
            cuota_local,
        )

        probabilidades_visitante.append(
            probabilidades["visitante"]
        )
        probabilidades_local.append(
            probabilidades["local"]
        )
        margenes.append(
            probabilidades["margen"]
        )

        if (
            mejor_cuota_visitante is None
            or cuota_visitante > mejor_cuota_visitante
        ):
            mejor_cuota_visitante = cuota_visitante
            mejor_casa_visitante = casa["title"]

        if (
            mejor_cuota_local is None
            or cuota_local > mejor_cuota_local
        ):
            mejor_cuota_local = cuota_local
            mejor_casa_local = casa["title"]

    if not probabilidades_visitante:
        return None

    return {
        "visitante": visitante,
        "local": local,
        "probabilidad_mercado_visitante": mean(
            probabilidades_visitante
        ),
        "probabilidad_mercado_local": mean(
            probabilidades_local
        ),
        "margen_promedio": mean(margenes),
        "mejor_cuota_visitante": mejor_cuota_visitante,
        "mejor_casa_visitante": mejor_casa_visitante,
        "mejor_cuota_local": mejor_cuota_local,
        "mejor_casa_local": mejor_casa_local,
        "cantidad_casas": len(
            probabilidades_visitante
        ),
    }
def analizar_valor(
    probabilidad_local_ia,
    resumen,
):
    probabilidad_local_ia = float(
        probabilidad_local_ia
    )

    if probabilidad_local_ia > 1:
        probabilidad_local_ia /= 100

    if not 0 <= probabilidad_local_ia <= 1:
        raise ValueError(
            "La probabilidad IA debe estar entre 0 y 1"
        )

    probabilidad_visitante_ia = (
        1 - probabilidad_local_ia
    )

    ventaja_visitante = (
        probabilidad_visitante_ia
        - resumen["probabilidad_mercado_visitante"]
    )
    ventaja_local = (
        probabilidad_local_ia
        - resumen["probabilidad_mercado_local"]
    )

    valor_visitante = calcular_valor_esperado(
        probabilidad_visitante_ia,
        resumen["mejor_cuota_visitante"],
    )
    valor_local = calcular_valor_esperado(
        probabilidad_local_ia,
        resumen["mejor_cuota_local"],
    )

    if valor_visitante >= valor_local:
        seleccion = resumen["visitante"]
        cuota = resumen["mejor_cuota_visitante"]
        casa = resumen["mejor_casa_visitante"]
        probabilidad_ia = probabilidad_visitante_ia
        probabilidad_mercado = resumen[
            "probabilidad_mercado_visitante"
        ]
        ventaja = ventaja_visitante
        valor_esperado = valor_visitante
    else:
        seleccion = resumen["local"]
        cuota = resumen["mejor_cuota_local"]
        casa = resumen["mejor_casa_local"]
        probabilidad_ia = probabilidad_local_ia
        probabilidad_mercado = resumen[
            "probabilidad_mercado_local"
        ]
        ventaja = ventaja_local
        valor_esperado = valor_local

    if ventaja < 0.03 or valor_esperado < 0.03:
        recomendacion = "No apostar"
    elif ventaja < 0.05 or valor_esperado < 0.08:
        recomendacion = "Vigilar"
    else:
        recomendacion = "Valor experimental"

    return {
        "seleccion": seleccion,
        "cuota": cuota,
        "casa": casa,
        "probabilidad_ia": probabilidad_ia,
        "probabilidad_mercado": probabilidad_mercado,
        "ventaja": ventaja,
        "valor_esperado": valor_esperado,
        "recomendacion": recomendacion,
    }
def normalizar_nombre_equipo(nombre):
    nombre = str(nombre).lower().strip()
    nombre = nombre.replace(".", "")

    alias = {
        "oakland athletics": "athletics",
    }

    return alias.get(nombre, nombre)


def crear_indice_cuotas(juegos):
    indice = {}

    for juego in juegos:
        resumen = resumir_cuotas_juego(juego)

        if resumen is None:
            continue

        clave = (
            normalizar_nombre_equipo(
                resumen["visitante"]
            ),
            normalizar_nombre_equipo(
                resumen["local"]
            ),
        )

        indice[clave] = resumen

    return indice


def buscar_cuotas_juego(
    indice,
    visitante,
    local,
):
    clave = (
        normalizar_nombre_equipo(visitante),
        normalizar_nombre_equipo(local),
    )

    return indice.get(clave)
def mostrar_cuotas():
    juegos, creditos = obtener_cuotas_mlb()

    print("=" * 50)
    print("CUOTAS MONEYLINE DE MLB")
    print(f"Juegos encontrados: {len(juegos)}")
    print(f"Créditos restantes: {creditos}")
    print("=" * 50)

    for juego in juegos:
        visitante = juego["away_team"]
        local = juego["home_team"]

        print()
        print(f"{visitante} vs. {local}")

        resumen = resumir_cuotas_juego(juego)

        if resumen is not None:
            prob_visitante = (
                resumen["probabilidad_mercado_visitante"]
                * 100
            )
            prob_local = (
                resumen["probabilidad_mercado_local"]
                * 100
            )

            print(
                f"  Consenso de "
                f"{resumen['cantidad_casas']} casas: "
                f"{visitante} {prob_visitante:.1f}% | "
                f"{local} {prob_local:.1f}%"
            )
            print(
                f"  Mejor cuota visitante: "
                f"{resumen['mejor_cuota_visitante']} "
                f"en {resumen['mejor_casa_visitante']}"
            )
            print(
                f"  Mejor cuota local: "
                f"{resumen['mejor_cuota_local']} "
                f"en {resumen['mejor_casa_local']}"
            )

        for casa in juego.get("bookmakers", [])[:3]:
            mercado = next(
                (
                    mercado
                    for mercado in casa.get("markets", [])
                    if mercado.get("key") == "h2h"
                ),
                None,
            )

            if mercado is None:
                continue

            precios = {
                resultado.get("name"): resultado.get("price")
                for resultado in mercado.get("outcomes", [])
            }

            cuota_visitante = precios.get(visitante, "N/D")
            cuota_local = precios.get(local, "N/D")

            print(
                f"  {casa['title']}: "
                f"{visitante} {cuota_visitante} | "
                f"{local} {cuota_local}"
            )


if __name__ == "__main__":
    mostrar_cuotas()