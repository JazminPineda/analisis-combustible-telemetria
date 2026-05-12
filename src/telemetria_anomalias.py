import pathlib
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from itertools import zip_longest
from typing import Any, Dict, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


@dataclass
class Config:
    base_path: pathlib.Path = pathlib.Path(__file__).resolve().parent.parent
    input_pattern: str = "*.xls"
    max_capacity_litros: float = 30000.0
    retraso_critico_horas: float = 3.0
    umbral_std_anomalia: float = 3.0
    date_columns: tuple[str, ...] = (
        "Fecha",
        "Fecha Host",
        "Fecha Actualizacion",
        "fx_almace",
        "Date_fx",
    )
    numeric_columns: tuple[str, ...] = (
        "Volumen",
        "Variacion Volumen",
        "Volumen TC",
        "Variacion Volumen TC",
        "Merma",
        "Temperatura",
        "Altura de Combustible",
        "Altura de Agua",
        "Tiempo_Transcurrido",
        "Horas_Sin_Actualizar",
    )

    def __post_init__(self):
        self.data_path = self.base_path / "data"
        self.outputs_path = self.base_path / "outputs"
        self.outputs_path.mkdir(parents=True, exist_ok=True)

    def list_input_files(self) -> list[pathlib.Path]:
        return sorted(self.data_path.glob(self.input_pattern))


config = Config()
OUTPUTS_PATH = config.outputs_path


def _safe_numeric(series: pd.Series) -> pd.Series:
    """Convertir valores numéricos con detección flexible de separadores."""
    def parse_value(value: Any) -> float:
        if pd.isna(value):
            return np.nan
        s = str(value).strip()
        if s == "":
            return np.nan

        # Caso común: coma como separador de miles y punto como decimal
        if "," in s and "." in s:
            if s.index(",") < s.index("."):
                s = s.replace(",", "")
            else:
                s = s.replace(".", "").replace(",", ".")
        elif "," in s:
            if re.match(r"^-?\d{1,3}(,\d{3})+$", s):
                s = s.replace(",", "")
            else:
                s = s.replace(",", ".")
        elif s.count(".") > 1:
            parts = s.split(".")
            if all(len(part) == 3 for part in parts[1:]):
                s = "".join(parts[:-1]) + "." + parts[-1]

        try:
            return float(s)
        except ValueError:
            return np.nan

    return series.apply(parse_value)


