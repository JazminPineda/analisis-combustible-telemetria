# analisis_reporte_telemetria/readers/form_reader.py

import pandas as pd
from pathlib import Path
from typing import Optional
from analisis_reporte_telemetria.config import FORM_DATA_PATH, FORM_FILE_NAME

class FormReader:
    """
    Responsable de leer el formulario de ingresos de combustible y trasvases.
    Extrae los datos de descarga por tanque, dividiendo las filas que contienen múltiples cargas.
    """

    def __init__(self, ruta_archivo: Optional[Path] = None):
        if ruta_archivo:
            self.ruta_archivo = ruta_archivo
        else:
            self.ruta_archivo = FORM_DATA_PATH / FORM_FILE_NAME

    def cargar_datos(self) -> pd.DataFrame:
        """
        Lee el archivo Excel y procesa las columnas para separar las cargas por tanque.
        Usa índices para evitar problemas con carácteres especiales en los nombres de las columnas.
        """
        if not self.ruta_archivo.exists():
            raise FileNotFoundError(f"No se encontró el archivo de formulario en: {self.ruta_archivo}")

        df = pd.read_excel(self.ruta_archivo)
        
        # Mapeo de índices de columnas base
        # 0: ID, 1: Hora de inicio, 2: Hora de finalización, 3: Correo electrónico, 
        # 4: Nombre, 6: Seleccione su legajo, 7: Tarea a realizar, 
        # 8: Seleccionar la empresa Proveedora, 9: Indicar el número de remito
        idx_base = [0, 1, 2, 3, 4, 6, 7, 8, 9]
        nombres_base = [
            'ID', 'Hora de inicio', 'Hora de finalización', 'Correo electrónico', 
            'Nombre', 'Legajo', 'Tarea', 'Proveedor', 'Remito'
        ]
        
        tanques_data = []
        
        # Índices para cada grupo de tanque (Tanque, Antes, Cargado, Despues)
        # Basado en la inspección visual/terminal:
        # T1: 10, 11, 12, 13
        # T2: 15, 16, 17, 18
        # T3: 20, 21, 22, 23
        # T4: 25, 26, 27, 28
        indices_tanques = [
            [10, 11, 12, 13], 
            [15, 16, 17, 18], 
            [20, 21, 22, 23], 
            [25, 26, 27, 28]
        ]
        
        for _, row in df.iterrows():
            # For each tank slot (1 to 4)
            for i in range(4):
                curr_idx_set = indices_tanques[i]
                
                # Verificar si el índice existe en el dataframe (por seguridad)
                if curr_idx_set[0] >= len(row):
                    continue
                    
                tanque_val = row.iloc[curr_idx_set[0]]
                
                if pd.notna(tanque_val) and str(tanque_val).strip() != "":
                    # Construir registro base
                    new_reg = {nombres_base[j]: row.iloc[idx_base[j]] for j in range(len(idx_base))}
                    
                    # Agregar datos específicos del tanque
                    new_reg['Tanque_Original'] = tanque_val
                    new_reg['Litros Antes'] = row.iloc[curr_idx_set[1]] if curr_idx_set[1] < len(row) else 0
                    new_reg['Litros Cargados'] = row.iloc[curr_idx_set[2]] if curr_idx_set[2] < len(row) else 0
                    new_reg['Litros Despues'] = row.iloc[curr_idx_set[3]] if curr_idx_set[3] < len(row) else 0
                    
                    tanques_data.append(new_reg)
                    
        if not tanques_data:
            return pd.DataFrame()

        df_exploded = pd.DataFrame(tanques_data)
        
        # Estandarizar Tanque_id (extraer el número)
        df_exploded['Tanque_id'] = df_exploded['Tanque_Original'].astype(str).str.extract('(\d+)').astype(float).fillna(0).astype(int)
        
        # Convertir Hora de inicio a datetime
        df_exploded['Hora de inicio'] = pd.to_datetime(df_exploded['Hora de inicio'], errors='coerce')
        df_exploded['Fecha'] = df_exploded['Hora de inicio'].dt.normalize()

        return df_exploded
        return df_exploded
