#!/usr/bin/env python3
"""
Script para convertir TODOS los datos reales del DM al formato estándar PortAda
Procesa todos los archivos de cabotaje y travesías de 1852-1914
"""

import json
import sys
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import glob

class DMDataConverterV2:
    """Convertidor mejorado de datos del DM al formato PortAda"""
    
    def __init__(self):
        self.conversion_stats = {
            'files_processed': 0,
            'files_converted': 0,
            'total_entries_processed': 0,
            'total_entries_converted': 0,
            'errors': 0,
            'warnings': []
        }
    
    def extract_date_from_source_file(self, source_file: str) -> Optional[str]:
        """Extrae fecha del nombre del archivo fuente"""
        try:
            parts = source_file.split('_')
            if len(parts) >= 3:
                year, month, day = parts[0], parts[1], parts[2]
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        except:
            pass
        return None
    
    def parse_arrival_date(self, arrival_date: str, publication_date: str) -> Optional[str]:
        """Parsea fecha de llegada del formato 'Día X:' """
        if not arrival_date or not publication_date:
            return publication_date
            
        # Buscar patrón "Día X:"
        match = re.search(r'Día\s+(\d+):', arrival_date)
        if match:
            try:
                day = int(match.group(1))
                pub_date = datetime.strptime(publication_date, '%Y-%m-%d')
                
                # Asumir que es el mismo mes/año que la publicación
                arrival_date_obj = pub_date.replace(day=day)
                return arrival_date_obj.strftime('%Y-%m-%d')
            except:
                pass
        
        return publication_date
    
    def normalize_ship_type(self, ship_type: str) -> str:
        """Normaliza el tipo de embarcación"""
        if not ship_type:
            return "desconocido"
        
        type_mapping = {
            'vap.': 'vapor',
            'vap': 'vapor',
            'gol.': 'goleta',
            'berg.': 'bergantín',
            'frag.': 'fragata',
            'pol.': 'polacra',
            'jab.': 'jabeque'
        }
        
        return type_mapping.get(ship_type.lower(), ship_type)
    
    def normalize_ship_flag(self, ship_flag: str) -> str:
        """Normaliza la bandera del barco"""
        if not ship_flag:
            return ""
        
        flag_mapping = {
            'am.': 'americano',
            'ing.': 'inglés',
            'inglesa': 'inglés',
            'esp.': 'español',
            'española': 'español',
            'fr.': 'francés',
            'francesa': 'francés',
            'it.': 'italiano',
            'italiana': 'italiano',
            'al.': 'alemán',
            'alemana': 'alemán'
        }
        
        return flag_mapping.get(ship_flag.lower(), ship_flag)
    
    def convert_cargo_list(self, cargo_list: List[Dict]) -> List[Dict]:
        """Convierte la lista de carga al formato PortAda estricto"""
        if not cargo_list:
            return []
        
        converted_cargo = []
        
        for cargo_item in cargo_list:
            cargo_name = cargo_item.get('cargo_name', '')
            cargo_count = cargo_item.get('cargo_count', '')
            cargo_units = cargo_item.get('cargo_units', '')
            
            if cargo_name:
                converted_item = {
                    "cargo_quantity": str(cargo_count) if cargo_count else "0",
                    "cargo_quantity_unit": cargo_units if cargo_units else "unidades",
                    "cargo_name": cargo_name,
                    "cargo_description": f"{cargo_count} {cargo_units} {cargo_name}".strip()
                }
                converted_cargo.append(converted_item)
        
        if converted_cargo:
            return [{
                "cargo_merchant_name": "Sin especificar",
                "cargo": converted_cargo
            }]
        
        return []
    
    def convert_entry(self, entry: Dict, data_type: str, year: str) -> Optional[Dict]:
        """Convierte una entrada individual al formato PortAda ESTRICTO"""
        try:
            self.conversion_stats['total_entries_processed'] += 1
            
            # Extraer fecha de publicación
            publication_date = self.extract_date_from_source_file(entry.get('source_file', ''))
            if not publication_date:
                publication_date = f"{year}-01-01"
            
            # Parsear fecha de llegada
            arrival_date_str = entry.get('arrival_date', '')
            travel_arrival_date = self.parse_arrival_date(arrival_date_str, publication_date)
            
            # Crear entrada convertida - SOLO CAMPOS ESTÁNDAR PORTADA
            converted_entry = {
                "model_version": "boat_fact-00.00.01",
                "publication_date": publication_date,
                "publication_name": "DM",
                "publication_edition": "U",
                "news_section": "E",
                "travel_departure_port": entry.get('travel_departure_port', ''),
                "travel_arrival_port": "La Habana",
                "travel_departure_date": publication_date,
                "travel_arrival_date": travel_arrival_date,
                "travel_arrival_moment": "día",
                "travel_duration_value": "1",
                "travel_duration_unit": "días",
                "travel_port_of_call_list": [],
                "ship_type": self.normalize_ship_type(entry.get('ship_type', '')),
                "ship_flag": self.normalize_ship_flag(entry.get('ship_flag', '')),
                "ship_name": entry.get('ship_name', ''),
                "ship_tons_capacity": "0",
                "ship_tons_unit": "toneladas",
                "master_role": entry.get('master_role', ''),
                "master_name": entry.get('master_name', ''),
                "ship_agent_name": "Sin especificar",
                "crew_number": 0,
                "cargo_list": self.convert_cargo_list(entry.get('cargo_list', []))
            }
            
            self.conversion_stats['total_entries_converted'] += 1
            return converted_entry
            
        except Exception as e:
            self.conversion_stats['errors'] += 1
            self.conversion_stats['warnings'].append(f"Error convirtiendo entrada: {str(e)}")
            return None
    
    def convert_file(self, input_file: str, output_file: str, data_type: str) -> bool:
        """Convierte un archivo completo"""
        try:
            print(f"🔄 Convirtiendo: {Path(input_file).name}")
            
            # Extraer año del nombre del archivo
            year = Path(input_file).stem.split('_')[0]
            
            # Cargar datos originales
            with open(input_file, 'r', encoding='utf-8') as f:
                original_data = json.load(f)
            
            print(f"   📊 Entradas originales: {len(original_data):,}")
            
            # Convertir entradas
            converted_data = []
            for entry in original_data:
                converted_entry = self.convert_entry(entry, data_type, year)
                if converted_entry:
                    converted_data.append(converted_entry)
            
            # Guardar datos convertidos
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(converted_data, f, indent=2, ensure_ascii=False)
            
            print(f"   ✅ Entradas convertidas: {len(converted_data):,}")
            print(f"   💾 Guardado en: {Path(output_file).name}")
            
            self.conversion_stats['files_processed'] += 1
            self.conversion_stats['files_converted'] += 1
            
            return True
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            self.conversion_stats['files_processed'] += 1
            self.conversion_stats['errors'] += 1
            return False

