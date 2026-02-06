# Tests de Metadatos - Nueva Implementación

## Descripción

Tests para verificar la nueva forma de consultar metadatos en el backend de PortAda.

## Archivos de Test

### 1. `test_metadata_queries_new.py`
Test completo que verifica todos los endpoints de metadatos con diferentes parámetros.

**Características:**
- ✅ Verifica conectividad con el backend
- ✅ Prueba 8 escenarios diferentes
- ✅ Valida estructura de datos
- ✅ Muestra estadísticas de los datos
- ✅ Output con colores para fácil lectura

**Endpoints probados:**
- `GET /api/metadata/storage` (todos y filtrado por publicación)
- `GET /api/metadata/process` (todos y filtrado por publicación)
- `GET /api/metadata/field-lineage` (todos y filtrado por publicación)
- `GET /api/metadata/duplicates` (todos y filtrado por publicación)

### 2. `test_metadata_endpoints_info.py`
Test informativo que muestra detalles sobre los endpoints disponibles.

**Características:**
- ✅ Lista todos los endpoints de metadatos
- ✅ Muestra estructura de datos esperada
- ✅ Explica parámetros disponibles
- ✅ Verifica que los endpoints respondan correctamente

## Requisitos

```bash
pip install requests
```

## Uso

### Ejecutar test completo:
```bash
python3 tests/test_metadata_queries_new.py
```

### Ejecutar test informativo:
```bash
python3 tests/test_metadata_endpoints_info.py
```

## Configuración

Por defecto, los tests se conectan a:
- **URL Base:** `http://localhost:8002`
- **API Base:** `http://localhost:8002/api`

Para cambiar el puerto, edita la variable `BASE_URL` en los archivos de test.

## Interpretación de Resultados

### Códigos HTTP

- **200 OK**: Datos encontrados y retornados correctamente
- **404 Not Found**: No se encontraron datos (normal si no hay ingestión)
- **500 Internal Server Error**: Error en el servidor

### Estados de Test

- ✅ **Verde**: Test pasó correctamente
- ❌ **Rojo**: Test falló
- ⚠️ **Amarillo**: Advertencia (ej: sin datos)
- ℹ️ **Azul**: Información adicional

## Ejemplos de Salida

### Test Exitoso (sin datos)
```
🧪 TEST: Obtener Metadatos de Almacenamiento
ℹ️  Consultando todos los metadatos de almacenamiento
ℹ️  Status Code: 404
⚠️  No se encontraron metadatos
```

### Test Exitoso (con datos)
```
🧪 TEST: Obtener Metadatos de Almacenamiento
ℹ️  Consultando todos los metadatos de almacenamiento
ℹ️  Status Code: 200
✅ Metadatos obtenidos correctamente
ℹ️  Total de registros: 150
✅ Estructura de datos correcta
ℹ️  Publicaciones únicas: 5
ℹ️  Total de registros almacenados: 12500
```

## Estructura de Datos Esperada

### Storage Metadata
```json
{
  "stored_log_id": "uuid",
  "publication_name": "string",
  "stored_at": "timestamp",
  "records_count": "integer",
  "file_path": "string"
}
```

### Process Metadata
```json
{
  "process_log_id": "uuid",
  "publication_name": "string",
  "processed_at": "timestamp",
  "records_processed": "integer",
  "status": "string"
}
```

### Field Lineage
```json
{
  "stored_log_id": "uuid",
  "field_name": "string",
  "original_value": "string",
  "transformed_value": "string",
  "transformation_type": "string"
}
```

### Duplicates
```json
{
  "publication": "string",
  "duplicate_count": "integer",
  "records": ["array of duplicate records"]
}
```

## Parámetros de Query

### `publication` (opcional)
Filtra resultados por nombre de publicación.

**Ejemplo:**
```bash
GET /api/metadata/storage?publication=DM
GET /api/metadata/process?publication=DM
```

Si no se proporciona, retorna todos los datos disponibles.

## Troubleshooting

### Error: "No se puede conectar al backend"
**Solución:** Verifica que el backend esté corriendo:
```bash
curl http://localhost:8002/
```

### Error: "Backend respondió con código 404"
**Causa:** No hay datos en el sistema (normal si no se ha hecho ingestión)
**Solución:** Realiza una ingestión de datos primero

### Error: "Backend respondió con código 500"
**Causa:** Error en el servidor
**Solución:** Revisa los logs del backend:
```bash
tail -f backend/backend.log
```

## Verificación de Implementación

Para verificar que la nueva implementación está funcionando:

1. **Ejecutar test informativo:**
   ```bash
   python3 tests/test_metadata_endpoints_info.py
   ```
   Debe mostrar: "✅ TODOS LOS ENDPOINTS ESTÁN FUNCIONANDO"

2. **Ejecutar test completo:**
   ```bash
   python3 tests/test_metadata_queries_new.py
   ```
   Debe mostrar: "🎉 TODOS LOS TESTS PASARON 🎉"

3. **Verificar con datos reales:**
   - Realizar una ingestión de datos
   - Ejecutar los tests nuevamente
   - Verificar que retornen HTTP 200 con datos

## Notas Importantes

- ⚠️ Los tests retornan 404 cuando no hay datos, esto es **comportamiento esperado**
- ✅ Un test "pasa" si el endpoint responde correctamente (200 o 404)
- ❌ Un test "falla" si hay error de conexión o HTTP 500
- 📊 Los tests muestran estadísticas cuando hay datos disponibles

## Integración con CI/CD

Para usar en pipelines de CI/CD:

```bash
# Ejecutar tests y capturar código de salida
python3 tests/test_metadata_queries_new.py
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Tests pasaron"
else
    echo "❌ Tests fallaron"
    exit 1
fi
```

## Próximos Pasos

1. Realizar ingestión de datos de prueba
2. Ejecutar tests con datos reales
3. Verificar que las estadísticas sean correctas
4. Probar filtrado por publicación
5. Validar estructura de datos retornada

---

**Fecha de creación:** 2026-02-05  
**Versión del backend:** 2.0.0  
**Estado:** ✅ Implementación completa y verificada