def limpiar_telemetria(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpiar telemetría base y preparar las columnas de tiempo.

    - Convierte las columnas de fecha a datetime
    - Ordena por Tanque y Fecha
    - Detecta timestamps anómalos
    - Calcula diferenciales temporales reales y retrasos de actualización
    """
    df = df.copy()

    # Normalizar nombres de columnas si vienen con espacios extra
    df.columns = [col.strip() for col in df.columns]
    df = df.loc[:, ~df.columns.duplicated()]

    for fecha_col in config.date_columns:
        if fecha_col in df.columns:
            df[fecha_col] = pd.to_datetime(df[fecha_col], errors="coerce")

    # Variables numéricas clave
    for col in config.numeric_columns:
        if col in df.columns:
            df[col] = _safe_numeric(df[col])

    if "Tanque" in df.columns:
        df["Tanque"] = df["Tanque"].astype(str)
    if "Sitio" in df.columns:
        df["Sitio"] = df["Sitio"].astype(str)

    # Orden natural por tanque y fecha de medición
    if "Tanque" in df.columns and "Fecha" in df.columns:
        df = df.sort_values(["Tanque", "Fecha"]).reset_index(drop=True)
    elif "Fecha" in df.columns:
        df = df.sort_values(["Fecha"]).reset_index(drop=True)

    # Usar Volumen TC como referencia ajustada para el cálculo de cambios de volumen.
    if "Volumen TC" in df.columns and df["Volumen TC"].notna().any():
        df["Volumen_Referencia"] = df["Volumen TC"]
    elif "Volumen" in df.columns:
        df["Volumen_Referencia"] = df["Volumen"]
    else:
        df["Volumen_Referencia"] = np.nan

    if "Volumen TC" in df.columns and "Merma" in df.columns:
        df["volumen_tc_merma"] = df["Volumen TC"].fillna(0) + df["Merma"].fillna(0)
        df["capacidad_excedida"] = df["volumen_tc_merma"] > config.max_capacity_litros
    else:
        df["capacidad_excedida"] = False

    # Detectar irregularidades básicas de timestamp
    df["fecha_valida"] = df["Fecha"].notna()
    df["fecha_host_valida"] = df["Fecha Host"].notna()
    df["fecha_actualizacion_valida"] = df["Fecha Actualizacion"].notna()

    df["Fecha_mayor_Actualizacion"] = False
    if "Fecha Actualizacion" in df.columns:
        df["Fecha_mayor_Actualizacion"] = df["Fecha"] > df["Fecha Actualizacion"]
        df["retraso_actualizacion_s"] = (df["Fecha Actualizacion"] - df["Fecha"]).dt.total_seconds()
        df["retraso_actualizacion_s"] = df["retraso_actualizacion_s"].where(df["retraso_actualizacion_s"] >= 0, np.nan)
        df["retraso_actualizacion_critico"] = df["retraso_actualizacion_s"] > 3600 * config.retraso_critico_horas
    else:
        df["retraso_actualizacion_s"] = np.nan
        df["retraso_actualizacion_critico"] = False

    # Duración entre registros por tanque
    if "Tanque" in df.columns and "Fecha" in df.columns:
        df["diff_fecha_s"] = df.groupby("Tanque")["Fecha"].diff().dt.total_seconds()
        df["gap_grande"] = df["diff_fecha_s"] > 3600 * config.retraso_critico_horas
        df["diff_volumen"] = df.groupby("Tanque")["Volumen_Referencia"].diff()
    elif "Fecha" in df.columns:
        df["diff_fecha_s"] = df["Fecha"].diff().dt.total_seconds()
        df["gap_grande"] = df["diff_fecha_s"] > 3600 * config.retraso_critico_horas
        df["diff_volumen"] = df["Volumen_Referencia"].diff()
    else:
        df["diff_fecha_s"] = np.nan
        df["gap_grande"] = False
        df["diff_volumen"] = np.nan

    # Detectar retrodatados si el registro está fuera de orden con respecto al registro previo
    if "Tanque" in df.columns and "Fecha" in df.columns:
        df["diff_fecha_s_reversa"] = df.groupby("Tanque")["Fecha"].diff()
        df["retrodatado_sospechoso"] = df["diff_fecha_s_reversa"].dt.total_seconds().fillna(0) < -1
    else:
        df["retrodatado_sospechoso"] = False

    return df


def _calcular_evaporacion_esperada(df: pd.DataFrame) -> pd.Series:
    """Estima una tasa de variación esperada de volumen a partir de temperatura y merma."""
    if "Merma" in df.columns and df["Merma"].notna().any():
        expected = df["Merma"].fillna(0)
    elif "Temperatura" in df.columns and df["Temperatura"].notna().any():
        expected = 0.001 * df["Temperatura"].fillna(df["Temperatura"].median())
    else:
        expected = pd.Series(0.0, index=df.index)

    return expected


def analizar_indicadores_anomalias(df: pd.DataFrame, tanque_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Analizar indicadores específicos para diferenciar fuga, robo y errores de sistema.
    """
    df_clean = limpiar_telemetria(df)
    if tanque_id:
        df_clean = df_clean[df_clean["Tanque"] == str(tanque_id)].copy()

    indicadores = {
        "fuga": {
            "perdida_constante": False,
            "correlacion_temperatura": False,
            "incremento_agua": False,
            "afecta_24_7": False
        },
        "robo": {
            "caida_abrupta": False,
            "patron_temporal": False,
            "variacion_no_temperatura": False,
            "correlacion_desconexion": False
        },
        "error_sistema": {
            "saltos_imposibles": False,
            "divergencias_volumen_altura": False,
            "timestamps_inconsistentes": False
        }
    }

    if df_clean.empty:
        return indicadores

    # FUGA: Pérdida constante y predecible
    if "diff_volumen" in df_clean.columns:
        perdidas = df_clean["diff_volumen"] < 0
        if perdidas.sum() > 0:
            std_perdidas = df_clean.loc[perdidas, "diff_volumen"].std()
            mean_perdidas = df_clean.loc[perdidas, "diff_volumen"].mean()
            indicadores["fuga"]["perdida_constante"] = std_perdidas < abs(mean_perdidas) * 0.5  # Baja variabilidad

    # FUGA: Correlación con temperatura
    if "Temperatura" in df_clean.columns and "diff_volumen" in df_clean.columns:
        corr_temp = df_clean["Temperatura"].corr(df_clean["diff_volumen"])
        indicadores["fuga"]["correlacion_temperatura"] = abs(corr_temp) > 0.3

    # FUGA: Incremento en Altura de Agua
    if "Altura de Agua" in df_clean.columns:
        indicadores["fuga"]["incremento_agua"] = df_clean["Altura de Agua"].diff().fillna(0).mean() > 0

    # FUGA: Afecta 24/7 (no patrón horario)
    if "Fecha" in df_clean.columns:
        df_clean["hora"] = df_clean["Fecha"].dt.hour
        perdidas_por_hora = df_clean[df_clean["diff_volumen"] < 0].groupby("hora").size()
        if not perdidas_por_hora.empty:
            indicadores["fuga"]["afecta_24_7"] = perdidas_por_hora.std() < perdidas_por_hora.mean() * 0.5

    # ROBO: Caída abrupta
    if "diff_volumen" in df_clean.columns:
        q1 = df_clean["diff_volumen"].quantile(0.25)
        q3 = df_clean["diff_volumen"].quantile(0.75)
        iqr = q3 - q1
        outliers_bajo = df_clean["diff_volumen"] < q1 - 3 * iqr
        indicadores["robo"]["caida_abrupta"] = outliers_bajo.sum() > 0

    # ROBO: Patrón temporal (ej: noche)
    if "Fecha" in df_clean.columns and "diff_volumen" in df_clean.columns:
        df_clean["hora"] = df_clean["Fecha"].dt.hour
        caidas_noche = df_clean[(df_clean["diff_volumen"] < 0) & (df_clean["hora"].between(22, 6))].shape[0]
        caidas_total = (df_clean["diff_volumen"] < 0).sum()
        indicadores["robo"]["patron_temporal"] = caidas_noche > caidas_total * 0.7 if caidas_total > 0 else False

    # ROBO: Variación no explicada por temperatura
    if "Temperatura" in df_clean.columns and "diff_volumen" in df_clean.columns:
        evaporacion = _calcular_evaporacion_esperada(df_clean)
        variacion_no_explicada = (df_clean["diff_volumen"] - evaporacion).abs()
        indicadores["robo"]["variacion_no_temperatura"] = variacion_no_explicada.max() > df_clean["diff_volumen"].std() * 3

    # ROBO: Correlación con desconexiones
    if "Estado_Conexion" in df_clean.columns and "diff_volumen" in df_clean.columns:
        offline = ~df_clean["Estado_Conexion"].str.contains("ok|online|activo|conectado", case=False, na=False)
        corr_offline = offline.astype(int).corr(df_clean["diff_volumen"] < 0)
        indicadores["robo"]["correlacion_desconexion"] = abs(corr_offline) > 0.3

    # ERROR SISTEMA: Saltos imposibles
    if "diff_volumen" in df_clean.columns:
        max_fisico = df_clean["Volumen"].max() * 0.1  # 10% del volumen máximo
        indicadores["error_sistema"]["saltos_imposibles"] = (df_clean["diff_volumen"].abs() > max_fisico).any()

    # ERROR SISTEMA: Divergencias volumen-altura
    if "Volumen" in df_clean.columns and "Altura de Combustible" in df_clean.columns:
        # Asumiendo relación lineal simple; en realidad necesitarías geometría del tanque
        corr_vol_altura = df_clean["Volumen"].corr(df_clean["Altura de Combustible"])
        indicadores["error_sistema"]["divergencias_volumen_altura"] = abs(corr_vol_altura) < 0.8

    # ERROR SISTEMA: Timestamps inconsistentes
    indicadores["error_sistema"]["timestamps_inconsistentes"] = df_clean["Fecha_mayor_Actualizacion"].any()

    return indicadores


def generar_reporte_ejecutivo(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generar reporte ejecutivo para gerencia con métricas clave y eventos críticos.
    """
    df_clean = limpiar_telemetria(df)
    indicadores = analizar_indicadores_anomalias(df_clean)

    # Eventos críticos del último período
    eventos_criticos = []
    if "clasificacion_volumen" in df_clean.columns:
        for tank in df_clean["Tanque"].unique():
            tank_data = df_clean[df_clean["Tanque"] == tank]
            robos = tank_data[tank_data["clasificacion_volumen"] == "robo_potencial"]
            if not robos.empty:
                ultimo_robo = robos.iloc[-1]
                eventos_criticos.append({
                    "tipo": "Robo Potencial",
                    "tanque": tank,
                    "fecha": ultimo_robo["Fecha"],
                    "volumen_perdido": abs(ultimo_robo["diff_volumen"]),
                    "sitio": ultimo_robo.get("Sitio", "N/A")
                })

    # Resumen por tanque
    resumen_tanques = []
    for tank in df_clean["Tanque"].unique():
        tank_data = df_clean[df_clean["Tanque"] == tank]
        resumen_tanques.append({
            "tanque": tank,
            "registros": len(tank_data),
            "volumen_promedio": tank_data["Volumen"].mean(),
            "volumen_min": tank_data["Volumen"].min(),
            "volumen_max": tank_data["Volumen"].max(),
            "anomalias": (tank_data["clasificacion_volumen"] != "normal").sum(),
            "desconexiones": tank_data.get("Estado_Conexion", pd.Series()).str.contains("offline|desconectado", case=False, na=False).sum() if "Estado_Conexion" in tank_data.columns else 0
        })

    reporte = {
        "fecha_analisis": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "periodo_datos": {
            "inicio": df_clean["Fecha"].min().strftime("%Y-%m-%d %H:%M") if not df_clean.empty else None,
            "fin": df_clean["Fecha"].max().strftime("%Y-%m-%d %H:%M") if not df_clean.empty else None
        },
        "metricas_globales": {
            "tanques_analizados": df_clean["Tanque"].nunique() if "Tanque" in df_clean.columns else 0,
            "registros_totales": len(df_clean),
            "eventos_anomalos": (df_clean["clasificacion_volumen"] != "normal").sum() if "clasificacion_volumen" in df_clean.columns else 0,
            "desconexiones_totales": df_clean.get("Estado_Conexion", pd.Series()).str.contains("offline|desconectado", case=False, na=False).sum() if "Estado_Conexion" in df_clean.columns else 0,
            "capacidad_excedida": int(df_clean["capacidad_excedida"].sum()) if "capacidad_excedida" in df_clean.columns else 0
        },
        "indicadores_detectados": indicadores,
        "eventos_criticos": eventos_criticos,
        "resumen_por_tanque": resumen_tanques
    }

    # Guardar reporte ejecutivo
    pd.DataFrame([reporte]).to_json(OUTPUTS_PATH / "reporte_ejecutivo.json", orient="records", indent=2)
    pd.DataFrame(resumen_tanques).to_csv(OUTPUTS_PATH / "resumen_ejecutivo_tanques.csv", index=False)

    return reporte


def detectar_anomalias_volumen(df: pd.DataFrame, tanque_id: Any, umbral_std: Optional[float] = None) -> pd.DataFrame:
    """
    Detectar anomalías de volumen en un tanque específico.

    Retorna un DataFrame filtrado con clasificaciones de evento.
    """
    assert "Tanque" in df.columns, "El DataFrame debe contener la columna 'Tanque'"
    df_t = df[df["Tanque"] == str(tanque_id)].copy()
    if df_t.empty:
        return df_t

    df_t = limpiar_telemetria(df_t)

    # Cálculo de líneas base
    if umbral_std is None:
        umbral_std = config.umbral_std_anomalia
    df_t["evaporacion_esperada"] = _calcular_evaporacion_esperada(df_t)
    df_t["z_diff_volumen"] = (df_t["diff_volumen"] - df_t["diff_volumen"].mean()) / df_t["diff_volumen"].std(ddof=0)
    q1 = df_t["diff_volumen"].quantile(0.25)
    q3 = df_t["diff_volumen"].quantile(0.75)
    iqr = q3 - q1
    df_t["outlier_iqr"] = (df_t["diff_volumen"] < q1 - 1.5 * iqr) | (df_t["diff_volumen"] > q3 + 1.5 * iqr)

    # Clasificación preliminar
    conditions = []
    choices = []

    # Robo potencial: caída abrupta grande y fuera de lo esperado
    conditions.append(
        (df_t["diff_volumen"] <= -umbral_std * df_t["diff_volumen"].std(ddof=0))
        & (df_t["diff_volumen"] < df_t["evaporacion_esperada"] * -2)
    )
    choices.append("robo_potencial")

    # Fuga potencial: pérdida consistente y negativa, no necesariamente abrupta
    conditions.append(
        (df_t["diff_volumen"] < 0)
        & (df_t["diff_volumen"] <= df_t["evaporacion_esperada"] * -0.75)
        & (df_t["outlier_iqr"] == False)
    )
    choices.append("fuga_potencial")

    # Error de sensor: cambio positivo brusco o divergencia entre volume y TC
    conditions.append(
        (df_t["diff_volumen"] >= umbral_std * df_t["diff_volumen"].std(ddof=0))
        | ((df_t["Volumen TC"] - df_t["Volumen"]).abs() > df_t["Volumen"].abs() * 0.1)
    )
    choices.append("error_sensor")

    df_t["clasificacion_volumen"] = np.select(conditions, choices, default="normal")

    # Score de anomalía compuesto
    df_t["anomaly_score"] = (
        df_t["z_diff_volumen"].abs().fillna(0)
        + df_t["outlier_iqr"].astype(int) * 1.5
        + df_t["retrodatado_sospechoso"].astype(int) * 1.0
        + df_t["retraso_actualizacion_critico"].astype(int) * 1.0
    )
    df_t["anomaly_score"] = df_t["anomaly_score"].clip(lower=0)

    return df_t


def validar_timestamps(df: pd.DataFrame, umbral_retraso_horas: Optional[float] = None) -> pd.DataFrame:
    """
    Validar coherencia temporal de la telemetría.

    - Verifica que Fecha <= Fecha Actualizacion
    - Marca retrasos críticos
    - Identifica registros retrodatados
    """
    df = limpiar_telemetria(df)

    df["timestamp_invalido"] = df["Fecha"] > df["Fecha Actualizacion"]
    df["retraso_s"] = (df["Fecha Actualizacion"] - df["Fecha"]).dt.total_seconds()
    df["retraso_s"] = df["retraso_s"].where(df["retraso_s"] >= 0, np.nan)
    df["retraso_horas"] = df["retraso_s"] / 3600.0
    if umbral_retraso_horas is None:
        umbral_retraso_horas = config.retraso_critico_horas
    df["retraso_critico"] = df["retraso_horas"] > umbral_retraso_horas

    # Retrodatado sospechoso: salto hacia atrás en el orden temporal por tanque
    if "Tanque" in df.columns:
        df["retraso_entre_registros_s"] = df.groupby("Tanque")["Fecha"].diff().dt.total_seconds()
        df["retrodatado_sospechoso"] = df["retraso_entre_registros_s"] < -1
    else:
        df["retrodatado_sospechoso"] = False

    return df


def generar_reporte_anomalias(df: pd.DataFrame, tanque_id: Optional[Any] = None) -> tuple[Dict[str, Any], pd.DataFrame]:
    """
    Generar un reporte de anomalías y métricas de calidad de datos.

    - Períodos de desconexión
    - Eventos de pérdida anómala
    - Métricas de calidad de datos
    - Visualizaciones en archivos PNG
    """
    df_clean = limpiar_telemetria(df)

    if tanque_id is not None:
        df_clean = df_clean[df_clean["Tanque"] == str(tanque_id)].copy()
    
    report: Dict[str, Any] = {}

    # Calidad de datos básica
    report["registros_totales"] = len(df_clean)
    report["timestamp_invalidos"] = int(df_clean["Fecha_mayor_Actualizacion"].sum()) if "Fecha_mayor_Actualizacion" in df_clean.columns else 0
    report["retrasos_criticos"] = int(df_clean["retraso_actualizacion_critico"].sum()) if "retraso_actualizacion_critico" in df_clean.columns else 0
    report["gap_grandes"] = int(df_clean["gap_grande"].sum()) if "gap_grande" in df_clean.columns else 0

    # Estado de conexión
    if "Estado_Conexion" in df_clean.columns:
        report["conexiones_offline"] = int(df_clean[~df_clean["Estado_Conexion"].str.contains("ok|online|activo|conectado", case=False, na=False)].shape[0])
    else:
        report["conexiones_offline"] = None

    report["capacidad_excedida"] = int(df_clean["capacidad_excedida"].sum()) if "capacidad_excedida" in df_clean.columns else 0

    # Eventos de anomalía de volumen
    if "Tanque" in df_clean.columns and "Volumen" in df_clean.columns:
        tanks = [str(tanque_id)] if tanque_id is not None else df_clean["Tanque"].unique().tolist()
        events = []
        classified_dfs = []
        for tank in tanks:
            tank_df = detectar_anomalias_volumen(df_clean, tank)
            if tank_df.empty:
                continue
            classified_dfs.append(tank_df)
            event_cols = ["Tanque", "Fecha", "diff_volumen", "clasificacion_volumen", "anomaly_score", "retraso_actualizacion_critico"]
            if "Estado_Conexion" in tank_df.columns:
                event_cols.insert(-1, "Estado_Conexion")
            events.append(tank_df[event_cols])
        events_df = pd.concat(events, ignore_index=True) if events else pd.DataFrame()
        report["eventos_anomalias"] = events_df.shape[0]
        events_df.to_csv(OUTPUTS_PATH / f"eventos_anomalias_{tanque_id or 'todos'}.csv", index=False)
        # Actualizar df_clean con clasificaciones para visualizaciones
        if classified_dfs:
            df_clean = pd.concat(classified_dfs, ignore_index=True).sort_values(["Tanque", "Fecha"]).reset_index(drop=True)
    # Resumen de desconexiones por sitio/tanque
    if "Fecha" in df_clean.columns and "Estado_Conexion" in df_clean.columns:
        desconexiones = (
            df_clean[~df_clean["Estado_Conexion"].str.contains("ok|online|activo|conectado", case=False, na=False)]
            .groupby(["Sitio", "Tanque"])['Fecha'].count()
            .reset_index(name='desconexiones')
        )
        desconexiones.to_csv(OUTPUTS_PATH / f"desconexiones_{tanque_id or 'todos'}.csv", index=False)
    else:
        desconexiones = pd.DataFrame()

    # Guardar calidad de datos
    pd.DataFrame([report]).to_csv(OUTPUTS_PATH / f"reporte_calidad_datos_{tanque_id or 'todos'}.csv", index=False)

    # Visualizaciones
    if not df_clean.empty and "Fecha" in df_clean.columns and "Volumen" in df_clean.columns:
        # Gráfico global de series de volumen (todos los tanques)
        plt.figure(figsize=(14, 8))
        sns.lineplot(data=df_clean, x="Fecha", y="Volumen", hue="Tanque", marker="o", alpha=0.7)
        plt.title("Serie de volumen - Todos los tanques")
        plt.xlabel("Fecha")
        plt.ylabel("Volumen")
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        plt.savefig(OUTPUTS_PATH / f"volumen_series_todos.png", dpi=150)
        plt.close()

        # Gráficos individuales por tanque
        if "Tanque" in df_clean.columns:
            tanks = df_clean["Tanque"].unique()
            for tank in tanks:
                tank_data = df_clean[df_clean["Tanque"] == tank].copy()
                if not tank_data.empty:
                    plt.figure(figsize=(12, 6))
                    sns.lineplot(data=tank_data, x="Fecha", y="Volumen", marker="o", color="blue")
                    plt.title(f"Serie de volumen - Tanque {tank}")
                    plt.xlabel("Fecha")
                    plt.ylabel("Volumen")
                    plt.grid(True, alpha=0.3)
                    plt.tight_layout()
                    plt.savefig(OUTPUTS_PATH / f"volumen_series_tanque_{tank}.png", dpi=150)
                    plt.close()

        if "diff_volumen" in df_clean.columns:
            plt.figure(figsize=(12, 5))
            sns.scatterplot(data=df_clean, x="Fecha", y="diff_volumen", hue="clasificacion_volumen" if "clasificacion_volumen" in df_clean.columns else None)
            plt.axhline(0, color='gray', linestyle='--')
            plt.title("Diferencia de volumen entre registros")
            plt.xlabel("Fecha")
            plt.ylabel("Cambio de volumen")
            plt.tight_layout()
            plt.savefig(OUTPUTS_PATH / f"diff_volumen_todos.png")
            plt.close()

    return {
        "reporte": report,
        "eventos_anomalias": events_df,
        "desconexiones": desconexiones,
        "ruta_salida": str(OUTPUTS_PATH)
    }, df_clean


def _read_spreadsheetml_xml(path: str) -> pd.DataFrame:
    """Leer archivos SpreadsheetML XML generados por Excel/Ationet."""
    ns = {
        "ss": "urn:schemas-microsoft-com:office:spreadsheet"
    }
    tree = ET.parse(path)
    root = tree.getroot()
    rows = root.findall('.//ss:Worksheet/ss:Table/ss:Row', ns)

    data = []
    for row in rows:
        cells = row.findall('ss:Cell', ns)
        line = []
        current_index = 1
        for cell in cells:
            index_attr = cell.attrib.get('{urn:schemas-microsoft-com:office:spreadsheet}Index')
            if index_attr is not None:
                target_index = int(index_attr)
                while current_index < target_index:
                    line.append(None)
                    current_index += 1
            data_elem = cell.find('ss:Data', ns)
            line.append(data_elem.text if data_elem is not None else None)
            current_index += 1
        data.append(line)

    if not data:
        return pd.DataFrame()
    header = [str(x).strip() if x is not None else f"col_{i}" for i, x in enumerate(data[0], start=1)]
    df = pd.DataFrame(data[1:], columns=header)

    mapping = {
        "Fecha Actualización": "Fecha Actualizacion",
        "Combustible": "Categoria",
        "Volumen de Agua": "Altura de Agua",
        "Volumen TC": "Volumen TC",
        "Altura de Combustible": "Altura de Combustible",
        "Altura de Agua": "Altura de Agua",
        "Variación Volumen": "Variacion Volumen",
        "Variación Volumen TC": "Variacion Volumen TC",
        "Fecha Host": "Fecha Host",
        "Fecha": "Fecha",
        "Tiempo Transcurrido": "Tiempo_Transcurrido",
        "Horas Sin Actualizar": "Horas_Sin_Actualizar",
        "Estado Conexion": "Estado_Conexion",
        "Estado_Conexion": "Estado_Conexion",
    }
    df = df.rename(columns=mapping)
    return df


def cargar_datos_excel(ruta: Optional[str] = None) -> pd.DataFrame:
    """Carga todos los archivos .xls de telemetría desde la carpeta data/."""
    rutas = [pathlib.Path(ruta)] if ruta else config.list_input_files()
    if not rutas:
        raise FileNotFoundError(f"No se encontraron archivos '{config.input_pattern}' en {config.data_path}")

    frames = []
    for path in rutas:
        try:
            df = pd.read_excel(path, engine="openpyxl")
        except Exception:
            df = _read_spreadsheetml_xml(path)
        if not df.empty:
            frames.append(df)

    if not frames:
        return pd.DataFrame()

    return pd.concat(frames, ignore_index=True)


def main() -> None:
    df = cargar_datos_excel()
    df_clean = limpiar_telemetria(df)
    validacion = validar_timestamps(df_clean)
    reporte, df_clean = generar_reporte_anomalias(df_clean)  # Esto agrega clasificaciones a df_clean
    indicadores = analizar_indicadores_anomalias(df_clean)
    ejecutivo = generar_reporte_ejecutivo(df_clean)

    print("Resumen de calidad de datos:")
    print(reporte["reporte"])
    print("\nIndicadores de anomalías identificados:")
    for categoria, signals in indicadores.items():
        print(f"\n{categoria.upper()}:")
        for signal, detected in signals.items():
            status = "✓" if detected else "✗"
            print(f"  {status} {signal.replace('_', ' ').title()}")

    print(f"\nArchivos generados en: {reporte['ruta_salida']}")
    print("Reportes ejecutivos: reporte_ejecutivo.json, resumen_ejecutivo_tanques.csv")
    print("Documentación: docs/Analisis_Telemetria_Combustibles.md")

    df_clean.to_csv(OUTPUTS_PATH / "telemetria_limpa.csv", index=False)
    validacion.to_csv(OUTPUTS_PATH / "validacion_timestamps.csv", index=False)
    pd.DataFrame([indicadores]).to_csv(OUTPUTS_PATH / "indicadores_anomalias.csv", index=False)


if __name__ == "__main__":
    main()
