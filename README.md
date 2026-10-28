# GeoEquidad: Avance de base de datos y modelos de regresión

Proyecto de la materia **Bases de Datos** (3er semestre, Universidad de Guadalajara, CUGDL).
Participantes: Christian Edén Ureña Vázquez y Tadeo Salvador Hernández Muñoz.

GeoEquidad (Sistema Inteligente de Focalización y Logística para Asistencia Social) busca apoyar la focalización de programas sociales a partir de datos oficiales de pobreza y carencias sociales.

Este avance cubre:

1. Obtención y limpieza de los datos de pobreza municipal 2020 (CONEVAL) para Jalisco.
2. Clasificación de la variable objetivo y de las variables predictoras.
3. Primeras pruebas de machine learning: regresión lineal simple y regresión lineal múltiple.

## Objetivo

Evaluar cómo las carencias sociales (rezago educativo, salud, seguridad social, vivienda, servicios básicos y alimentación) se asocian con el porcentaje de población en pobreza en los 125 municipios de Jalisco.

## Estructura del proyecto

```
.
├── 01_base_original/
│   └── Concentrado_indicadores_de_pobreza_2020.xlsx   # archivo oficial CONEVAL, sin modificar
├── 02_base_limpia/
│   └── pobreza_municipal_jalisco_2020_limpia.csv      # 125 municipios x 22 columnas
├── 03_programas/
│   ├── 01_limpieza.py          # genera la base limpia desde el Excel original
│   ├── 02_modelos.py           # regresión simple, múltiple y validación cruzada
│   └── resultados_modelos.txt  # salida de 02_modelos.py
├── 04_documento/
│   ├── GeoEquidad_Avance.tex   # documento del avance (fuente)
│   └── GeoEquidad_Avance.pdf   # documento del avance
└── README.md
```

## Fuente de datos

- **Institución:** CONEVAL (Consejo Nacional de Evaluación de la Política de Desarrollo Social).
- **Archivo:** Concentrado de indicadores de pobreza 2020, hoja *Concentrado municipal*.
- **Unidad:** municipio. Se usaron los 125 municipios de Jalisco (clave de entidad 14).
- **Cortes:** población, pobreza y carencias sociales, corte 2020.

El archivo original no fue modificado. Todo el procesamiento se hace con código sobre una copia.

## Base limpia

`01_limpieza.py` hace lo siguiente:

- Lee el Excel original (los encabezados están repartidos en varias filas).
- Conserva solo los municipios (clave de 5 dígitos) y filtra Jalisco.
- Renombra columnas a `snake_case` y convierte tipos.
- Crea las categorías `tipo_municipio_poblacion` y `nivel_intensidad_carencias`, con sus indicadoras 0/1.
- Verifica que no haya faltantes, duplicados ni porcentajes fuera de [0, 100].

Resultado: 125 filas y 22 columnas, sin valores faltantes. Verificamos que el programa reproduce el CSV entregado valor por valor.

## Variables del modelo

| Rol | Variable | Tipo |
|---|---|---|
| Y (objetivo) | `pobreza_porcentaje` | Cuantitativa continua (0–100) |
| X (simple) | `carencia_vivienda_porcentaje` | Cuantitativa continua |
| X (múltiple) | `rezago_educativo_porcentaje`, `carencia_salud_porcentaje`, `carencia_seguridad_social_porcentaje`, `carencia_vivienda_porcentaje`, `carencia_servicios_basicos_porcentaje`, `carencia_alimentacion_porcentaje` | Cuantitativas continuas |
| X (múltiple) | `ind_semiurbano_medio`, `ind_urbano_grande` (referencia: `Rural_Pequeno`) | Categórica (dummies 0/1) |

Variables excluidas, con motivo:

- `ingreso_inferior_lpi_porcentaje`: correlación de 0.94 con la Y. La pobreza se define con ingreso y carencias, así que incluirla hace el modelo circular.
- `nivel_intensidad_carencias`: se calcula a partir de `carencias_promedio`, que es función de las carencias.
- `pobreza_extrema_porcentaje`, `pobreza_personas`, `carencias_promedio`: son parte de la Y o resúmenes de las mismas carencias.

## Cómo correr el proyecto

Requisitos: Python 3.10 o superior.

```bash
pip install pandas openpyxl numpy statsmodels scikit-learn

# desde la carpeta raíz del proyecto
python 03_programas/01_limpieza.py   # genera 02_base_limpia/...csv
python 03_programas/02_modelos.py    # imprime resultados de los modelos
```

## Resultados principales

| Modelo | Predictoras | R² | R² ajustado | R² validación cruzada | RMSE CV (pp) |
|---|---|---|---|---|---|
| Simple | 1 (vivienda) | 0.369 | 0.364 | 0.265 | 8.03 |
| Múltiple | 8 | 0.625 | 0.599 | 0.501 | 6.59 |

Interpretación:

- **Simple:** por cada punto porcentual de carencia de vivienda, la pobreza municipal aumenta 0.85 puntos porcentuales en promedio (p < 0.001).
- **Múltiple:** controlando por las demás variables, las carencias significativas son seguridad social (+0.33, p = 0.0005), vivienda (+0.53, p = 0.005) y alimentación (+0.35, p = 0.014). Rezago educativo, salud y servicios básicos no son significativas, y las indicadoras de tipo de municipio tampoco.
- El modelo múltiple predice mejor que el simple: el error de validación baja de 8.03 a 6.59 puntos porcentuales.

La validación cruzada (5 folds, repetida 20 veces) mide la capacidad de predecir municipios que no se usaron para ajustar. Por eso reportamos ese R² junto con el R² normal.

## Limitaciones

- **Muestra pequeña y regional:** 125 municipios de un solo estado. Los coeficientes pueden cambiar con otros estados o a nivel nacional. En el análisis preliminar nacional, por ejemplo, servicios básicos sí fue significativa.
- **Asociación, no causalidad:** los modelos describen qué carencias acompañan a mayor pobreza, no qué la causa.
- **Circularidad parcial:** la pobreza se define con carencias e ingreso, así que el R² no mide qué tanto explican las carencias la pobreza en general.
- **Dependencia entre municipios:** comparten entidad y condiciones regionales.
- **Municipios atípicos:** algunos tienen error grande (Atenguillo y Mixtlán, con pobreza real muy menor a la predicha). Conviene revisarlos antes de usar el modelo para focalizar recursos.

## Pendientes

- Agregar el programa de carga a MySQL (`02_limpiar_y_cargar_mysql.py`), que el documento menciona pero no está en esta carpeta.
- Agregar las capturas de pantalla (Figura 1 y Figura 2) que el documento cita en la sección 4.
- Verificar en la nota técnica de CONEVAL cómo se estiman las cifras de pobreza municipal.
