# 🧹 Limpiar Datos del Frontend

## Método 1: DevTools del Navegador
1. Abre DevTools (F12)
2. Ve a la pestaña **Application** (Chrome) o **Storage** (Firefox)
3. En el panel izquierdo, busca **Local Storage**
4. Selecciona tu dominio (localhost:5174)
5. Busca la clave **"upload-storage"**
6. Haz clic derecho → **Delete**
7. Recarga la página

## Método 2: Consola del Navegador
```javascript
// Ejecuta esto en la consola del navegador
localStorage.removeItem('upload-storage');
location.reload();
```

## Método 3: Limpiar todo el localStorage
```javascript
// ⚠️ CUIDADO: Esto borra TODOS los datos del localStorage
localStorage.clear();
location.reload();
```