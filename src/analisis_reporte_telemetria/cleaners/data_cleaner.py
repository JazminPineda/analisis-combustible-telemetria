# analisis_reporte_telemetria/cleaners/data_cleaner.py
import pandas as pd
import numpy as np
from analisis_reporte_telemetria.utils.helpers import clean_and_extract_numbers, extract_last_char_to_int

"""
Aquí encapsulamos toda la lógica de limpieza y preprocesamiento. Esta clase no lee archivos ni aplica 
la lógica de negocio del combustible
"""

class DataCleaner:
    """
    Encapsula las operaciones de limpieza y transformación de datos comunes.
    """

    @staticmethod
    def limpiar_columna_numerica(df: pd.DataFrame, columna: str) -> pd.DataFrame:
        """
        Aplica la limpieza de números a una columna específica del DataFrame.
        No modifica el original, devuelve una copia.
        """
        df = df.copy()
        if columna in df.columns:
            df[columna] = clean_and_extract_numbers(df[columna])
        return df

    @staticmethod
    def convertir_fechas_y_crear_llaves(df: pd.DataFrame,
                                      col_fecha: str = 'Fecha',
                                      col_almacen: str = 'Almacen',
                                      col_fecha_remito: str = 'Fecha Remito') -> pd.DataFrame:
        """
        Convierte columnas de fecha a datetime y genera llaves únicas temporales.
        Retorna un NUEVO DataFrame con las columnas añadidas.
        """
        df = df.copy()

        # Conversión de fechas vectorizada
        df['Date'] = pd.to_datetime(df[col_fecha], dayfirst=True, errors='coerce').dt.normalize()
        df['Date_fx'] = pd.to_datetime(df[col_fecha_remito], dayfirst=True, errors='coerce').dt.normalize()

        # Creación de períodos
        df['Año_mes'] = df['Date_fx'].dt.to_period('M').astype(str)
        df['unico_mes'] = df[col_almacen].astype(str) + '_' + df['Año_mes']
        df['unico_mes_Almacen'] = df['unico_mes'] # Redundante, unifiquemos.
        return df

    @staticmethod
    def extraer_tanque_a_entero(df: pd.DataFrame, col_tanque: str = 'Tanque') -> pd.DataFrame:
        """Convierte la columna de Tanque extrayendo el último carácter a entero."""
        df = df.copy()
        df[col_tanque] = extract_last_char_to_int(df[col_tanque])
        return df