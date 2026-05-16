"""
madrid_routes_matrix.py
========================
Consulta la Google Maps Routes API (computeRouteMatrix) para rutas de Madrid
en transporte privado (coche) y público, hora a hora (01:00 – 24:00).


COLUMNAS DEL CSV:
  · duracion_sin_trafico_min  → campo "duration"        (DRIVE + TRANSIT)
  · duracion_con_trafico_min  → campo "duration" con routingPreference=TRAFFIC_AWARE_OPTIMAL
                                 (solo DRIVE; ambas se obtienen con DOS peticiones por ruta,
                                  una TRAFFIC_UNAWARE y una TRAFFIC_AWARE_OPTIMAL)
  · diferencia_trafico_min    → con_trafico - sin_trafico (solo DRIVE)

LÍMITES DE LA ROUTES API (desde 2025):
  · 10.000 requests/mes gratis por SKU.
  · TRANSIT: máx. 100 elementos por request (origins × destinations ≤ 100).
  · DRIVE TRAFFIC_AWARE_OPTIMAL: máx. 100 elementos por request.
  · Rate limit: ver documentación de Google Maps Platform.
  · departureTime debe estar en ISO 8601 UTC (RFC3339).
  · Para TRANSIT, departureTime puede ser pasado (hasta 7 días).
  · Para DRIVE, departureTime debe ser futuro.

INSTALACIÓN:
    pip install requests python-dotenv

USO:
    Crea un fichero .env junto al script con:
        GOOGLE_MAPS_API_KEY=tu_clave_aqui
    Activa "Routes API" en tu proyecto de Google Cloud Console.
    Luego ejecuta:
        python madrid_routes_matrix.py
"""

import os
import csv
import time
import datetime
import requests
from pathlib import Path

# ─────────────────────────────────────────────────────────────────
# CONFIGURACIÓN — ajusta estos valores según tus necesidades
# ─────────────────────────────────────────────────────────────────

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "TU_API_KEY_AQUI")

# ── Número máximo de peticiones en esta ejecución ────────────────────
MAX_REQUESTS = 1000

# ── Horas del día a consultar (1 = 01:00 … 24 = medianoche) ──────────
HOURS = list(range(1, 25))

# ── Modos de transporte ───────────────────────────────────────────────
TRANSPORT_MODES = ["DRIVE", "TRANSIT"]

# ── Modelo de tráfico para DRIVE ──────────────────────────────────────
#    Opciones: "BEST_GUESS" | "PESSIMISTIC" | "OPTIMISTIC"
TRAFFIC_MODEL = "BEST_GUESS"

# ── Pausa entre peticiones en segundos ───────────────────────────────
REQUEST_DELAY = 0.15

# ── Directorio de salida ─────────────────────────────────────────────
OUTPUT_DIR = Path(__file__).parent

# ─────────────────────────────────────────────────────────────────
# CONTINUACIÓN — para retomar desde donde se dejó
# ─────────────────────────────────────────────────────────────────
# Si quieres empezar desde el principio:
#   START_HOUR  = 1
#   START_MODE  = "DRIVE"
#   APPEND_TO_CSV = None
#
# Si quieres continuar desde donde lo dejaste, por ejemplo la
# última fila guardada fue hora=08:00, modo=TRANSIT:
#   START_HOUR    = 8       ← hora donde quieres retomar (1-24)
#   START_MODE    = "TRANSIT"  ← "DRIVE" o "TRANSIT"
#   APPEND_TO_CSV = "madrid_rutas.csv"  ← nombre del CSV existente
#                                          (None = crear fichero nuevo)
#
# El script saltará todas las combinaciones anteriores a START_HOUR/START_MODE
# y añadirá las nuevas filas al final del CSV indicado.
# ─────────────────────────────────────────────────────────────────
START_HOUR    = 24       # hora de inicio (1-24)
START_MODE    = "TRANSIT"  # modo de inicio: "DRIVE" o "TRANSIT"
APPEND_TO_CSV = None     # None = nuevo fichero | "nombre.csv" = añadir a ese fichero

# ─────────────────────────────────────────────────────────────────
# ENDPOINT Y FIELD MASKS
# ─────────────────────────────────────────────────────────────────

