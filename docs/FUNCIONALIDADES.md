# Funcionalidades del Sistema PortAda

## 📋 Resumen Ejecutivo

Sistema completo de ingesta y análisis de datos históricos de periódicos usando la librería PortAda con Delta Lake.

---

## 🔄 BACKEND (FastAPI + PortAda)

### 1. Ingesta de Datos

#### 1.1 Carga de Datos de Extracción
- **Endpoint**: `POST /api/ingestion/upload`
- **Tipo**: `extraction`
- **Formato**: JSON
- **Proceso**:
  - Sube archivo JSON con datos extraídos de periódicos
  - Almacena temporalmente en `<ingestion_folder>/<periodico>/<user_name>/<fichero_temporal>`
  - Procesa asíncronamente con background tasks
  - Usa `layer_news.ingest(data_path_delta_lake, local_path=file_path)`
  - ⚠️ **IMPORTANTE**: El archivo fuente se elimina después de la ingesta

#### 1.2 Carga de Entidades Conocidas
- **Endpoint**: `POST /api/ingestion/upload`
- **Tipo**: `known_entities`
- **Formato**: YAML
- **Proceso**:
  - Sube archivo YAML con entidades conocidas
  - Usa `layer_entities.copy_ingested_entities()` y `save_raw_entities()`
  - Procesa asíncronamente

#### 1.3 Monitoreo de Ingesta
- **Endpoint**: `GET /api/ingestion/status/{task_id}`
- **Retorna**:
  - Estado: pending, processing, completed, failed
  - Progreso (0-100%)
  - Registros procesados
  - Mensajes de error si aplica

---

### 2. Análisis de Datos

#### 2.1 Fechas Faltantes
- **Endpoint**: `POST /api/analysis/missing-dates`
- **Parámetros**:
  - `publication_name`: Periódico (DB, DM, SM, etc.) - **OBLIGATORIO**
  - `query_mode`: "file" o "date_range"
  - **Modo File**:
    - `date_and_edition_list`: Contenido del archivo (YAML, JSON o lista)
  - **Modo Date Range**:
    - `start_date`: Fecha inicio (YYYY-MM-DD) - opcional
    - `end_date`: Fecha final (YYYY-MM-DD) - opcional
- **Librería PortAda**:
  ```python
  layer_news.get_missing_dates_from_a_newspaper(
      data_path,
      publication_name=publication_name
  )
  ```
- **Retorna**: Lista de fechas y ediciones faltantes con duración del gap

#### 2.2 Duplicados
- **Endpoint Master**: `POST /api/analysis/duplicates`
- **Parámetros** (todos opcionales):
  - `user_responsible`: Usuario responsable de la carga
  - `publication`: Periódico (db, dm, sm, etc.)
  - `start_date`: Fecha inicio
  - `end_date`: Fecha final
- **Librería PortAda**:
  ```python
  df_dup = metadata.read_log("duplicates_log")
  # Aplicar filtros
  df_dup = df_dup.filter(...)
  ```
- **Retorna**: Vista maestro con metadatos de duplicados por día/edición

- **Endpoint Detalle**: `GET /api/analysis/duplicates/{log_id}/details`
- **Parámetros**:
  - `duplicates_filter`: Filtro de la fila seleccionada
  - `duplicate_ids`: IDs de duplicados (comma-separated)
- **Librería PortAda**:
  ```python
  df_duplicates = metadata.read_log("duplicates_records")
  filtered = df_duplicates.filter(duplicates_filter)
                          .filter(df_duplicates.entry_id.isin(duplicate_ids))
  ```
- **Retorna**: Registros duplicados detallados

#### 2.3 Metadatos de Almacenamiento
- **Endpoint Master**: `POST /api/analysis/storage-metadata`
- **Parámetros** (opcionales):
  - `table_name`: Nombre de la tabla (ej: "ship_entries")
  - `process`: Nombre del proceso responsable
- **Filtro Automático**: `stage = 0` (siempre)
- **Librería PortAda**:
  ```python
  df_storage = metadata.read_log("storage_log")
  df_storage = df_storage.filter("stage == 0")
  # Aplicar filtros adicionales
  ```
- **Retorna**: Vista maestro con metadatos de almacenamiento

- **Endpoint Detalle**: `GET /api/analysis/storage-metadata/{log_id}/lineage`
- **Librería PortAda**:
  ```python
  df_lineage = metadata.read_log("field_lineage_log")
  df_lineage = df_lineage.filter(df_lineage.stored_log_id == log_id)
  ```
- **Retorna**: Linaje de campos (cambios realizados en el dataframe)

#### 2.4 Metadatos de Procesos
- **Endpoint**: `POST /api/analysis/process-metadata`
- **Parámetros**:
  - `process_name`: Nombre del proceso (opcional)
  - **Default**: Filtra por `process = 'ingest.save_raw_data'`
- **Filtro Automático**: `stage = 0` (siempre)
- **Librería PortAda**:
  ```python
  df_process = metadata.read_log("process_log")
  df_process = df_process.filter("process = 'ingest.save_raw_data'")
  ```
- **Retorna**: Metadatos de procesos ejecutados con errores si aplica

---

## 🎨 FRONTEND (React + TypeScript)

### 1. Vista de Ingesta (`/ingestion`)

#### Características Implementadas (según rectificación):
- ✅ **Dropdown de selección** de tipo de ingesta:
  - Extracción
  - Entidades Conocidas
