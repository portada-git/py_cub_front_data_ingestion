# Análisis de Archivos JSON Oficiales - Problemas Identificados

## Resumen Ejecutivo

Se han analizado los archivos JSON oficiales proporcionados y se han identificado múltiples problemas de formato y estructura que impiden su procesamiento correcto por PortAda.

---

## ARCHIVO 1: JSON con estructura anidada (1903-02-01)

### ❌ PROBLEMAS CRÍTICOS IDENTIFICADOS:

#### 1. **Estructura General Incorrecta**
- **Problema**: Usa estructura anidada con metadatos en el nivel superior
- **Actual**: `{"files": [...], "publication_date": "...", "entries": [...]}`
- **Requerido**: Array plano `[{entrada1}, {entrada2}, ...]`
- **Impacto**: PortAda no puede procesar esta estructura

#### 2. **Campo `files` No Reconocido**
- **Problema**: Campo `files` no existe en la especificación PortAda
- **Actual**: `"files": ["1903_02_01_HAB_DM_U_01_0_V_001-621.txt", ...]`
- **Solución**: Eliminar este campo o moverlo a `obs`

#### 3. **Campos Faltantes Obligatorios**
Cada entrada carece de campos requeridos:
- ❌ `model_version` (obligatorio)
- ❌ `ship_agent_name` (debería ser explícito, no null)
- ❌ `ship_amount` y `ship_origin_area` (deben estar presentes como null)

#### 4. **Estructura `cargo_list` Incorrecta**
- **Problema**: Campos vacíos en lugar de null
- **Actual**: `"cargo_quantity": "", "cargo_unit": ""`
- **Requerido**: `"cargo_quantity": null, "cargo_unit": null`

#### 5. **Campo `passenger_account` No Estándar**
- **Problema**: Campo no reconocido en especificación PortAda
- **Actual**: `"passenger_account": 71`
- **Solución**: Mover a campo `obs` o crear campo específico

#### 6. **Inconsistencias en Tipos de Datos**
- **Problema**: Mezcla de tipos numéricos y string
- **Ejemplo**: `"ship_tons_capacity": 1604` (debería ser `"1604"`)
- **Ejemplo**: `"travel_duration_value": 6.5` (debería ser `"6.5"`)

#### 7. **Valores `null` como String**
- **Problema**: `"ship_flag": null` correcto, pero inconsistente
- **Algunos campos**: Usan `null` correctamente
- **Otros campos**: Usan strings vacías `""`

### 📋 ENTRADA POR ENTRADA:

#### Entrada 1 (Olivette):
- ✅ Campos básicos presentes
- ❌ `cargo_quantity` y `cargo_unit` vacíos en lugar de null
- ❌ `passenger_account` no estándar
- ❌ Falta `model_version`

#### Entrada 2 (Ing. Verben):
- ✅ Estructura básica correcta
- ❌ `ship_flag`: null (debería tener valor o ser string)
- ❌ `cargo_quantity` y `cargo_unit` vacíos
- ❌ Falta `model_version`

#### Entrada 3 (Vivina):
- ✅ Campos de fecha correctos
- ❌ `travel_departure_date`: "1902-12-31" (año anterior, verificar si es correcto)
- ❌ Mismos problemas de cargo_list
- ❌ Falta `model_version`

#### Entrada 4 (Marla Theresia):
- ✅ `travel_port_of_call_list` con datos
- ❌ `travel_duration_value` y `travel_duration_unit`: null (inconsistente con texto)
- ❌ Texto menciona "Kainerm" pero no está en campos estructurados
- ❌ Falta `model_version`

---

## ARCHIVO 2: Entradas individuales con IDs (1852-01-01)

### ❌ PROBLEMAS CRÍTICOS IDENTIFICADOS:

#### 1. **Estructura Completamente Incorrecta**
- **Problema**: No es un array JSON válido, son objetos separados
- **Actual**: `{"id": 4, ...}{"id": 7, ...}` (JSON malformado)
- **Requerido**: `[{"id": 4, ...}, {"id": 7, ...}]`

#### 2. **Campos No Estándar**
- ❌ `id`: No existe en especificación PortAda
- ❌ `source_file`: No estándar
- ❌ `extracted_at`: No estándar

