// Script para limpiar el localStorage del frontend
// Ejecutar en la consola del navegador

console.log('🧹 Limpiando localStorage del frontend...');

// Limpiar el store de uploads
localStorage.removeItem('upload-storage');

// Limpiar otros datos relacionados si existen
const keysToRemove = [];
for (let i = 0; i < localStorage.length; i++) {
  const key = localStorage.key(i);
  if (key && (key.includes('upload') || key.includes('portada') || key.includes('ingestion'))) {
    keysToRemove.push(key);
  }
}

keysToRemove.forEach(key => {
  localStorage.removeItem(key);
  console.log(`✅ Eliminado: ${key}`);
});

console.log('🎉 localStorage limpiado completamente');
console.log('🔄 Recargando página...');

// Recargar la página
location.reload();