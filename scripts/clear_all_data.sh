#!/bin/bash

# 🧹 Script para limpiar todos los datos procesados
# Ejecutar desde la raíz del proyecto

echo "🗑️  Limpiando todos los datos procesados..."

# Borrar datos de PortAda
echo "📁 Borrando datos de PortAda..."
rm -rf .storage/portada_data/*
echo "✅ Datos de PortAda eliminados"

# Borrar logs de ingestion
echo "📁 Borrando logs de ingestion..."
rm -rf .storage/ingestion/*
rm -rf .storage/logs/*
rm -rf .storage/metadata/*
echo "✅ Logs eliminados"

# Recrear estructura básica
echo "📁 Recreando estructura básica..."
mkdir -p .storage/ingestion
mkdir -p .storage/logs  
mkdir -p .storage/metadata
mkdir -p .storage/portada_data
echo "✅ Estructura recreada"

echo ""
echo "🎉 ¡Todos los datos han sido eliminados!"
echo ""
echo "📋 Para completar la limpieza:"
echo "   1. Recarga el frontend (Ctrl+F5)"
echo "   2. O limpia localStorage del navegador"
echo "   3. Los nuevos uploads empezarán desde cero"
echo ""