"""
02_modelos.py
Regresion lineal simple y multiple: porcentaje de pobreza municipal 2020 (Jalisco).

Y (variable objetivo) : pobreza_porcentaje
Simple                : pobreza ~ carencia_vivienda
Multiple              : pobreza ~ rezago educativo + salud + seguridad social + vivienda
                        + servicios basicos + alimentacion
                        + indicadoras de tipo de municipio (ref.: Rural_Pequeno)

Excluidas a proposito:
- ingreso_inferior_lpi_porcentaje -> correlacion 0.94 con la Y (casi la misma variable)
- nivel_intensidad_carencias      -> se define con carencias_promedio (circular)
- pobreza extrema / moderada / vulnerables / no pobre -> partes o complementos de la Y
Ejecutar desde la raiz del proyecto:  python 03_programas/02_modelos.py
"""
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import RepeatedKFold, cross_validate
from sklearn.metrics import r2_score

DATOS = "02_base_limpia/pobreza_municipal_jalisco_2020_limpia.csv"
Y = "pobreza_porcentaje"

CARENCIAS = [
    "rezago_educativo_porcentaje",
    "carencia_salud_porcentaje",
    "carencia_seguridad_social_porcentaje",
    "carencia_vivienda_porcentaje",
    "carencia_servicios_basicos_porcentaje",
    "carencia_alimentacion_porcentaje",
]
TIPO = ["ind_semiurbano_medio", "ind_urbano_grande"]

MODELOS = {
    "Simple": ["carencia_vivienda_porcentaje"],
    "Multiple": CARENCIAS + TIPO,
}

df = pd.read_csv(DATOS, dtype={"clave_municipio": str, "clave_entidad": str})
print(f"Municipios: {len(df)}  |  Y = {Y}\n")

cv = RepeatedKFold(n_splits=5, n_repeats=20, random_state=42)
resumen = []

for nombre, X_cols in MODELOS.items():
    X = df[X_cols].astype(float)
    y = df[Y].astype(float)
    Xc = sm.add_constant(X)

    # --- Inferencia (statsmodels, errores robustos HC3) ---
    ols = sm.OLS(y, Xc).fit(cov_type="HC3")
    print(f"=================== Modelo {nombre} ===================")
    print(f"R2 = {ols.rsquared:.4f} | R2 ajustado = {ols.rsquared_adj:.4f} | "
          f"RMSE dentro de muestra = {np.sqrt(ols.mse_resid):.2f}")
    tabla = pd.DataFrame({
        "coef": ols.params, "error_HC3": ols.bse, "p_valor": ols.pvalues,
        "IC95_inf": ols.conf_int()[0], "IC95_sup": ols.conf_int()[1],
    }).round(4)
    print(tabla.to_string(), "\n")

    # --- Validacion cruzada (scikit-learn) ---
    modelo_sk = make_pipeline(StandardScaler(), LinearRegression())
    cvres = cross_validate(
        modelo_sk, X, y, cv=cv,
        scoring={"r2": "r2", "rmse": "neg_root_mean_squared_error", "mae": "neg_mean_absolute_error"},
    )
    print(f"Validacion cruzada 5x20: R2 = {cvres['test_r2'].mean():.4f} (sd {cvres['test_r2'].std():.3f}) | "
          f"RMSE = {-cvres['test_rmse'].mean():.2f} | MAE = {-cvres['test_mae'].mean():.2f}\n")

    # --- Colinealidad (solo en el multiple) ---
    if len(X_cols) > 1:
        vifs = pd.Series([variance_inflation_factor(Xc.values, i) for i in range(1, Xc.shape[1])], index=X_cols)
        print("VIF:\n" + vifs.round(2).to_string() + "\n")

    resumen.append({
        "modelo": nombre,
        "k_predictoras": len(X_cols),
        "R2": round(ols.rsquared, 4),
        "R2_ajustado": round(ols.rsquared_adj, 4),
        "R2_CV": round(cvres["test_r2"].mean(), 4),
        "RMSE_CV": round(-cvres["test_rmse"].mean(), 2),
    })

print("=================== Comparacion ===================")
print(pd.DataFrame(resumen).to_string(index=False))
