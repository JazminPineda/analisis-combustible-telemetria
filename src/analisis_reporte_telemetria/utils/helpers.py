# analisis_reporte_telemetria/utils/helpers.py

"""
Funciones de utilidad pura, altamente reutilizables y sin estado
"""
import pandas as pd
from analisis_reporte_telemetria.config import COMMON_NULL_VALUES

def join_unique(series: pd.Series) -> str:
    """
    Une valores únicos de una serie en un string, excluyendo nulos.
    Ideal para agregaciones.
    """
    valores = set(str(v) for v in series if pd.notna(v) and str(v).lower() != 'nan')
    return ', '.join(sorted(valores))

def clean_and_extract_numbers(series: pd.Series) -> pd.Series:
    """
    Limpia una serie de texto para extraer solo dígitos.
    Maneja nulos comunes y convierte a string numérico.
    """
    series = series.astype(str).str.strip()
    series = series.replace(COMMON_NULL_VALUES, pd.NA)
    # Extrae solo dígitos. Si no hay, resultará en string vacío.
    series = series.str.replace(r'[^0-9]', '', regex=True)
    # Reemplaza strings vacíos con '0' y llena NAs con '0'
    series = series.replace('', '0').fillna('0')
    return series

def extract_last_char_to_int(series: pd.Series) -> pd.Series:
    """Extrae el último carácter de una columna string y lo convierte a entero."""
    return series.astype(str).str[-1:].astype('int64')