# analisis_reporte_telemetria/readers/gestion_bus_reader.py

"""
Una clase dedicada exclusivamente a la lectura y el parseo inicial de los archivos de Gestión Bus. 
Abierta a extensión (para otros formatos) pero cerrada a modificación (OCP) Open Closed Principle.
"""

import pandas as pd
from pathlib import Path
from typing import Optional
from analisis_reporte_telemetria.config import HEADERS_FIJOS2, HEADERS_FINAL2, GESTION_BUS_PATH

class GestionBusReader:
    """
    Responsable de leer archivos de Gestión Bus (.xlsx) y concatenarlos
    en un único DataFrame.
    """

    def __init__(self, ruta_datos: Optional[Path] = None):
        """
        Inicializa el lector con una ruta de datos.
        Args:
            ruta_datos: Path a la carpeta con archivos .xlsx. Si es None, usa la ruta por defecto.
        """
        self.ruta_datos = ruta_datos or GESTION_BUS_PATH

    def _read_single_file(self, file_path: Path) -> pd.DataFrame | None:
        """
        Lee un único archivo Excel y lo alinea a los headers fijos.
        SRP: Esta clase solo se encarga de la lectura, no de la limpieza avanzada.
        """
        try:
            df = pd.read_excel(file_path)
            # Reindexar asegura que todos los DataFrames tengan las mismas columnas en el mismo orden.
            df = df.reindex(columns=HEADERS_FIJOS2, fill_value=0)
            df['archivo'] = file_path.stem
            return df
        except Exception as e:
            print(f"Error al leer el archivo {file_path}: {e}")
            return None

    def cargar_datos(self) -> pd.DataFrame:
        """
        Carga todos los archivos .xlsx de la ruta especificada,
        los concatena y estandariza los nombres de las columnas.
        """
        archivos_excel = list(self.ruta_datos.glob('*.xlsx'))
        if not archivos_excel:
            raise FileNotFoundError(f"No se encontraron archivos .xlsx en la ruta: {self.ruta_datos}")

        dataframes = [df for f in archivos_excel if (df := self._read_single_file(f)) is not None]
        
        if not dataframes:
            raise ValueError("No se pudo leer ningún archivo .xlsx correctamente.")
            
        df_final = pd.concat(dataframes, ignore_index=True)
        df_final.columns = HEADERS_FINAL2
        print(f"Cantidad de Registros cargados: {len(df_final)}")
        return df_final