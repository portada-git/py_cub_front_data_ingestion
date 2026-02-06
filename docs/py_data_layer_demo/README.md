# Delta Data Layer - Portada

Sistema de gestión de datos basado en Delta Lake para el procesamiento y análisis de datos de embarcaciones históricas.

## Descripción

Este proyecto implementa una capa de datos utilizando Delta Lake y Apache Spark para la ingesta, procesamiento y limpieza de datos relacionados con registros históricos de embarcaciones. El sistema incluye funcionalidades para:

- Gestión de datos en formato Delta Lake
- Ingesta de datos desde archivos JSON
- Limpieza y transformación de datos
- Gestión de metadatos y linaje de datos
- Detección de duplicados
- Gestión de entidades conocidas

## Requisitos

### Dependencias del Sistema

- Python 3.8 o superior
- Java 8 o superior (requerido por Apache Spark)

### Dependencias de Python

```
pyspark==3.5.3
delta-spark==3.2.1
hdfs==2.7.0
py4j
pyyaml
xmltodict
```

## Instalación

1. Clona el repositorio:
```bash
git clone [url-del-repositorio]
cd [nombre-del-directorio]
```

2. Instala las dependencias:
```bash
pip install -r requirements.txt
```

3. Configura las rutas en el archivo `main.py` según tu sistema operativo (macOS o Linux).

## Configuración

El script detecta automáticamente el sistema operativo y configura las rutas correspondientes:

### macOS (Darwin)
- Base path: `/Users/josepcanellas/Dropbox/feinesJordi/implementacio/delta_lake/delta_test`
- JSON path: `/Users/josepcanellas/Dropbox/feinesJordi/dades/resultats/prova`

### Linux
- Base path: `/home/josep/Dropbox/feinesJordi/implementacio/delta_lake/delta_test`
- JSON path: `/home/josep/Dropbox/feinesJordi/dades/resultats/prova`

**Importante:** Debes modificar estas rutas en el archivo `main.py` para que coincidan con tu estructura de directorios.

## Archivos de Configuración Necesarios

El sistema requiere los siguientes archivos de configuración:

1. `schema.json` - Define el esquema de datos
2. `mapping_to_clean_chars.json` - Mapeo para limpieza de caracteres
3. `delta_data_layer_config.json` - Configuración general del sistema

## Uso

### Ejecución Básica

```bash
python main.py
```

### Funcionalidades Principales

#### 1. Creación de Delta Lake Básico

El script crea un Delta Lake y realiza operaciones básicas de escritura y lectura:

```python
builder = (
    DeltaDataLayerBuilder()
    .protocol("file://")
    .base_path(base_path)
    .app_name("DeltaLakeExample")
    .config("spark.sql.shuffle.partitions", "1")
)
layer = builder.build()
layer.start_session()
```

#### 2. Ingesta de Datos

Procesa archivos JSON con datos de embarcaciones:

```python
layer.ingest(data_path, user=user, local_path=json_path)
```

#### 3. Lectura de Datos

Lee datos filtrados por criterios específicos:

```python
df = layer.read_raw_data(data_path, user=user, publication_name="DB", d="2[0-5]")
```

#### 4. Gestión de Metadatos

Consulta logs de procesos, almacenamiento y duplicados:

```python
metadata = DataLakeMetadataManager(layer.get_configuration())
df_meta = metadata.read_log("process_log")
df_dup = metadata.read_log("duplicates_log")
```

#### 5. Limpieza de Datos

Aplica esquemas y reglas de limpieza:

```python
layer = builder.build(PortadaCleaning.__name__)
df = layer.use_schema(schema).use_mapping_to_clean_chars(regex_mapping).cleaning(df)
```

## Estructura del Proyecto

```
.
├── main.py                 # Script principal
├── requirements.txt        # Dependencias del proyecto
└── README.md              # Este archivo
```

## Características del Sistema

### Gestión de Duplicados
El sistema detecta y registra entradas duplicadas, permitiendo su consulta y análisis.

### Linaje de Datos
Mantiene un registro completo de las transformaciones aplicadas a los datos, incluyendo:
- Nombre del transformador
- Acción realizada
- Argumentos utilizados
- Columnas involucradas

### Detección de Fechas Faltantes
Identifica fechas faltantes en las publicaciones de periódicos históricos.

### Gestión de Entidades Conocidas
Permite la ingesta y gestión de entidades conocidas (como puertos, personas, etc.).

## Salida del Sistema

El script genera información detallada sobre:

- Conteo de entradas procesadas
- Esquemas de datos
- Logs de procesos y almacenamiento
- Registros de duplicados
- Linaje de campos
- Fechas faltantes en publicaciones

## Notas Importantes

1. El sistema elimina el directorio base (`base_path`) en cada ejecución para empezar con datos limpios.
2. Los datos se procesan utilizando Apache Spark con configuraciones optimizadas.
3. El sistema está diseñado para trabajar con datos históricos de embarcaciones en formato JSON.
4. Se recomienda revisar y ajustar las configuraciones de Spark según los recursos disponibles.

## Solución de Problemas

### Error: Java no encontrado
Asegúrate de tener Java 8 o superior instalado y configurado en tu PATH.

### Error: Rutas no encontradas
Verifica que todas las rutas configuradas en `main.py` existan en tu sistema.

### Error: Archivos de configuración faltantes
Asegúrate de tener los archivos `schema.json`, `mapping_to_clean_chars.json` y `delta_data_layer_config.json` en las rutas especificadas.

## Licencia

[Especificar licencia del proyecto]

## Contacto

[Información de contacto del equipo]
