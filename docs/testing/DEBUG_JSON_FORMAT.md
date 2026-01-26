# Debug: Formato JSON para PortAda

## ✅ PROBLEMA RESUELTO: Formato JSON para PortAda

## Resumen de la Solución

El error "dictionary update sequence element #0 has length 1; 2 is required" ha sido **completamente resuelto**. El problema estaba en el formato JSON esperado por la biblioteca PortAda.

## Causa del Error

PortAda espera que el archivo JSON contenga un **array plano de entradas**, no una estructura anidada con metadatos. Cuando se pasaba un objeto con estructura anidada, la biblioteca iteraba sobre las claves del objeto en lugar de las entradas individuales.

## Solución Implementada

Se actualizó el servicio PortAda (`backend/app/services/portada_service.py`) para:

1. **Detectar automáticamente el formato JSON**
2. **Convertir formato anidado a array plano** cuando sea necesario
3. **Mantener compatibilidad con ambos formatos**
4. **Preservar metadatos** agregándolos a cada entrada individual

### Formatos Soportados

#### ✅ Formato Anidado (se convierte automáticamente):
```json
{
  "publication_date": "1903-02-01",
  "publication_name": "DM", 
  "publication_edition": "U",
  "entries": [
    {
      "publication_date": "1903-01-31",
      "travel_arrival_port": "La Habana",
      "travel_departure_port": "Cayo Hueso",
      "ship_name": "Olivette",
      "ship_type": "vapor",
      "master_name": "Allen",
      "parsed_text": "De Cayo Hueso, vapor Olivette, capitán Allen."
    }
  ]
}
```

#### ✅ Formato Array Plano (se procesa directamente):
```json
[
  {
    "publication_date": "1903-01-31",
    "publication_name": "DM",
    "publication_edition": "U", 
    "travel_arrival_port": "La Habana",
    "travel_departure_port": "Cayo Hueso",
    "ship_name": "Olivette",
    "ship_type": "vapor",
    "master_name": "Allen",
    "parsed_text": "De Cayo Hueso, vapor Olivette, capitán Allen."
  }
]
```

## Resultados de las Pruebas

### ✅ Pruebas Exitosas:
- **Formato anidado**: ✅ Funciona perfectamente
- **Formato array plano**: ✅ Funciona perfectamente  
- **API completa**: ✅ Upload y procesamiento exitoso
- **Spark + Hadoop**: ✅ Inicialización correcta
- **Java 17**: ✅ Configurado y funcionando
- **Clasificación/deduplicación**: ✅ Sin errores

### Logs de Éxito:
```
✅ Starting ingestion process
✅ Converted nested format to flat array with 1 entries
✅ File copied to Hadoop file system  
✅ Classification/deduplication completed
✅ 1 records processed successfully
```

## Cambios Realizados

### 1. Servicio PortAda (`backend/app/services/portada_service.py`)
- Detección automática de formato JSON
- Conversión de formato anidado a array plano
- Creación de archivo temporal con formato correcto
- Preservación de metadatos en cada entrada
- Limpieza automática de archivos temporales

### 2. Configuración CORS (`backend/.env`)
- Agregado soporte para puerto 5174 del frontend
- Mantenida compatibilidad con puerto 5173

## Estado Final

🎉 **COMPLETAMENTE FUNCIONAL**

- ✅ Todos los formatos JSON funcionan
- ✅ API de ingestion operativa
- ✅ Frontend y backend comunicándose correctamente
- ✅ PortAda procesando datos sin errores
- ✅ Java 17 configurado correctamente
- ✅ Spark + Hadoop operativos

El sistema está listo para uso en producción con soporte completo para ambos formatos JSON.

## Formato JSON Completo Según Manual de Desarrolladores

Después de analizar el manual de desarrolladores de PortAda (`docs/ManualDesarrolladores.md`), se identificó el formato JSON completo que PortAda espera:

