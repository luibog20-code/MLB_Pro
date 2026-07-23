import csv
from datetime import date
from pathlib import Path

import requests
from mlb_api import obtener_juegos as consultar_juegos
from mlb_api import obtener_estadisticas_pitcher as consultar_pitcher
from mlb_api import obtener_estadisticas_bateo as consultar_bateo
ARCHIVO_HISTORIAL = Path("data") / "analisis_diario.csv"
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

print("=" * 50)
print("MLB PRO AI")
print(f"Juegos del día: {fecha_hoy}")
print("=" * 50)

if not juegos:
    print("No hay juegos de MLB programados para hoy.")
else:
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
        bateo_visitante = consultar_bateo(id_visitante)
        bateo_local = consultar_bateo(id_local)
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
        print(f"   Estado: {estado}")
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
                "ventaja_ofensiva": ventaja_ofensiva
            })
        print()
