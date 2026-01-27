#!/usr/bin/env python3
"""
Script para transformar los archivos JSON de .data/real al formato esperado por el backend
Agrega el campo 'parsed_text' usando el campo 'raw_text' existente
"""

import json
import os
from pathlib import Path

def transform_entry(entry):
    """
    Transforma una entrada del formato antiguo al nuevo formato
    """
    # Crear una copia del entry
    transformed = entry.copy()
    
    # Agregar parsed_text usando raw_text si existe
    if 'raw_text' in entry and entry['raw_text']:
        transformed['parsed_text'] = entry['raw_text']
    else:
        # Si no hay raw_text, crear un parsed_text básico
        transformed['parsed_text'] = f"Entrada sin texto original disponible"
    
    # Agregar publication_date basado en source_file si existe
    if 'source_file' in entry and entry['source_file']:
        # source_file tiene formato "1852_01_01" -> convertir a "1852-01-01"
        source_file = str(entry['source_file'])
        parts = source_file.split('_')
        if len(parts) >= 3:
            try:
                year = parts[0]
                month = parts[1].zfill(2)
                day = parts[2].zfill(2)
                transformed['publication_date'] = f"{year}-{month}-{day}"
            except (ValueError, IndexError):
                transformed['publication_date'] = None
        else:
            transformed['publication_date'] = None
    else:
        transformed['publication_date'] = None
    
    # Asegurar que todos los campos requeridos existen
    # Agregar campos que podrían faltar con valores por defecto
    defaults = {
        'model_version': 'boat_fact-00.00.01',
        'publication_name': 'DM',
        'publication_edition': 'U',
        'news_section': 'E',
        'quarantine': False,
        'forced_arrival': False,
        'ship_amount': None,
        'ship_origin_area': None,
        'obs': None
    }
    
    for key, default_value in defaults.items():
        if key not in transformed:
            transformed[key] = default_value
    
    return transformed


def transform_file(input_path, output_path):
    """
    Transforma un archivo JSON completo
    """
    print(f"Transformando: {input_path}")
    
    try:
        # Leer el archivo original
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Transformar cada entrada
        transformed_data = [transform_entry(entry) for entry in data]
        
        # Guardar el archivo transformado
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(transformed_data, f, ensure_ascii=False, indent=2)
        
        print(f"  ✓ Transformado exitosamente: {len(transformed_data)} entradas")
        return True
        
    except Exception as e:
        print(f"  ✗ Error transformando {input_path}: {e}")
        return False


def main():
    """
    Función principal que transforma todos los archivos en .data/real
    """
    # Directorios
    real_dir = Path('.data/real')
    converted_dir = Path('.data/converted')
    
    # Crear directorio de salida si no existe
    converted_dir.mkdir(exist_ok=True)
    
    # Obtener todos los archivos JSON en .data/real
    json_files = list(real_dir.glob('*.json'))
    
    if not json_files:
        print("No se encontraron archivos JSON en .data/real")
        return
    
    print(f"Encontrados {len(json_files)} archivos para transformar\n")
    
    # Transformar cada archivo
    success_count = 0
    for json_file in sorted(json_files):
        # Crear nombre de archivo de salida
        output_name = json_file.stem + '_converted.json'
        output_path = converted_dir / output_name
        
        # Transformar
        if transform_file(json_file, output_path):
            success_count += 1
        
        print()  # Línea en blanco entre archivos
    
    # Resumen
    print("=" * 60)
    print(f"Transformación completada:")
    print(f"  Total archivos: {len(json_files)}")
    print(f"  Exitosos: {success_count}")
    print(f"  Fallidos: {len(json_files) - success_count}")
    print(f"\nArchivos guardados en: {converted_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
