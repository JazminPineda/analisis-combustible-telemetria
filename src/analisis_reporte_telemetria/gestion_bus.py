import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import re

# ruta_datos = Path("C:\Users\jpineda\Desktop\Tableros Grupo\1_OPERACIONES\Github\analisis-combustible-telemetria\data\gestion-bus")

HEADERS_FINAL2 =  ['Nro. Mov', 'Fecha', 'Codigo', 'Tipo', 'Ingreso', 'Sociedad', 'Almacen',
    'Tanque', 'Surtidor', 'Unidad', 'Kms_Carga', 'Kms_Odometro',
    'Kms_Recorrido', 'Litros', 'PrecioLitro', 'NroSolicitud',
    'FechaSolicitud', 'NroPedido', 'EstadoSolicitud',
    'LitrosSolicitado', 'Litros Entregado', 'Nro. Remito', 'Fecha Remito',
    'Importe Remito', 'EuroDiesel', 'Nro. Precinto',
    'Nro. Precinto Anterior', 'Tiene Precinto Anterior',
    'Observacion Precinto Anterior', 'Nro. Factura', 'Fecha Factura',
    'Importe Factura', 'Localidad Carga', 'Proveedor Carga',
    'Sociedad Pagadora', 'Nro. Cierre', 'Observación', 'Usuario',
    'Fecha Hora','archivo']


def read_xls_file2(file_path: Path) -> pd.DataFrame | None:
    
    HEADERS_FIJOS2 =  ['Nro. Mov', 'Fecha', 'Codigo', 'Tipo', 'Ingreso', 'Sociedad', 'Almacen',
       'Tanque', 'Surtidor', 'Unidad', 'Kms. Carga', 'Kms. Odometro',
       'Kms. Recorrido', 'Litros', 'Precio Litro', 'Nro. Solicitud',
       'Fecha Solicitud', 'Nro. Pedido', 'Estado Solicitud',
       'Litros Solicitado', 'Litros Entregado', 'Nro. Remito', 'Fecha Remito',
       'Importe Remito', 'EuroDiesel', 'Nro. Precinto',
       'Nro. Precinto Anterior', 'Tiene Precinto Anterior',
       'Observacion Precinto Anterior', 'Nro. Factura', 'Fecha Factura',
       'Importe Factura', 'Localidad Carga', 'Proveedor Carga',
       'Sociedad Pagadora', 'Nro. Cierre', 'Observación', 'Usuario',
       'Fecha Hora']

   
    try:
        # Detectamos las columnas del archivo
        temp_df = pd.read_excel(file_path, skiprows=0, nrows=0)
        cols_detectadas = HEADERS_FIJOS2

        # Leemos el archivo completo con esas columnas corregidas
        df = pd.read_excel(file_path)

        # Reindexamos para que coincida con el orden estándar
        df = df.reindex(columns=HEADERS_FIJOS2, fill_value=0)

        # Agregamos metadatos
        df['file'] = file_path.stem
        return df
    except Exception as e:
        print(f"Error al leer el archivo {file_path}: {e}")
        return None