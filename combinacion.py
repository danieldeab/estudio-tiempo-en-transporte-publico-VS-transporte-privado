import pandas as pd
from pathlib import Path

#Cogemos todos los archivos que empiezan por madrid_rutas
archivos = sorted(Path(".").glob("madrid_rutas*.csv"))
df = pd.concat([pd.read_csv(f) for f in archivos], ignore_index=True)

# Eliminar duplicados exactos por si hay solapamiento
df.drop_duplicates(subset=["origen", "destino", "modo_transporte", "hora_salida"], inplace=True)
df.to_csv("combinado1.csv", index=False)
print(f"{len(df)} filas en total")

# Rutas con errores agrupadas
errores = df[df["duracion_sin_trafico_min"].isna()].reset_index()
print(errores.groupby(["index", "origen", "destino", "modo_transporte"]).size())

