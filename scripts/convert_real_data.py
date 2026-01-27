#!/usr/bin/env python3
"""
Script para convertir datos reales del DM al formato estándar PortAda
Maneja dos tipos: cabotage (cabotaje) y traversing (travesías)
"""

import json
import sys
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

class DMDataConverter:
    """Convertidor de datos del DM al formato PortAda"""
    
    def __init__(self):
        self.conversion_stats = {
            'processed': 0,
            'converted': 0,
            'errors': 0,
            'warnings': []
        }
    
    def extract_date_from_source_file(self, source_file: str) -> Optional[str]:
        """Extrae fecha del nombre del archivo fuente"""
        # Formato: 1903_01_06 -> 1903-01-06
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
            return None
            
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
        
        return None
    
    def normalize_ship_type(self, ship_type: str) -> str:
        """Normaliza el tipo de embarcación"""
        if not ship_type:
            return "desconocido"
        
        # Mapeo de tipos comunes
        type_mapping = {
            'vap.': 'vapor',
            'vap': 'vapor',
            'gol.': 'goleta',
            'berg.': 'bergantín',
            'frag.': 'fragata'
        }
        
        return type_mapping.get(ship_type.lower(), ship_type)
    
    def normalize_ship_flag(self, ship_flag: str) -> str:
        """Normaliza la bandera del barco"""
        if not ship_flag:
            return ""
        
        # Mapeo de banderas comunes
        flag_mapping = {
            'am.': 'americano',
            'ing.': 'inglés',
            'esp.': 'español',
            'fr.': 'francés',
            'it.': 'italiano',
            'al.': 'alemán'
        }
        
        return flag_mapping.get(ship_flag.lower(), ship_flag)
    
    def convert_cargo_list(self, cargo_list: List[Dict]) -> List[Dict]:
        """Convierte la lista de carga al formato PortAda"""
        if not cargo_list:
            return []
        
        # Formato PortAda requiere estructura específica
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
        
        # Envolver en estructura de comerciante
        if converted_cargo:
            return [{
                "cargo_merchant_name": "Sin especificar",
                "cargo": converted_cargo
            }]
        
        return []
    
    def determine_travel_type(self, data_type: str, travel_departure_port: str) -> str:
        """Determina si es cabotaje o travesía"""
        if data_type == "cabotage":
            return "cabotaje"
        elif data_type == "traversing":
            return "travesía"
        
        # Puertos cubanos comunes para cabotaje
        cuban_ports = [
            'caibarién', 'sagua', 'mantua', 'matanzas', 'cárdenas', 
            'cienfuegos', 'trinidad', 'santiago', 'baracoa', 'manzanillo'
        ]
        
        if any(port in travel_departure_port.lower() for port in cuban_ports):
            return "cabotaje"
        else:
            return "travesía"
    
    def convert_entry(self, entry: Dict, data_type: str, year: str) -> Optional[Dict]:
        """Convierte una entrada individual al formato PortAda"""
        try:
            self.conversion_stats['processed'] += 1
            
            # Extraer fecha de publicación
            publication_date = self.extract_date_from_source_file(entry.get('source_file', ''))
            if not publication_date:
                publication_date = f"{year}-01-01"  # Fallback
            
            # Determinar puerto de llegada
            travel_arrival_port = "La Habana"  # Asumir La Habana como puerto de llegada por defecto
            
            # Parsear fecha de llegada
            arrival_date_str = entry.get('arrival_date', '')
            travel_arrival_date = self.parse_arrival_date(arrival_date_str, publication_date)
            if not travel_arrival_date:
                travel_arrival_date = publication_date  # Fallback
            
            # Crear entrada convertida
            converted_entry = {
                "model_version": "boat_fact-00.00.01",
                "publication_date": publication_date,
                "publication_name": "DM",
                "publication_edition": "U",  # Asumir edición única
                "news_section": "E",
                "travel_departure_port": entry.get('travel_departure_port', ''),
                "travel_arrival_port": travel_arrival_port,
                "travel_departure_date": publication_date,  # Asumir mismo día
                "travel_arrival_date": travel_arrival_date,
                "travel_arrival_moment": "día",  # Valor por defecto
                "travel_duration_value": "1",  # Valor por defecto
                "travel_duration_unit": "días",
                "travel_port_of_call_list": [],
                "ship_type": self.normalize_ship_type(entry.get('ship_type', '')),
                "ship_flag": self.normalize_ship_flag(entry.get('ship_flag', '')),
                "ship_name": entry.get('ship_name', ''),
                "ship_tons_capacity": "0",  # No disponible en datos originales
                "ship_tons_unit": "toneladas",
                "master_role": entry.get('master_role', ''),
                "master_name": entry.get('master_name', ''),
                "ship_agent_name": "Sin especificar",  # No disponible
                "crew_number": 0,  # No disponible
                "cargo_list": self.convert_cargo_list(entry.get('cargo_list', [])),
                
                # Campos adicionales para preservar información original
                "original_source_file": entry.get('source_file', ''),
                "original_raw_text": entry.get('raw_text', ''),
                "travel_type": self.determine_travel_type(data_type, entry.get('travel_departure_port', '')),
                "data_source": f"DM_{year}_{data_type}"
            }
            
            self.conversion_stats['converted'] += 1
            return converted_entry
            
        except Exception as e:
            self.conversion_stats['errors'] += 1
            self.conversion_stats['warnings'].append(f"Error convirtiendo entrada: {str(e)}")
            return None
    
    def convert_file(self, input_file: str, output_file: str, data_type: str) -> bool:
        """Convierte un archivo completo"""
        try:
            print(f"🔄 Convirtiendo: {input_file}")
            
            # Extraer año del nombre del archivo
            year = Path(input_file).stem.split('_')[0]
            
            # Cargar datos originales
            with open(input_file, 'r', encoding='utf-8') as f:
                original_data = json.load(f)
            
            print(f"   📊 Entradas originales: {len(original_data)}")
            
            # Convertir entradas
            converted_data = []
            for entry in original_data:
                converted_entry = self.convert_entry(entry, data_type, year)
                if converted_entry:
                    converted_data.append(converted_entry)
            
            # Guardar datos convertidos
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(converted_data, f, indent=2, ensure_ascii=False)
            
            print(f"   ✅ Entradas convertidas: {len(converted_data)}")
            print(f"   💾 Guardado en: {output_file}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False

def main():
    """Función principal"""
    print("🔄 CONVERSIÓN DE DATOS REALES DEL DM")
    print("=" * 50)
    
    converter = DMDataConverter()
    
    # Crear directorio de salida
    output_dir = Path(".data/converted")
    output_dir.mkdir(exist_ok=True)
    
    # Archivos de prueba
    test_files = [
        (".data/real/1903_cabotage.json", "cabotage"),
        (".data/real/1903_traversing.json", "traversing")
    ]
    
    success_count = 0
    
    for input_file, data_type in test_files:
        if not Path(input_file).exists():
            print(f"⚠️  Archivo no encontrado: {input_file}")
            continue
        
        # Generar nombre de archivo de salida
        input_path = Path(input_file)
        output_file = output_dir / f"{input_path.stem}_converted.json"
        
        # Convertir archivo
        if converter.convert_file(input_file, str(output_file), data_type):
            success_count += 1
    
    # Mostrar estadísticas
    print(f"\n📊 ESTADÍSTICAS DE CONVERSIÓN")
    print("=" * 40)
    print(f"✅ Archivos convertidos: {success_count}/{len(test_files)}")
    print(f"📊 Entradas procesadas: {converter.conversion_stats['processed']}")
    print(f"✅ Entradas convertidas: {converter.conversion_stats['converted']}")
    print(f"❌ Errores: {converter.conversion_stats['errors']}")
    
    if converter.conversion_stats['warnings']:
        print(f"\n⚠️  ADVERTENCIAS:")
        for warning in converter.conversion_stats['warnings'][:5]:
            print(f"   • {warning}")
    
    print(f"\n📁 Archivos convertidos guardados en: {output_dir}")
    
    return success_count > 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)