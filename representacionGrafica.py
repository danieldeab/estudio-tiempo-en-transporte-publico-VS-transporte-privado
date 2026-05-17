import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ─────────────────────────────────────────────
# 1. CARGA DE DATOS
# ─────────────────────────────────────────────
df_drive = pd.read_csv('datos_limpios_drive.csv')
df_trans = pd.read_csv('datos_limpios_transportes.csv')

# ─────────────────────────────────────────────
# 2. COLUMNAS IMPORTANTES
# ─────────────────────────────────────────────
COL_ORIGEN      = 'origen'
COL_DESTINO     = 'destino'
COL_DIST        = 'distancia_km'
COL_PRIVADO_CON = 'duracion_con_trafico_min'
COL_PUBLICO     = 'duracion_sin_trafico_min'

# ─────────────────────────────────────────────
# 3. AGRUPAR POR ORIGEN-DESTINO (MEDIA POR TRAYECTO)
# ─────────────────────────────────────────────
drive_agg = (
    df_drive
    .dropna(subset=[COL_DIST, COL_PRIVADO_CON])
    .groupby([COL_ORIGEN, COL_DESTINO], as_index=False)
    .agg(
        distancia_drive  = (COL_DIST,        'mean'),
        tiempo_privado   = (COL_PRIVADO_CON, 'mean'),
        n_drive          = (COL_PRIVADO_CON, 'count')
    )
)

trans_agg = (
    df_trans
    .dropna(subset=[COL_DIST, COL_PUBLICO])
    .groupby([COL_ORIGEN, COL_DESTINO], as_index=False)
    .agg(
        distancia_publico = (COL_DIST,    'mean'),
        tiempo_publico    = (COL_PUBLICO, 'mean'),
        n_publico         = (COL_PUBLICO, 'count')
    )
)

# ─────────────────────────────────────────────
# 4. UNIR SOLO LOS TRAYECTOS COMUNES
# ─────────────────────────────────────────────
df = pd.merge(
    drive_agg,
    trans_agg,
    on=[COL_ORIGEN, COL_DESTINO],
    how='inner'
)

# ─────────────────────────────────────────────
# 5. DISTANCIA MEDIA DEL TRAYECTO
# ─────────────────────────────────────────────
df['distancia_km'] = df[['distancia_drive', 'distancia_publico']].mean(axis=1)

# Peso de cada trayecto: media entre n_drive y n_publico
df['peso'] = (df['n_drive'] + df['n_publico']) / 2

# Etiqueta del trayecto
df['trayecto'] = df[COL_ORIGEN].astype(str) + ' → ' + df[COL_DESTINO].astype(str)

# Ordenar por distancia
df = df.sort_values('distancia_km').reset_index(drop=True)
df['trayecto_id'] = range(1, len(df) + 1)

# ─────────────────────────────────────────────
# 6. RESUMEN GENERAL
# ─────────────────────────────────────────────
print("\n" + "="*80)
print("RESUMEN GENERAL DE TRAYECTOS COMPARABLES")
print("="*80)

print(f"Total de trayectos comparables: {len(df)}\n")

print("Primeros trayectos ordenados por distancia:")
print(df[['trayecto', 'distancia_km',
          'tiempo_privado', 'tiempo_publico',
          'n_drive', 'n_publico', 'peso']].head(20).to_string(index=False))

# ─────────────────────────────────────────────
# 7. GRÁFICOS
# ─────────────────────────────────────────────
ZOOM_KM = 100   # límite del diagrama de dispersión ampliado

# Rangos de distancia para diagramas detallados
RANGOS = [
    (0,  20,  'Distancias cortas'),
    (20, 40,  'Distancias medias'),
    (40, df['distancia_km'].max(), 'Distancias largas'),
]

fig, axes = plt.subplots(7, 1, figsize=(16, 44))

# ─────────────────────────────────────────────
# GRÁFICO 1: DIAGRAMA LINEAL
# ─────────────────────────────────────────────
axes[0].plot(df['distancia_km'], df['tiempo_privado'],
             label='Transporte privado', linewidth=2.2, marker='o', markersize=3)
