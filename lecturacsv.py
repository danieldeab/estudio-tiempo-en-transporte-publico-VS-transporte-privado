import pandas as pd
import numpy as np
import glob

# ==========================
# 1. Leer todos los CSV
# ==========================

archivos = glob.glob("*.csv")

# Si no hay archivos en el directorio actual, buscar en el subdirectorio
if not archivos:
    archivos = glob.glob("Private-vs-Public-transport-travel-time-analysis/*.csv")

df = pd.concat([pd.read_csv(f) for f in archivos], ignore_index=True)
df_drive = df[df["modo_transporte"] == "DRIVE"].copy()

print("Filas originales:", len(df))


# ==========================
# 2. Crear variable minutos por km
# ==========================

df_drive["min_por_km"] = df_drive["duracion_con_trafico_min"] / df_drive["distancia_km"]


# ==========================
# 3. Calcular cuartiles
# ==========================

Q1 = df_drive["min_por_km"].quantile(0.25)
Q3 = df_drive["min_por_km"].quantile(0.75)

IQR = Q3 - Q1

limite_inferior = Q1 - 1.5 * IQR
limite_superior = Q3 + 1.5 * IQR

print("Q1:", Q1)
print("Q3:", Q3)
print("IQR:", IQR)


# ==========================
# 4. Filtrar outliers
# ==========================

df_limpio_drive = df_drive[
    (df_drive["min_por_km"] >= limite_inferior) &
    (df_drive["min_por_km"] <= limite_superior)
]

print("Filas después de limpiar:", len(df_limpio_drive))


# ==========================
# 5. Crear datos limpios para transportes públicos
# ==========================

# Filtrar solo datos de transporte público
df_transit = df[df["modo_transporte"] == "TRANSIT"].copy()

# Para transporte público, usar duracion_sin_trafico_min
df_transit["min_por_km"] = df_transit["duracion_sin_trafico_min"] / df_transit["distancia_km"]

# Calcular cuartiles para transit
Q1_transit = df_transit["min_por_km"].quantile(0.25)
Q3_transit = df_transit["min_por_km"].quantile(0.75)
IQR_transit = Q3_transit - Q1_transit
limite_inferior_transit = Q1_transit - 1.5 * IQR_transit
limite_superior_transit = Q3_transit + 1.5 * IQR_transit

# Filtrar outliers para transit
df_transit_limpio = df_transit[
    (df_transit["min_por_km"] >= limite_inferior_transit) &
    (df_transit["min_por_km"] <= limite_superior_transit)
]

print("Filas de transporte público limpias:", len(df_transit_limpio))

# Guardar el archivo limpio de transportes
df_transit_limpio.to_csv("datos_limpios_transportes.csv", index=False)


# ==========================
# 5. Guardar CSV limpio
# ==========================

df_limpio_drive.to_csv("datos_limpios_drive.csv", index=False)

print("Archivo guardado: datos_limpios_drive.csv y datos_limpios_transportes.csv")