import pandas as pd
from pathlib import Path


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
    
def cargar_datos_gestion_bus(ruta_datos: Path) -> pd.DataFrame:
    dfs_carga2 = [df2 for f2 in ruta_datos.glob('*.xlsx') if (df2 := read_xls_file2(f2)) is not None]
    df_combustible_movimientos = pd.concat(dfs_carga2, ignore_index=True)
    df_combustible_movimientos.columns = HEADERS_FINAL2
    print(f"Cantidad de Registros: {len(df_combustible_movimientos)}")
    return df_combustible_movimientos


def limpieza_numerica(df, pedido='NroPedido'):
    # Creamos una copia para no afectar el dataframe original
    df = df.copy()
    
    # Definimos la lista de nulos comunes
    common_nulls = ["-", " ", "N/A", "nd", "n/d", "None", "", "nan", "NaN", "unnamed"]
    
    if pedido in df.columns:
        # 1. Convertir a string y limpiar espacios básicos
        df[pedido] = df[pedido].astype(str).str.strip()
        
        # 2. Reemplazar nulos conocidos por NaN real
        df[pedido] = df[pedido].replace(common_nulls, np.nan)
        
        # 3. EXTRAER SOLO NÚMEROS (Regex: [^0-9] significa "todo lo que NO sea un número")
        # Reemplazamos cualquier carácter no numérico por un string vacío
        df[pedido] = df[pedido].str.replace(r'[^0-9]', '', regex=True)
        
        # 4. Manejo de vacíos: Si después de limpiar quedó vacío o era NaN, poner "0"
        # Primero reemplazamos los strings vacíos que dejó la limpieza de letras
        df[pedido] = df[pedido].replace('', np.nan)
        
        # Finalmente, llenamos todos los NaN con "0"
        df[pedido] = df[pedido].fillna("0")
    
    return df


def procesar_fechas_y_llaves(df, col_fecha='Fecha', col_Almacen='Almacen',  remito= 'Fecha Remito'):
    """
    Procesa para generar las fechas y llaves únicas.
    """
    df = df.copy()

    # 1. Conversión de fecha vectorizada (toda la columna a la vez)
    df['Date'] = pd.to_datetime(df[col_fecha], dayfirst=True, errors='coerce').dt.normalize()
    df['Date_fx'] = pd.to_datetime(df[remito], dayfirst=True, errors='coerce').dt.normalize()
    # 2. Año-Mes vectorizado
    df['Año_mes'] = df['Date_fx'].dt.to_period('M').astype(str)
    df['SemanaRemito'] = df['Date_fx'].dt.isocalendar().week
   
    # 3. Creación de llaves vectorizada (Concatenación de Series)
    # Pandas optimiza la unión de strings cuando se hace así:
    df['unico_semana_almacen'] = df[col_Almacen].astype(str) + '-' + df['SemanaRemito'].astype(str)
  
    df['unico_mes'] = df[col_Almacen].astype(str) + '_' + df['Año_mes']
    df['unico_mes_Almacen'] = df[col_Almacen].astype(str) + '_' + df['Año_mes']

    return df

# Función para limpiar y unir valores únicos
def join_unique(x):
    valores = set(str(v) for v in x if pd.notna(v) and str(v).lower() != 'nan')
    return ', '.join(sorted(valores))