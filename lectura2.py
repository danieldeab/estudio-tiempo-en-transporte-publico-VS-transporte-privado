import pandas as pd
import numpy as np

# ==========================
# 1. Leer el CSV
# ==========================

df = pd.read_csv("combinado1.csv")
print(f"Filas originales: {len(df)}")
print(df["modo_transporte"].value_counts())


# ==========================
# 2. Separar por modo de transporte
# ==========================

df_drive   = df[df["modo_transporte"] == "DRIVE"].copy()
df_transit = df[df["modo_transporte"] == "TRANSIT"].copy()


# ==========================
# 3. Crear variable minutos por km
#    DRIVE   -> usa duracion_con_trafico_min  (tiene datos reales de trafico)
#    TRANSIT -> usa duracion_sin_trafico_min  (duracion_con_trafico_min esta vacia para este modo)
# ==========================

df_drive["min_por_km"]   = df_drive["duracion_con_trafico_min"]  / df_drive["distancia_km"]
df_transit["min_por_km"] = df_transit["duracion_sin_trafico_min"] / df_transit["distancia_km"]


# ==========================
# 4. Eliminar duplicados internos dentro de cada modo
#    (misma distancia y misma duracion dentro del mismo modo de transporte)
#    Se permite que DRIVE y TRANSIT compartan valores entre ellos
# ==========================

antes_drive   = len(df_drive)
antes_transit = len(df_transit)

df_drive   = df_drive.drop_duplicates(subset=["distancia_km", "duracion_con_trafico_min"])
df_transit = df_transit.drop_duplicates(subset=["distancia_km", "duracion_sin_trafico_min"])

print(f"\n--- Tras eliminar duplicados internos ---")
print(f"  DRIVE:   {antes_drive} -> {len(df_drive)} filas (eliminados: {antes_drive - len(df_drive)})")
print(f"  TRANSIT: {antes_transit} -> {len(df_transit)} filas (eliminados: {antes_transit - len(df_transit)})")


# ==========================
# 5. Calcular IQR global combinado (mismo rango para comparar ambos modos)
# ==========================

todos_min_por_km = pd.concat([df_drive["min_por_km"], df_transit["min_por_km"]])

Q1  = todos_min_por_km.quantile(0.25)
Q3  = todos_min_por_km.quantile(0.75)
IQR = Q3 - Q1

limite_inferior = Q1 - 1.5 * IQR
limite_superior = Q3 + 1.5 * IQR

print(f"\n--- IQR GLOBAL (mismo rango para ambos modos) ---")
print(f"  Q1: {Q1:.4f} | Q3: {Q3:.4f} | IQR: {IQR:.4f}")
print(f"  Limite inferior: {limite_inferior:.4f} | Limite superior: {limite_superior:.4f}")


# ==========================
# 6. Filtrar outliers con los limites globales
# ==========================

df_drive_limpio = df_drive[
    (df_drive["min_por_km"] >= limite_inferior) &
    (df_drive["min_por_km"] <= limite_superior)
]
df_transit_limpio = df_transit[
    (df_transit["min_por_km"] >= limite_inferior) &
    (df_transit["min_por_km"] <= limite_superior)
]

print(f"\n--- DRIVE ---")
print(f"  Filas antes: {len(df_drive)} | Filas despues: {len(df_drive_limpio)}")
print(f"\n--- TRANSIT ---")
print(f"  Filas antes: {len(df_transit)} | Filas despues: {len(df_transit_limpio)}")


# ==========================
# 7. Igualar numero de registros (muestreo aleatorio)
# ==========================

n = min(len(df_drive_limpio), len(df_transit_limpio))
print(f"\nNumero final de registros por modo (equilibrado): {n}")

df_drive_final   = df_drive_limpio.sample(n=n, random_state=42).reset_index(drop=True)
df_transit_final = df_transit_limpio.sample(n=n, random_state=42).reset_index(drop=True)


# ==========================
# 8. Guardar CSVs
# ==========================

df_drive_final.to_csv("datos_DRIVE.csv",   index=False)
df_transit_final.to_csv("datos_TRANSIT.csv", index=False)

print("\nArchivos guardados:")
print(f"  datos_DRIVE.csv   -> {len(df_drive_final)} filas")
print(f"  datos_TRANSIT.csv -> {len(df_transit_final)} filas")
