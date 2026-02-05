# Documentación Técnica - main.py

## Índice

1. [Descripción General](#descripción-general)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Dependencias](#dependencias)
4. [Configuración del Entorno](#configuración-del-entorno)
5. [Flujo de Ejecución](#flujo-de-ejecución)
6. [Componentes Principales](#componentes-principales)
7. [Funciones y Métodos](#funciones-y-métodos)
8. [Ejemplos de Uso](#ejemplos-de-uso)
9. [Gestión de Errores](#gestión-de-errores)

---

## Descripción General

`main.py` es el script principal que implementa un sistema completo de gestión de datos utilizando Delta Lake y Apache Spark. El sistema está diseñado específicamente para procesar datos históricos de embarcaciones, proporcionando funcionalidades de ingesta, transformación, limpieza y análisis de datos.

### Propósito

- Demostrar el uso de Delta Lake para almacenamiento de datos
- Implementar pipelines de ingesta y procesamiento de datos
- Gestionar metadatos y linaje de datos
- Detectar y manejar duplicados
- Limpiar y normalizar datos históricos

---

## Arquitectura del Sistema

### Componentes Principales

```
┌─────────────────────────────────────────┐
│         main.py (Orquestador)           │
└─────────────────┬───────────────────────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
    ▼             ▼             ▼
┌─────────┐  ┌─────────┐  ┌──────────┐
│ Delta   │  │ Portada │  │ Portada  │
│ Builder │  │ Builder │  │ Cleaning │
└─────────┘  └─────────┘  └──────────┘
    │             │             │
    └─────────────┼─────────────┘
                  ▼
         ┌────────────────┐
         │   Delta Lake   │
         │   (Storage)    │
         └────────────────┘
```

### Capas del Sistema

1. **Capa de Configuración**: Gestiona rutas y parámetros según el sistema operativo
2. **Capa de Construcción**: Builders para crear instancias de Delta Lake
3. **Capa de Datos**: Operaciones CRUD sobre Delta Lake
4. **Capa de Metadatos**: Gestión de logs y linaje
5. **Capa de Limpieza**: Transformación y normalización de datos

---

## Dependencias

### Módulos Estándar de Python

```python
import datetime          # Manejo de fechas y timestamps
import json             # Procesamiento de archivos JSON
import logging          # Sistema de logging
import os.path          # Operaciones con rutas de archivos
import platform         # Detección del sistema operativo
import shutil           # Operaciones de archivos (copiar, eliminar)
import sys              # Información del sistema Python
```

### Módulos Externos

```python
import xmltodict        # Conversión XML a diccionarios
from pyspark           # Framework de procesamiento distribuido
from delta-spark       # Integración Delta Lake con Spark
```

### Módulos del Proyecto (portada_data_layer)

```python
from portada_data_layer.boat_fact_model import BoatFactDataModel
from portada_data_layer.data_lake_metadata_manager import DataLakeMetadataManager
from portada_data_layer import DeltaDataLayerBuilder, PortadaBuilder
from portada_data_layer.portada_cleaning import PortadaCleaning
```

---

## Configuración del Entorno

### Detección del Sistema Operativo

El script detecta automáticamente el sistema operativo y configura las rutas correspondientes:

```python
so = platform.system()
if so == "Darwin":  # macOS
    # Configuración para macOS
else:               # Linux
    # Configuración para Linux
```

### Variables de Configuración

#### Rutas Principales

| Variable | Descripción | Ejemplo (macOS) |
|----------|-------------|-----------------|
| `base_path` | Directorio base para Delta Lake | `/Users/.../delta_test` |
| `json_path_to_copy` | Origen de archivos JSON | `/Users/.../resultats/prova` |
| `copy_path` | Directorio temporal para copias | `/Users/.../tmp/json_data` |
| `schema_path` | Ruta al esquema JSON | `/Users/.../schema.json` |
| `regex_mapping_path` | Mapeo de limpieza | `/Users/.../mapping_to_clean_chars.json` |
| `config_path` | Configuración general | `/Users/.../delta_data_layer_config.json` |

#### Parámetros del Sistema

```python
user = "jcanell4"                    # Usuario del sistema
data_path = "dummy_data"             # Ruta de datos de prueba
json_name = "results_boatdata.extractor.json"  # Archivo JSON principal
```

### Configuración de Logging

```python
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s"
)
logger = logging.getLogger("delta_data_layer")
logger.setLevel(logging.INFO)
```

---

## Flujo de Ejecución

### Fase 1: Inicialización y Pruebas Básicas

```
1. Detección del SO y configuración de rutas
2. Creación del builder básico de Delta Lake
3. Eliminación del directorio base (limpieza)
4. Inicio de sesión Spark
5. Creación de DataFrame de prueba
6. Escritura en Delta Lake (3 formas diferentes)
7. Lectura desde Delta Lake (3 formas diferentes)
8. Validación de consistencia de datos
9. Registro de tabla temporal y consulta SQL
```

### Fase 2: Ingesta de Datos de Embarcaciones

```
1. Carga de configuración desde JSON
2. Creación del PortadaBuilder
3. Copia del archivo JSON de datos
4. Ingesta de datos al sistema
5. Lectura de datos con filtros
6. Análisis de conteo por fechas
7. Filtrado y guardado de datos específicos
```

### Fase 3: Gestión de Metadatos

```
1. Inicialización del MetadataManager
2. Lectura de logs de procesos
3. Análisis de logs de almacenamiento
4. Consulta de duplicados
5. Análisis de linaje de campos
6. Generación de reportes
```

### Fase 4: Detección de Fechas Faltantes

```
1. Obtención de fechas faltantes (sin rango)
2. Obtención con fecha de inicio
3. Obtención con rango completo (inicio-fin)
```

### Fase 5: Gestión de Entidades Conocidas

```
1. Cambio al builder de entidades
2. Copia de archivo de entidades
3. Ingesta de entidades
4. Guardado en formato raw
5. Lectura y visualización
```

### Fase 6: Limpieza de Datos

```
1. Cambio al builder de limpieza
2. Carga de esquema y mapeo de regex
3. Aplicación de limpieza a DataFrame
4. Visualización de resultados
5. Comparación de valores originales vs limpios
```

---

## Componentes Principales

### 1. DeltaDataLayerBuilder

Constructor para crear instancias básicas de Delta Lake.

**Métodos de Configuración:**

```python
builder = (
    DeltaDataLayerBuilder()
    .protocol("file://")                              # Protocolo de acceso
    .base_path(base_path)                            # Ruta base
    .app_name("DeltaLakeExample")                    # Nombre de la aplicación
    .config("spark.sql.shuffle.partitions", "1")     # Configuración Spark
)
```

**Operaciones Disponibles:**

- `write_delta()`: Escribe DataFrames en formato Delta
- `read_delta()`: Lee datos desde Delta Lake
- `register_temp_table()`: Registra tabla temporal para SQL
- `sql()`: Ejecuta consultas SQL
- `start_session()`: Inicia sesión Spark
- `stop_session()`: Detiene sesión Spark

### 2. PortadaBuilder

Constructor especializado para datos de Portada (noticias históricas).

**Configuración:**

```python
builder = (
    PortadaBuilder(config)
    .protocol("file://")
    .base_path(base_path)
    .app_name("DeltaLakeExample")
    .project_name("default_portada")
    .config("spark.sql.shuffle.partitions", "4")
)
```

**Tipos de Construcción:**

- `builder.NEWS_TYPE`: Para datos de noticias
- `builder.KNOWN_ENTITIES_TYPE`: Para entidades conocidas
- `PortadaCleaning.__name__`: Para limpieza de datos

**Operaciones Específicas:**

```python
# Ingesta de datos
layer.ingest(data_path, user=user, local_path=json_path)

# Lectura con filtros
df = layer.read_raw_data(data_path, user=user, publication_name="DB", d="2[0-5]")

# Guardado de datos
layer.save_raw_data(data_path, data=data2, user=user)

# Fechas faltantes
missing_dates = layer.get_missing_dates_from_a_newspaper(
    data_path, 
    publication_name="db",
    start_date="1850-01-26",
    end_date="1850-02-03"
)
```

### 3. DataLakeMetadataManager

Gestor de metadatos y logs del sistema.

**Tipos de Logs:**

| Log | Descripción |
|-----|-------------|
| `process_log` | Registro de procesos ejecutados |
| `storage_log` | Registro de operaciones de almacenamiento |
| `duplicates_log` | Registro de duplicados detectados |
| `duplicates_records` | Registros duplicados completos |
| `field_lineage_log` | Linaje de transformaciones de campos |

**Uso:**

```python
metadata = DataLakeMetadataManager(layer.get_configuration())

# Leer log específico
df_meta = metadata.read_log("process_log")

# Filtrar por proceso
df_meta.filter("process = 'ingest.save_raw_data'").show()

# Usar expresiones regulares
df_meta.filter(df_meta.process.rlike("save_raw_data$")).show()
```

### 4. PortadaCleaning

Componente para limpieza y normalización de datos.

**Configuración:**

```python
layer = builder.build(PortadaCleaning.__name__)
layer.start_session()

# Cargar esquema y mapeo
with open(schema_path) as f:
    schema = json.load(f)

with open(regex_mapping_path) as f:
    regex_mapping = json.load(f)
```

**Operaciones de Limpieza:**

```python
# Aplicar limpieza completa
df = layer.use_schema(schema)\
          .use_mapping_to_clean_chars(regex_mapping)\
          .cleaning(df)

# Guardar valores originales
layer.save_original_values_of_ship_entries(df)

# Eliminar campos no aceptados
df = layer.use_schema(schema).prune_unaccepted_fields(df)
```

---

## Funciones y Métodos

### Operaciones de Escritura Delta

```python
# Forma 1: Con string simple
df = layer.write_delta(data_path, "vaixells", df=df)

# Forma 2: Con tupla
df = layer.write_delta((data_path, "vaixells2"), df=df)

# Forma 3: Con path completo
df = layer.write_delta(f"{data_path}/vaixells3", df=df)
```

### Operaciones de Lectura Delta

```python
# Forma 1: Con dos parámetros
df = layer.read_delta(data_path, "vaixells")

# Forma 2: Con tupla
df = layer.read_delta((data_path, "vaixells"))

# Forma 3: Con path completo
df = layer.read_delta(f"{data_path}/vaixells")
```

### Validación de Consistencia

```python
if df2_0.subtract(df2_1).count() == 0:
    print("Ok for df2_0 and df2_1")
else:
    print("KO for df2_0 and df2_1")
```

### Consultas SQL

```python
# Registrar tabla temporal
layer.register_temp_table(df, "vaixells")

# Ejecutar consulta
result = layer.sql("SELECT COUNT(*) AS total FROM vaixells")
result.show()
```

### Procesamiento de Fechas

```python
# Filtrar por rango de días
df = layer.read_raw_data(data_path, publication_name="DB", d="2[0-5]")

# Iterar por días específicos
for d in range(20, 26, 1):
    df = layer.read_raw_data(data_path, publication_name="DB", d=d)
    count = 0 if df is None else df.count()
```

### Análisis de Duplicados

```python
# Leer log de duplicados
df_dup = metadata.read_log("duplicates_log")

# Filtrar por publicación
df_dup.filter("lower(publication)='db'").show()

# Obtener duplicados de una fecha específica
df_dup_date = df_dup.filter("lower(publication)='db' AND date == '1850-01-22'").first()

# Leer registros duplicados
duplicates = metadata.read_log("duplicates_records")
duplicates.filter(df_dup_date.duplicates_filter)\
          .filter(duplicates.entry_id.isin(df_dup_date.duplicate_ids))\
          .show()
```

### Análisis de Linaje

```python
df_meta_lineage = metadata.read_log("field_lineage_log")
rows = df_meta_storage.take(5)

for row in rows:
    rows2 = df_meta_lineage.filter(
        df_meta_lineage.stored_log_id == row.log_id
    ).collect()
    
    for row2 in rows2:
        print(f"transformer_name: {row2.transformer_name}")
        print(f"dataframe_name: {row2.dataframe_name}")
        print(f"action: {row2.change_action}({row2.arguments})")
        print(f"involved_columns: {','.join(row2.involved_columns)}")
```

### Gestión de Entidades

```python
# Copiar e ingestar entidades
data, dest = layer.copy_ingested_entities(
    entity="pr",
    local_path=file_path,
    return_dest_path=True
)

# Guardar entidades
odata = {"source_path": dest, "data": data}
layer.save_raw_entities(entity="pr", data=odata)

# Leer entidades
df_entity = layer.read_raw_entities(entity="pr")
```

---

## Ejemplos de Uso

### Ejemplo 1: Crear y Consultar Delta Lake Básico

```python
# Configurar builder
builder = (
    DeltaDataLayerBuilder()
    .protocol("file://")
    .base_path("/path/to/delta")
    .app_name("MiApp")
)

# Crear layer
layer = builder.build()
layer.start_session()

# Crear datos
df = layer.spark.createDataFrame(
    [(1, "Barco A"), (2, "Barco B")],
    ["id", "nombre"]
)

# Guardar
layer.write_delta("datos", "barcos", df=df)

# Leer
df_leido = layer.read_delta("datos", "barcos")
df_leido.show()
```

### Ejemplo 2: Ingestar y Filtrar Datos

```python
# Configurar con archivo de configuración
with open("config.json") as f:
    config = json.load(f)

builder = PortadaBuilder(config)\
    .protocol("file://")\
    .base_path("/path/to/data")\
    .project_name("mi_proyecto")

layer = builder.build(builder.NEWS_TYPE)
layer.start_session()

# Ingestar
layer.ingest("ship_data", user="usuario", local_path="data.json")

# Leer con filtros
df = layer.read_raw_data(
    "ship_data",
    publication_name="DB",
    d="2[0-5]"  # Días 20-25
)

print(f"Total entradas: {df.count()}")
```

### Ejemplo 3: Analizar Metadatos

```python
metadata = DataLakeMetadataManager(layer.get_configuration())

# Ver procesos de ingesta
df_process = metadata.read_log("process_log")
df_process.filter("process = 'ingest.save_raw_data'").show()

# Ver duplicados
df_dup = metadata.read_log("duplicates_log")
df_dup.filter("lower(publication)='db'").show()

# Ver linaje
df_lineage = metadata.read_log("field_lineage_log")
df_lineage.show()
```

### Ejemplo 4: Limpiar Datos

```python
# Cargar configuraciones
with open("schema.json") as f:
    schema = json.load(f)

with open("mapping.json") as f:
    mapping = json.load(f)

# Configurar limpieza
layer = builder.build(PortadaCleaning.__name__)
layer.start_session()

# Aplicar limpieza
df_limpio = layer\
    .use_schema(schema)\
    .use_mapping_to_clean_chars(mapping)\
    .cleaning(df_original)

# Comparar resultados
df_limpio.select("campo_importante").show()
```

---

## Gestión de Errores

### Errores Comunes

1. **Rutas no encontradas**
   - Verificar que todas las rutas configuradas existan
   - Ajustar rutas según el sistema operativo

2. **Archivos de configuración faltantes**
   - Asegurar que existan: `schema.json`, `mapping_to_clean_chars.json`, `delta_data_layer_config.json`

3. **Problemas con Spark**
   - Verificar instalación de Java
   - Ajustar configuraciones de memoria si es necesario

4. **Errores de permisos**
   - Verificar permisos de escritura en `base_path`
   - Verificar permisos de lectura en rutas de origen

### Recomendaciones

- Siempre llamar a `start_session()` antes de operar con el layer
- Llamar a `stop_session()` al finalizar (aunque está comentado en el código)
- Verificar que el directorio base tenga suficiente espacio
- Revisar los logs para diagnóstico de problemas

---

## Notas Adicionales

### Comportamiento Destructivo

⚠️ **ADVERTENCIA**: El script elimina el directorio `base_path` en cada ejecución:

```python
if os.path.exists(base_path):
    shutil.rmtree(base_path)
```

Esto es útil para pruebas pero puede ser peligroso en producción.

### Optimizaciones de Spark

El número de particiones se configura según el tipo de operación:
- Operaciones básicas: 1 partición
- Operaciones de Portada: 4 particiones

### Formato de Fechas

Las fechas se manejan en formato timestamp (milisegundos desde epoch):

```python
ts = datetime.datetime.fromtimestamp(int(b_json["publication_date"]) / 1000)
```

### Expresiones Regulares en Filtros

Se pueden usar expresiones regulares para filtrar:

```python
# Filtrar días 20-25
df = layer.read_raw_data(data_path, d="2[0-5]")

# Filtrar procesos que terminan en "save_raw_data"
df_meta.filter(df_meta.process.rlike("save_raw_data$"))
```

---

## Conclusión

Este script proporciona un ejemplo completo de implementación de un sistema de gestión de datos basado en Delta Lake, incluyendo todas las fases desde la ingesta hasta la limpieza y análisis de datos. Es especialmente útil como referencia para proyectos que requieran:

- Almacenamiento versionado de datos
- Trazabilidad completa (linaje)
- Detección de duplicados
- Limpieza y normalización de datos históricos
- Gestión de metadatos robusta
