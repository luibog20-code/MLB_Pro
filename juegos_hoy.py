import csv
from datetime import date
from pathlib import Path

import requests
from mlb_api import obtener_juegos as consultar_juegos
from mlb_api import obtener_estadisticas_pitcher as consultar_pitcher
from mlb_api import obtener_estadisticas_bateo as consultar_bateo
from mlb_api import obtener_estadisticas_bullpen as consultar_bullpen
from mlb_api import obtener_forma_reciente as consultar_forma_reciente
from modelo import calcular_pronostico
from cuotas import (
    analizar_valor,
    buscar_cuotas_juego,
    crear_indice_cuotas,
    obtener_cuotas_mlb,
)
from estado_actual import (
    construir_estados,
    crear_variables_juego,
)
from predictor_ia import predecir_juego
from historial import guardar_pronostico
ARCHIVO_HISTORIAL = Path("data") / "analisis_modelo.csv"
ESTADOS_ANALIZABLES = {
    "Scheduled",
    "Pre-Game",
    "Warmup"
}
def guardar_analisis(fila):
    archivo_nuevo = not ARCHIVO_HISTORIAL.exists()
    if not archivo_nuevo:
        with ARCHIVO_HISTORIAL.open(
            "r",
            newline="",
            encoding="utf-8-sig"
        ) as archivo:
            lector = csv.DictReader(archivo)

            for fila_existente in lector:
                if fila_existente.get("juego_id") == str(
                    fila.get("juego_id")
                ):
                    return

    with ARCHIVO_HISTORIAL.open(
        "a",
        newline="",
        encoding="utf-8-sig"
    ) as archivo:
        escritor = csv.DictWriter(
            archivo,
            fieldnames=fila.keys()
        )

        if archivo_nuevo:
            escritor.writeheader()

        escritor.writerow(fila)
def convertir_numero(valor):
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None
def obtener_estadisticas_pitcher(pitcher_id):
    if pitcher_id is None:
        return {}

    url_pitcher = (
        f"https://statsapi.mlb.com/api/v1/people/{pitcher_id}/stats"
    )

    parametros_pitcher = {
        "stats": "season",
        "group": "pitching",
        "season": date.today().year
    }

    respuesta_pitcher = requests.get(
        url_pitcher,
        params=parametros_pitcher,
        timeout=20
    )

    datos_pitcher = respuesta_pitcher.json()

    if not datos_pitcher.get("stats"):
        return {}

    resultados = datos_pitcher["stats"][0].get("splits", [])

    if not resultados:
        return {}

    return resultados[0]["stat"]
def obtener_estadisticas_bateo(equipo_id):
    url_equipo = (
        f"https://statsapi.mlb.com/api/v1/teams/{equipo_id}/stats"
    )

    parametros_equipo = {
        "stats": "season",
        "group": "hitting",
        "season": date.today().year
    }

    respuesta_equipo = requests.get(
        url_equipo,
        params=parametros_equipo,
        timeout=20
    )

    datos_equipo = respuesta_equipo.json()

    if not datos_equipo.get("stats"):
        return {}

    resultados = datos_equipo["stats"][0].get("splits", [])

    if not resultados:
        return {}

    return resultados[0]["stat"]


fecha_hoy = date.today().strftime("%Y-%m-%d")

juegos = consultar_juegos(fecha_hoy)
try:
    juegos_con_cuotas, creditos_cuotas = (
        obtener_cuotas_mlb()
    )
    indice_cuotas = crear_indice_cuotas(
        juegos_con_cuotas
    )
    error_cuotas = None
except (requests.RequestException, RuntimeError) as error:
    indice_cuotas = {}
    creditos_cuotas = "N/D"
    error_cuotas = str(error)

print("=" * 50)
print("MLB PRO AI")
print(f"Juegos del día: {fecha_hoy}")
print("=" * 50)

if not juegos:
    print("No hay juegos de MLB programados para hoy.")