ROUTES_API_URL = "https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix"

# Campos que pedimos: obligatorio incluir status para detectar errores
FIELD_MASK = "originIndex,destinationIndex,status,condition,distanceMeters,duration,staticDuration"

# ─────────────────────────────────────────────────────────────────
# RUTAS DE MADRID
# ─────────────────────────────────────────────────────────────────

ROUTES = [
    # ── Dentro de Madrid capital ─────────────────────────────────────────
    ("Puerta del Sol, Madrid",          "Aeropuerto Adolfo Suárez Madrid-Barajas, Madrid"),
    ("Puerta del Sol, Madrid",          "Estación de Atocha, Madrid"),
    ("Puerta del Sol, Madrid",          "Estación de Chamartín, Madrid"),
    ("Puerta del Sol, Madrid",          "Plaza de Castilla, Madrid"),
    ("Puerta del Sol, Madrid",          "Vallecas, Madrid"),
    ("Puerta del Sol, Madrid",          "Moncloa, Madrid"),
    ("Puerta del Sol, Madrid",          "Cuatro Caminos, Madrid"),
    ("Gran Vía, Madrid",                "Estadio Santiago Bernabéu, Madrid"),
    ("Gran Vía, Madrid",                "Estadio Cívitas Metropolitano, Madrid"),
    ("Nuevos Ministerios, Madrid",      "Aeropuerto Adolfo Suárez Madrid-Barajas, Madrid"),
    ("Nuevos Ministerios, Madrid",      "Estación de Atocha, Madrid"),
    ("Retiro, Madrid",                  "Ciudad Universitaria, Madrid"),
    ("Retiro, Madrid",                  "Leganés, Madrid"),
    ("Retiro, Madrid",                  "Getafe, Madrid"),

    # ── Madrid → Área metropolitana (corta distancia) ────────────────────
    ("Estación de Atocha, Madrid",      "Alcalá de Henares, Madrid"),
    ("Estación de Atocha, Madrid",      "Aranjuez, Madrid"),
    ("Estación de Atocha, Madrid",      "Alcobendas, Madrid"),
    ("Estación de Atocha, Madrid",      "San Sebastián de los Reyes, Madrid"),
    ("Estación de Atocha, Madrid",      "Móstoles, Madrid"),
    ("Estación de Atocha, Madrid",      "Fuenlabrada, Madrid"),
    ("Estación de Atocha, Madrid",      "Parla, Madrid"),
    ("Estación de Atocha, Madrid",      "Pinto, Madrid"),
    ("Estación de Chamartín, Madrid",   "Tres Cantos, Madrid"),
    ("Estación de Chamartín, Madrid",   "Colmenar Viejo, Madrid"),
    ("Estación de Chamartín, Madrid",   "Alcobendas, Madrid"),
    ("Moncloa, Madrid",                 "Las Rozas de Madrid, Madrid"),
    ("Moncloa, Madrid",                 "Majadahonda, Madrid"),
    ("Moncloa, Madrid",                 "Pozuelo de Alarcón, Madrid"),
    ("Moncloa, Madrid",                 "Boadilla del Monte, Madrid"),
    ("Moncloa, Madrid",                 "Villanueva de la Cañada, Madrid"),
    ("Puerta del Sol, Madrid",          "Alcorcón, Madrid"),
    ("Puerta del Sol, Madrid",          "Leganés, Madrid"),
    ("Puerta del Sol, Madrid",          "Getafe, Madrid"),
    ("Puerta del Sol, Madrid",          "Torrejón de Ardoz, Madrid"),
    ("Puerta del Sol, Madrid",          "Coslada, Madrid"),

    # ── Madrid → Media distancia ─────────────────────────────────────────
    ("Estación de Atocha, Madrid",      "Toledo"),
    ("Estación de Atocha, Madrid",      "Segovia"),
    ("Estación de Atocha, Madrid",      "Guadalajara"),
    ("Estación de Atocha, Madrid",      "Ávila"),
    ("Estación de Atocha, Madrid",      "Cuenca"),
    ("Estación de Chamartín, Madrid",   "Valladolid"),
    ("Estación de Chamartín, Madrid",   "Burgos"),
    ("Estación de Chamartín, Madrid",   "Salamanca"),
    ("Estación de Atocha, Madrid",      "Córdoba"),
    ("Estación de Atocha, Madrid",      "Ciudad Real"),

    # ── Madrid → Larga distancia ─────────────────────────────────────────
    ("Estación de Atocha, Madrid",      "Barcelona Sants, Barcelona"),
    ("Estación de Atocha, Madrid",      "Valencia, España"),
    ("Estación de Atocha, Madrid",      "Sevilla, España"),
    ("Estación de Atocha, Madrid",      "Zaragoza, España"),
    ("Estación de Atocha, Madrid",      "Málaga, España"),
    ("Estación de Chamartín, Madrid",   "Bilbao, España"),
    ("Estación de Chamartín, Madrid",   "San Sebastián, España"),

    # ── Intermunicipales dentro de la Comunidad de Madrid ────────────────
    ("Alcalá de Henares, Madrid",       "Guadalajara"),
    ("Alcalá de Henares, Madrid",       "Torrejón de Ardoz, Madrid"),
    ("Móstoles, Madrid",                "Alcorcón, Madrid"),
    ("Móstoles, Madrid",                "Leganés, Madrid"),
    ("Móstoles, Madrid",                "Fuenlabrada, Madrid"),
    ("Getafe, Madrid",                  "Parla, Madrid"),
    ("Getafe, Madrid",                  "Leganés, Madrid"),
    ("Las Rozas de Madrid, Madrid",     "Majadahonda, Madrid"),
    ("Tres Cantos, Madrid",             "Alcobendas, Madrid"),
    ("Aranjuez, Madrid",                "Valdemoro, Madrid"),
    ("Aranjuez, Madrid",                "Ocaña, Toledo"),
]