- ✅ **Upload único** según tipo seleccionado (no simultáneo)
- ✅ **Validación de archivos**: .json, .yml, .yaml
- ✅ **Respuesta simplificada**: Mensaje de confirmación/error
- ✅ **Procesamiento asíncrono**: Background tasks
- ✅ **Estados de upload**:
  - idle: Sin archivo
  - uploading: Subiendo (con barra de progreso)
  - success: Completado
  - error: Error

#### Flujo de Usuario:
1. Selecciona tipo de ingesta (dropdown)
2. Arrastra/selecciona archivo
3. Ve progreso de upload
4. Recibe confirmación
5. Procesamiento continúa en background

---

### 2. Vista de Análisis

#### 2.1 Fechas Faltantes (`/analysis/missing-dates`)

**Características**:
- ✅ **Selección obligatoria** de periódico (DB, DM, SM)
- ✅ **Dos modos de consulta**:
  
  **Modo 1: Archivo**
  - Upload de archivo con lista de fechas/ediciones
  - Formatos soportados:
    - **YAML**: 
      ```yaml
      1850-10-01:
        - U
      1850-10-02:
        - M
        - T
      ```
    - **JSON**: 
      ```json
      [{"1850-10-01":["U"]}, {"1850-10-02":["M","T"]}]
      ```
    - **Lista**: Una fecha por línea
  
  **Modo 2: Rango de Fechas**
  - Fecha inicio (opcional)
  - Fecha final (opcional)
  - Formato: YYYY-MM-DD

- ✅ **Resultados con scroll**: Lista puede ser muy larga
- ✅ **Información del gap**: Duración de cada falta

---

#### 2.2 Duplicados (`/analysis/duplicates`)

**Características**:
- ✅ **Filtros opcionales**:
  - Usuario responsable
  - Periódico (db, dm, sm)
  - Rango de fechas
- ✅ **Vista Master-Detail**:
  - **Master**: Tabla con metadatos por día/edición
    - log_id
    - fecha
    - edición
    - publicación
    - usuario
    - cantidad de duplicados
  - **Detail**: Expandible por fila
    - Registros duplicados específicos
    - Contenido completo
    - Score de similitud

---

#### 2.3 Metadatos de Almacenamiento (`/analysis/storage-metadata`)

**Características**:
- ✅ **Filtros opcionales**:
  - Nombre de tabla (ej: "ship_entries")
  - Proceso
- ✅ **Filtro automático**: stage = 0
- ✅ **Vista Master-Detail**:
  - **Master**: Metadatos de almacenamiento
    - log_id
    - nombre de tabla
    - proceso
    - timestamp
    - cantidad de registros
  - **Detail**: Field Lineage
    - Nombre del campo
    - Operación realizada
    - Valor anterior
    - Valor nuevo
    - Timestamp

---

#### 2.4 Metadatos de Procesos (`/analysis/process-metadata`)

**Características**:
- ✅ **Filtro opcional**: Nombre del proceso
- ✅ **Filtro por defecto**: `process = 'ingest.save_raw_data'`
- ✅ **Filtro automático**: stage = 0
- ✅ **Información mostrada**:
  - log_id
  - proceso
  - timestamp
  - duración
  - estado (success/error)
  - registros procesados
  - mensaje de error (si aplica)

---

## 🔧 Integración PortAda

### Clases Utilizadas:
```python
from portada_data_layer import PortadaBuilder, DataLakeMetadataManager

# Builder
builder = (
    PortadaBuilder()
    .protocol("file://")
    .base_path(base_path)
    .app_name(app_name)
    .project_name(project_name)
)

# Capas de datos
layer_news = builder.build(builder.NEWS_TYPE)
layer_entities = builder.build(builder.KNOWN_ENTITIES_TYPE)

# Metadata Manager
metadata = DataLakeMetadataManager(layer_news.get_configuration())
```

### Logs Disponibles:
- `duplicates_log`: Metadatos de duplicados
- `duplicates_records`: Registros duplicados detallados
- `storage_log`: Metadatos de almacenamiento
- `field_lineage_log`: Linaje de campos
- `process_log`: Metadatos de procesos

---

## ✅ Cumplimiento de Rectificaciones

### Ingesta:
- ✅ Separación de procesos (dropdown en lugar de uploads simultáneos)
- ✅ Respuesta simplificada (asíncrona)
- ✅ Almacenamiento temporal en estructura de carpetas

### Análisis:
- ✅ Dropdown en sidebar con 4 tipos de análisis
- ✅ Pantallas individuales para cada consulta
- ✅ Vistas master-detail donde corresponde
- ✅ Filtros opcionales implementados
- ✅ Filtros automáticos (stage = 0) aplicados

---

## 🚀 Estado de Implementación

**Backend**: ✅ 100% Funcional
- Todos los endpoints implementados
- Integración con PortAda v0.1.3
- Procesamiento asíncrono
- Validaciones y manejo de errores

**Frontend**: ✅ 100% Implementado
- Todas las vistas según especificación
- UI/UX moderna y responsive
- Manejo de estados y errores
- Integración con API backend

**Documentación**: ✅ Completa
- API docs auto-generada (Swagger/ReDoc)
- Guías de integración
- Verificación de endpoints

---

## 📝 Notas Importantes

1. **Archivos de ingesta**: Se eliminan después del procesamiento (comportamiento de PortAda)
2. **Procesamiento asíncrono**: Usar endpoint de status para monitorear
3. **Python 3.12+**: Requerido por la librería PortAda
4. **Java**: Necesario para PySpark (dependencia de PortAda)
5. **Delta Lake**: Formato de almacenamiento subyacente
