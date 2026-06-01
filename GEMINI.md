# Contexto del Proyecto para Modelos de IA: Análisis de Combustible y Telemetría

Este archivo (`GEMINI.md`) sirve como la "fuente de la verdad" técnica y contextual para que cualquier LLM o Agente de IA asista eficientemente en el desarrollo, refactorización y automatización de este repositorio.

---

## 1. Visión General del Proyecto
* **Nombre:** `analisis-combustible-telemetria`
* **Dominio:** Sector de transporte de pasajeros de larga distancia.
* **Objetivo:** Analizar datos telemétricos (sensores, protocolos CANbus) y registros de carga para optimizar la eficiencia operativa, calcular métricas de consumo de combustible y determinar costos críticos por kilómetro ($/km$).
* **Tecnologías Clave:** Python Stack (`pandas`, `NumPy`, `openpyxl`, `seaborn`, `matplotlib`).

---

## 2. Entorno y Gestión de Dependencias
El proyecto utiliza **`uv`** como gestor de paquetes y entornos virtuales ultrarrápido.
* **Ubicación del Entorno:** `.venv/` en la raíz del proyecto.
* **Flujo de Trabajo Común con `uv`:**
  * Sincronizar entorno: `uv sync`
  * Agregar dependencia: `uv add <paquete>`
  * Ejecutar scripts de forma aislada: `uv run scripts/nombre_script.py`

---

## 3. Arquitectura del Repositorio y Estructura de Directorios

El proyecto sigue una estructura limpia y modular que separa el entorno, los datos crudos/procesados, el análisis exploratorio y el código fuente empaquetable:

```text
analisis-combustible-telemetria/
├── .venv/                            # Entorno virtual administrado por uv (omitir en búsquedas de código)
├── data/                             # Repositorio de datos locales
│   ├── formulario/                   # Cargas manuales, encuestas o planillas de control de combustible
│   └── gestion-bus/                  # Extracciones del sistema de gestión y logs de telemetría vehicular
├── docs/                             # Documentación técnica, metodologías y diagramas
├── notebooks/                        # Jupyter Notebooks para Análisis Exploratorio de Datos (EDA) y prototipos
├── outputs/                          # Reportes generados, gráficos exportados y archivos .xlsx finales
├── scripts/                          # Scripts de automatización y orquestación de tareas en producción
├── src/                              # Código fuente principal del paquete (Paquete Editable)
│   └── analisis_reporte_telemetria/  # Namespace principal del paquete
│       ├── readers/                  # Capa de Ingesta: Lectura de archivos (CSV, Excel, APIs)
│       ├── cleaners/                 # Capa de Calidad: Limpieza de datos, tipados, imputaciones y manejo de nulos
│       ├── processors/               # Capa de Negocio: Cálculo de KPIs, métricas de consumo, CANbus e integraciones
│       └── utils/                    # Funciones transversales auxiliares (configuraciones, formateo, logging)
├── pyproject.toml                    # Configuración del proyecto y dependencias de uv
└── GEMINI.md                         # Este archivo de contexto para IA