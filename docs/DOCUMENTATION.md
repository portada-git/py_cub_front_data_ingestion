# Documentación del Proyecto PortAda

Este documento proporciona una visión detallada de la arquitectura, configuración y desarrollo del proyecto PortAda.

## 📖 Visión General

PortAda es una plataforma diseñada para la ingesta, procesamiento y análisis de datos históricos (principalmente marítimos). Utiliza una arquitectura moderna basada en contenedores para garantizar la reproducibilidad y escalabilidad.

El sistema se compone de dos partes principales:

1.  **Frontend**: Una interfaz web moderna para subir archivos y visualizar análisis.
2.  **Backend**: Una API REST que gestiona la subida de archivos, el procesamiento y las consultas sobre el Data Lake.

## 🏗 Arquitectura Técnica

### Componentes

- **Frontend**:
  - **Framework**: React 18 con TypeScript y Vite.
  - **Estilos**: Tailwind CSS.
  - **Gestión de Estado**: Zustand.
  - **Docker**: Nginx sirviendo la build estática.

- **Backend (API)**:
  - **Framework**: FastAPI (Python 3.12).
  - **Procesamiento de Datos**: PySpark 3.5.3 y Delta Lake 3.2.1.
  - **Almacenamiento de Estado**: Redis 7 (utilizado para el seguimiento de uploads, usuarios y colas de tareas).
  - **Persistencia de Datos**: Sistema de archivos local estructurado como Delta Lake.

- **Infraestructura**:
  - **Orquestación**: Docker Compose.
  - **Base de Datos NoKy**: Redis se utiliza como base de datos de clave-valor para metadatos rápidos y control de sesiones simples.

### Flujo de Datos

1.  **Ingesta**: El usuario sube archivos JSON (datos de barcos) o YAML (entidades) a través del Frontend.
2.  **Recepción**: La API recibe los archivos y los guarda en un volumen compartido (`delta_lake/ingest`).
3.  **Registro**: Se registra el evento de subida y el estado inicial en Redis.
4.  **Procesamiento**: El backend (o workers asociados) procesa estos archivos crudos y los transforma/mueve a capas estructuradas del Delta Lake.
5.  **Consulta**: Los endpoints de análisis consultan las tablas Delta o logs de auditoría para mostrar métricas de duplicados, fechas faltantes, etc.

## 🚀 Guía de Inicio Rápido

### Prerrequisitos

- Docker y Docker Compose instalados.

### Instalación y Ejecución

Para levantar todo el entorno (backend, frontend y redis):

```bash
docker-compose up --build
```

Esto iniciará los siguientes servicios:

- **API**: [http://localhost:8000](http://localhost:8000)
- **Documentación API (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Frontend**: [http://localhost:5173](http://localhost:5173) (mapeado al puerto 80 interno del contenedor)

### Desarrollo Local (Sin Docker)

Si prefieres ejecutar los servicios localmente para desarrollo:

#### Backend

Se requiere Python 3.12 y un servidor Redis ejecutándose localmente.

```bash
cd portada_backend
pip install -r requirements.txt
# Asegúrate de tener dependencias base también
pip install -r requirements-base.txt
uvicorn app.main:app --reload
```

#### Frontend

Se requiere Bun (o Node.js).

```bash
cd frontend
bun install
bun run dev
```

## 📂 Estructura del Proyecto

```
/
├── config/                 # Configuraciones globales (e.g., config data layer)
├── delta_lake/             # Volumen de datos persistente (Simulación de Data Lake)
│   ├── ingest/             # Zona de aterrizaje para archivos subidos
│   ├── metadata/           # Logs y metadatos de procesos
│   └── sequencer/          # Secuenciadores para IDs
├── docs/                   # Documentación adicional
├── frontend/               # Código fuente del Frontend (React/Vite)
├── portada_backend/        # Código fuente del Backend (FastAPI)
│   ├── app/                # Lógica de la aplicación
│   │   ├── routers/        # Endpoints de la API
│   │   └── services/       # Lógica de negocio
├── scripts/                # Scripts de utilidad (migración de datos, ETL manual)
└── docker-compose.yml      # Definición de servicios Docker
```

## 🛠 Scripts de Utilidad

En la carpeta `scripts/` encontrarás herramientas para migración de datos:

- `convert_all_real_data.py`: Convierte datos históricos (formato DM) al esquema esperado por PortAda.
- `transform_real_data.py`: Posiblemente para transformaciones intermedias.

## 🧪 Pruebas

El backend cuenta con tests automatizados en la carpeta `tests/`.

```bash
# Ejecutar tests (requiere entorno configurado o contenedor)
pytest tests/
```

## 📝 Notas sobre la Base de Datos

Aunque existen referencias a PostgreSQL en el código (`database.py`), la implementación actual utiliza **Redis** como fuente de verdad para la gestión de sesiones de usuario y metadatos de archivos en tránsito. La persistencia principal de los datos de negocio reside en archivos (Delta Lake).
