
Actúa como un Data Scientist especializado en detección de anomalías en sistemas de telemetría industrial y análisis forense de combustibles.

**CONTEXTO DEL PROBLEMA:**
Necesito analizar datos de telemetría de tanques de combustible para:
1. Detectar fugas o robos (pérdidas anómalas de volumen)
2. Realizar conciliación de datos (validar coherencia de registros)
3. Identificar problemas de conectividad o calidad de datos

**SISTEMA:**
- Proveedor: Ationet SaaS (https://github.com/Ationet/ationetdocs)
- Herramienta de análisis: Python/pandas, uv (manejo de paquetes)
- Frecuencia de datos: [especifica si es cada minuto, hora, etc.]
- Número aproximado de tanques: [X]
- Período de análisis: [rango de fechas]
- Ruta al archivo: data/Inventarios20260512164148.xls

**ESTRUCTURA DE DATOS:**
DataFrame con columnas:
```
['Fecha', 'Fecha Host', 'Fecha Actualizacion', 'Sitio', 'Tanque', 
 'Categoria', 'Volumen', 'Variacion Volumen', 'Volumen TC', 
 'Variacion Volumen TC', 'Merma', 'Temperatura', 
 'Altura de Combustible', 'Altura de Agua', 'Tiempo_Transcurrido', 
 'Horas_Sin_Actualizar', 'Estado_Conexion', 'fx_almace', 'Date_fx', 'Año_mes']
```

---

**PARTE 1 – ACLARACIÓN DE COLUMNAS TEMPORALES:**

Explica la diferencia entre estas tres columnas y su impacto en el análisis:
- `Fecha`: [¿timestamp del evento de medición?]
- `Fecha Host`: [¿timestamp del servidor Ationet?]
- `Fecha Actualizacion`: [¿cuándo se sincronizó al sistema?]

**Preguntas específicas:**
1. ¿Qué significa un gap significativo entre `Fecha` y `Fecha Actualizacion`?
2. ¿Cómo impacta esto en la detección de fugas? (ej: ¿puede enmascarar eventos?)
3. ¿Cuál columna debo usar como referencia temporal para análisis de variaciones?
4. ¿Cómo detectar datos "retrasados" vs datos "retrodatados" sospechosos?

---

**PARTE 2 – ANÁLISIS EXPLORATORIO PARA DETECCIÓN DE ANOMALÍAS:**

Proporciona **código pandas comentado** para realizar estos análisis:

**A) ANÁLISIS TEMPORAL:**
1. Identificar gaps temporales (períodos sin datos > umbral esperado)
2. Detectar timestamps duplicados o fuera de orden
3. Analizar patrones de `Horas_Sin_Actualizar` y `Estado_Conexion`
4. Correlacionar desconexiones con pérdidas de volumen

**B) ANÁLISIS DE VOLUMEN (detección de fugas/robos):**
1. Calcular tasas de variación esperadas vs anómalas
   - Variación normal por evaporación (usar `Temperatura` y `Merma`)
   - Desviaciones estadísticas (Z-score, IQR outliers)
2. Detectar:
   - Caídas abruptas de volumen (posible robo)
   - Pérdidas graduales pero consistentes (posible fuga)
   - Incrementos anómalos (errores de sensor o inyecciones no registradas)
3. Comparar `Variacion Volumen` vs `Variacion Volumen TC` (temperatura compensada)
   - ¿Cuándo divergen y qué significa?

**C) ANÁLISIS DE COHERENCIA (validación de datos):**
1. Verificar relación `Altura de Combustible` ↔ `Volumen`
   - Detectar inconsistencias que sugieran error de calibración
2. Revisar `Altura de Agua` (contaminación o error de sensor)
3. Validar que `Volumen TC` sea coherente con `Volumen` + `Temperatura`
4. Cross-validar `Tiempo_Transcurrido` con diferencia entre timestamps

**D) ANÁLISIS POR TANQUE/SITIO:**
1. Comparar comportamiento entre tanques del mismo sitio
2. Identificar tanques outliers (comportamiento atípico consistente)
3. Agrupar por `Categoria` y buscar patrones anómalos

---

**PARTE 3 – INDICADORES DE FUGA vs ROBO:**

Lista de señales para diferenciar:

**FUGA (pérdida gradual):**
- [ ] Pérdida constante y predecible en el tiempo
- [ ] Correlación con temperatura/presión
- [ ] Incremento en `Altura de Agua` (si es fuga al suelo)
- [ ] Afecta 24/7 (no tiene patrón horario)

**ROBO (pérdida súbita):**
- [ ] Caída abrupta de volumen en corto período
- [ ] Patrón temporal (ej: siempre de noche, fines de semana)
- [ ] Variación no explicada por temperatura
- [ ] Posible correlación con desconexiones (`Estado_Conexion`)

**ERRORES DE SISTEMA:**
- [ ] Saltos imposibles (física) en volumen
- [ ] Divergencias entre `Volumen` y `Altura de Combustible`
- [ ] Timestamps inconsistentes (Fecha > Fecha_Actualizacion)

Proporciona código para calcular un **"anomaly score"** por registro.

---

**PARTE 4 – CÓDIGO ESPECÍFICO SOLICITADO:**

Genera funciones reutilizables en pandas para:

1. **Limpieza de datos:**
```python
def limpiar_telemetria(df):
    """
    - Convertir fechas a datetime
    - Ordenar por Tanque + Fecha
    - Detectar y marcar registros con timestamps anómalos
    - Calcular diferencias temporales reales
    """
    pass
```

2. **Detección de anomalías de volumen:**
```python
def detectar_anomalias_volumen(df, tanque_id, umbral_std=3):
    """
    - Calcular variación esperada por evaporación
    - Identificar outliers estadísticos
    - Clasificar en: fuga_potencial, robo_potencial, error_sensor
    """
    pass
```

3. **Análisis de coherencia temporal:**
```python
def validar_timestamps(df):
    """
    - Verificar que Fecha <= Fecha_Actualizacion
    - Detectar retrasos > umbral crítico
    - Identificar registros "retrodatados"
    """
    pass
```

4. **Dashboard de análisis:**
```python
def generar_reporte_anomalias(df, tanque_id=None):
    """
    Generar resumen con:
    - Períodos de desconexión
    - Eventos de pérdida anómala
    - Métricas de calidad de datos
    - Visualizaciones (matplotlib/seaborn)
    """
    pass
```


---

**OUTPUT ESPERADO:**

1. **Explicación conceptual** de las columnas temporales (500 palabras)
2. **Código Python completo** con las 4 funciones anteriores
3. **Checklist de análisis** para ejecutar paso a paso
4. **Ejemplo de detección**: muestra cómo identificar un caso de robo vs fuga con código
5. **Recomendaciones**: mejores prácticas para monitoreo continuo
6. **Resultado de analisis**: Guardar en la carpeta `outputs`

**FORMATO:**
- Código en bloques python con docstrings
- Explicaciones en español
- Comentarios técnicos en el código
- Ejemplos con datos sintéticos si es necesario
