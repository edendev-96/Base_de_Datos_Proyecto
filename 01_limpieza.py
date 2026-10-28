"""
01_limpieza.py
Limpia el Concentrado de indicadores de pobreza 2020 (CONEVAL, nivel municipal)
y genera la base limpia de Jalisco (125 municipios, 22 columnas).

Entrada : 01_base_original/Concentrado_indicadores_de_pobreza_2020.xlsx (sin modificar)
Salida  : 02_base_limpia/pobreza_municipal_jalisco_2020_limpia.csv
Ejecutar desde la carpeta raiz del proyecto:  python 03_programas/01_limpieza.py
"""
from pathlib import Path
import pandas as pd
import numpy as np

ORIGEN = Path("01_base_original/Concentrado_indicadores_de_pobreza_2020.xlsx")
DESTINO = Path("02_base_limpia/pobreza_municipal_jalisco_2020_limpia.csv")

# 1. Lectura del libro sin encabezado (los encabezados estan repartidos en las filas 4 y 5)
raw = pd.read_excel(ORIGEN, sheet_name="Concentrado municipal", header=None, dtype=object)

# 2. Filtrado: solo filas de municipios (clave de municipio de 5 digitos).
#    Quedan fuera titulos, renglones vacios y notas metodologicas al final.
datos = raw.iloc[6:].copy()
es_municipio = datos[3].astype(str).str.fullmatch(r"\d{5}")
datos = datos[es_municipio]

# 3. Seleccion y renombrado de columnas (indices de columna del Excel original)
mapa = {
    1: "clave_entidad",
    2: "entidad_federativa",
    3: "clave_municipio",
    4: "municipio",
    7: "poblacion_2020",
    10: "pobreza_porcentaje",
    13: "pobreza_personas",
    16: "carencias_promedio",
    19: "pobreza_extrema_porcentaje",
    58: "rezago_educativo_porcentaje",
    67: "carencia_salud_porcentaje",
    76: "carencia_seguridad_social_porcentaje",
    85: "carencia_vivienda_porcentaje",
    94: "carencia_servicios_basicos_porcentaje",
    103: "carencia_alimentacion_porcentaje",
    130: "ingreso_inferior_lpi_porcentaje",
}
df = datos[list(mapa)].rename(columns=mapa)

# 4. Acotacion a Jalisco (antes de convertir a numero: hay "n.d." en otros estados)
df["clave_entidad"] = df["clave_entidad"].astype(str).str.zfill(2)
df = df[df["clave_entidad"] == "14"].reset_index(drop=True)

# 5. Conversion de tipos
df["clave_municipio"] = df["clave_municipio"].astype(str).str.zfill(5)
for c in df.columns.difference(["clave_entidad", "entidad_federativa", "clave_municipio", "municipio"]):
    df[c] = pd.to_numeric(df[c], errors="raise")  # aqui fallaria si hubiera "n.d."
df["poblacion_2020"] = df["poblacion_2020"].astype(int)
df["pobreza_personas"] = df["pobreza_personas"].astype(int)
columnas_pct = [c for c in df.columns if c.endswith("_porcentaje") or c == "carencias_promedio"]
df[columnas_pct] = df[columnas_pct].round(2)

# 6. Variables categoricas derivadas (cortes observados en la base limpia)
#    tipo de municipio por poblacion: Rural < 15,000 <= Semiurbano < 100,000 <= Urbano
df["tipo_municipio_poblacion"] = np.select(
    [df["poblacion_2020"] < 15000, df["poblacion_2020"] < 100000],
    ["Rural_Pequeno", "Semiurbano_Medio"],
    default="Urbano_Grande",
)
#    nivel de intensidad por carencias promedio: Baja < 1.90 <= Moderada < 2.30 <= Alta
df["nivel_intensidad_carencias"] = np.select(
    [df["carencias_promedio"] < 1.90, df["carencias_promedio"] < 2.30],
    ["Intensidad_Baja", "Intensidad_Moderada"],
    default="Intensidad_Alta",
)
# 7. Indicadoras binarias (0/1)
df["ind_urbano_grande"] = (df["tipo_municipio_poblacion"] == "Urbano_Grande").astype(int)
df["ind_semiurbano_medio"] = (df["tipo_municipio_poblacion"] == "Semiurbano_Medio").astype(int)
df["ind_intensidad_alta"] = (df["nivel_intensidad_carencias"] == "Intensidad_Alta").astype(int)
df["ind_intensidad_moderada"] = (df["nivel_intensidad_carencias"] == "Intensidad_Moderada").astype(int)

# 8. Controles de calidad
assert len(df) == 125, f"Se esperaban 125 municipios y hay {len(df)}"
assert df.isna().sum().sum() == 0, "Hay valores vacios"
assert df["clave_municipio"].is_unique, "Hay claves duplicadas"
assert df.filter(like="_porcentaje").apply(lambda s: s.between(0, 100)).all().all()

# 9. Exportacion (mismo orden de columnas que la base limpia entregada)
orden = ["clave_municipio", "clave_entidad", "entidad_federativa", "municipio", "poblacion_2020",
         "pobreza_porcentaje", "pobreza_personas", "carencias_promedio", "pobreza_extrema_porcentaje",
         "rezago_educativo_porcentaje", "carencia_salud_porcentaje", "carencia_seguridad_social_porcentaje",
         "carencia_vivienda_porcentaje", "carencia_servicios_basicos_porcentaje",
         "carencia_alimentacion_porcentaje", "ingreso_inferior_lpi_porcentaje",
         "tipo_municipio_poblacion", "nivel_intensidad_carencias",
         "ind_urbano_grande", "ind_semiurbano_medio", "ind_intensidad_alta", "ind_intensidad_moderada"]
df = df[orden]
DESTINO.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(DESTINO, index=False, encoding="utf-8")
print(f"Base limpia: {df.shape[0]} filas x {df.shape[1]} columnas -> {DESTINO}")