axes[0].plot(df['distancia_km'], df['tiempo_publico'],
             label='Transporte público', linewidth=2.2, marker='s', markersize=3)

axes[0].set_title('Tiempo medio de viaje por trayecto origen-destino — vista completa', fontsize=13, fontweight='bold')
axes[0].set_xlabel('Distancia del trayecto (km)', fontsize=10)
axes[0].set_ylabel('Duración media (min)', fontsize=10)
axes[0].axvline(x=ZOOM_KM, color='red', linestyle=':', linewidth=1.5, label=f'Límite zoom ({ZOOM_KM} km)')
axes[0].grid(True, linestyle='--', alpha=0.4)
axes[0].legend()

# ─────────────────────────────────────────────
# GRÁFICO 2: DIAGRAMA LINEAL AMPLIADO (zoom)
# ─────────────────────────────────────────────
df_zoom_line = df[df['distancia_km'] <= ZOOM_KM].copy()

axes[1].plot(df_zoom_line['distancia_km'], df_zoom_line['tiempo_privado'],
             label='Transporte privado', linewidth=2.2, marker='o', markersize=4)
axes[1].plot(df_zoom_line['distancia_km'], df_zoom_line['tiempo_publico'],
             label='Transporte público', linewidth=2.2, marker='s', markersize=4)

axes[1].set_title(
    f'Tiempo medio de viaje — ampliado ≤ {ZOOM_KM} km ({len(df_zoom_line)} de {len(df)} trayectos)',
    fontsize=13, fontweight='bold'
)
axes[1].set_xlabel('Distancia del trayecto (km)', fontsize=10)
axes[1].set_ylabel('Duración media (min)', fontsize=10)
axes[1].set_xlim(0, ZOOM_KM)
axes[1].grid(True, linestyle='--', alpha=0.4)
axes[1].legend()

# ─────────────────────────────────────────────
# GRÁFICO 3: DIAGRAMA DE DISPERSIÓN COMPLETO
# ─────────────────────────────────────────────
scatter_size = df['peso'] / df['peso'].max() * 150 + 20

axes[2].scatter(df['distancia_km'], df['tiempo_privado'],
                alpha=0.7, s=scatter_size, label='Transporte privado')
axes[2].scatter(df['distancia_km'], df['tiempo_publico'],
                alpha=0.7, s=scatter_size, label='Transporte público', marker='s')

axes[2].axvline(x=ZOOM_KM, color='red', linestyle=':', linewidth=1.5,
                label=f'Límite zoom ({ZOOM_KM} km)')

axes[2].set_title(
    'Dispersión de tiempos medios según la distancia — vista completa\n'
    '(tamaño del punto proporcional al número de mediciones)',
    fontsize=13, fontweight='bold'
)
axes[2].set_xlabel('Distancia media del trayecto (km)', fontsize=10)
axes[2].set_ylabel('Duración media (min)', fontsize=10)
axes[2].grid(True, linestyle='--', alpha=0.4)
axes[2].legend()

# ─────────────────────────────────────────────
# GRÁFICO 4: DIAGRAMA DE DISPERSIÓN AMPLIADO (zoom)
# ─────────────────────────────────────────────
df_zoom = df[df['distancia_km'] <= ZOOM_KM].copy()
scatter_size_zoom = df_zoom['peso'] / df_zoom['peso'].max() * 150 + 20

axes[3].scatter(df_zoom['distancia_km'], df_zoom['tiempo_privado'],
                alpha=0.7, s=scatter_size_zoom, label='Transporte privado')
axes[3].scatter(df_zoom['distancia_km'], df_zoom['tiempo_publico'],
                alpha=0.7, s=scatter_size_zoom, label='Transporte público', marker='s')

