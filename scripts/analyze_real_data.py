#!/usr/bin/env python3
"""
Script para analizar la estructura de los datos reales del DM
y compararla con el formato estándar PortAda
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict

def load_json_file(file_path: str) -> List[Dict]:
    """Carga un archivo JSON"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error cargando {file_path}: {e}")
        return []

def analyze_structure(data: List[Dict], file_type: str) -> Dict:
    """Analiza la estructura de los datos"""
    if not data:
        return {}
    
    # Contar campos presentes
    field_counts = defaultdict(int)
    field_types = defaultdict(set)
    field_examples = defaultdict(list)
    
    for entry in data[:10]:  # Solo primeras 10 entradas para análisis
        for field, value in entry.items():
            field_counts[field] += 1
            field_types[field].add(type(value).__name__)
            if len(field_examples[field]) < 3:
                field_examples[field].append(str(value)[:50])
    
    return {
        'file_type': file_type,
        'total_entries': len(data),
        'fields': dict(field_counts),
        'field_types': {k: list(v) for k, v in field_types.items()},
        'field_examples': dict(field_examples)
    }

def compare_with_standard(real_data_analysis: Dict) -> Dict:
    """Compara con el formato estándar PortAda"""
    
    # Campos requeridos por PortAda (basado en demo que funciona)
    required_fields = {
        "model_version": "boat_fact-00.00.01",
        "publication_date": "YYYY-MM-DD",
        "publication_name": "DM",
        "publication_edition": "U/M/T",
        "news_section": "E",
        "travel_departure_port": "string",
        "travel_arrival_port": "string", 
        "travel_departure_date": "YYYY-MM-DD",
        "travel_arrival_date": "YYYY-MM-DD",
        "travel_arrival_moment": "string",
        "travel_duration_value": "string",
        "travel_duration_unit": "string",
        "travel_port_of_call_list": "array",
        "ship_type": "string",
        "ship_flag": "string",
        "ship_name": "string",
        "ship_tons_capacity": "string",
        "ship_tons_unit": "string",
        "master_role": "string",
        "master_name": "string",
        "ship_agent_name": "string",
        "crew_number": "number",
        "cargo_list": "array with specific structure"
    }
    
    real_fields = set(real_data_analysis.get('fields', {}).keys())
    required_fields_set = set(required_fields.keys())
    
    missing_fields = required_fields_set - real_fields
    extra_fields = real_fields - required_fields_set
    common_fields = real_fields & required_fields_set
    
    return {
        'missing_fields': list(missing_fields),
        'extra_fields': list(extra_fields),
        'common_fields': list(common_fields),
        'required_total': len(required_fields_set),
        'coverage_percentage': (len(common_fields) / len(required_fields_set)) * 100
    }

def main():
    """Función principal"""
    print("🔍 ANÁLISIS DE DATOS REALES DEL DM")
    print("=" * 50)
    
    # Archivos a analizar
    test_files = [
        (".data/real/1903_cabotage.json", "cabotage"),
        (".data/real/1903_traversing.json", "traversing")
    ]
    
    analyses = {}
    
    for file_path, file_type in test_files:
        print(f"\n📊 Analizando: {file_path}")
        
        data = load_json_file(file_path)
        if not data:
            continue
            
        analysis = analyze_structure(data, file_type)
        analyses[file_type] = analysis
        
        print(f"   📈 Total entradas: {analysis['total_entries']:,}")
        print(f"   📋 Campos encontrados: {len(analysis['fields'])}")
        
        # Mostrar campos principales
        print(f"   🔑 Campos principales:")
        for field, count in list(analysis['fields'].items())[:10]:
            types = ', '.join(analysis['field_types'][field])
            example = analysis['field_examples'][field][0] if analysis['field_examples'][field] else "N/A"
            print(f"      • {field}: {types} (ej: {example})")
    
    # Comparar con estándar
    print(f"\n🎯 COMPARACIÓN CON ESTÁNDAR PORTADA")
    print("=" * 50)
    
    for file_type, analysis in analyses.items():
        print(f"\n📊 {file_type.upper()}:")
        comparison = compare_with_standard(analysis)
        
        print(f"   ✅ Cobertura: {comparison['coverage_percentage']:.1f}%")
        print(f"   📋 Campos comunes: {len(comparison['common_fields'])}/{comparison['required_total']}")
        
        if comparison['missing_fields']:
            print(f"   ❌ Campos faltantes ({len(comparison['missing_fields'])}):")
            for field in comparison['missing_fields'][:10]:
                print(f"      • {field}")
        
        if comparison['extra_fields']:
            print(f"   ➕ Campos adicionales ({len(comparison['extra_fields'])}):")
            for field in comparison['extra_fields'][:10]:
                print(f"      • {field}")
    
    # Recomendaciones
    print(f"\n💡 RECOMENDACIONES")
    print("=" * 30)
    
    for file_type, analysis in analyses.items():
        comparison = compare_with_standard(analysis)
        coverage = comparison['coverage_percentage']
        
        if coverage >= 70:
            print(f"✅ {file_type}: BUENA cobertura ({coverage:.1f}%) - Adaptación simple")
        elif coverage >= 50:
            print(f"⚠️  {file_type}: MEDIA cobertura ({coverage:.1f}%) - Requiere adaptación")
        else:
            print(f"❌ {file_type}: BAJA cobertura ({coverage:.1f}%) - Requiere transformación completa")
    
    return analyses

if __name__ == "__main__":
    analyses = main()