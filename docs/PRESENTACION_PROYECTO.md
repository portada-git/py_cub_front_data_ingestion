# PortAda - Sistema de Ingestión y Análisis de Datos Históricos

## 📋 Índice

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [¿Qué es PortAda?](#qué-es-portada)
3. [Contexto del Proyecto](#contexto-del-proyecto)
4. [Arquitectura del Sistema](#arquitectura-del-sistema)
5. [Funcionalidades Principales](#funcionalidades-principales)
6. [Entidades Conocidas](#entidades-conocidas)
7. [Flujo de Trabajo](#flujo-de-trabajo)
8. [Tecnologías Utilizadas](#tecnologías-utilizadas)
9. [Casos de Uso](#casos-de-uso)
10. [Resultados y Métricas](#resultados-y-métricas)

---

## 1. Resumen Ejecutivo

**PortAda Ingestion** es una plataforma web moderna para la ingestión, procesamiento y análisis de datos históricos de periódicos del siglo XIX y principios del XX. El sistema permite digitalizar y analizar información sobre movimientos marítimos, comercio y eventos históricos registrados en publicaciones de la época.

### Objetivos Principales

- ✅ **Digitalización**: Convertir datos históricos en formato digital estructurado
- ✅ **Análisis**: Identificar patrones, duplicados y datos faltantes
- ✅ **Accesibilidad**: Proporcionar una interfaz intuitiva para investigadores
- ✅ **Escalabilidad**: Procesar grandes volúmenes de datos históricos

### Valor del Proyecto

- 📚 **Preservación histórica**: Digitalización de información valiosa
- 🔍 **Investigación**: Facilita estudios históricos y económicos
- 📊 **Análisis de datos**: Identifica patrones en el comercio marítimo histórico
- 🌐 **Acceso universal**: Datos históricos disponibles para investigadores

---

## 2. ¿Qué es PortAda?

PortAda es un sistema completo que consta de:

### 2.1 Frontend (Interfaz de Usuario)
- Aplicación web moderna construida con React y TypeScript
- Interfaz intuitiva con diseño responsive
- Visualizaciones interactivas de datos
- Monitoreo en tiempo real de procesos

### 2.2 Backend (Servidor)
- API REST construida con FastAPI (Python)
- Procesamiento asíncrono de archivos
- Integración con la librería `portada-data-layer`
- Almacenamiento en Delta Lake

### 2.3 Librería PortAda Data Layer
- Capa de abstracción para Delta Lake
- Gestión de metadatos
- Detección de duplicados
- Análisis de datos históricos

---

## 3. Contexto del Proyecto

### 3.1 Fuentes de Datos

El sistema procesa datos extraídos de periódicos históricos como:

- **Diario Mercantil (DM)** - La Habana, Cuba (1852-1914)
- **Diario de Barcelona (DB)** - Barcelona, España
- **Semanario Mercantil (SM)** - Publicaciones semanales

### 3.2 Tipos de Información

Los periódicos históricos contienen:

- 🚢 **Movimientos de embarcaciones**: Llegadas y salidas de puertos
- 📦 **Carga transportada**: Productos, cantidades, origen/destino
- 👥 **Pasajeros**: Nombres, procedencias, destinos
- 🏢 **Comerciantes**: Consignatarios, capitanes, armadores
- 📅 **Fechas**: Fechas de publicación, fechas de eventos

### 3.3 Desafíos

- **Volumen**: Miles de entradas por año
- **Calidad**: Datos extraídos con OCR pueden tener errores
- **Duplicados**: Misma información publicada en múltiples ediciones
- **Fechas faltantes**: Periódicos no publicados algunos días
- **Entidades**: Nombres de personas, lugares y embarcaciones variables

---

## 4. Arquitectura del Sistema

### 4.1 Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                      USUARIO                                 │
│                    (Investigador)                            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   FRONTEND (React)                           │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐  │
│  │Dashboard │Ingestión │ Análisis │ Procesos │Metadatos │  │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘  │
│                    Puerto: 5173                              │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/REST API
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   BACKEND (FastAPI)                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              API Routes                               │  │
│  │  /ingestion  /analysis  /health  /status             │  │
│  └────────────────────┬─────────────────────────────────┘  │
│                       │                                      │
│  ┌────────────────────▼─────────────────────────────────┐  │
│  │           Services Layer                              │  │
│  │  • PortAda Service  • Task Service                   │  │
│  │  • File Service     • Storage Service                │  │
│  └────────────────────┬─────────────────────────────────┘  │
│                    Puerto: 8002                              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│            PORTADA DATA LAYER (Librería Python)              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  • News Layer (Datos de extracción)                  │  │
│  │  • Entities Layer (Entidades conocidas)             │  │
│  │  • Metadata Manager (Metadatos)                      │  │
│  └────────────────────┬─────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   DELTA LAKE (Almacenamiento)                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  📁 ship_entries/                                     │  │
│  │     └── publication_name=DM/                         │  │
│  │         └── publication_date=1914-01-02/             │  │
│  │             └── edition=U/                           │  │
│  │                 └── data.parquet                     │  │
│  │                                                       │  │
│  │  📁 known_entities/                                   │  │
│  │  📁 metadata/                                         │  │
│  │     ├── duplicates_log/                              │  │
│  │     ├── field_lineage_log/                           │  │
│  │     └── process_log/                                 │  │
│  └──────────────────────────────────────────────────────┘  │
│                  Formato: Parquet + Delta                    │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Componentes Principales

#### Frontend (React + TypeScript)
- **Vistas**: Dashboard, Ingestión, Análisis, Procesos
- **Componentes**: Formularios, tablas, gráficos, notificaciones
- **Estado**: Zustand para gestión de estado global
- **Estilos**: Tailwind CSS para diseño responsive

#### Backend (FastAPI + Python)
- **API REST**: Endpoints para ingestión y análisis
- **Procesamiento asíncrono**: Tareas en background
- **Validación**: Pydantic para validación de datos
- **Logging**: Sistema de logs detallado

#### Delta Lake
- **Formato**: Parquet con transacciones ACID
- **Particionamiento**: Por publicación, fecha y edición
- **Metadatos**: Logs de duplicados, linaje de campos, procesos

---

## 5. Funcionalidades Principales

### 5.1 Ingestión de Datos

#### 5.1.1 Datos de Extracción (JSON)

**Propósito**: Cargar datos extraídos de periódicos históricos

**Formato de entrada**:
```json
[
  {
    "publication_name": "DM",
    "publication_date": "1914-01-02",
    "publication_edition": "U",
    "entry_type": "ship_arrival",
    "ship_name": "Vapor Español",
    "captain": "Juan Pérez",
    "origin_port": "Cádiz",
    "cargo": "Vino, aceite",
    "passengers": 45,
    "parsed_text": "Llegó el vapor español..."
  }
]
```

**Proceso**:
1. Usuario selecciona archivo JSON
2. Sistema valida formato y estructura
3. Archivo se procesa en background
4. Datos se organizan en Delta Lake por publicación/fecha/edición
5. Se detectan y registran duplicados automáticamente

**Resultado**: Datos estructurados listos para análisis

#### 5.1.2 Entidades Conocidas (YAML)

**Propósito**: Cargar diccionarios de referencia para normalización

**Formato de entrada**:
```yaml
ships:
  - name: "Vapor Español"
    aliases: ["V. Español", "Vap. Español"]
    type: "steamship"
    
persons:
  - name: "Juan Pérez"
    role: "captain"
    nationality: "Spanish"
    
places:
  - name: "Cádiz"
    country: "Spain"
    type: "port"
```

**Uso**: Normalizar nombres variables en los datos históricos

---

### 5.2 Análisis de Datos

#### 5.2.1 Fechas Faltantes

**Propósito**: Identificar días sin publicación o datos faltantes

**Funcionalidad**:
- Analiza el rango completo de fechas de una publicación
- Identifica días sin entradas
- Calcula duración de gaps (vacíos)
- Distingue por edición (Mañana, Tarde, Única)

**Ejemplo de resultado**:
```
Publicación: DM (Diario Mercantil)
Período: 1914-01-01 a 1914-12-31
Fechas faltantes: 23 días
- 1914-01-15 (Edición U) - Gap: 1 día
- 1914-02-20 (Edición U) - Gap: 3 días
- 1914-12-25 (Edición U) - Gap: 1 día (Navidad)
```

**Valor**: Identificar periodos sin datos para investigación adicional

#### 5.2.2 Duplicados

**Propósito**: Detectar entradas duplicadas entre ediciones

**Detección automática**:
- Compara entradas por fecha y contenido
- Identifica duplicados exactos y similares
- Registra metadata de duplicación
- Permite revisión manual

**Visualización**:
```
┌─────────────────────────────────────────────────────────┐
│ Fecha: 1914-01-02 | Edición: U | Duplicados: 93        │
├─────────────────────────────────────────────────────────┤
│ IDs duplicados: [uuid1, uuid2, uuid3, ...]             │
│ Filtro aplicado: Sin filtro                            │
│ Subido por: api_user                                   │
└─────────────────────────────────────────────────────────┘
```

**Valor**: Evitar conteo doble en análisis estadísticos

#### 5.2.3 Entradas Diarias

**Propósito**: Visualizar distribución temporal de datos

**Métricas**:
- Total de entradas por día
- Promedio de entradas por día
- Días con más/menos actividad
- Tendencias temporales

**Visualización**:
```
Estadísticas:
├─ Total Entradas: 3,499
├─ Días con Datos: 588
├─ Promedio/Día: 6
├─ Máximo: 15 entradas
└─ Mínimo: 1 entrada

Gráfico de barras horizontal:
1914-01-02 ████████████████ 12
1914-01-03 ██████████ 8
1914-01-04 ████████████████████ 15
...
```

**Valor**: Identificar patrones de actividad comercial

#### 5.2.4 Metadatos de Almacenamiento

**Propósito**: Rastrear linaje y transformaciones de datos

**Información disponible**:
- Tablas en Delta Lake
- Campos y sus transformaciones
- Procesos responsables
- Fechas de creación/modificación

**Ejemplo**:
```
Tabla: ship_entries
├─ Campo: ship_name
│  └─ Linaje: raw_text → parsed_text → ship_name
├─ Campo: publication_date
│  └─ Linaje: date_string → normalized_date → publication_date
└─ Proceso: data_extraction_v2
   └─ Fecha: 2026-01-27 00:45:23
```

**Valor**: Auditoría y trazabilidad de datos

#### 5.2.5 Metadatos de Proceso

**Propósito**: Monitorear ejecución de procesos

**Información**:
- Nombre del proceso
- Estado (Completado, Fallido, En ejecución)
- Registros procesados
- Tiempo de inicio/fin
- Errores y warnings

**Ejemplo**:
```
Proceso: data_extraction
├─ Estado: Completado ✓
├─ Registros: 71
├─ Inicio: 2026-01-27 00:37:01
├─ Fin: 2026-01-27 00:38:15
└─ Duración: 1m 14s
```

**Valor**: Debugging y optimización de procesos

---

## 6. Entidades Conocidas

### 6.1 ¿Qué son las Entidades Conocidas?

Las **entidades conocidas** son diccionarios de referencia que contienen información normalizada sobre:

- 🚢 **Embarcaciones**: Nombres de barcos, tipos, banderas
- 👥 **Personas**: Capitanes, consignatarios, pasajeros
- 🌍 **Lugares**: Puertos, ciudades, países
- 🏢 **Organizaciones**: Compañías navieras, casas comerciales
- 📦 **Productos**: Mercancías, unidades de medida

### 6.2 ¿Por qué son Importantes?

#### Problema: Variabilidad en Datos Históricos

Los periódicos históricos tienen inconsistencias:

```
Mismo barco, diferentes nombres:
- "Vapor Español"
- "V. Español"
- "Vap. Español"
- "El Vapor Español"

Mismo puerto, diferentes escrituras:
- "Cádiz"
- "Cadiz"
- "Puerto de Cádiz"
```

#### Solución: Normalización con Entidades Conocidas

```yaml
# Archivo: known_entities.yaml
ships:
  - canonical_name: "Vapor Español"
    aliases:
      - "V. Español"
      - "Vap. Español"
      - "El Vapor Español"
    type: "steamship"
    flag: "Spanish"
    
ports:
  - canonical_name: "Cádiz"
    aliases:
      - "Cadiz"
      - "Puerto de Cádiz"
    country: "Spain"
    coordinates: [36.5297, -6.2920]
```

### 6.3 Proceso de Uso

1. **Carga**: Investigador sube archivo YAML con entidades
2. **Almacenamiento**: Sistema guarda en Delta Lake
3. **Normalización**: Durante ingestión, nombres se normalizan
4. **Consulta**: Análisis usa nombres canónicos

### 6.4 Beneficios

✅ **Consistencia**: Todos los análisis usan los mismos nombres
✅ **Búsqueda**: Encontrar todas las menciones de una entidad
✅ **Estadísticas**: Conteos precisos sin duplicados por variación
✅ **Enriquecimiento**: Agregar información adicional (tipo, país, etc.)

### 6.5 Ejemplo de Análisis

**Sin entidades conocidas**:
```
Embarcaciones más frecuentes:
1. Vapor Español: 45 menciones
2. V. Español: 23 menciones
3. Vap. Español: 12 menciones
Total: 3 embarcaciones diferentes (?)
```

**Con entidades conocidas**:
```
Embarcaciones más frecuentes:
1. Vapor Español: 80 menciones
   (incluye: V. Español, Vap. Español, El Vapor Español)
Total: 1 embarcación (correcto)
```

---

## 7. Flujo de Trabajo

### 7.1 Flujo Completo de Ingestión y Análisis

```
┌─────────────────────────────────────────────────────────────┐
│ FASE 1: PREPARACIÓN DE DATOS                                │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
    ┌────────────────────────────────────────┐
    │ 1. Extracción de Periódicos            │
    │    - OCR de imágenes históricas        │
    │    - Parsing de texto                  │
    │    - Generación de JSON                │
    └────────────────┬───────────────────────┘
                     │
                     ▼
    ┌────────────────────────────────────────┐
    │ 2. Preparación de Entidades            │
    │    - Investigación de nombres          │
    │    - Creación de diccionarios          │
    │    - Generación de YAML                │
    └────────────────┬───────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ FASE 2: CARGA EN PORTADA                                    │
└─────────────────────────────────────────────────────────────┘
                     │
                     ▼
    ┌────────────────────────────────────────┐
    │ 3. Carga de Entidades Conocidas       │
    │    - Upload de archivo YAML            │
    │    - Validación de formato             │
    │    - Almacenamiento en Delta Lake      │
    └────────────────┬───────────────────────┘
                     │
                     ▼
    ┌────────────────────────────────────────┐
    │ 4. Carga de Datos de Extracción       │
    │    - Upload de archivo JSON            │
    │    - Validación de estructura          │
    │    - Procesamiento asíncrono           │
    │    - Detección de duplicados           │
    │    - Normalización con entidades       │
    │    - Particionamiento por fecha        │
    └────────────────┬───────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ FASE 3: ANÁLISIS Y CONSULTAS                                │
└─────────────────────────────────────────────────────────────┘
                     │
                     ▼
    ┌────────────────────────────────────────┐
    │ 5. Análisis de Calidad                 │
    │    - Identificar fechas faltantes      │
    │    - Revisar duplicados                │
    │    - Verificar completitud             │
    └────────────────┬───────────────────────┘
                     │
                     ▼
    ┌────────────────────────────────────────┐
    │ 6. Análisis Estadístico                │
    │    - Entradas por día                  │
    │    - Distribución temporal             │
    │    - Patrones de actividad             │
    └────────────────┬───────────────────────┘
                     │
                     ▼
    ┌────────────────────────────────────────┐
    │ 7. Exportación de Resultados           │
    │    - Descarga de CSV                   │
    │    - Generación de reportes            │
    │    - Visualizaciones                   │
    └────────────────────────────────────────┘
```

### 7.2 Ejemplo Práctico: Procesamiento de Diario Mercantil 1914

#### Paso 1: Preparación
```bash
# Archivo: 1914_traversing_converted.json
# Contenido: 71 entradas de llegadas de barcos
# Fecha: 1914-01-02
# Publicación: DM (Diario Mercantil)
```

#### Paso 2: Carga de Entidades
```yaml
# Archivo: dm_entities.yaml
ships:
  - name: "Vapor Español"
    type: "steamship"
ports:
  - name: "Cádiz"
    country: "Spain"
```

#### Paso 3: Ingestión
```
1. Usuario accede a PortAda
2. Selecciona "Ingestión" → "Datos de Extracción"
3. Sube archivo 1914_traversing_converted.json
4. Sistema procesa en ~60 segundos
5. Resultado: 71 registros ingresados
```

#### Paso 4: Verificación
```
1. Usuario accede a "Análisis" → "Entradas Diarias"
2. Selecciona publicación "DM"
3. Ve: 1914-01-02 → 71 entradas
4. Exporta CSV para análisis externo
```

#### Paso 5: Análisis de Calidad
```
1. Usuario accede a "Análisis" → "Duplicados"
2. Ve: 93 duplicados detectados en 1914-01-02
3. Revisa IDs para investigación
4. Documenta hallazgos
```

---

## 8. Tecnologías Utilizadas

### 8.1 Frontend

| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| **React** | 18.x | Framework UI |
| **TypeScript** | 5.x | Tipado estático |
| **Vite** | 5.x | Build tool |
| **Tailwind CSS** | 3.x | Estilos |
| **Zustand** | 4.x | Estado global |
| **React Router** | 6.x | Navegación |
| **Lucide React** | - | Iconos |
| **i18next** | - | Internacionalización |

### 8.2 Backend

| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| **Python** | 3.11+ | Lenguaje base |
| **FastAPI** | 0.104+ | Framework web |
| **Pydantic** | 2.x | Validación |
| **Uvicorn** | 0.24+ | Servidor ASGI |
| **UV** | - | Gestor de paquetes |
| **PySpark** | 3.x | Procesamiento |
| **Delta Lake** | 3.x | Almacenamiento |

### 8.3 Infraestructura

| Tecnología | Propósito |
|------------|-----------|
| **Docker** | Containerización |
| **Docker Compose** | Orquestación |
| **Delta Lake** | Data Lake |
| **Parquet** | Formato de datos |

### 8.4 Librerías Clave

#### portada-data-layer
```python
# Librería principal para interacción con Delta Lake
from portada_data_layer import PortadaBuilder, DataLakeMetadataManager

# Inicialización
builder = PortadaBuilder()
    .protocol("file://")
    .base_path("/path/to/data")
    .app_name("portada_ingestion")
    .project_name("portada")

# Capas disponibles
news_layer = builder.build("news")        # Datos de extracción
entities_layer = builder.build("known_entities")  # Entidades
```

---

## 9. Casos de Uso

### 9.1 Investigación Histórica

**Caso**: Estudiar el comercio marítimo entre España y Cuba en 1914

**Proceso**:
1. Cargar datos del Diario Mercantil de 1914
2. Analizar entradas diarias para identificar patrones
3. Identificar embarcaciones más frecuentes
4. Analizar rutas comerciales (origen/destino)
5. Exportar datos para análisis estadístico

**Resultado**: Comprensión del volumen y naturaleza del comercio

### 9.2 Análisis Económico

**Caso**: Estudiar el impacto de eventos históricos en el comercio

**Proceso**:
1. Cargar datos de múltiples años (1852-1914)
2. Identificar fechas faltantes (posibles cierres de puerto)
3. Analizar variaciones en entradas diarias
4. Correlacionar con eventos históricos conocidos
5. Generar visualizaciones temporales

**Resultado**: Identificación de patrones económicos históricos

### 9.3 Genealogía y Migración

**Caso**: Rastrear movimientos de pasajeros históricos

**Proceso**:
1. Cargar entidades conocidas con nombres de personas
2. Buscar menciones en datos de extracción
3. Identificar rutas de viaje
4. Documentar fechas y embarcaciones
5. Exportar información para investigación genealógica

**Resultado**: Trazabilidad de movimientos migratorios

### 9.4 Historia Naval

**Caso**: Catalogar embarcaciones del siglo XIX

**Proceso**:
1. Cargar entidades conocidas de embarcaciones
2. Analizar frecuencia de apariciones
3. Identificar rutas habituales
4. Documentar capitanes y armadores
5. Crear catálogo histórico

**Resultado**: Base de datos de embarcaciones históricas

---

## 10. Resultados y Métricas

### 10.1 Datos Procesados (Ejemplo Real)

**Publicación**: Diario Mercantil (DM)
**Período**: 1852-1914
**Archivos procesados**: 42 archivos JSON

```
📊 Estadísticas Generales:
├─ Total de entradas: 3,499
├─ Días con datos: 588
├─ Promedio por día: 6 entradas
├─ Máximo en un día: 15 entradas
└─ Mínimo en un día: 1 entrada

🔍 Análisis de Calidad:
├─ Duplicados detectados: 12 registros
├─ Fechas faltantes: Identificadas automáticamente
└─ Entidades normalizadas: Sí

⚡ Rendimiento:
├─ Tiempo de ingestión: ~60s por archivo (71 registros)
├─ Consultas: < 2 segundos
└─ Exportación CSV: Instantánea
```

### 10.2 Capacidades del Sistema

| Métrica | Valor |
|---------|-------|
| **Archivos procesados** | 42+ archivos |
| **Registros totales** | 3,499+ entradas |
| **Período cubierto** | 1852-1914 (62 años) |
| **Publicaciones** | DM, DB, SM |
| **Tipos de análisis** | 6 diferentes |
| **Formatos soportados** | JSON, YAML |
| **Tiempo de respuesta** | < 2 segundos |
| **Disponibilidad** | 24/7 |

### 10.3 Mejoras Implementadas

#### Interfaz de Usuario
- ✅ Logo integrado en login y sidebar
- ✅ Visualizaciones mejoradas (gráficos de barras)
- ✅ Estadísticas en tarjetas coloridas
- ✅ Exportación a CSV
- ✅ Filtros avanzados
- ✅ Notificaciones en tiempo real

#### Backend
- ✅ Procesamiento asíncrono
- ✅ Detección automática de duplicados
- ✅ Validación robusta de datos
- ✅ Logging detallado
- ✅ Manejo de errores mejorado
- ✅ API REST completa

#### Análisis
- ✅ Fechas faltantes con gaps
- ✅ Duplicados con metadata
- ✅ Entradas diarias con gráficos
- ✅ Metadatos de almacenamiento
- ✅ Metadatos de proceso
- ✅ Entidades conocidas

---

## 11. Roadmap y Futuras Mejoras

### 11.1 Corto Plazo (1-3 meses)

- 🔄 **Optimización de rendimiento**: Reducir tiempo de ingestión de 60s a 2-3s
- 📊 **Más visualizaciones**: Gráficos de líneas, mapas de calor
- 🔍 **Búsqueda avanzada**: Búsqueda full-text en entradas
- 📱 **App móvil**: Versión responsive mejorada

### 11.2 Medio Plazo (3-6 meses)

- 🤖 **Machine Learning**: Detección automática de entidades
- 🌐 **API pública**: Acceso programático para investigadores
- 📚 **Documentación**: Guías de usuario detalladas
- 🔐 **Autenticación avanzada**: OAuth, roles y permisos

### 11.3 Largo Plazo (6-12 meses)

- 🗺️ **Visualización geográfica**: Mapas interactivos de rutas
- 📈 **Análisis predictivo**: Tendencias y patrones
- 🔗 **Integración con otros sistemas**: APIs externas
- 🌍 **Multilenguaje**: Soporte para más idiomas

---

## 12. Conclusiones

### 12.1 Logros Principales

✅ **Sistema funcional**: Plataforma completa de ingestión y análisis
✅ **Datos reales**: Procesamiento de 3,499+ entradas históricas
✅ **Interfaz moderna**: UI intuitiva y responsive
✅ **Análisis completo**: 6 tipos de análisis diferentes
✅ **Calidad de datos**: Detección automática de duplicados
✅ **Escalabilidad**: Arquitectura preparada para crecimiento

### 12.2 Valor del Proyecto

📚 **Académico**: Facilita investigación histórica
💡 **Tecnológico**: Stack moderno y escalable
🔍 **Analítico**: Insights sobre datos históricos
🌐 **Accesible**: Interfaz web fácil de usar

### 12.3 Impacto

El sistema PortAda democratiza el acceso a datos históricos, permitiendo que investigadores, estudiantes y entusiastas de la historia puedan:

- Explorar datos de periódicos del siglo XIX
- Identificar patrones en el comercio marítimo
- Rastrear movimientos de personas y mercancías
- Contribuir al conocimiento histórico colectivo

---

## 13. Recursos Adicionales

### 13.1 Documentación Técnica

- 📄 `README.md` - Guía de inicio rápido
- 📄 `DIAGNOSTICO_RENDIMIENTO.md` - Análisis de performance
- 📄 `METADATA_VIEWS_FIX.md` - Correcciones implementadas
- 📄 `LOGO_INTEGRATION.md` - Integración de branding

### 13.2 Acceso al Sistema

- 🌐 **Frontend**: http://localhost:5173
- 🔌 **Backend API**: http://localhost:8002
- 📚 **API Docs**: http://localhost:8002/api/docs

### 13.3 Repositorio

```bash
# Clonar repositorio
git clone [repository-url]

# Iniciar con Docker
./docker-run.sh dev

# Acceder a la aplicación
open http://localhost:5173
```

### 13.4 Contacto y Soporte

Para preguntas, sugerencias o reportar problemas:
- 📧 Email: [contact-email]
- 💬 Issues: [github-issues-url]
- 📖 Wiki: [wiki-url]

---

## 14. Glosario de Términos

| Término | Definición |
|---------|------------|
| **Delta Lake** | Sistema de almacenamiento con transacciones ACID sobre Parquet |
| **Entidad Conocida** | Referencia normalizada de persona, lugar u objeto |
| **Extracción** | Proceso de obtener datos estructurados de periódicos |
| **Gap** | Período sin datos o publicaciones |
| **Ingestión** | Proceso de cargar datos en el sistema |
| **Linaje** | Historial de transformaciones de un campo de datos |
| **Metadata** | Datos sobre los datos (origen, transformaciones, etc.) |
| **Normalización** | Proceso de estandarizar nombres variables |
| **OCR** | Reconocimiento Óptico de Caracteres |
| **Parquet** | Formato columnar eficiente para big data |
| **Particionamiento** | División de datos por criterios (fecha, publicación) |

---

## 15. Apéndices

### Apéndice A: Estructura de Datos JSON

```json
{
  "publication_name": "DM",
  "publication_date": "1914-01-02",
  "publication_edition": "U",
  "entry_type": "ship_arrival",
  "ship_name": "Vapor Español",
  "ship_flag": "Spanish",
  "captain": "Juan Pérez",
  "origin_port": "Cádiz",
  "destination_port": "La Habana",
  "cargo": "Vino, aceite, conservas",
  "cargo_quantity": "500 toneladas",
  "passengers": 45,
  "consignee": "García y Cía",
  "parsed_text": "Llegó ayer el vapor español...",
  "raw_text": "Original text from newspaper..."
}
```

### Apéndice B: Estructura de Entidades YAML

```yaml
entities:
  ships:
    - canonical_name: "Vapor Español"
      aliases: ["V. Español", "Vap. Español"]
      type: "steamship"
      flag: "Spanish"
      tonnage: 2500
      
  persons:
    - canonical_name: "Juan Pérez"
      role: "captain"
      nationality: "Spanish"
      active_years: [1900, 1920]
      
  ports:
    - canonical_name: "Cádiz"
      country: "Spain"
      region: "Andalucía"
      coordinates: [36.5297, -6.2920]
      type: "seaport"
```

### Apéndice C: Comandos Útiles

```bash
# Desarrollo
./docker-run.sh dev          # Iniciar desarrollo
./docker-run.sh logs         # Ver logs
./docker-run.sh stop         # Detener servicios

# Producción
./docker-run.sh prod         # Iniciar producción
./docker-run.sh build        # Construir imágenes

# Limpieza
./docker-run.sh clean        # Limpiar todo
```

---

**Documento preparado para presentación del proyecto PortAda**  
**Fecha**: Enero 2026  
**Versión**: 1.0  
**Estado**: Completo y funcional ✅
