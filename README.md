# PortAda: Data Ingestion & Analysis Platform

Plataforma full-stack para la ingesta, validación y análisis de datos históricos utilizando tecnologías de Big Data.

## 🚀 Estado del Proyecto

- **Frontend**: Activo (React + Vite)
- **Backend**: Activo (FastAPI + PySpark/Delta Lake)
- **Infraestructura**: Dockerizada

## 📚 Documentación

Para una guía detallada sobre la arquitectura, desarrollo y uso del sistema, consulta:

👉 **[Documentación Completa](DOCUMENTATION.md)**

## ⚡ Inicio Rápido

La forma recomendada de ejecutar el proyecto es usando Docker Compose.

```bash
# En la raíz del proyecto
docker-compose up --build
```

Esto levantará:

- **Frontend**: http://localhost:5173
- **Backend**: http://localhost:8000
- **Redis**: Puerto 6379

## 🧪 Estructura de Carpetas

- `frontend/`: Aplicación web React.
- `portada_backend/`: API REST Service.
- `delta_lake/`: Almacenamiento de datos y logs.
- `scripts/`: Herramientas de migración de datos.

## 🔧 Configuración para Desarrollo

Consulta [DOCUMENTATION.md](DOCUMENTATION.md#desarrollo-local-sin-docker) para instrucciones detalladas sobre cómo configurar el entorno de desarrollo local.
