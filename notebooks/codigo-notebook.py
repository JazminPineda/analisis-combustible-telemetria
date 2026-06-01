# %%
import pandas as pd
import numpy as np
from pathlib import Path
from analisis_reporte_telemetria import (
    cargar_datos_gestion_bus,
    procesar_fechas_y_llaves,
    join_unique,
    extraer_caracter
)

# %% [markdown]
# # Movimiento Intercompañia

# %%
# Uso
path2 = Path(r"..\data\gestion-bus")
    
df_combustible_movimientos = cargar_datos_gestion_bus(path2)

# %%
# Clave para analizar Entregas / Remito
df_combustible_movimientos = procesar_fechas_y_llaves(df_combustible_movimientos, 'Fecha', 'Almacen', 'Fecha Remito')
df_combustible_movimientos_ = df_combustible_movimientos.copy()

## Seleccion Almacen para Analizar
df_combustible_lujan = df_combustible_movimientos_[(df_combustible_movimientos_['Almacen']== "903 BARRACAS Lujan")]

# Clave para analizar Recargas
df_combustible_lujan = procesar_fechas_y_llaves(df_combustible_lujan, 'Fecha', 'Almacen', 'Fecha')


# %%
df_combustible_lujan['Tipo'].value_counts()

# %% [markdown]
# ## Movimientos y ajustes

# %%
tipos_movimientos = ['Trasvase Combustible (Egreso)',
'Trasvase Combustible (Ingreso)',
'Corrección Negativa',
'Corrección Positiva'
]

df_movimientos = df_combustible_lujan[df_combustible_lujan['Tipo'].isin(tipos_movimientos)]

df_movimientos_agrupado = df_movimientos.groupby(
    ['Año_mes',  'unico_mes','unico_mes_Almacen','Almacen', 'Tipo', 'Tanque']
).agg(
    Litros_Entregados_Sum=('Litros', 'sum'),
    Cantidad_veces=('Litros', 'count'),
    Observacion = ( 'Observación', join_unique),
    Usuario=('Usuario', join_unique),
    Fecha_Hora = ('Fecha Hora', join_unique)

).reset_index()

df_movimientos_agrupado.head(2)
df_movimientos_agrupado.to_excel(r"C:\Users\jpineda\Desktop\Tableros Grupo\1_OPERACIONES\2_Reporte Combustible\20_Compensacion\Kardex\0_Trasvase-Tanques.xlsx", index=False)

# %% [markdown]
# # Recargas y Entregas

# %%
df_entrega = df_combustible_lujan[df_combustible_lujan['Tipo']=="Entrega de Combustible"]
df_recargas = df_combustible_lujan[df_combustible_lujan['Tipo']=="Carga de Combustible"]


# %% [markdown]
# <a id="seccion_clave_unica"></a>
# ## 4. Recargas Gestion Bus

# %%
df_recargas = extraer_caracter(df_recargas, 'Tanque')
df_recargas = procesar_fechas_y_llaves(df_recargas, 'Fecha', 'Tanque', 'Fecha')
df_recargas['Date_fx'] = pd.to_datetime(df_recargas['Fecha'], format='%d/%m/%Y', errors='coerce').dt.date


# %%

# Por ahora no vamos a ver como se distribuye por tanque ese va ser otro paso 
df_combustible_recargas_agrupado = df_recargas.groupby(
    ['Año_mes',  'unico_mes', 'Tipo','Date_fx', 'Almacen', 'Tanque']
).agg(
    Litros_GB_Recargas=('Litros', 'sum'),
    Cantidad_veces=('Litros', 'count'),
    Surtidor = ( 'Surtidor', join_unique), 


).reset_index()
#df_combustible_agrupado_entregas['Date_fx'] = pd.to_datetime(df_combustible_agrupado_entregas['Date_fx'])

df_combustible_recargas_agrupado['unico_almacen'] = df_combustible_recargas_agrupado['Almacen'] + '_' + df_combustible_recargas_agrupado['Tanque'].astype(str) + '_' + df_combustible_recargas_agrupado['Date_fx'].astype(str) + '_' + df_combustible_recargas_agrupado['Litros_GB_Recargas'].astype(str)


df_combustible_recargas_agrupado.head(2)
#df_combustible_recargas_agrupado.to_excel(r"C:\Users\jpineda\Desktop\Tableros Grupo\1_OPERACIONES\2_Reporte Combustible\20_Compensacion\Kardex\2-Agrupacion-recargas_GB.xlsx", index=False)
#df_recargas.to_excel(r"C:\Users\jpineda\Desktop\Tableros Grupo\1_OPERACIONES\2_Reporte Combustible\20_Compensacion\Kardex\2-Recargas-Completo-GB.xlsx", index=False)

