import os

from dotenv import load_dotenv
from supabase import create_client


load_dotenv()


def obtener_cliente():
    url = os.getenv("SUPABASE_URL")
    clave = os.getenv("SUPABASE_SECRET_KEY")

    if not url or not clave:
        raise RuntimeError(
            "Faltan SUPABASE_URL o SUPABASE_SECRET_KEY en el archivo .env"
        )

    return create_client(url, clave)


def probar_conexion():
    cliente = obtener_cliente()

    cliente.table("pronosticos").select(
        "juego_id"
    ).limit(1).execute()

    return True

CAMPOS_PRONOSTICO = (
    "juego_id",
    "fecha",
    "visitante",
    "local",
    "ganador_pronosticado",
    "probabilidad",
    "recomendacion",
    "mercado_visitante",
    "mercado_local",
    "seleccion_valor",
    "cuota",
    "casa",
    "ventaja_mercado",
    "valor_esperado",
    "decision_valor",
)


CAMPOS_DECIMALES = (
    "probabilidad",
    "mercado_visitante",
    "mercado_local",
    "ventaja_mercado",
    "valor_esperado",
)


def convertir_decimal_db(valor):
    if valor is None:
        return None

    if str(valor).strip().lower() in ("", "nan", "n/d", "none"):
        return None

    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


def guardar_pronostico_db(fila):
    cliente = obtener_cliente()

    registro = {
        campo: fila.get(campo)
        for campo in CAMPOS_PRONOSTICO
    }

    registro["juego_id"] = int(registro["juego_id"])

    for campo in CAMPOS_DECIMALES:
        registro[campo] = convertir_decimal_db(
            registro.get(campo)
        )

    cuota = convertir_decimal_db(registro.get("cuota"))
    registro["cuota"] = int(cuota) if cuota is not None else None

    cliente.table("pronosticos").upsert(
        registro,
        on_conflict="juego_id",
    ).execute()

    return True
def cargar_pronosticos_db():
    cliente = obtener_cliente()

    respuesta = (
        cliente.table("pronosticos")
        .select("*")
        .order("fecha", desc=True)
        .execute()
    )

    return respuesta.data or []