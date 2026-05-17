import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# -----------------------------
# Estadísticos conocidos
# -----------------------------
mean_drive = 64.623652
std_drive = 87.336185

mean_transit = 72.673113
std_transit = 75.018465

mean_diff = 8.049461
std_diff = 54.548856

n = 1391

# -----------------------------
# Generar datos simulados
# -----------------------------
np.random.seed(1)

drive = np.random.normal(mean_drive, std_drive, n)
transit = np.random.normal(mean_transit, std_transit, n)

diferencia = transit - drive

df = pd.DataFrame({
    "drive": drive,
    "transit": transit,
    "diferencia": diferencia
})

# -----------------------------
# Correlaciones de Pearson
# -----------------------------
r_drive = df["drive"].corr(df["diferencia"])
r_transit = df["transit"].corr(df["diferencia"])

r2_drive = r_drive**2
r2_transit = r_transit**2

print("\nCoeficientes de correlación de Pearson\n")

print(f"DRIVE vs DIFERENCIA (r): {r_drive:.3f}")
print(f"DRIVE vs DIFERENCIA (r²): {r2_drive:.3f}\n")

print(f"TRANSIT vs DIFERENCIA (r): {r_transit:.3f}")
print(f"TRANSIT vs DIFERENCIA (r²): {r2_transit:.3f}\n")

# -----------------------------
# Gráfico DRIVE vs DIFERENCIA
# -----------------------------
plt.figure()

plt.scatter(df["drive"], df["diferencia"], alpha=0.5)

plt.xlabel("Duración DRIVE (min)")
plt.ylabel("Diferencia (TRANSIT - DRIVE)")
plt.title("Relación entre duración en coche y diferencia de tiempo")

plt.grid(True)

plt.show()

# -----------------------------
# Gráfico TRANSIT vs DIFERENCIA
# -----------------------------
plt.figure()

plt.scatter(df["transit"], df["diferencia"], alpha=0.5)

plt.xlabel("Duración TRANSIT (min)")
plt.ylabel("Diferencia (TRANSIT - DRIVE)")
plt.title("Relación entre duración en transporte público y diferencia")

plt.grid(True)

plt.show()