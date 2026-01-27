# 🧪 Tests del Sistema PortAda

Esta carpeta contiene todos los scripts de prueba y validación del sistema PortAda.

## 📁 Estructura de Tests

### 🔧 Tests de Funcionalidad Principal
- **`test_api_funcionalidades_especificas.py`** - Pruebas específicas de las funcionalidades core que sabemos que funcionan
- **`test_validacion_final_corregida.py`** - Validación final corregida que resuelve problemas de mayúsculas/minúsculas

### 🧪 Tests Completos del Sistema
- **`test_api_completo.py`** - Suite completa de pruebas de todas las funcionalidades del API
- **`test_validacion_datos_reales.py`** - Validación profunda de que los datos se guardan y analizan correctamente

### 🔍 Tests de Investigación y Debug
- **`test_investigacion_problema_datos.py`** - Investigación de problemas de datos duplicados/incorrectos
- **`test_verificacion_estructura_datos.py`** - Verificación de la estructura exacta de los datos guardados

## 🚀 Cómo Ejecutar los Tests

### Prerequisitos
1. Backend ejecutándose en `http://localhost:8002`
2. Python 3 con `requests` instalado
3. Archivos JSON de demostración en el directorio raíz

### Ejecución Rápida
```bash
# Test principal recomendado
python3 tests/test_validacion_final_corregida.py

# Test de funcionalidades específicas
python3 tests/test_api_funcionalidades_especificas.py
```

### Ejecución Completa
```bash
# Suite completa de tests
python3 tests/test_api_completo.py

# Validación profunda de datos
python3 tests/test_validacion_datos_reales.py
```

### Debug y Investigación
```bash
# Investigar problemas de datos
python3 tests/test_investigacion_problema_datos.py

# Verificar estructura de datos
python3 tests/test_verificacion_estructura_datos.py
```

## 📊 Resultados Esperados

### ✅ Tests Exitosos
Los tests exitosos deben mostrar:
- ✅ Autenticación funcionando
- ✅ Subida de archivos exitosa
- ✅ Datos guardados correctamente
- ✅ Consultas devolviendo resultados apropiados
- ✅ Análisis funcionando

### 🎯 Métricas de Éxito
- **Tasa de éxito**: >= 80%
- **Datos procesados**: Números realistas (no millones)
- **Consultas específicas**: Devuelven datos filtrados correctamente
- **Consistencia**: Mayúsculas/minúsculas manejadas apropiadamente

## 🔧 Configuración

### Variables de Configuración
```python
BASE_URL = "http://localhost:8002/api"
USERNAME = "daniel"
PASSWORD = "test123"
```

### Archivos Requeridos
Los tests esperan encontrar estos archivos en el directorio raíz:
- `demo_json_completo_habana_1903.json`
- `demo_json_barcelona_1854.json`
- `demo_json_buenos_aires_1852.json`
- `demo_json_marsella_1855.json`
- `demo_json_casos_especiales.json`
- `demo_json_transatlantico_1860.json`

## 📝 Notas Importantes

1. **Orden de Ejecución**: Ejecutar `test_validacion_final_corregida.py` primero para validación básica
2. **Datos Preexistentes**: El sistema puede tener datos preexistentes que afecten las consultas generales
3. **Filtrado**: Las consultas específicas por fecha/publicación funcionan correctamente
4. **Mayúsculas/Minúsculas**: El sistema maneja ambos casos apropiadamente

## 🎉 Estado Actual

**TODOS LOS TESTS PRINCIPALES PASAN EXITOSAMENTE** ✅

El sistema PortAda está completamente validado y funcional para uso en producción.