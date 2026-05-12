# Análisis de Telemetría de Combustibles - Detección de Anomalías

## Fecha del Análisis
Mayo 12, 2026

## Contexto del Proyecto
Este análisis se realiza sobre datos de telemetría de tanques de combustible del sistema Ationet SaaS. El objetivo es detectar fugas, robos o errores de sistema en tiempo real para prevenir pérdidas económicas y operativas.

## Metodología de Análisis

### 1. Limpieza y Preparación de Datos
- **Conversión de formatos**: Las fechas se convierten a datetime. Los valores numéricos (volumen, temperatura, etc.) se convierten desde formato europeo (coma como decimal) a formato estándar.
- **Ordenamiento temporal**: Los datos se ordenan por tanque y fecha de medición.
- **Detección de anomalías temporales**: Se identifican gaps grandes (>3 horas), timestamps inconsistentes y registros retrodatados.

### 2. Análisis de Volumen
- **Cálculo de variaciones**: Se calcula la diferencia de volumen entre registros consecutivos por tanque.
- **Variación esperada**: Se estima evaporación normal basada en temperatura y merma.
- **Clasificación de anomalías**:
  - **robo_potencial**: Caídas abruptas fuera del rango normal.
  - **fuga_potencial**: Pérdidas consistentes pero no extremas.
  - **error_sensor**: Cambios imposibles o divergencias entre volumen y altura.
  - **normal**: Dentro de parámetros esperados.

### 3. Validación de Coherencia
- **Timestamps**: Verificación de que Fecha ≤ Fecha Actualizacion.
- **Relaciones físicas**: Correlación entre Volumen y Altura de Combustible.
- **Diferencias temporales**: Validación de Tiempo_Transcurrido vs. diferencias calculadas.

### 4. Indicadores Específicos
Se analizan señales para diferenciar tipos de anomalías:

**Fuga (pérdida gradual)**:
- Pérdida constante y predecible
- Correlación con temperatura
- Incremento en Altura de Agua
- Afecta 24/7 (sin patrón horario)

**Robo (pérdida súbita)**:
- Caída abrupta de volumen
- Patrón temporal (ej: nocturno)
- Variación no explicada por temperatura
- Correlación con desconexiones

**Errores de Sistema**:
- Saltos imposibles físicamente
- Divergencias entre Volumen y Altura
- Timestamps inconsistentes

## Interpretación de Resultados

### Diccionario de Datos y Unidades

- `Fecha`, `Fecha Host`, `Fecha Actualizacion`: Fechas y horas en formato ISO.
- `Sitio`, `Tanque`, `Categoria`: Identificadores de ubicación y tipo de combustible.
- `Volumen`: Litros de combustible estimados en el tanque, generalmente medidos directamente.
- `Volumen TC`: Litros ajustados por el sistema de telemetría y control. Esta columna se utiliza como referencia prioritaria para calcular los cambios de volumen cuando está disponible.
- `Volumen_Referencia`: Volumen de referencia usado en el cálculo de `diff_volumen`. Usa `Volumen TC` si está presente, o `Volumen` como respaldo.
- `Merma`: Litros de merma reportados por el sensor o la lógica de cálculo.
- `Temperatura`: Grados Celsius.
  - Si al exportar se ve un valor como `2767`, eso indica un problema de parseo de formato numérico; el valor real esperado es 27.67 °C cuando se usa punto decimal.
- `Altura de Combustible`, `Altura de Agua`: Altura reportada por el sensor, generalmente en unidades de distancia con decimal implícito (por ejemplo 44.494 => 44.494 unidades de altura del sensor).
- `Volumen TC + Merma`: Debe ser menor o igual a 30.000 litros, que corresponde a la capacidad máxima del tanque.
- `diff_volumen`: Cambio de volumen entre registros consecutivos del mismo tanque, calculado sobre `Volumen_Referencia` en litros.
- `retraso_actualizacion_s`: Retraso en segundos entre `Fecha` y `Fecha Actualizacion`.
- `retraso_actualizacion_critico`: Indicador booleano si el retraso supera 3 horas.
- `gap_grande`: Indicador booleano si hay un vacío mayor a 3 horas entre registros.
- `clasificacion_volumen`: Categoría de anomalía asignada por regla.
- `anomaly_score`: Puntuación compuesta de riesgo basada en varias señales de inconsistencia.

### Metodología del cálculo de `anomaly_score`

El score compuesto se calcula en `src/telemetria_anomalias.py` como la suma de los siguientes componentes:

- `abs(z_diff_volumen)`: magnitud estandarizada del cambio de volumen entre registros.
- `outlier_iqr * 1.5`: penaliza los cambios que están fuera del rango intercuartílico.
- `retrodatado_sospechoso * 1.0`: penaliza registros cuya fecha es anterior al registro anterior del mismo tanque.
- `retraso_actualizacion_critico * 1.0`: penaliza registros que llegan con más de 3 horas de retraso.

En la práctica, este score es un indicador de riesgo: valores cercanos a 0 son normales, mientras que valores mayores tienden a corresponder con eventos anómalos. Sin embargo, la clasificación final se asigna mediante reglas adicionales:

