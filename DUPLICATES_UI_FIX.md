# Fix: Interfaz de Duplicados con Campos Incorrectos

## Problema
La interfaz de duplicados mostraba los datos pero con campos incorrectos o mal mapeados. Los nombres de las columnas no coincidían con los datos del backend.

## Causa Raíz
El componente del frontend esperaba campos diferentes a los que el backend estaba devolviendo:

### Frontend esperaba:
- `user` → Backend devuelve: `uploaded_by`
- `process_date` → Backend devuelve: `date`
- `duplicates_count` → Backend devuelve: `duplicate_count`
- `created_at` → Backend devuelve: (no existe)
- `duplicates_metadata` → Backend devuelve: `duplicates`

## Solución Aplicada

### Archivo Modificado: `frontend/src/components/analysis/DuplicatesAnalysis.tsx`

#### 1. Actualizar Interface (líneas ~15-23)
```typescript
// ❌ ANTES
interface DuplicateMetadata extends Record<string, unknown> {
  log_id: string;
  user: string;
  publication: string;
  process_date: string;
  duplicates_count: number;
  duplicates_filter: string;
  created_at: string;
}

// ✅ DESPUÉS
interface DuplicateMetadata extends Record<string, unknown> {
  log_id: string;
  date: string;
  edition: string;
  publication: string;
  uploaded_by: string;
  duplicate_count: number;
  duplicates_filter: string;
  duplicate_ids: string[];
}
```

#### 2. Actualizar Carga de Datos (línea ~60)
```typescript
// ❌ ANTES
setMasterData((response as any).duplicates_metadata || []);

// ✅ DESPUÉS
setMasterData((response as any).duplicates || []);
```

#### 3. Actualizar Columnas de la Tabla (líneas ~100-180)

**Columnas actualizadas:**

| Columna | Campo Backend | Ancho | Formato |
|---------|---------------|-------|---------|
| ID LOG | `log_id` | 200px | Truncado (8 chars) |
| FECHA | `date` | 120px | YYYY-MM-DD |
| EDICIÓN | `edition` | 100px | Badge azul |
| PUBLICACIÓN | `publication` | 120px | Uppercase |
| SUBIDO POR | `uploaded_by` | 150px | Texto normal |
| CANTIDAD | `duplicate_count` | 100px | Badge rojo (bold) |
| FILTRO APLICADO | `duplicates_filter` | Auto | Truncado |

#### 4. Actualizar Exportación CSV (líneas ~90-110)
```typescript
// ❌ ANTES
'ID Log,Usuario,Publicación,Fecha Proceso,Cantidad Duplicados,Filtro,Fecha Creación'

// ✅ DESPUÉS
'ID Log,Fecha,Edición,Publicación,Subido Por,Cantidad Duplicados,Filtro'
```

## Mejoras de UI Aplicadas

### 1. Columnas Más Claras
- **ID LOG**: Muestra solo los primeros 8 caracteres del UUID
- **FECHA**: Formato YYYY-MM-DD (histórico, ej: 1914-01-02)
- **EDICIÓN**: Badge azul para mejor visibilidad
- **CANTIDAD**: Badge rojo en negrita para destacar duplicados
- **SUBIDO POR**: Muestra el usuario que subió los datos

### 2. Mejor Legibilidad
- Encabezados en mayúsculas para mejor jerarquía visual
- Anchos de columna fijos para consistencia
- Badges de colores para información importante
- Truncado de texto largo con tooltip

### 3. Datos Históricos Correctos
- Las fechas ahora muestran el período histórico correcto (1914)
- La publicación se muestra en mayúsculas (DM)
- La edición se muestra claramente (U)

## Resultado Visual

### Antes:
```
ID Log | Usuario | Publicación | Fecha Proceso | Duplicados | Filtro | Fecha Creación
(vacío o error 500)
```

### Después:
```
ID LOG      | FECHA      | EDICIÓN | PUBLICACIÓN | SUBIDO POR | CANTIDAD | FILTRO APLICADO
a1b2c3d4... | 1/1/1914   | [U]     | DM          | api_user   | [93]     | Sin filtro
b2c3d4e5... | 1/3/1914   | [U]     | DM          | api_user   | [93]     | Sin filtro
```

## Testing

### Pasos para Verificar:
1. Refresca la página del frontend (Ctrl+F5)
2. Ve a "Análisis" → "Duplicados"
3. Haz clic en "Buscar"
4. Verifica que:
   - ✅ Las columnas muestran los nombres correctos
   - ✅ Los datos se muestran correctamente
   - ✅ Las fechas son históricas (1914)
   - ✅ Los badges tienen colores apropiados
   - ✅ No hay error 500

### Resultado Esperado:
- Tabla con 12 registros de duplicados
- Fechas históricas de 1914
- Publicación "DM" en mayúsculas
- Cantidad de duplicados en badge rojo
- Usuario "api_user" visible

## Estado

✅ **IMPLEMENTADO** - Frontend actualizado

## Archivos Modificados

1. `frontend/src/components/analysis/DuplicatesAnalysis.tsx`
   - Interface `DuplicateMetadata` (líneas ~15-23)
   - Función `loadDuplicatesMetadata` (línea ~60)
   - Función `handleExportMaster` (líneas ~90-110)
   - Constante `masterColumns` (líneas ~100-180)

## Relacionado

Este fix completa la serie de correcciones para el análisis de duplicados:
1. ✅ Fix backend: Convertir PySpark Row a dict (`DUPLICATES_FIX.md`)
2. ✅ Fix frontend: Mapear campos correctamente (este fix)

## Próximos Pasos

1. Refrescar el navegador para ver los cambios
2. Verificar que la exportación CSV funcione correctamente
3. Probar los filtros de búsqueda (usuario, publicación, fechas)