axes[3].set_title(
    f'Dispersión ampliada — trayectos ≤ {ZOOM_KM} km ({len(df_zoom)} de {len(df)} trayectos)\n'
    '(tamaño del punto proporcional al número de mediciones)',
    fontsize=13, fontweight='bold'
)
axes[3].set_xlabel('Distancia media del trayecto (km)', fontsize=10)
axes[3].set_ylabel('Duración media (min)', fontsize=10)
axes[3].set_xlim(0, ZOOM_KM)
axes[3].grid(True, linestyle='--', alpha=0.4)
axes[3].legend()

# ─────────────────────────────────────────────
# GRÁFICOS 5-7: DIAGRAMA LINEAL POR RANGO DE DISTANCIA
# ─────────────────────────────────────────────
for idx, (km_min, km_max, etiqueta) in enumerate(RANGOS, start=4):
    df_rango = df[(df['distancia_km'] > km_min) & (df['distancia_km'] <= km_max)].copy()

    if len(df_rango) == 0:
        axes[idx].set_title(f'{etiqueta} ({km_min}–{km_max} km) — sin datos', fontsize=13)
        continue

    axes[idx].plot(df_rango['distancia_km'], df_rango['tiempo_privado'],
                   label='Transporte privado', linewidth=2.2, marker='o', markersize=4)
    axes[idx].plot(df_rango['distancia_km'], df_rango['tiempo_publico'],
                   label='Transporte público', linewidth=2.2, marker='s', markersize=4)

    axes[idx].set_title(
        f'Tiempo medio de viaje — {etiqueta} ({km_min}–{km_max} km) · {len(df_rango)} trayectos',
        fontsize=13, fontweight='bold'
    )
    axes[idx].set_xlabel('Distancia del trayecto (km)', fontsize=10)
    axes[idx].set_ylabel('Duración media (min)', fontsize=10)
    axes[idx].set_xlim(km_min, km_max)
    if etiqueta == 'Distancias largas':
        axes[idx].set_xticks(np.arange(km_min, km_max + 10, 10))
        axes[idx].tick_params(axis='x', rotation=45)
    axes[idx].grid(True, linestyle='--', alpha=0.4)
    axes[idx].legend()

plt.tight_layout()
plt.savefig('comparativa_lineal_y_dispersion.png', dpi=150, bbox_inches='tight')
plt.show()

print("\nGráficos guardados como 'comparativa_lineal_y_dispersion.png'")

# ─────────────────────────────────────────────
# 8. EXPORTAR TABLA FINAL
# ─────────────────────────────────────────────
df.to_csv('tabla_comparativa_trayectos.csv', index=False)
print("Tabla exportada como 'tabla_comparativa_trayectos.csv'")

# ─────────────────────────────────────────────
# 9. COEFICIENTE DE DETERMINACIÓN r² PONDERADO
# ─────────────────────────────────────────────
weights = df['peso']

def r2_ponderado(x, y, w):
    """Pearson r ponderado al cuadrado entre dos series."""
    x_bar = np.average(x, weights=w)
    y_bar = np.average(y, weights=w)
    num = np.sum(w * (x - x_bar) * (y - y_bar))
    den = np.sqrt(
        np.sum(w * (x - x_bar)**2) *
        np.sum(w * (y - y_bar)**2)
    )
    return (num / den) ** 2

def r2_sin_ponderar(x, y):
    return x.corr(y) ** 2

# ── transporte privado  vs  transporte público ────────────────────────────────
r2_p  = r2_ponderado(df['tiempo_privado'], df['tiempo_publico'], weights)
r2_sp = r2_sin_ponderar(df['tiempo_privado'], df['tiempo_publico'])

print("\n" + "="*70)
print("COEFICIENTE DE DETERMINACIÓN r²")
print("="*70)
print(f"{'Comparación':<45} {'Ponderado':>10} {'Sin pond.':>10}")
print("-"*70)
print(f"{'Transporte privado  vs  Transporte público':<45} {r2_p:>10.3f} {r2_sp:>10.3f}")
print("="*70)
print("(Ponderado = por número de mediciones de cada trayecto)")