def main():
    """Función principal"""
    print("🔄 CONVERSIÓN MASIVA DE DATOS REALES DEL DM")
    print("=" * 60)
    
    converter = DMDataConverterV2()
    
    # Crear directorio de salida
    output_dir = Path(".data/converted")
    output_dir.mkdir(exist_ok=True)
    
    # Encontrar todos los archivos JSON reales
    real_data_dir = Path(".data/real")
    if not real_data_dir.exists():
        print(f"❌ Directorio no encontrado: {real_data_dir}")
        return False
    
    # Buscar archivos por patrón
    cabotage_files = sorted(glob.glob(str(real_data_dir / "*_cabotage.json")))
    traversing_files = sorted(glob.glob(str(real_data_dir / "*_traversing.json")))
    
    all_files = [(f, "cabotage") for f in cabotage_files] + [(f, "traversing") for f in traversing_files]
    
    print(f"📁 Archivos encontrados:")
    print(f"   🚢 Cabotaje: {len(cabotage_files)} archivos")
    print(f"   🌊 Travesías: {len(traversing_files)} archivos")
    print(f"   📊 Total: {len(all_files)} archivos")
    
    if not all_files:
        print("❌ No se encontraron archivos para procesar")
        return False
    
    # Procesar archivos
    print(f"\n🔄 INICIANDO CONVERSIÓN...")
    print("=" * 40)
    
    success_count = 0
    
    for input_file, data_type in all_files:
        input_path = Path(input_file)
        output_file = output_dir / f"{input_path.stem}_converted.json"
        
        if converter.convert_file(input_file, str(output_file), data_type):
            success_count += 1
    
    # Mostrar estadísticas finales
    print(f"\n📊 ESTADÍSTICAS FINALES")
    print("=" * 40)
    print(f"✅ Archivos convertidos: {success_count}/{len(all_files)}")
    print(f"📊 Entradas procesadas: {converter.conversion_stats['total_entries_processed']:,}")
    print(f"✅ Entradas convertidas: {converter.conversion_stats['total_entries_converted']:,}")
    print(f"❌ Errores: {converter.conversion_stats['errors']:,}")
    
    if converter.conversion_stats['warnings']:
        print(f"\n⚠️  ADVERTENCIAS ({len(converter.conversion_stats['warnings'])}):")
        for warning in converter.conversion_stats['warnings'][:5]:
            print(f"   • {warning}")
        if len(converter.conversion_stats['warnings']) > 5:
            print(f"   ... y {len(converter.conversion_stats['warnings']) - 5} más")
    
    # Resumen por década
    print(f"\n📅 RESUMEN POR PERÍODO:")
    decades = {}
    for input_file, _ in all_files:
        year = int(Path(input_file).stem.split('_')[0])
        decade = (year // 10) * 10
        if decade not in decades:
            decades[decade] = 0
        decades[decade] += 1
    
    for decade in sorted(decades.keys()):
        print(f"   📆 {decade}s: {decades[decade]} archivos")
    
    print(f"\n📁 Archivos convertidos guardados en: {output_dir}")
    
    # Sugerencias para siguiente paso
    print(f"\n🚀 PRÓXIMOS PASOS:")
    print(f"   1. Probar algunos archivos convertidos en el sistema")
    print(f"   2. Si funcionan, crear script de carga masiva")
    print(f"   3. Procesar todos los archivos en lotes")
    
    return success_count > 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)