### ✅ Formato Completo Requerido:
```json
[
  {
    "model_version": "boat_fact-00.00.01",
    "publication_date": "1903-02-01",
    "publication_name": "DM",
    "publication_edition": "U",
    "news_section": "E",
    "travel_departure_port": "Cayo Hueso",
    "travel_arrival_port": "La Habana",
    "travel_departure_date": "1903-01-30",
    "travel_arrival_date": "1903-01-31",
    "travel_arrival_moment": "mañana",
    "travel_duration_value": "1",
    "travel_duration_unit": "días",
    "travel_port_of_call_list": [],
    "ship_type": "vapor",
    "ship_flag": "americano",
    "ship_name": "Olivette",
    "ship_tons_capacity": "1500",
    "ship_tons_unit": "tons",
    "master_role": "capitán",
    "master_name": "Allen",
    "ship_agent_name": "J. Cibils",
    "crew_number": 25,
    "cargo_list": [
      {
        "cargo_merchant_name": "G. Lawton Childs y cp.",
        "cargo": [
          {
            "cargo_quantity": "40",
            "cargo_unit": "pipas",
            "cargo_commodity": "caña"
          }
        ]
      }
    ],
    "quarantine": false,
    "forced_arrival": false,
    "ship_amount": null,
    "ship_origin_area": null,
    "parsed_text": "De Cayo Hueso, vapor americano Olivette, capitán Allen..."
  }
]
```

### Campos Obligatorios Identificados:

#### Metadatos de Publicación:
- `model_version`: Versión del modelo (ej: "boat_fact-00.00.01")
- `publication_date`: Fecha de publicación (YYYY-MM-DD)
- `publication_name`: Nombre del periódico (DM, DB, SM, LP, etc.)
- `publication_edition`: Edición (U=única, M=mañana, T=tarde, N=noche)
- `news_section`: Tipo de noticia (E=entradas, M=manifiestos)

#### Información de Viaje:
- `travel_departure_port`: Puerto de salida
- `travel_arrival_port`: Puerto de llegada
- `travel_departure_date`: Fecha de salida
- `travel_arrival_date`: Fecha de llegada
- `travel_arrival_moment`: Momento de llegada (opcional)
- `travel_duration_value`: Duración del viaje
- `travel_duration_unit`: Unidad de tiempo
- `travel_port_of_call_list`: Lista de puertos de escala (array)

#### Información del Barco:
- `ship_type`: Tipo de embarcación (vapor, bergantín, etc.)
- `ship_flag`: Bandera/nacionalidad
- `ship_name`: Nombre del barco
- `ship_tons_capacity`: Capacidad en toneladas (como string)
- `ship_tons_unit`: Unidad de tonelaje
- `master_role`: Cargo del responsable (capitán, patrón)
- `master_name`: Nombre del responsable
- `ship_agent_name`: Agente marítimo (opcional)
- `crew_number`: Número de tripulantes (opcional)

#### Información de Carga:
- `cargo_list`: Array de objetos con estructura específica:
  ```json
  {
    "cargo_merchant_name": "Nombre del destinatario",
    "cargo": [
      {
        "cargo_quantity": "cantidad como string",
        "cargo_unit": "unidad de medida",
        "cargo_commodity": "tipo de mercancía"
      }
    ]
  }
  ```

#### Otros Campos:
- `quarantine`: Boolean para cuarentena
- `forced_arrival`: Boolean para arribada forzosa
- `ship_amount`: Para modelos cuantitativos (opcional)
- `ship_origin_area`: Para modelos cuantitativos (opcional)
- `parsed_text`: Texto original de la noticia

### Archivos de Prueba Creados:
- `test_portada_format.json`: ✅ 1 registro procesado exitosamente
- `test_portada_multiple_entries.json`: ✅ 2 registros procesados exitosamente

Ambos archivos utilizan el formato completo especificado en el manual de desarrolladores y funcionan perfectamente con PortAda.