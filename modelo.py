def calcular_pronostico(
    visitante,
    local,
    puntos_pitcher_visitante,
    puntos_pitcher_local,
    puntos_ofensiva_visitante,
    puntos_ofensiva_local,
):
    ventaja_local = 0.25

    total_visitante = (
        puntos_pitcher_visitante
        + puntos_ofensiva_visitante
    )

    total_local = (
        puntos_pitcher_local
        + puntos_ofensiva_local
        + ventaja_local
    )

    diferencia = total_visitante - total_local

    if diferencia > 0:
        ganador = visitante
    elif diferencia < 0:
        ganador = local
    else:
        ganador = "Empate"

    probabilidad = 50 + min(abs(diferencia) * 5, 20)

    return {
        "ganador": ganador,
        "probabilidad": round(probabilidad, 1),
        "puntos_visitante": total_visitante,
        "puntos_local": total_local,
    }