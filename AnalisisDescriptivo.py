import pandas as pd
import numpy as np

# ============================================================
# 1. Leer los CSVs limpios
# ============================================================

df_drive   = pd.read_csv("datos_DRIVE.csv")
df_transit = pd.read_csv("datos_TRANSIT.csv")

# Columna de duracion segun modo
df_drive["duracion_min"]   = df_drive["duracion_con_trafico_min"]
df_transit["duracion_min"] = df_transit["duracion_sin_trafico_min"]


# ============================================================
# 2. Formulas manuales de estadisticos descriptivos
# ============================================================

def calcular_media(serie):
    return sum(serie) / len(serie)

def calcular_mediana(serie):
    ordenada = sorted(serie)
    n = len(ordenada)
    mitad = n // 2
    if n % 2 == 0:
        return (ordenada[mitad - 1] + ordenada[mitad]) / 2
    else:
        return ordenada[mitad]

def calcular_moda(serie):
    frecuencias = {}
    for valor in serie:
        frecuencias[valor] = frecuencias.get(valor, 0) + 1
    return max(frecuencias, key=frecuencias.get)

def calcular_varianza(serie):
    media = calcular_media(serie)
    return sum((x - media) ** 2 for x in serie) / (len(serie) - 1)  # varianza muestral

def calcular_desv_tipica(serie):
    return calcular_varianza(serie) ** 0.5

def calcular_rango(serie):
    return max(serie) - min(serie)


def descriptivos(serie, nombre):
    valores = serie.dropna().tolist()
    media   = calcular_media(valores)
    return {
        "Variable"     : nombre,
        "N"            : len(valores),
        "Media"        : round(media, 4),
        "Mediana"      : round(calcular_mediana(valores), 4),
        "Moda"         : round(calcular_moda(valores), 4),
        "Desv. Tipica" : round(calcular_desv_tipica(valores), 4),
        "Varianza"     : round(calcular_varianza(valores), 4),
        "Rango"        : round(calcular_rango(valores), 4),
        "Min"          : round(min(valores), 4),
        "Max"          : round(max(valores), 4),
    }


# ============================================================
# 3. Estadisticos descriptivos por modo
# ============================================================

stats_list = [
    descriptivos(df_drive["distancia_km"],    "DRIVE   - Distancia (km)"),
    descriptivos(df_drive["duracion_min"],     "DRIVE   - Duracion (min)"),
    descriptivos(df_transit["distancia_km"],  "TRANSIT - Distancia (km)"),
    descriptivos(df_transit["duracion_min"],  "TRANSIT - Duracion (min)"),
]

df_stats = pd.DataFrame(stats_list).set_index("Variable")

print("=" * 70)
print("ESTADISTICOS DESCRIPTIVOS")
print("=" * 70)
print(df_stats.to_string())
print()


# ============================================================
# 4. Tabla bivariante: intervalos de distancia vs duracion
#    X = distancia_km (intervalos)   Y = duracion_min
# ============================================================

bins   = [0, 10, 20, 30, 50, 100, 200, 300, 400, 500, 700]
labels = ["0-10", "10-20", "20-30", "30-50", "50-100",
          "100-200", "200-300", "300-400", "400-500", "500-700"]

def tabla_bivariante(df, modo):
    df = df.copy()
    df["intervalo_km"] = pd.cut(df["distancia_km"], bins=bins, labels=labels, right=True)

    filas = []
    for intervalo in labels:
        grupo = df[df["intervalo_km"] == intervalo]["duracion_min"].dropna().tolist()
        if len(grupo) == 0:
            filas.append({
                "Intervalo distancia (km)" : intervalo,
                "N"          : 0,
                "Media (min)": None,
                "Mediana (min)": None,
                "Desv. Tipica": None,
                "Min (min)"  : None,
                "Max (min)"  : None,
            })
        else:
            filas.append({
                "Intervalo distancia (km)" : intervalo,
                "N"            : len(grupo),
                "Media (min)"  : round(calcular_media(grupo), 2),
                "Mediana (min)": round(calcular_mediana(grupo), 2),
                "Desv. Tipica" : round(calcular_desv_tipica(grupo), 2) if len(grupo) > 1 else 0.0,
                "Min (min)"    : round(min(grupo), 2),
                "Max (min)"    : round(max(grupo), 2),
            })

    tabla = pd.DataFrame(filas).set_index("Intervalo distancia (km)")
    tabla.index.name = f"Distancia (km) [{modo}]"
    return tabla

biv_drive   = tabla_bivariante(df_drive,   "DRIVE")
biv_transit = tabla_bivariante(df_transit, "TRANSIT")

print("=" * 70)
print("TABLA BIVARIANTE - DRIVE  (X: distancia km | Y: duracion min)")
print("=" * 70)
print(biv_drive.to_string())
print()

print("=" * 70)
print("TABLA BIVARIANTE - TRANSIT (X: distancia km | Y: duracion min)")
print("=" * 70)
print(biv_transit.to_string())
print()


# ============================================================
# 5. Tabla comparativa DRIVE vs TRANSIT lado a lado
# ============================================================

comp = pd.concat(
    [biv_drive[["N", "Media (min)"]], biv_transit[["N", "Media (min)"]]],
    axis=1,
    keys=["DRIVE", "TRANSIT"]
)
comp.columns = ["DRIVE N", "DRIVE Media (min)", "TRANSIT N", "TRANSIT Media (min)"]

print("=" * 70)
print("COMPARATIVA DRIVE vs TRANSIT — Media de duracion por distancia")
print("=" * 70)
print(comp.to_string())
print()


# ============================================================
# 6. Guardar todo en CSV
# ============================================================

df_stats.to_csv("estadisticos_descriptivos.csv")
biv_drive.to_csv("bivariante_DRIVE.csv")
biv_transit.to_csv("bivariante_TRANSIT.csv")
comp.to_csv("comparativa_DRIVE_vs_TRANSIT.csv")

print("Archivos guardados:")
print("  estadisticos_descriptivos.csv")
print("  bivariante_DRIVE.csv")
print("  bivariante_TRANSIT.csv")
print("  comparativa_DRIVE_vs_TRANSIT.csv")
