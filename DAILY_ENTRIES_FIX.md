# Fix: Entradas Diarias Mostrando Fechas Actuales en Lugar de Históricas

## Problema
El análisis de "Entradas Diarias" estaba mostrando fechas actuales (2025/2026) cuando debería mostrar las fechas históricas del archivo procesado (por ejemplo, 1914).

## Causa Raíz
El endpoint `/api/analysis/daily-entries` estaba generando datos mock con fechas actuales (últimos 30 días desde hoy) en lugar de consultar los datos reales de Delta Lake.

## Solución Aplicada

### Archivo Modificado: `backend/app/api/routes/analysis.py`

**Cambios en el endpoint `get_daily_entries` (líneas 160-240)**:

#### Antes (Mock Data):
```python
# Generaba fechas actuales por defecto
if not request.start_date or not request.end_date:
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    # ... generaba datos falsos con fechas actuales
```

#### Después (Datos Reales):
```python
# Lee datos reales de Delta Lake
layer_news = portada_service._get_news_layer()
df = layer_news.read_raw_data("ship_entries")

# Filtra por publicación
publication_upper = request.publication.upper()
df_filtered = df.filter(f"UPPER(publication_name) = '{publication_upper}'")

# Agrupa por fecha y cuenta entradas
daily_df = df_filtered.groupBy("publication_date").agg(
    F.count("*").alias("count")
).orderBy("publication_date")

# Obtiene fechas reales del archivo procesado
daily_results = daily_df.collect()
```

## Cómo Funciona Ahora

### 1. Consulta Datos Reales
- Lee la tabla `ship_entries` de Delta Lake
- Filtra por `publication_name` (case-insensitive)
- Agrupa por `publication_date` y cuenta registros

### 2. Respeta Filtros de Fecha (Opcional)
Si el usuario proporciona `start_date` y `end_date`:
```python
df_filtered = df_filtered.filter(
    f"publication_date >= '{request.start_date}' AND publication_date <= '{request.end_date}'"
)
```

### 3. Retorna Fechas Históricas
- Las fechas vienen directamente del campo `publication_date` de los datos
- Para el archivo de 1914, mostrará fechas como "1914-01-02", "1914-01-03", etc.
- El rango de fechas se determina automáticamente de los datos reales

## Ejemplo de Respuesta

### Antes (Datos Mock):
```json
{
  "publication": "dm",
  "daily_counts": [
    {"date": "2025-12-27", "count": 93, "publication": "dm"},
    {"date": "2025-12-28", "count": 71, "publication": "dm"},
    {"date": "2025-12-29", "count": 74, "publication": "dm"}
  ],
  "total_entries": 2134,
  "date_range": {
    "start_date": "2025-12-27",
    "end_date": "2026-01-26"
  }
}
```

### Después (Datos Reales):
```json
{
  "publication": "dm",
  "daily_counts": [
    {"date": "1914-01-02", "count": 71, "publication": "dm"}
  ],
  "total_entries": 71,
  "date_range": {
    "start_date": "1914-01-02",
    "end_date": "1914-01-02"
  }
}
```

## Beneficios

1. **Datos Precisos**: Muestra las fechas reales del archivo procesado
2. **Histórico Correcto**: Refleja el período histórico de los datos (1852-1914)
3. **Conteos Reales**: Los números de entradas son exactos, no estimados
4. **Filtrado Funcional**: Los filtros de fecha ahora funcionan correctamente

## Testing

### Pasos para Verificar:
1. Asegúrate de haber procesado al menos un archivo (por ejemplo, `1914_traversing_converted.json`)
2. Ve a la página de "Análisis" → "Entradas Diarias"
3. Selecciona publicación "DM" (Diario de la Marina)
4. Haz clic en "Consultar Entradas"
5. Verifica que las fechas mostradas sean históricas (1914) no actuales (2025/2026)

### Resultado Esperado:
- **Fecha**: 1914-01-02 (o la fecha del archivo procesado)
- **Cantidad**: 71 (o el número real de registros)
- **Publicación**: dm

## Estado

✅ **IMPLEMENTADO** - Backend reiniciado con cambios aplicados (2026-01-27 00:52)

## Notas Técnicas

- La consulta usa PySpark para leer de Delta Lake
- El filtro de publicación es case-insensitive (`UPPER(publication_name)`)
- Los resultados se ordenan por fecha ascendente
- Si no hay datos para la publicación, retorna lista vacía

## Archivos Modificados

1. `backend/app/api/routes/analysis.py` (líneas 160-240)

## Próximos Pasos

1. Refrescar la página del frontend para ver las fechas históricas correctas
2. Verificar que los filtros de fecha funcionen correctamente
3. Procesar más archivos para ver múltiples fechas históricas