- `normal`: cambios esperados dentro de los límites de comportamiento histórico.
- `error_sensor`: cambios imposibles o divergencias entre `Volumen` y `Volumen TC` mayores al 10 %.
- `fuga_potencial`: pérdida consistente negativa que no es un outlier extremo, pero excede la evaporación esperada.
- `robo_potencial`: caída abrupta muy grande (≥ 3 desviaciones estándar) y mayor que el doble de la evaporación esperada.

### Regla de capacidad máxima

- Se valida que `Volumen TC + Merma` no supere `30.000` litros.
- Si se sobrepasa ese umbral, la fila se marca con `capacidad_excedida = True`.

### Observaciones de formato numérico

- El dataset asume que los números utilizan coma como separador de miles y punto como separador de decimales.
- Esto significa que un valor como `2,763.50` debe leerse como `2763.50` litros, y no como `2.763`.
- En `telemetria_limpa.csv` los valores ya se normalizan a formato numérico estándar sin separadores de miles.

### Gráficas

#### Serie de Volumen por Tanque
- **Archivo**: `outputs/volumen_series_tanque_{ID}.png`
- **Interpretación**: Muestra la evolución temporal del volumen para cada tanque individualmente.
- **Qué buscar**:
  - Caídas repentinas (posible robo)
  - Descensos graduales (posible fuga)
  - Fluctuaciones irregulares (errores de sensor)
  - Períodos sin datos (desconexiones)

#### Diferencia de Volumen
- **Archivo**: `outputs/diff_volumen_todos.png`
- **Interpretación**: Puntos coloreados por clasificación de anomalía.
- **Colores**:
  - Azul: normal
  - Rojo: robo_potencial
  - Naranja: fuga_potencial
  - Verde: error_sensor

### Reportes Técnicos

#### Para Equipo Técnico/Operativo
- **`outputs/telemetria_limpa.csv`**: Datos limpios con todas las columnas procesadas.
- **`outputs/validacion_timestamps.csv`**: Análisis de coherencia temporal.
- **`outputs/eventos_anomalias_todos.csv`**: Lista detallada de eventos clasificados.
- **`outputs/desconexiones_todos.csv`**: Períodos de desconexión por sitio/tanque.

#### Para Gerencia/Ejecutivos
- **`outputs/reporte_calidad_datos_todos.csv`**: Resumen ejecutivo con métricas clave.
- **`outputs/indicadores_anomalias.csv`**: Checklist de indicadores detectados.
- **Gráficas individuales por tanque**: Para revisión visual rápida.

## Métricas de Calidad de Datos

### Resumen Ejecutivo
- **Registros totales**: Número total de mediciones procesadas.
- **Timestamps inválidos**: Registros donde Fecha > Fecha Actualizacion (problemas de sincronización).
- **Retrasos críticos**: Datos que llegan con más de 3 horas de retraso.
- **Gaps grandes**: Períodos sin datos > 3 horas.
- **Eventos de anomalías**: Número total de eventos clasificados como sospechosos.

### Indicadores de Anomalías
- **Fuga**: Señales de pérdida gradual.
- **Robo**: Señales de pérdida súbita.
- **Error de Sistema**: Problemas técnicos en sensores o transmisión.

## Recomendaciones de Monitoreo

### Alertas Automáticas
1. **Caídas abruptas**: Notificar inmediatamente al supervisor de turno.
2. **Pérdidas graduales**: Acumuladas > umbral diario, investigar calibración.
3. **Desconexiones prolongadas**: > 3 horas, verificar conectividad.
4. **Timestamps inconsistentes**: Revisar configuración de relojes en equipos.

### Frecuencia de Revisión
- **Diaria**: Reporte ejecutivo con anomalías del día.
- **Semanal**: Análisis de tendencias por tanque.
- **Mensual**: Revisión de calibraciones y mantenimiento.

### Acciones Correctivas
- **Robo sospechado**: Verificar CCTV, inventario físico, cadena de custodia.
- **Fuga detectada**: Inspección visual del tanque, medición de agua.
- **Errores de sensor**: Recalibración, reemplazo de sensores defectuosos.
- **Problemas de conectividad**: Revisar antenas, routers, configuración de red.

## Archivos Generados

### Carpeta `outputs/`
- `telemetria_limpa.csv`: Datos procesados completos.
- `validacion_timestamps.csv`: Análisis temporal.
- `eventos_anomalias_todos.csv`: Eventos clasificados.
- `desconexiones_todos.csv`: Períodos offline.
- `reporte_calidad_datos_todos.csv`: Métricas resumen.
- `indicadores_anomalias.csv`: Checklist de señales.
- `volumen_series_tanque_{ID}.png`: Gráfico individual por tanque.
- `diff_volumen_todos.png`: Diferencias con clasificación.

### Notas Técnicas
- Los datos se procesan asumiendo formato europeo para números.
- Las clasificaciones son probabilísticas y requieren validación humana.
- Los umbrales (3 horas, 3 desviaciones estándar) son configurables.
- El análisis es retrospectivo; para monitoreo en tiempo real se requiere integración con sistema de alertas.

## Contacto
Para preguntas técnicas: Equipo de Data Science
Para interpretación de resultados: Gerencia de Operaciones