# ─────────────────────────────────────────────────────────────────
# FUNCIONES AUXILIARES
# ─────────────────────────────────────────────────────────────────

def get_next_weekday_datetimes(hours: list) -> dict:
    """
    Devuelve {hora: datetime} para el próximo día laborable.
    DRIVE requiere departure_time en el futuro.
    Se elige día laborable para maximizar la disponibilidad de TRANSIT.
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    target_date = now.date() + datetime.timedelta(days=1)
    while target_date.weekday() >= 5:
        target_date += datetime.timedelta(days=1)

    result = {}
    for h in hours:
        if h == 24:
            dt = datetime.datetime(target_date.year, target_date.month,
                                   target_date.day, 0, 0, 0,
                                   tzinfo=datetime.timezone.utc)
            dt += datetime.timedelta(days=1)
        else:
            dt = datetime.datetime(target_date.year, target_date.month,
                                   target_date.day, h, 0, 0,
                                   tzinfo=datetime.timezone.utc)
        result[h] = dt
    return result


def to_rfc3339(dt: datetime.datetime) -> str:
    """Convierte datetime UTC a formato RFC3339 requerido por la Routes API."""
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def call_route_matrix(origin: str, destination: str,
                      mode: str, departure_dt: datetime.datetime) -> dict | None:
    """
    Hace UNA petición a computeRouteMatrix y devuelve ambas duraciones.

    Para DRIVE con TRAFFIC_AWARE_OPTIMAL + departureTime, la respuesta incluye:
      - duration        → tiempo CON tráfico real/histórico
      - staticDuration  → tiempo SIN tráfico (solo red de carreteras)
    Ambos campos en una sola petición: no se consume el doble de cuota.

    Para TRANSIT:
      - duration        → tiempo de viaje en transporte público
      - staticDuration  → igual que duration (no hay concepto de tráfico)
    """
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
        "X-Goog-FieldMask": FIELD_MASK,
    }

    body = {
        "origins": [{"waypoint": {"location": {"latLng": None}, "address": origin}}],
        "destinations": [{"waypoint": {"location": {"latLng": None}, "address": destination}}],
        "travelMode": mode,
        "languageCode": "es",
    }

    # Simplificar: usar formato address directo sin latLng
    body["origins"]      = [{"waypoint": {"address": origin}}]
    body["destinations"] = [{"waypoint": {"address": destination}}]

    if mode == "DRIVE":
        # TRAFFIC_AWARE_OPTIMAL + departureTime activa tráfico real
        # y devuelve tanto duration (con tráfico) como staticDuration (sin tráfico)
        body["routingPreference"] = "TRAFFIC_AWARE_OPTIMAL"
        body["departureTime"] = to_rfc3339(departure_dt)
        body["trafficModel"] = TRAFFIC_MODEL

    if mode == "TRANSIT":
        # TRANSIT acepta departureTime pero NO routingPreference
        body["departureTime"] = to_rfc3339(departure_dt)
        body["transitPreferences"] = {
            "allowedTravelModes": ["BUS", "SUBWAY", "TRAIN", "LIGHT_RAIL", "RAIL"]
        }

    try:
        resp = requests.post(ROUTES_API_URL, headers=headers,
                             json=body, timeout=10)
        if not resp.ok:
            try:
                err_detail = resp.json()
                print(f"  [ERROR API {resp.status_code}] {err_detail}")
            except Exception:
                print(f"  [ERROR API {resp.status_code}] {resp.text[:200]}")
            return None
        data = resp.json()
    except requests.RequestException as e:
        print(f"  [ERROR RED] {e}")
        return None

    if not isinstance(data, list) or len(data) == 0:
        print(f"  [RESPUESTA VACÍA] {origin} → {destination} ({mode})")
        return None

    element = data[0]

    status = element.get("status", {})
    if isinstance(status, dict) and status.get("code", 0) != 0:
        msg = status.get("message", "desconocido")
        print(f"  [ELEMENT ERROR] {msg} — {origin[:25]} → {destination[:25]} ({mode})")
        return None

    condition = element.get("condition", "")
    if condition in ("ROUTE_NOT_FOUND", "ROUTE_EXISTS_BUT_NOT_RETURNED"):
        print(f"  [SIN RUTA] {condition} — {origin[:25]} → {destination[:25]} ({mode})")
        return None

    # duration = con tráfico (DRIVE) / tiempo de viaje (TRANSIT)
    duration_str        = element.get("duration", "")
    # staticDuration = sin tráfico (DRIVE) / igual que duration (TRANSIT)
    static_duration_str = element.get("staticDuration", duration_str)
    distance_m          = element.get("distanceMeters", 0)

    if not duration_str:
        print(f"  [SIN DURACIÓN] {origin[:25]} → {destination[:25]} ({mode})")
        return None

    duration_sec        = int(duration_str.rstrip("s"))
    static_duration_sec = int(static_duration_str.rstrip("s")) if static_duration_str else duration_sec

    return {
        "duration_con_trafico_min":  round(duration_sec / 60, 1),
        "duration_sin_trafico_min":  round(static_duration_sec / 60, 1),
        "distance_km":               round(distance_m / 1000, 2),
    }


def query_route(origin: str, destination: str,
                mode: str, departure_dt: datetime.datetime,
                request_counter: list) -> dict | None:
    """
    Hace UNA sola petición por ruta (tanto DRIVE como TRANSIT).
    Para DRIVE devuelve duration (con tráfico) y staticDuration (sin tráfico).
    Para TRANSIT solo duration (no hay tráfico en transporte público).
    """
    if request_counter[0] >= MAX_REQUESTS:
        return None

    res = call_route_matrix(origin, destination, mode, departure_dt)
    request_counter[0] += 1
    time.sleep(REQUEST_DELAY)

    if res is None:
        return None

    duracion_con = res["duration_con_trafico_min"]
    duracion_sin = res["duration_sin_trafico_min"]
    distancia_km = res["distance_km"]

    # Para TRANSIT las dos columnas tienen el mismo valor; dejamos con_trafico vacío
    if mode == "TRANSIT":
        diferencia   = None
        duracion_con = None
    else:
        diferencia = round(duracion_con - duracion_sin, 1)

    return {
        "distancia_km":             distancia_km,
        "duracion_sin_trafico_min": duracion_sin,
        "duracion_con_trafico_min": duracion_con,
        "diferencia_trafico_min":   diferencia,
    }


def unique_csv_path(directory: Path, base_name: str) -> Path:
    """Devuelve una ruta CSV única: si ya existe añade _1, _2, etc."""
    candidate = directory / f"{base_name}.csv"
    if not candidate.exists():
        return candidate
    counter = 1
    while True:
        candidate = directory / f"{base_name}_{counter}.csv"
        if not candidate.exists():
            return candidate
        counter += 1


# ─────────────────────────────────────────────────────────────────
# EJECUCIÓN PRINCIPAL
# ─────────────────────────────────────────────────────────────────

def main():
    if API_KEY == "TU_API_KEY_AQUI":
        print("⚠  AVISO: API Key no configurada.")
        print("   Crea un fichero .env con: GOOGLE_MAPS_API_KEY=<tu_clave>")
        print("   Asegúrate de tener 'Routes API' activada en Google Cloud Console.")
        return

    print("=" * 68)
    print("  Google Maps Routes API (computeRouteMatrix) — Madrid")
    print("=" * 68)

    hour_datetimes = get_next_weekday_datetimes(HOURS)
    fecha_consulta = list(hour_datetimes.values())[0].strftime("%Y-%m-%d")

    # DRIVE consume 2 requests por ruta/hora, TRANSIT consume 1
    total_posible = len(ROUTES) * len(HOURS) * len(TRANSPORT_MODES)  # 1 petición por ruta/hora/modo

    print(f"  Fecha de consulta programada  : {fecha_consulta}")
    print(f"  Rutas disponibles             : {len(ROUTES)}")
    print(f"  Horas a consultar             : {len(HOURS)} (01:00 – 24:00)")
    print(f"  Modos de transporte           : {TRANSPORT_MODES}")
    print(f"  Modelo de tráfico (DRIVE)     : {TRAFFIC_MODEL}")
    print(f"  Peticiones posibles totales   : {total_posible}")
    print(f"    (1 petición por ruta: DRIVE devuelve duration + staticDuration)")
    print(f"  Máx. peticiones configuradas  : {MAX_REQUESTS}")
    print()
    print("  COLUMNAS DE DURACIÓN (1 sola petición por ruta):")
    print("  · duracion_sin_trafico_min → TRAFFIC_UNAWARE   (DRIVE + TRANSIT)")
    print("  · duracion_con_trafico_min → TRAFFIC_AWARE_OPT (solo DRIVE)")
    print("  · diferencia_trafico_min   → con - sin tráfico (solo DRIVE)")
    print("=" * 68)

    # Test rápido de conectividad
    print("  Verificando conexión con la API...", end=" ", flush=True)
    test_dt = list(hour_datetimes.values())[0]
    test_result = call_route_matrix(
        "Puerta del Sol, Madrid", "Estación de Atocha, Madrid",
        "DRIVE", test_dt
    )
    if test_result is None:
        print("FALLO")
        print()
        print("  El test ha fallado. Comprueba:")
        print("  1. API Key correcta en el .env")
        print("  2. Routes API activada en Google Cloud Console")
        print("  3. Facturación activada en el proyecto")
        return
    print(f"OK ({test_result['distance_km']} km | sin tráfico: {test_result['duration_sin_trafico_min']} min | con tráfico: {test_result['duration_con_trafico_min']} min)")
    print()

    fieldnames = [
        "origen",
        "destino",
        "modo_transporte",
        "hora_salida",
        "fecha_consulta",
        "distancia_km",
        "duracion_sin_trafico_min",
        "duracion_con_trafico_min",
        "diferencia_trafico_min",
    ]

    # ── Decidir si crear fichero nuevo o añadir a uno existente ──────────
    if APPEND_TO_CSV:
        csv_path     = OUTPUT_DIR / APPEND_TO_CSV
        file_mode    = "a"
        write_header = False
        if not csv_path.exists():
            print(f"  ⚠  '{APPEND_TO_CSV}' no existe, se creará nuevo.")
            file_mode    = "w"
            write_header = True
    else:
        csv_path     = unique_csv_path(OUTPUT_DIR, "madrid_rutas")
        file_mode    = "w"
        write_header = True

    mode_order     = {m: i for i, m in enumerate(TRANSPORT_MODES)}
    start_mode_idx = mode_order.get(START_MODE, 0)

    print(f"  Fichero CSV                   : {csv_path.name} ({'nuevo' if file_mode == 'w' else 'continuando'})")
    print(f"  Empezando desde               : hora {START_HOUR:02d}:00, modo {START_MODE}")
    print()

    request_counter = [0]
    total_filas_ok  = 0
    total_filas_err = 0

    with open(csv_path, file_mode, newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()

        for hour in HOURS:
            if request_counter[0] >= MAX_REQUESTS:
                break
            if hour < START_HOUR:
                continue

            dep_dt   = hour_datetimes[hour]
            hora_str = f"{hour:02d}:00" if hour < 24 else "00:00 (+1d)"

            for mode_idx, mode in enumerate(TRANSPORT_MODES):
                if request_counter[0] >= MAX_REQUESTS:
                    break
                if hour == START_HOUR and mode_idx < start_mode_idx:
                    continue

                for origin, destination in ROUTES:
                    if request_counter[0] >= MAX_REQUESTS:
                        break

                    print(f"  [{request_counter[0] + 1:04d}/{MAX_REQUESTS}] "
                          f"{hora_str} | {mode:7s} | "
                          f"{origin[:27]:27s} → {destination[:27]}")

                    result = query_route(origin, destination, mode,
                                         dep_dt, request_counter)

                    if result:
                        writer.writerow({
                            "origen":                   origin,
                            "destino":                  destination,
                            "modo_transporte":          mode,
                            "hora_salida":              hora_str,
                            "fecha_consulta":           fecha_consulta,
                            "distancia_km":             result["distancia_km"],
                            "duracion_sin_trafico_min": result["duracion_sin_trafico_min"],
                            "duracion_con_trafico_min": result["duracion_con_trafico_min"],
                            "diferencia_trafico_min":   result["diferencia_trafico_min"],
                        })
                        csvfile.flush()
                        total_filas_ok += 1
                    else:
                        total_filas_err += 1

    print()
    print("=" * 68)
    print(f"  Peticiones a la API realizadas : {request_counter[0]}")
    print(f"  Filas escritas en el CSV       : {total_filas_ok}")
    print(f"  Rutas sin datos / con error    : {total_filas_err}")
    print(f"  Fichero CSV                    : {csv_path.name}")
    print("=" * 68)

    # Mostrar cómo continuar en la próxima ejecución
    if request_counter[0] >= MAX_REQUESTS:
        # Calcular cuál fue la última hora+modo procesados
        last_hour = START_HOUR
        last_mode = START_MODE
        count = 0
        done = False
        for hour in HOURS:
            if hour < START_HOUR or done:
                continue
            for mode_idx, mode in enumerate(TRANSPORT_MODES):
                if hour == START_HOUR and mode_idx < mode_order.get(START_MODE, 0):
                    continue
                count += len(ROUTES)
                if count >= MAX_REQUESTS:
                    last_hour = hour
                    last_mode = mode
                    done = True
                    break

        # Calcular siguiente posición
        mode_list   = TRANSPORT_MODES
        mode_idx    = mode_list.index(last_mode)
        if mode_idx + 1 < len(mode_list):
            next_mode = mode_list[mode_idx + 1]
            next_hour = last_hour
        else:
            next_mode = mode_list[0]
            next_hour = last_hour + 1 if last_hour < 24 else None

        print()
        print("  ⏸  Ejecución pausada por MAX_REQUESTS.")
        print("  Para continuar en la próxima ejecución, pon en el script:")
        if next_hour and next_hour <= 24:
            print(f"    START_HOUR    = {next_hour}")
            print('    START_MODE    = "' + next_mode + '"')
            print('    APPEND_TO_CSV = "' + csv_path.name + '"')
            print(" En caso de que parara sin terminar un tipo de transporte, inicialo de nuevo en el mismo tipo,")
            print(" mejor limpiar el dataset que tener datos faltantes.")
        else:
            print("  ✅ Todas las horas y modos han sido procesados.")
    else:
        print()
        print("  ✅ Todas las combinaciones solicitadas han sido procesadas.")


if __name__ == "__main__":
    main()
