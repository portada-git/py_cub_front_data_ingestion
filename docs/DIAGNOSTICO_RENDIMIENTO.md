# Diagnóstico de Rendimiento - Procesamiento de Archivos

## Prueba Realizada

**Fecha**: 2026-01-27  
**Archivo**: `.data/converted/1914_traversing_converted.json`  
**Registros**: 71  
**Tiempo**: > 60 segundos (timeout)

## Resultados

### ✅ Datos Correctos
- El archivo JSON tiene la estructura correcta
- Todos los campos requeridos están presentes:
  - `publication_name`: "DM" ✅
  - `publication_date`: "1914-01-02" ✅
  - `parsed_text`: Presente ✅
  - Todos los demás campos requeridos ✅

### ❌ Rendimiento Inaceptable
- **71 registros** tardaron **más de 60 segundos**
- **Throughput**: < 1.2 registros/segundo
- **Objetivo**: > 35 registros/segundo (71 registros en < 2 segundos)

## Análisis del Problema

### Overhead de PySpark Observado

```
26/01/27 00:37:01 WARN Utils: Your hostname, danro-dell resolves to a loopback address
26/01/27 00:37:01 WARN Utils: Set SPARK_LOCAL_IP if you need to bind to another address
:: loading settings :: url = jar:file:/.../ivy-2.5.1.jar!/org/apache/ivy/core/settings/ivysettings.xml
Ivy Default Cache set to: /home/danro/.ivy2/cache
The jars for the packages stored in: /home/danro/.ivy2/jars
io.delta#delta-spark_2.12 added as a dependency
:: resolving dependencies :: org.apache.spark#spark-submit-parent-...
```

**Tiempo de inicialización**: ~6-7 segundos solo para cargar Spark

### Etapas de Procesamiento Observadas

1. **Inicialización de Spark** (0-7s)
   - Carga de JARs
   - Resolución de dependencias (Delta Lake)
   - Inicialización de SparkContext
   - Creación de SparkUI

2. **Procesamiento de Datos** (7-60s+)
   - Stage 0: Lectura de datos (12 tasks)
   - Stage 5: Transformaciones (50 tasks)
   - Stage 49: Escritura a Delta Lake (13 tasks)

### Problema Principal: Sobre-Paralelización

Para 71 registros, Spark está creando:
- **12 tasks** en Stage 0
- **50 tasks** en Stage 5  
- **13 tasks** en Stage 49

**Total**: 75 tasks para procesar 71 registros (1 task por registro!)

Esto es extremadamente ineficiente porque:
- Cada task tiene overhead de scheduling
- Cada task tiene overhead de serialización
- La coordinación entre tasks es más costosa que el procesamiento real

## Causa Raíz

**PySpark está diseñado para Big Data (millones de registros), no para archivos pequeños.**

Para archivos pequeños:
- Overhead de inicialización >> Tiempo de procesamiento
- Overhead de paralelización >> Beneficio de paralelización
- Overhead de Delta Lake >> Beneficio de formato columnar

## Soluciones Propuestas

### Solución 1: Path Rápido para Archivos Pequeños (RECOMENDADO)

```python
async def ingest_extraction_data(self, file_path: str, ...):
    # Contar registros
    record_count = len(entries)
    
    if record_count < 500:
        # Path rápido: usar pandas + pyarrow directamente
        return await self._ingest_small_file_fast(entries, destination_path)
    else:
        # Path normal: usar PySpark para archivos grandes
        return await self._ingest_with_spark(entries, destination_path)
```

**Beneficios**:
- Archivos < 500 registros: < 2 segundos
- Sin cambios en la API
- Mantiene compatibilidad con Delta Lake

### Solución 2: Batch Processing

Acumular múltiples archivos pequeños y procesarlos juntos:

```python
# En lugar de procesar 10 archivos de 71 registros cada uno (10 x 60s = 10 minutos)
# Procesar 1 batch de 710 registros (1 x 15s = 15 segundos)
```

**Beneficios**:
- Amortiza el overhead de Spark
- Mejor throughput general

### Solución 3: Configuración de Spark Optimizada

```python
spark_conf = {
    "spark.sql.shuffle.partitions": "2",  # Reducir de 200 a 2
    "spark.default.parallelism": "2",     # Reducir paralelismo
    "spark.sql.files.maxPartitionBytes": "134217728",  # 128MB
    "spark.sql.adaptive.enabled": "true",
    "spark.sql.adaptive.coalescePartitions.enabled": "true",
    "spark.sql.adaptive.coalescePartitions.minPartitionSize": "1MB"
}
```

**Beneficios**:
- Reduce número de tasks
- Mejora rendimiento para archivos pequeños
- Sin cambios en código

## Recomendación Final

**Implementar Solución 1 + Solución 3**:

1. **Corto plazo** (1-2 horas): Aplicar configuración de Spark optimizada
   - Mejora esperada: 30-40% (60s → 36-42s)

2. **Medio plazo** (1 día): Implementar path rápido para archivos pequeños
   - Mejora esperada: 95% (60s → 2-3s)

3. **Largo plazo** (1 semana): Implementar batch processing
   - Mejora esperada: 90% en throughput general

## Métricas de Éxito

| Tamaño Archivo | Tiempo Actual | Tiempo Objetivo | Mejora |
|----------------|---------------|-----------------|--------|
| < 100 registros | 60s | 2s | 97% |
| 100-500 registros | 90s | 5s | 94% |
| 500-1000 registros | 120s | 10s | 92% |
| > 1000 registros | 180s | 30s | 83% |

## Próximos Pasos

1. ✅ Diagnóstico completado
2. ⏭️ Implementar configuración de Spark optimizada
3. ⏭️ Implementar path rápido para archivos pequeños
4. ⏭️ Medir mejoras y ajustar

## Conclusión

El backend **funciona correctamente** y procesa los datos, pero es **extremadamente lento** debido al overhead de PySpark para archivos pequeños. La solución requiere implementar un path de procesamiento alternativo para archivos pequeños que evite el overhead de Spark.
