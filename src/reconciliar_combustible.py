# scripts/reconciliar_combustible.py

import sys
import os
from pathlib import Path

# Agregar src al path para poder importar el paquete
sys.path.append(str(Path(__file__).parent.parent / "src"))

from analisis_reporte_telemetria.readers.form_reader import FormReader
from analisis_reporte_telemetria.readers.gestion_bus_reader import GestionBusReader
from analisis_reporte_telemetria.processors.reconciliation_processor import ReconciliationProcessor

def main():
    print("Iniciando proceso de conciliación de combustible...")
    
    try:
        # 1. Leer datos del formulario
        print("Cargando datos del formulario de ingresos...")
        form_reader = FormReader()
        df_form = form_reader.cargar_datos()
        print(f"Datos de formulario cargados: {len(df_form)} registros de descarga.")
        
        # 2. Leer datos de Gestión Bus
        print("Cargando datos de Gestión Bus...")
        gb_reader = GestionBusReader()
        df_gb = gb_reader.cargar_datos()
        
        # 3. Realizar conciliación
        print("Procesando conciliación...")
        processor = ReconciliationProcessor()
        df_conciliado = processor.conciliar(df_form, df_gb)
        
        # 4. Guardar resultados
        print("Guardando reporte final...")
        processor.guardar_reporte(df_conciliado)
        
        print("Proceso completado con éxito.")
        
    except Exception as e:
        print(f"ERROR durante el proceso: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
