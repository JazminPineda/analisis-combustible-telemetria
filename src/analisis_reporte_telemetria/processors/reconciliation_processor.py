# analisis_reporte_telemetria/processors/reconciliation_processor.py

import pandas as pd
from pathlib import Path
from typing import Optional
from analisis_reporte_telemetria.config import CONCILIACION_OUTPUT_PATH

class ReconciliationProcessor:
    """
    Se encarga de conciliar los datos del Formulario de Ingresos con los datos de Gestión Bus.
    La conciliación se basa en Fecha, Hora de Inicio y Tanque.
    """

    def __init__(self, output_path: Optional[Path] = None):
        self.output_path = output_path or CONCILIACION_OUTPUT_PATH
        self.output_path.mkdir(parents=True, exist_ok=True)

    def conciliar(self, df_formulario: pd.DataFrame, df_gestion_bus: pd.DataFrame) -> pd.DataFrame:
        """
        Realiza el cruce de datos entre el formulario y gestion bus.
        """
        # Preparación de datos de Gestión Bus
        gb = df_gestion_bus.copy()
        
        # Asegurarse de que Tanque sea comparable
        if 'Tanque' in gb.columns:
            gb['Tanque_id'] = gb['Tanque'].astype(str).str.extract('(\d+)').astype(float).fillna(0).astype(int)
        
        # Procesar fechas en GB
        gb['GB_DateTime'] = pd.to_datetime(gb['Fecha Hora'], errors='coerce')
        gb['GB_Date'] = gb['GB_DateTime'].dt.normalize()
        gb['Hora_H'] = gb['GB_DateTime'].dt.hour
        
        # Preparación de datos de Formulario
        form = df_formulario.copy()
        form['Form_DateTime'] = pd.to_datetime(form['Hora de inicio'], errors='coerce')
        form['Form_Date'] = form['Form_DateTime'].dt.normalize()
        form['Hora_H'] = form['Form_DateTime'].dt.hour

        # Cruce (Merge)
        # Conciliar por Fecha, Tanque y Hora (H)
        conciliacion = pd.merge(
            form,
            gb,
            left_on=['Form_Date', 'Tanque_id', 'Hora_H'],
            right_on=['GB_Date', 'Tanque_id', 'Hora_H'],
            how='outer',
            suffixes=('_Form', '_GB')
        )
        
        # Calcular Variación
        # Litros Cargados (Form) vs Litros (Gestion Bus)
        conciliacion['Diferencia_Litros'] = conciliacion['Litros Cargados'].fillna(0) - conciliacion['Litros'].fillna(0)
        
        return conciliacion

    def guardar_reporte(self, df_conciliado: pd.DataFrame, filename: str = "variacion_diaria.xlsx"):
        """
        Guarda el resultado en un archivo Excel.
        """
        ruta_final = self.output_path / filename
        df_conciliado.to_excel(ruta_final, index=False)
        print(f"Reporte de conciliación guardado en: {ruta_final}")
        return ruta_final
