
# analisis_reporte_telemetria/processors/fuel_processor.py
import pandas as pd
import numpy as np
from analisis_reporte_telemetria.readers.gestion_bus_reader import GestionBusReader
from analisis_reporte_telemetria.cleaners.data_cleaner import DataCleaner
from analisis_reporte_telemetria.utils.helpers import join_unique


"""
Orquesta el uso del reader y del cleaner, y aplica las transformaciones de alto nivel
(filtros, agrupaciones, clasificaciones).
"""
class FuelProcessor:
    """
    Orquesta la lógica de negocio para el procesamiento de combustible.
    Depende de abstracciones (Reader, Cleaner) no de implementaciones concretas (DIP).
    """
    def __init__(self, reader: GestionBusReader, cleaner: DataCleaner):
        self.reader = reader
        self.cleaner = cleaner

    def obtener_datos_procesados(self) -> pd.DataFrame:
        """Flujo principal para obtener y limpiar los datos de Gestión Bus."""
        df_raw = self.reader.cargar_datos()
        #df_clean = self.cleaner.convertir_fechas_y_crear_llaves(df_raw)
        # Aplicar otras limpiezas si es necesario
        # df_clean = self.cleaner.limpiar_columna_numerica(df_raw, 'NroPedido')
        df_clean = df_raw.copy() # Por ahora, sin limpiezas adicionales para no afectar el flujo principal
            # 1. Conversión de fecha vectorizada (toda la columna a la vez)
        df_clean['Date'] = pd.to_datetime(df_clean['Fecha'], dayfirst=True, errors='coerce').dt.normalize()
        # 2. Año-Mes vectorizado
        df_clean['Año_mes'] = df_clean['Date'].dt.to_period('M').astype(str)
        df_clean['SemanaRemito'] = df_clean['Date'].dt.isocalendar().week
        df_clean['unico_mes'] = df_clean['Almacen'].astype(str) + '_' + df_clean['Año_mes']
        df_clean['unico_mes_Almacen'] = df_clean['Almacen'].astype(str) + '_' + df_clean['Año_mes']

        return df_clean

    def filtrar_por_almacen(self, df: pd.DataFrame, almacen: str) -> pd.DataFrame:
        """Filtra el DataFrame por el almacén especificado y retorna una copia."""
        return df[df['Almacen'] == almacen].copy()

    def agrupar_movimientos(self, df_filtrado: pd.DataFrame) -> pd.DataFrame:
        """Agrupa los movimientos específicos (Trasvases, Correcciones)."""
        tipos_movimientos = ['Trasvase Combustible (Egreso)',
                             'Trasvase Combustible (Ingreso)',
                             'Corrección Negativa',
                             'Corrección Positiva']
        df_mov = df_filtrado[df_filtrado['Tipo'].isin(tipos_movimientos)]

        return df_mov.groupby(
            ['Año_mes', 'unico_mes', 'unico_mes_Almacen', 'Almacen', 'Tipo', 'Tanque']
        ).agg(
            Litros_Entregados_Sum=('Litros', 'sum'),
            Cantidad_veces=('Litros', 'count'),
            Observacion=('Observación', join_unique),
            Usuario=('Usuario', join_unique),
            Fecha_Hora=('Fecha Hora', join_unique)
        ).reset_index()

    def agrupar_recargas(self, df_filtrado: pd.DataFrame) -> pd.DataFrame:
        """Prepara y agrupa los datos de recargas."""
        df_recargas = df_filtrado[df_filtrado['Tipo'] == "Carga de Combustible"].copy()
        df_recargas = self.cleaner.extraer_tanque_a_entero(df_recargas)
        df_recargas = self.cleaner.convertir_fechas_y_crear_llaves(df_recargas, 'Fecha', 'Tanque', 'Fecha')
        df_recargas['Date_fx'] = pd.to_datetime(df_recargas['Fecha'], format='%d/%m/%Y', errors='coerce').dt.date
        
        df_agrupado = df_recargas.groupby(
            ['Año_mes', 'unico_mes', 'Tipo', 'Date_fx', 'Almacen', 'Tanque']
        ).agg(
            Litros_GB_Recargas=('Litros', 'sum'),
            Cantidad_veces=('Litros', 'count'),
            Surtidor=('Surtidor', join_unique),
        ).reset_index()
        
        # Creación de llave única para conciliación
        df_agrupado['unico_almacen'] = (df_agrupado['Almacen'] + '_' + 
                                         df_agrupado['Tanque'].astype(str) + '_' + 
                                         df_agrupado['Date_fx'].astype(str) + '_' + 
                                         df_agrupado['Litros_GB_Recargas'].astype(str))
        return df_agrupado

    def agrupar_entregas(self, df_filtrado: pd.DataFrame) -> pd.DataFrame:
        """Agrupa los datos de entregas de combustible."""
        df_entregas = df_filtrado[df_filtrado['Tipo'] == "Entrega de Combustible"].copy()
        df_entregas = self.cleaner.convertir_fechas_y_crear_llaves(df_entregas, 'Fecha', 'Almacen', 'Fecha Remito')
        
        df_agrupado = df_entregas.groupby(
            ['Año_mes', 'unico_mes', 'unico_mes_Almacen',
             'Sociedad', 'Tipo', 'Nro Pedido', 'Almacen', 'Date_fx']
        ).agg(
            Litros_GB=('Litros', 'sum'),
            Cantidad_veces=('Litros', 'count'),
            Remito=('Nro Remito', join_unique), # revisar si es correcto usar 'Nro. Remito' o 'NroRemito' según el header final
            L_Entregados=('Litros Entregado', 'max'),
            L_Solicitados=('LitrosSolicitado', 'max'),
            Nro_Presinto=('Nro Precinto', join_unique), # revisar si es correcto usar 'Nro. Precinto' o 'NroPrecinto' según el header final
            Usuario=('Usuario', join_unique),
        ).reset_index()
        
        df_agrupado['unico_almacen'] = (df_agrupado['Almacen'] + '_' + 
                                         df_agrupado['Date_fx'].astype(str) + '_' + 
                                         df_agrupado['Litros_GB'].astype(str))
        
        df_agrupado['Date_fx'] = pd.to_datetime(df_agrupado['Date_fx'], dayfirst=True, errors='coerce').dt.normalize()
        df_agrupado["Dif GB vs Entreg"] = df_agrupado['Litros_GB'] - df_agrupado['L_Entregados']
        
        return df_agrupado

    @staticmethod
    def clasificar_conciliacion(row: pd.Series) -> str:
        """Clasifica el resultado de una conciliación."""
        diferencia = row.get('Suma_Compensatoria', 0)
        if pd.isna(diferencia):
            return 'Sin datos suficientes'
            
        abs_diff = abs(diferencia)
        if abs_diff <= 50: return 'OK - Conciliado'
        if abs_diff <= 100: return 'Compensado (Desfase de tiempo)'
        
        # Clasificación granular para sobrantes
        if diferencia > 100:
            return 'Sobrante entre 101 y 1000L' if diferencia < 1000 else 'Sobrante (Carga no registrada) >= 1000L'
        # Clasificación granular para faltantes
        if diferencia < -100:
            return 'Faltante (Posible merma o robo) entre -101 y -1000L' if diferencia > -1000 else 'Faltante (Crítico - Posible robo) <= -1000L'
        
        return 'Revisar manualmente'