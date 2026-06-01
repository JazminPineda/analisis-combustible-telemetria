
"""
Centraliza todas las constantes, paths y configuraciones. Esto evita "números mágicos" y facilita los cambios.
"""

# analisis_reporte_telemetria/config.py
from pathlib import Path

# --- Rutas Base ---
# Usar pathlib es más robusto y portable que strings crudos.
# Se asume que la carpeta 'data' está en la raíz del proyecto.
BASE_DATA_PATH = Path("..\data")

# --- Configuraciones Específicas por Módulo ---
GESTION_BUS_PATH = BASE_DATA_PATH / "gestion-bus"

# --- Constantes de Datos ---
COMMON_NULL_VALUES = ["-", " ", "N/A", "nd", "n/d", "None", "", "nan", "NaN", "unnamed"]

# --- Headers para Gestión Bus ---
HEADERS_FIJOS2 = [
    'Nro. Mov', 'Fecha', 'Codigo', 'Tipo', 'Ingreso', 'Sociedad', 'Almacen',
    'Tanque', 'Surtidor', 'Unidad', 'Kms. Carga', 'Kms. Odometro',
    'Kms. Recorrido', 'Litros', 'Precio Litro', 'Nro. Solicitud',
    'Fecha Solicitud', 'NroPedido', 'Estado Solicitud',
    'LitrosSolicitado', 'Litros Entregado', 'Nro. Remito', 'Fecha Remito',
    'Importe Remito', 'EuroDiesel', 'Nro. Precinto',
    'Nro. Precinto Anterior', 'Tiene Precinto Anterior',
    'Observacion Precinto Anterior', 'Nro. Factura', 'Fecha Factura',
    'Importe Factura', 'Localidad Carga', 'Proveedor Carga',
    'Sociedad Pagadora', 'Nro. Cierre', 'Observación', 'Usuario',
    'Fecha Hora'
]

HEADERS_FINAL2 = [h.replace('.', '') for h in HEADERS_FIJOS2] + ['archivo']