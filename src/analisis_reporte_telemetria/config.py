
"""
Centraliza todas las constantes, paths y configuraciones. Esto evita "números mágicos" y facilita los cambios.
"""

# analisis_reporte_telemetria/config.py
from pathlib import Path

# --- Rutas Base ---
# Usar Path(__file__) para que las rutas sean relativas al archivo de configuración
BASE_DIR = Path(__file__).parent.parent.parent
BASE_DATA_PATH = BASE_DIR / "data"

# --- Configuraciones Específicas por Módulo ---
GESTION_BUS_PATH = BASE_DATA_PATH / "gestion-bus"
FORM_DATA_PATH = BASE_DATA_PATH / "formulario"
OUTPUT_BASE_PATH = BASE_DIR / "outputs"
CONCILIACION_OUTPUT_PATH = OUTPUT_BASE_PATH / "conciliacion"
FORM_FILE_NAME = "Ingresos de combustible y Trasvases(1-18) (1) (1).xlsx"

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