# %% [markdown]
# # Entregas

# %%

# Por ahora no vamos a ver como se distribuye por tanque ese va ser otro paso 
df_combustible_lujan = df_combustible_lujan.groupby(
    ['Año_mes',  'unico_mes', 'unico_semana_almacen' ,'unico_mes_Almacen', 'Sociedad','Tipo', 'NroPedido','Almacen', 'Date_fx' ]
).agg(
    Litros_GB=('Litros', 'sum'),
    Cantidad_veces=('Litros', 'count'),
   # Date_fx = ( 'Fecha Remito', join_unique),
    Remito = ('Nro. Remito', join_unique),
    L_Entregados = ('Litros Entregado', 'max'),
    L_Solicitados = ('LitrosSolicitado', 'max'),
    Nro_Presinto=( 'Nro. Precinto', join_unique),
   
    Usuario=('Usuario', join_unique),

).reset_index()



df_combustible_lujan['unico_almacen'] = df_combustible_lujan['Almacen'] + '_' + df_combustible_lujan['Date_fx'].astype(str) + '_' + df_combustible_lujan['Litros_GB'].astype(str)

df_combustible_lujan['Date_fx']  = pd.to_datetime(df_combustible_lujan['Date_fx'],  dayfirst=True, errors='coerce').dt.normalize().astype('datetime64[ns]')
df_combustible_lujan.head(2)
#df_combustible_lujan.to_excel(r"C:\Users\jpineda\Desktop\Tableros Grupo\1_OPERACIONES\2_Reporte Combustible\20_Compensacion\Outs\Agrupacion-Combustible-por-Almacen_GB.xlsx", index=False)

# %% [markdown]
# ## Analisis Recargas por Almacen

# %%

def limpieza_fecha(df, columna_fecha='Date_fx'):
    # 1. Copia de seguridad
    df = df.copy()
    
    # 2. Definimos nulos comunes para pre-limpieza
    common_nulls = ["-", " ", "N/A", "nd", "n/d", "None", "", "nan", "NaN", "unnamed"]
    
    if columna_fecha in df.columns:
        # 3. Limpieza básica de strings y reemplazo de nulos conocidos
        df[columna_fecha] = df[columna_fecha].astype(str).str.strip().replace(common_nulls, np.nan)
        
        # 4. Conversión a Datetime
        # errors='coerce' transformará cualquier texto que no sea fecha en NaT (Not a Time)
        df[columna_fecha] = pd.to_datetime(df[columna_fecha], dayfirst=True, errors='coerce')
        
        # 5. Manejo de nulos (Incluir "0" o una fecha mínima)
        # Nota: Las columnas de fecha en Pandas no aceptan el número 0 directamente si quieres 
        # mantener el tipo datetime. Aquí tienes dos opciones:
        
        # Opción A: Convertir a texto y poner "0" (si solo lo quieres para reporte)
        # df[columna_fecha] = df[columna_fecha].dt.strftime('%Y-%m-%d').fillna("0")
        
        # Opción B: Mantener como fecha y poner una fecha muy antigua (ej. 1900-01-01)
        # # Esto es mejor para poder seguir filtrando por fechas luego.
        # fecha_defecto = pd.Timestamp('1900-01-01')
        # df[columna_fecha] = df[columna_fecha].fillna(fecha_defecto)
        
    return df

# %%
#df_combustible_lujan = limpieza_fecha(df_combustible_lujan) 

# %%

df_combustible_lujan['unico_almacen'] = df_combustible_lujan['Almacen'] + '_' + df_combustible_lujan['Date_fx'].astype(str)+ '_' + df_combustible_lujan['Litros_GB'].astype(str)


df_combustible_lujan["Dif GB vs Entreg"] = df_combustible_lujan['Litros_GB']-df_combustible_lujan['L_Entregados']

df_combustible_lujan.to_excel(r"C:\Users\jpineda\Desktop\Tableros Grupo\1_OPERACIONES\2_Reporte Combustible\20_Compensacion\Outs\Agrupacion-Combustible-por-Almacen_GB.xlsx", index=False)
#df_combustible_lujan.to_excel(r"C:\Users\jpineda\Desktop\Tableros Grupo\1_OPERACIONES\2_Reporte Combustible\20_Compensacion\Outs\GB-Analisis-pedido_lujan_v2.xlsx", index=False)


# %% [markdown]
# # anterior