#### 3. **Campo `cargo_list` como String**
- **Problema**: Está serializado como string JSON en lugar de objeto
- **Actual**: `"cargo_list": "[{\"cargo_merchant_name\": null, ...}]"`
- **Requerido**: `"cargo_list": [{"cargo_merchant_name": null, ...}]`

#### 4. **Valores "null" como String**
- **Problema**: Usa `"null"` en lugar de `null`
- **Ejemplo**: `"travel_arrival_date": "null"` (debería ser `null`)

#### 5. **Campos Faltantes Críticos**
- ❌ `model_version`
- ❌ `publication_name`
- ❌ `publication_edition`
- ❌ `news_section`
- ❌ `travel_arrival_port`

#### 6. **Inconsistencias en Booleanos**
- **Problema**: Usa `0` en lugar de `false`
- **Actual**: `"quarantine": 0, "forced_arrival": 0`
- **Requerido**: `"quarantine": false, "forced_arrival": false`

### 📋 ENTRADA POR ENTRADA:

#### Entrada ID 4 (Anuta):
- ❌ JSON malformado (no es array)
- ❌ `cargo_list` serializado como string
- ❌ Múltiples campos faltantes
- ❌ `publication_date` formato incorrecto ("1852_01_01" vs "1852-01-01")

#### Entrada ID 7 (Antio):
- ❌ Mismos problemas estructurales
- ❌ `ship_type`: "null" como string
- ❌ `ship_flag`: "null" como string
- ❌ Texto indica "por el sol." que no es tipo de barco válido

---

## 🛠️ SOLUCIONES RECOMENDADAS

### Para Archivo 1 (1903-02-01):
1. **Convertir a array plano**: Extraer entradas del objeto anidado
2. **Agregar campos faltantes**: `model_version`, etc.
3. **Corregir cargo_list**: Cambiar strings vacías por null
4. **Estandarizar tipos**: Todos los números como strings
5. **Mover campos no estándar**: `passenger_account` → `obs`

### Para Archivo 2 (1852-01-01):
1. **Corregir JSON**: Crear array válido
2. **Deserializar cargo_list**: Convertir string a objeto
3. **Corregir valores null**: `"null"` → `null`
4. **Agregar campos obligatorios**: Todos los campos faltantes
5. **Corregir booleanos**: `0` → `false`

### Formato Correcto Esperado:
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
    "travel_departure_date": "1903-01-31",
    "travel_arrival_date": "1903-01-31",
    "travel_arrival_moment": null,
    "travel_duration_value": "7",
    "travel_duration_unit": "horas",
    "travel_port_of_call_list": [],
    "ship_type": "vapor",
    "ship_flag": "americano",
    "ship_name": "Olivette",
    "ship_tons_capacity": "1604",
    "ship_tons_unit": "toneladas",
    "master_role": "cap.",
    "master_name": "Allen",
    "ship_agent_name": "G. Lawton Childs y cp.",
    "crew_number": 55,
    "cargo_list": [
      {
        "cargo_merchant_name": "G. Lawton Childs y cp.",
        "cargo": [
          {
            "cargo_quantity": null,
            "cargo_unit": null,
            "cargo_commodity": "carga general"
          }
        ]
      }
    ],
    "quarantine": false,
    "forced_arrival": false,
    "ship_amount": null,
    "ship_origin_area": null,
    "parsed_text": "De Cayo Hueso, en 7 horas, vapor americano Olivette, capitán Allen, tripulantes 55, toneladas 1.604 con carga general, correspondencia y 71 pasajeros á G. Lawton Childs y cp.",
    "obs": "71 pasajeros"
  }
]
```

## 📊 Resumen de Problemas por Categoría

| Categoría | Archivo 1 | Archivo 2 | Total |
|-----------|-----------|-----------|-------|
| Estructura JSON | 1 | 1 | 2 |
| Campos Faltantes | 4 | 8 | 12 |
| Tipos de Datos | 3 | 4 | 7 |
| Campos No Estándar | 2 | 3 | 5 |
| Valores Null | 1 | 2 | 3 |
| **TOTAL** | **11** | **18** | **29** |

## ⚠️ IMPACTO EN PORTADA

Estos archivos **NO FUNCIONARÁN** con PortAda hasta que se corrijan todos los problemas identificados. El sistema actual puede manejar la conversión automática de estructura anidada, pero no puede corregir los problemas de tipos de datos y campos faltantes.