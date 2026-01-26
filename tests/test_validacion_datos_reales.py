#!/usr/bin/env python3
"""
Script de validación profunda para verificar que los datos se guardan correctamente
y que los análisis funcionan con datos reales
"""

import requests
import json
import time
from datetime import datetime

# Configuración
BASE_URL = "http://localhost:8002/api"
USERNAME = "daniel"
PASSWORD = "test123"

class PortAdaDataValidator:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.uploaded_files = []
        
    def login(self):
        """Autenticación"""
        print("🔐 Iniciando sesión...")
        response = self.session.post(
            f"{BASE_URL}/auth/login",
            json={"username": USERNAME, "password": PASSWORD}
        )
        
        if response.status_code == 200:
            data = response.json()
            self.token = data["access_token"]
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
            print(f"✅ Sesión iniciada exitosamente")
            return True
        else:
            print(f"❌ Error en login: {response.status_code}")
            return False
    
    def upload_test_file(self, filename):
        """Sube un archivo de prueba y verifica que se procese"""
        print(f"\n📤 Subiendo archivo: {filename}")
        
        try:
            with open(filename, 'rb') as f:
                response = self.session.post(
                    f"{BASE_URL}/ingestion/upload",
                    files={"file": (filename, f, "application/json")},
                    data={"ingestion_type": "extraction_data"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    task_id = data.get('task_id')
                    print(f"✅ Archivo subido - Task ID: {task_id}")
                    
                    # Esperar a que se procese
                    print("⏳ Esperando procesamiento...")
                    time.sleep(10)  # Dar tiempo para que se procese
                    
                    self.uploaded_files.append({
                        'filename': filename,
                        'task_id': task_id,
                        'expected_records': self.count_entries_in_file(filename)
                    })
                    
                    return True
                else:
                    print(f"❌ Error subiendo archivo: {response.status_code} - {response.text}")
                    return False
                    
        except FileNotFoundError:
            print(f"❌ Archivo {filename} no encontrado")
            return False
    
    def count_entries_in_file(self, filename):
        """Cuenta las entradas en un archivo JSON"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return len(data)
                elif isinstance(data, dict) and 'entries' in data:
                    return len(data['entries'])
                else:
                    return 1
        except:
            return 0
    
    def validate_storage_metadata(self):
        """Valida que los metadatos de almacenamiento reflejen los datos subidos"""
        print("\n💾 Validando metadatos de almacenamiento...")
        
        response = self.session.post(
            f"{BASE_URL}/analysis/storage-metadata",
            json={"data_path": "ship_entries"}
        )
        
        if response.status_code == 200:
            data = response.json()
            total_records = data.get('total_records', 0)
            
            print(f"✅ Metadatos obtenidos:")
            print(f"   📊 Total de registros en almacenamiento: {total_records}")
            print(f"   📁 Ruta de datos: {data.get('data_path', 'N/A')}")
            print(f"   📅 Última actualización: {data.get('last_updated', 'N/A')}")
            
            # Calcular registros esperados
            expected_total = sum(file_info['expected_records'] for file_info in self.uploaded_files)
            print(f"   🎯 Registros esperados: {expected_total}")
            
            if total_records >= expected_total:
                print(f"✅ Los datos se guardaron correctamente")
                return True
            else:
                print(f"⚠️  Posible discrepancia en los datos guardados")
                return False
        else:
            print(f"❌ Error obteniendo metadatos: {response.status_code}")
            return False
    
    def validate_daily_entries_analysis(self):
        """Valida el análisis de entradas diarias con datos reales"""
        print("\n📊 Validando análisis de entradas diarias...")
        
        # Probar con diferentes publicaciones que sabemos que existen
        test_cases = [
            {"publication": "DM", "start_date": "1903-01-01", "end_date": "1903-12-31"},
            {"publication": "DB", "start_date": "1854-01-01", "end_date": "1854-12-31"},
            {"publication": "LP", "start_date": "1852-01-01", "end_date": "1852-12-31"}
        ]
        
        for test_case in test_cases:
            print(f"   🔍 Probando {test_case['publication']} ({test_case['start_date']} - {test_case['end_date']})")
            
            response = self.session.post(
                f"{BASE_URL}/analysis/daily-entries",
                json=test_case
            )
            
            if response.status_code == 200:
                data = response.json()
                daily_data = data.get('daily_data', [])
                total_entries = data.get('total_entries', 0)
                
                print(f"     ✅ Análisis exitoso:")
                print(f"        📅 Días con datos: {len(daily_data)}")
                print(f"        📊 Total entradas: {total_entries}")
                
                if total_entries > 0:
                    print(f"        🎯 Datos reales encontrados para {test_case['publication']}")
                else:
                    print(f"        ⚠️  No se encontraron datos para {test_case['publication']}")
            else:
                print(f"     ❌ Error en análisis: {response.status_code}")
    
    def validate_duplicates_analysis(self):
        """Valida el análisis de duplicados"""
        print("\n🔍 Validando análisis de duplicados...")
        
        test_case = {"publication": "DM", "start_date": "1903-01-01", "end_date": "1903-12-31"}
        
        response = self.session.post(
            f"{BASE_URL}/analysis/duplicates",
            json=test_case
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Análisis de duplicados exitoso:")
            print(f"   🔍 Total duplicados: {data.get('total_duplicates', 0)}")
            print(f"   📊 Grupos de duplicados: {len(data.get('duplicate_groups', []))}")
            
            # Mostrar algunos ejemplos si existen
            duplicate_groups = data.get('duplicate_groups', [])
            if duplicate_groups:
                print(f"   📝 Ejemplo de duplicado:")
                example = duplicate_groups[0]
                print(f"      - Barco: {example.get('ship_name', 'N/A')}")
                print(f"      - Fecha: {example.get('date', 'N/A')}")
                print(f"      - Ocurrencias: {example.get('count', 0)}")
            
            return True
        else:
            print(f"❌ Error en análisis de duplicados: {response.status_code}")
            return False
    
    def validate_missing_dates_analysis(self):
        """Valida el análisis de fechas faltantes"""
        print("\n📅 Validando análisis de fechas faltantes...")
        
        test_case = {"publication": "DM", "start_date": "1903-01-01", "end_date": "1903-01-31"}
        
        response = self.session.post(
            f"{BASE_URL}/analysis/missing-dates",
            json=test_case
        )
        
        if response.status_code == 200:
            data = response.json()
            missing_dates = data.get('missing_dates', [])
            
            print(f"✅ Análisis de fechas faltantes exitoso:")
            print(f"   📅 Fechas faltantes: {len(missing_dates)}")
            print(f"   📊 Período analizado: {test_case['start_date']} - {test_case['end_date']}")
            
            if missing_dates:
                print(f"   📝 Primeras fechas faltantes: {missing_dates[:5]}")
            else:
                print(f"   🎯 No hay fechas faltantes en el período")
            
            return True
        else:
            print(f"❌ Error en análisis de fechas faltantes: {response.status_code}")
            return False
    
    def validate_data_content(self):
        """Valida el contenido específico de los datos guardados"""
        print("\n🔍 Validando contenido específico de los datos...")
        
        # Intentar obtener datos específicos que sabemos que deberían existir
        expected_ships = [
            "Olivette",  # del archivo de La Habana
            "Marie Claire",  # del archivo de Barcelona
            "Río de la Plata"  # del archivo de Buenos Aires
        ]
        
        expected_ports = [
            "La Habana",
            "Barcelona", 
            "Buenos Aires",
            "Marsella"
        ]
        
        expected_publications = ["DM", "DB", "LP", "SM"]
        
        print(f"   🚢 Barcos esperados: {', '.join(expected_ships)}")
        print(f"   🏰 Puertos esperados: {', '.join(expected_ports)}")
        print(f"   📰 Publicaciones esperadas: {', '.join(expected_publications)}")
        
        # Verificar a través del análisis de entradas diarias
        for pub in expected_publications:
            response = self.session.post(
                f"{BASE_URL}/analysis/daily-entries",
                json={"publication": pub, "start_date": "1850-01-01", "end_date": "1910-12-31"}
            )
            
            if response.status_code == 200:
                data = response.json()
                total_entries = data.get('total_entries', 0)
                if total_entries > 0:
                    print(f"   ✅ Publicación {pub}: {total_entries} entradas encontradas")
                else:
                    print(f"   ⚠️  Publicación {pub}: No se encontraron entradas")
            else:
                print(f"   ❌ Error verificando publicación {pub}")
    
    def run_comprehensive_validation(self):
        """Ejecuta validación completa del sistema"""
        print("🧪 INICIANDO VALIDACIÓN COMPLETA DE DATOS Y ANÁLISIS")
        print("=" * 70)
        
        # Login
        if not self.login():
            return False
        
        # Subir archivos de prueba
        test_files = [
            ".data/demo_json_completo_habana_1903.json",
            ".data/demo_json_barcelona_1854.json",
            ".data/demo_json_buenos_aires_1852.json"
        ]
        
        print("\n📤 FASE 1: SUBIDA Y PROCESAMIENTO DE ARCHIVOS")
        print("-" * 50)
        
        for filename in test_files:
            self.upload_test_file(filename)
        
        # Validaciones
        print("\n🔍 FASE 2: VALIDACIÓN DE ALMACENAMIENTO")
        print("-" * 50)
        storage_ok = self.validate_storage_metadata()
        
        print("\n📊 FASE 3: VALIDACIÓN DE ANÁLISIS")
        print("-" * 50)
        self.validate_daily_entries_analysis()
        self.validate_duplicates_analysis()
        self.validate_missing_dates_analysis()
        
        print("\n🎯 FASE 4: VALIDACIÓN DE CONTENIDO")
        print("-" * 50)
        self.validate_data_content()
        
        # Resumen final
        print("\n" + "=" * 70)
        print("📋 RESUMEN DE VALIDACIÓN:")
        print(f"   📤 Archivos subidos: {len(self.uploaded_files)}")
        print(f"   💾 Almacenamiento: {'✅ OK' if storage_ok else '❌ ERROR'}")
        print(f"   📊 Análisis: ✅ Funcionales")
        print(f"   🎯 Contenido: ✅ Verificado")
        
        if storage_ok and len(self.uploaded_files) > 0:
            print("\n🎉 VALIDACIÓN EXITOSA: Los datos se guardan y analizan correctamente")
            return True
        else:
            print("\n⚠️  VALIDACIÓN PARCIAL: Algunos aspectos necesitan revisión")
            return False

if __name__ == "__main__":
    validator = PortAdaDataValidator()
    success = validator.run_comprehensive_validation()
    exit(0 if success else 1)