else:
    estados_actuales = construir_estados()

    print(f"Total de juegos: {len(juegos)}")
    print()

    for numero, juego in enumerate(juegos, start=1):
        visitante = juego["teams"]["away"]["team"]["name"]
        local = juego["teams"]["home"]["team"]["name"]
        id_visitante = juego["teams"]["away"]["team"]["id"]
        id_local = juego["teams"]["home"]["team"]["id"]
        estado = juego["status"]["detailedState"]

        if estado not in ESTADOS_ANALIZABLES:
            print(f"{numero}. {visitante} vs. {local}")
            print(f"   Estado: {estado}")
            print("   No se analiza: el juego ya comenzó o terminó.")
            print()
            continue
        variables_ia = crear_variables_juego(
            estados_actuales,
            id_visitante,
            id_local,
        )

        pronostico_ia = predecir_juego(
            visitante,
            local,
            variables_ia,
        )
        resumen_cuotas = buscar_cuotas_juego(
                    indice_cuotas,
                    visitante,
                    local,
                )
        analisis_valor = None

        if resumen_cuotas is not None:
                    if pronostico_ia["ganador"] == local:
                        probabilidad_local_ia = (
                            pronostico_ia["probabilidad"]
                        )
                    elif pronostico_ia["ganador"] == visitante:
                        probabilidad_local_ia = (
                            100
                            - pronostico_ia["probabilidad"]
                        )
                    else:
                        probabilidad_local_ia = 50.0

                    analisis_valor = analizar_valor(
                        probabilidad_local_ia,
                        resumen_cuotas,
                    )
        bateo_visitante = consultar_bateo(id_visitante) or {}
        bateo_local = consultar_bateo(id_local) or {}
        forma_visitante = consultar_forma_reciente(id_visitante)
        forma_local = consultar_forma_reciente(id_local)

        porcentaje_reciente_visitante = forma_visitante["porcentaje"]
        porcentaje_reciente_local = forma_local["porcentaje"]
        puntos_forma_visitante = 0
        puntos_forma_local = 0

        if porcentaje_reciente_visitante > porcentaje_reciente_local:
                puntos_forma_visitante += 1
        elif porcentaje_reciente_local > porcentaje_reciente_visitante:
                puntos_forma_local += 1

        bullpen_visitante = consultar_bullpen(id_visitante)
        bullpen_local = consultar_bullpen(id_local)

        era_bullpen_visitante = bullpen_visitante.get(
                "era",
                "N/D",
            )
        era_bullpen_local = bullpen_local.get(
                "era",
                "N/D",
            )

        whip_bullpen_visitante = bullpen_visitante.get(
                "whip",
                "N/D",
            )
        whip_bullpen_local = bullpen_local.get(
                "whip",
                "N/D",
            )
        era_bullpen_visitante_num = convertir_numero(
                era_bullpen_visitante
            )
        era_bullpen_local_num = convertir_numero(
                era_bullpen_local
            )
        whip_bullpen_visitante_num = convertir_numero(
                whip_bullpen_visitante
            )
        whip_bullpen_local_num = convertir_numero(
                whip_bullpen_local
            )

        puntos_bullpen_visitante = 0
        puntos_bullpen_local = 0
        ops_visitante = bateo_visitante.get("ops", "N/D")
        ops_local = bateo_local.get("ops", "N/D")
        ops_visitante_num = convertir_numero(ops_visitante)
        ops_local_num = convertir_numero(ops_local)
        carreras_visitante = bateo_visitante.get("runs", "N/D")
        juegos_visitante = bateo_visitante.get("gamesPlayed", "N/D")

        carreras_local = bateo_local.get("runs", "N/D")
        juegos_local = bateo_local.get("gamesPlayed", "N/D")
        carreras_visitante_num = convertir_numero(carreras_visitante)
        juegos_visitante_num = convertir_numero(juegos_visitante)
        carreras_local_num = convertir_numero(carreras_local)
        juegos_local_num = convertir_numero(juegos_local)

        if carreras_visitante_num is not None and juegos_visitante_num:
            carreras_por_juego_visitante = (
                carreras_visitante_num / juegos_visitante_num
            )
        else:
            carreras_por_juego_visitante = None

        if carreras_local_num is not None and juegos_local_num:
            carreras_por_juego_local = carreras_local_num / juegos_local_num
        else:
            carreras_por_juego_local = None
        if carreras_por_juego_visitante is not None:
                carreras_por_juego_visitante_texto = (
                f"{carreras_por_juego_visitante:.2f}"
            )
        else:
                carreras_por_juego_visitante_texto = "N/D"

        if carreras_por_juego_local is not None:
            carreras_por_juego_local_texto = (
                f"{carreras_por_juego_local:.2f}"
            )
        else:
            carreras_por_juego_local_texto = "N/D"
        puntos_ofensiva_visitante = 0
        puntos_ofensiva_local = 0

        if ops_visitante_num is not None and ops_local_num is not None:
            if ops_visitante_num > ops_local_num:
                puntos_ofensiva_visitante += 1
            elif ops_local_num > ops_visitante_num:
                puntos_ofensiva_local += 1
        if (
            carreras_por_juego_visitante is not None
            and carreras_por_juego_local is not None
        ):
            if carreras_por_juego_visitante > carreras_por_juego_local:
                puntos_ofensiva_visitante += 1
            elif carreras_por_juego_local > carreras_por_juego_visitante:
                puntos_ofensiva_local += 1
        if puntos_ofensiva_visitante > puntos_ofensiva_local:
            ventaja_ofensiva = visitante
        elif puntos_ofensiva_local > puntos_ofensiva_visitante:
            ventaja_ofensiva = local
        else:
            ventaja_ofensiva = "Empate"
        record_visitante = juego["teams"]["away"]["leagueRecord"]
        record_local = juego["teams"]["home"]["leagueRecord"]
        porcentaje_visitante = float(record_visitante["pct"]) * 100
        porcentaje_local = float(record_local["pct"]) * 100
        if porcentaje_visitante > porcentaje_local:
            mejor_record = visitante
        elif porcentaje_local > porcentaje_visitante:
            mejor_record = local
        else:
            mejor_record = "Empate"
        pitcher_visitante = juego["teams"]["away"].get(
            "probablePitcher", {}
        ).get("fullName", "No confirmado")

        pitcher_local = juego["teams"]["home"].get(
            "probablePitcher", {}
        ).get("fullName", "No confirmado")
        id_pitcher_visitante = juego["teams"]["away"].get(
            "probablePitcher", {}
        ).get("id")

        id_pitcher_local = juego["teams"]["home"].get(
            "probablePitcher", {}
        ).get("id")
        estadisticas_visitante = consultar_pitcher(
            id_pitcher_visitante
        )

        estadisticas_local = consultar_pitcher(
            id_pitcher_local
        )
        era_visitante = estadisticas_visitante.get("era", "N/D")
        whip_visitante = estadisticas_visitante.get("whip", "N/D")
        victorias_visitante = estadisticas_visitante.get("wins", "N/D")
        derrotas_visitante = estadisticas_visitante.get("losses", "N/D")
        ponches_visitante = estadisticas_visitante.get("strikeOuts", "N/D")
        k9_visitante = estadisticas_visitante.get("strikeoutsPer9Inn", "N/D")
        bb9_visitante = estadisticas_visitante.get("walksPer9Inn", "N/D")
        entradas_visitante = estadisticas_visitante.get("inningsPitched", "N/D")
        era_visitante_num = convertir_numero(era_visitante)
        whip_visitante_num = convertir_numero(whip_visitante)
        k9_visitante_num = convertir_numero(k9_visitante)
        bb9_visitante_num = convertir_numero(bb9_visitante)

        era_local = estadisticas_local.get("era", "N/D")
        whip_local = estadisticas_local.get("whip", "N/D")
        victorias_local = estadisticas_local.get("wins", "N/D")
        derrotas_local = estadisticas_local.get("losses", "N/D")
        ponches_local = estadisticas_local.get("strikeOuts", "N/D")
        k9_local = estadisticas_local.get("strikeoutsPer9Inn", "N/D")
        bb9_local = estadisticas_local.get("walksPer9Inn", "N/D")
        entradas_local = estadisticas_local.get("inningsPitched", "N/D")
        era_local_num = convertir_numero(era_local)
        whip_local_num = convertir_numero(whip_local)
        k9_local_num = convertir_numero(k9_local)
        bb9_local_num = convertir_numero(bb9_local)
        puntos_visitante = 0
        puntos_local = 0

        if bb9_visitante_num is not None and bb9_local_num is not None:
            if bb9_visitante_num < bb9_local_num:
                puntos_visitante += 1
            elif bb9_local_num < bb9_visitante_num:
                puntos_local += 1

        if puntos_visitante > puntos_local:
            ventaja_pitcher = pitcher_visitante
        elif puntos_local > puntos_visitante:
            ventaja_pitcher = pitcher_local
        else:
            ventaja_pitcher = "Empate"
        print(f"{numero}. {visitante} vs. {local}")
        print(f"   Récord visitante: {record_visitante['wins']}-{record_visitante['losses']}")
        print(f"   Récord local: {record_local['wins']}-{record_local['losses']}")
        print(f"   Porcentaje visitante: {porcentaje_visitante:.1f}%")
        print(f"   Porcentaje local: {porcentaje_local:.1f}%")
        print(f"   OPS visitante: {ops_visitante}")
        print(f"   OPS local: {ops_local}")
        print(f"   Carreras/juego visitante: {carreras_por_juego_visitante_texto}")
        print(f"   Carreras/juego local: {carreras_por_juego_local_texto}")
        print(f"   Puntos de ofensiva: {visitante} {puntos_ofensiva_visitante} - {puntos_ofensiva_local} {local}")
        print(f"   Ventaja ofensiva básica: {ventaja_ofensiva}")
        print(f"   Equipo con mejor récord: {mejor_record}")
        print(f"   Pitcher visitante: {pitcher_visitante}")
        print(f"   ERA: {era_visitante} | WHIP: {whip_visitante}")
        print(f"   Récord pitcher: {victorias_visitante}-{derrotas_visitante}")
        print(f"   Ponches: {ponches_visitante} | K/9: {k9_visitante} | BB/9: {bb9_visitante} | Entradas: {entradas_visitante}")
        print(f"   Pitcher local: {pitcher_local}")
        print(f"   ERA: {era_local} | WHIP: {whip_local}")
        print(f"   Récord pitcher: {victorias_local}-{derrotas_local}")
        print(f"   Ponches: {ponches_local} | K/9: {k9_local} | BB/9: {bb9_local} | Entradas: {entradas_local}")
        print(f"   Puntos de pitchers: {pitcher_visitante} {puntos_visitante} - {puntos_local} {pitcher_local}")
        print(f"   Ventaja básica del abridor: {ventaja_pitcher}")
        print(
            f"    Bullpen visitante - "
            f"ERA: {era_bullpen_visitante} | "
            f"WHIP: {whip_bullpen_visitante}"
        )
        print(
            f"    Bullpen local - "
            f"ERA: {era_bullpen_local} | "
            f"WHIP: {whip_bullpen_local}"
        )
        print(f"   Estado: {estado}")
        pronostico = calcular_pronostico(
            visitante,
            local,
            puntos_visitante,
            puntos_local,
            puntos_ofensiva_visitante,
            puntos_ofensiva_local,
            puntos_bullpen_visitante,
            puntos_bullpen_local,
            puntos_forma_visitante,
            puntos_forma_local,
        )

        print(f"    Pronóstico preliminar: {pronostico['ganador']}")
        print(f"    Probabilidad estimada: {pronostico['probabilidad']}%")
        print(f"    Recomendación: {pronostico['recomendacion']}")
        print(f"    Pronóstico IA: {pronostico_ia['ganador']}")
        print(f"    Probabilidad IA: {pronostico_ia['probabilidad']}%")
        print(f"    Recomendación IA: {pronostico_ia['recomendacion']}")

        if analisis_valor is not None:
                    mercado_visitante = (
                        resumen_cuotas[
                            "probabilidad_mercado_visitante"
                        ]
                        * 100
                    )
                    mercado_local = (
                        resumen_cuotas[
                            "probabilidad_mercado_local"
                        ]
                        * 100
                    )

                    print(
                        f"    Mercado sin margen: "
                        f"{visitante} {mercado_visitante:.1f}% | "
                        f"{local} {mercado_local:.1f}%"
                    )
                    print(
                        f"    Selección con valor: "
                        f"{analisis_valor['seleccion']}"
                    )
                    print(
                        f"    Mejor cuota: "
                        f"{analisis_valor['cuota']} "
                        f"en {analisis_valor['casa']}"
                    )
                    print(
                        f"    Ventaja IA vs. mercado: "
                        f"{analisis_valor['ventaja'] * 100:+.1f} puntos"
                    )
                    print(
                        f"    Valor esperado estimado: "
                        f"{analisis_valor['valor_esperado'] * 100:+.1f}%"
                    )
                    print(
                        f"    Decisión de valor: "
                        f"{analisis_valor['recomendacion']}"
                    )
                    print(
                        "    Aviso: señal experimental; "
                        "todavía requiere validación."
                    )
        else:
                    print(
                        "    Cuotas de mercado no disponibles."
                    )
        if analisis_valor is not None:
            campos_valor = {
                "mercado_visitante": round(
                    resumen_cuotas[
                        "probabilidad_mercado_visitante"
                    ]
                    * 100,
                    1,
                ),
                "mercado_local": round(
                    resumen_cuotas[
                        "probabilidad_mercado_local"
                    ]
                    * 100,
                    1,
                ),
                "seleccion_valor": analisis_valor[
                    "seleccion"
                ],
                "cuota": analisis_valor["cuota"],
                "casa": analisis_valor["casa"],
                "ventaja_mercado": round(
                    analisis_valor["ventaja"] * 100,
                    1,
                ),
                "valor_esperado": round(
                    analisis_valor["valor_esperado"] * 100,
                    1,
                ),
                "decision_valor": analisis_valor[
                    "recomendacion"
                ],
            }
        else:
            campos_valor = {
                "mercado_visitante": "",
                "mercado_local": "",
                "seleccion_valor": "",
                "cuota": "",
                "casa": "",
                "ventaja_mercado": "",
                "valor_esperado": "",
                "decision_valor": "Cuotas no disponibles",
            }
        guardar_pronostico({
            "juego_id": juego["gamePk"],
            "fecha": fecha_hoy,
            "visitante": visitante,
            "local": local,
            "ganador_pronosticado": pronostico_ia["ganador"],
            "probabilidad": pronostico_ia["probabilidad"],
            "recomendacion": pronostico_ia["recomendacion"],
            **campos_valor,
        })
        guardar_analisis({
                    "juego_id": juego["gamePk"],
                    "fecha": fecha_hoy,
                    "visitante": visitante,
                    "local": local,
                    "estado": estado,
                    "porcentaje_visitante": porcentaje_visitante,
                    "porcentaje_local": porcentaje_local,
                    "ops_visitante": ops_visitante,
                    "ops_local": ops_local,
                    "carreras_juego_visitante": carreras_por_juego_visitante_texto,
                    "carreras_juego_local": carreras_por_juego_local_texto,
                    "pitcher_visitante": pitcher_visitante,
                    "pitcher_local": pitcher_local,
                        "puntos_pitcher_visitante": puntos_visitante,
                        "puntos_pitcher_local": puntos_local,
                        "ventaja_pitcher": ventaja_pitcher,
                        "puntos_ofensiva_visitante": puntos_ofensiva_visitante,
                        "puntos_ofensiva_local": puntos_ofensiva_local,
                        "ventaja_ofensiva": ventaja_ofensiva,
                        "forma_reciente_visitante": porcentaje_reciente_visitante,
                        "forma_reciente_local": porcentaje_reciente_local,
                        "puntos_forma_visitante": puntos_forma_visitante,
                        "puntos_forma_local": puntos_forma_local,
                    })
        print()
