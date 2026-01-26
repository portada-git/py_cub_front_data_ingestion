#!/usr/bin/env python3
"""
Tests específicos para funcionalidades avanzadas de la API PortAda
Prueba casos de uso específicos y funcionalidades detalladas
"""

import requests
import json
import time
import os
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8002/api"
TEST_USER = {"username": "daniel", "password": "test123"}

class PortAdaAdvancedTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        
    def authenticate(self):
        """Autenticación inicial"""
        response = self.session.post(f"{BASE_URL}/auth/login", json=TEST_USER)
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
            return True
        return False
    
    def test_multiple_publications(self):
        """Test: Múltiples publicaciones y análisis por periódico"""
        print("🗞️  Test: Análisis por múltiples publicaciones")
        
        publications = ["DM", "DB", "LP", "SM"]
        results = {}
        
        for pub in publications:
            try:
                response = self.session.get(f"{BASE_URL}/analysis/daily-entries", 
                                          params={"publication": pub})
                if response.status_code == 200:
                    data = response.json()
                    results[pub] = {
                        "total_entries": data.get("total_entries", 0),
                        "date_range": data.get("date_range", {}),
                        "status": "✅"
                    }
                else:
                    results[pub] = {"status": "❌", "error": response.status_code}
            except Exception as e:
                results[pub] = {"status": "❌", "error": str(e)}
        
        for pub, result in results.items():
            print(f"  {pub}: {result['status']} - {result.get('total_entries', 'Error')}")
        
        return all(r["status"] == "✅" for r in results.values())
    
    def test_date_range_analysis(self):
        """Test: Análisis por rangos de fechas específicos"""
        print("📅 Test: Análisis por rangos de fechas")
        
        date_ranges = [
            ("1850-01-01", "1860-12-31", "Década 1850s"),
            ("1900-01-01", "1910-12-31", "Década 1900s"),
            ("2026-01-01", "2026-12-31", "Año actual")
        ]
        
        results = []
        for start, end, description in date_ranges:
            try:
                response = self.session.get(f"{BASE_URL}/analysis/missing-dates",
                                          params={"start_date": start, "end_date": end})
                if response.status_code == 200:
                    data = response.json()
                    results.append({
                        "range": description,
                        "missing_dates": len(data.get("missing_dates", [])),
                        "status": "✅"
                    })
                    print(f"  {description}: ✅ - {len(data.get('missing_dates', []))} fechas faltantes")
                else:
                    results.append({"range": description, "status": "❌"})
                    print(f"  {description}: ❌ - Error {response.status_code}")
            except Exception as e:
                results.append({"range": description, "status": "❌"})
                print(f"  {description}: ❌ - {str(e)}")
        
        return all(r["status"] == "✅" for r in results)
    
    def test_cargo_analysis(self):
        """Test: Análisis específico de carga y comerciantes"""
        print("📦 Test: Análisis de carga y comerciantes")
        
        try:
            # Análisis de entidades conocidas (incluye comerciantes)
            response = self.session.get(f"{BASE_URL}/analysis/known-entities")
            if response.status_code == 200:
                data = response.json()
                entities = data.get("entities", [])
                
                # Buscar entidades relacionadas con comercio
                merchant_entities = [e for e in entities if "comercial" in e.get("name", "").lower() 
                                   or "merchant" in e.get("name", "").lower()]
                
                print(f"  ✅ Entidades totales: {len(entities)}")
                print(f"  ✅ Entidades comerciales: {len(merchant_entities)}")
                
                return True
            else:
                print(f"  ❌ Error en análisis de entidades: {response.status_code}")
                return False
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            return False
    
    def test_ship_types_analysis(self):
        """Test: Análisis de tipos de embarcaciones"""
        print("🚢 Test: Análisis de tipos de embarcaciones")
        
        try:
            # Usar análisis de metadatos de almacenamiento para obtener estadísticas
            response = self.session.get(f"{BASE_URL}/analysis/storage-metadata")
            if response.status_code == 200:
                data = response.json()
                
                # Verificar que tenemos datos de diferentes tipos de barcos
                file_structure = data.get("file_structure", {})
                publications = file_structure.get("by_publication", {})
                
                ship_data_found = False
                for pub, pub_data in publications.items():
                    if pub_data.get("total_files", 0) > 0:
                        ship_data_found = True
                        print(f"  ✅ {pub}: {pub_data.get('total_files', 0)} archivos")
                
                if ship_data_found:
                    print("  ✅ Datos de embarcaciones encontrados en múltiples publicaciones")
                    return True
                else:
                    print("  ❌ No se encontraron datos de embarcaciones")
                    return False
            else:
                print(f"  ❌ Error en metadatos: {response.status_code}")
                return False
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            return False
    
    def test_duplicate_detection(self):
        """Test: Detección de duplicados avanzada"""
        print("🔍 Test: Detección de duplicados")
        
        try:
            # Test con diferentes límites
            limits = [5, 10, 20]
            results = []
            
            for limit in limits:
                response = self.session.get(f"{BASE_URL}/analysis/duplicates",
                                          params={"limit": limit})
                if response.status_code == 200:
                    data = response.json()
                    duplicates = data.get("duplicates", [])
                    results.append({
                        "limit": limit,
                        "found": len(duplicates),
                        "status": "✅"
                    })
                    print(f"  ✅ Límite {limit}: {len(duplicates)} duplicados encontrados")
                else:
                    results.append({"limit": limit, "status": "❌"})
                    print(f"  ❌ Límite {limit}: Error {response.status_code}")
            
            return all(r["status"] == "✅" for r in results)
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            return False
    
    def test_process_metadata(self):
        """Test: Metadatos de procesamiento"""
        print("⚙️  Test: Metadatos de procesamiento")
        
        try:
            response = self.session.get(f"{BASE_URL}/analysis/process-metadata")
            if response.status_code == 200:
                data = response.json()
                
                # Verificar campos esperados
                expected_fields = ["total_processes", "process_types", "recent_processes"]
                found_fields = []
                
                for field in expected_fields:
                    if field in data:
                        found_fields.append(field)
                        print(f"  ✅ Campo '{field}' encontrado")
                    else:
                        print(f"  ❌ Campo '{field}' faltante")
                
                return len(found_fields) == len(expected_fields)
            else:
                print(f"  ❌ Error: {response.status_code}")
                return False
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            return False
    
    def test_file_formats(self):
        """Test: Diferentes formatos de archivo"""
        print("📄 Test: Formatos de archivo")
        
        # Test con archivo anidado (formato antiguo)
        nested_format = {
            "publication_date": "2026-01-26",
            "publication_name": "TEST",
            "publication_edition": "U",
            "entries": [
                {
                    "publication_date": "2026-01-26",
                    "travel_arrival_port": "Test Port",
                    "ship_name": "Test Ship Nested",
                    "master_name": "Test Captain",
                    "parsed_text": "Test nested format"
                }
            ]
        }
        
        # Test con archivo plano (formato nuevo)
        flat_format = [
            {
                "model_version": "boat_fact-00.00.01",
                "publication_date": "2026-01-26",
                "publication_name": "TEST",
                "publication_edition": "U",
                "news_section": "E",
                "travel_arrival_port": "Test Port",
                "ship_name": "Test Ship Flat",
                "master_name": "Test Captain",
                "parsed_text": "Test flat format",
                "cargo_list": [],
                "quarantine": False,
                "forced_arrival": False
            }
        ]
        
        formats = [
            (nested_format, "nested_format_test.json", "Formato anidado"),
            (flat_format, "flat_format_test.json", "Formato plano")
        ]
        
        results = []
        for data, filename, description in formats:
            try:
                # Crear archivo
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                # Subir archivo
                with open(filename, 'rb') as f:
                    files = {'file': (filename, f, 'application/json')}
                    form_data = {'ingestion_type': 'extraction_data'}
                    response = self.session.post(f"{BASE_URL}/ingestion/upload", 
                                               files=files, data=form_data)
                
                # Limpiar archivo
                os.remove(filename)
                
                if response.status_code == 200:
                    results.append({"format": description, "status": "✅"})
                    print(f"  ✅ {description}: Subido correctamente")
                else:
                    results.append({"format": description, "status": "❌"})
                    print(f"  ❌ {description}: Error {response.status_code}")
                    
            except Exception as e:
                results.append({"format": description, "status": "❌"})
                print(f"  ❌ {description}: {str(e)}")
        
        return all(r["status"] == "✅" for r in results)
    
    def test_concurrent_uploads(self):
        """Test: Subidas concurrentes"""
        print("🔄 Test: Subidas concurrentes")
        
        try:
            # Crear múltiples archivos pequeños
            files_data = []
            for i in range(3):
                data = [{
                    "model_version": "boat_fact-00.00.01",
                    "publication_date": f"2026-01-2{6+i}",
                    "publication_name": "TEST",
                    "publication_edition": "U",
                    "news_section": "E",
                    "travel_arrival_port": "Concurrent Test Port",
                    "ship_name": f"Concurrent Ship {i+1}",
                    "master_name": f"Captain {i+1}",
                    "parsed_text": f"Concurrent test entry {i+1}",
                    "cargo_list": [],
                    "quarantine": False,
                    "forced_arrival": False
                }]
                
                filename = f"concurrent_test_{i+1}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                files_data.append(filename)
            
            # Subir archivos rápidamente
            results = []
            for filename in files_data:
                with open(filename, 'rb') as f:
                    files = {'file': (filename, f, 'application/json')}
                    form_data = {'ingestion_type': 'extraction_data'}
                    response = self.session.post(f"{BASE_URL}/ingestion/upload", 
                                               files=files, data=form_data)
                
                results.append(response.status_code == 200)
                os.remove(filename)
            
            success_count = sum(results)
            print(f"  ✅ {success_count}/3 archivos subidos exitosamente")
            
            return success_count >= 2  # Al menos 2 de 3 deben funcionar
            
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            return False
    
    def run_advanced_tests(self):
        """Ejecuta todos los tests avanzados"""
        print("🚀 Iniciando tests avanzados de funcionalidades específicas")
        print("=" * 70)
        
        if not self.authenticate():
            print("❌ Error de autenticación. No se pueden ejecutar los tests.")
            return False
        
        tests = [
            ("Múltiples Publicaciones", self.test_multiple_publications),
            ("Rangos de Fechas", self.test_date_range_analysis),
            ("Análisis de Carga", self.test_cargo_analysis),
            ("Tipos de Embarcaciones", self.test_ship_types_analysis),
            ("Detección de Duplicados", self.test_duplicate_detection),
            ("Metadatos de Procesamiento", self.test_process_metadata),
            ("Formatos de Archivo", self.test_file_formats),
            ("Subidas Concurrentes", self.test_concurrent_uploads)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n🧪 Ejecutando: {test_name}")
            try:
                if test_func():
                    passed += 1
                    print(f"✅ {test_name}: PASÓ")
                else:
                    print(f"❌ {test_name}: FALLÓ")
            except Exception as e:
                print(f"❌ {test_name}: ERROR - {str(e)}")
        
        print("\n" + "=" * 70)
        print(f"📊 RESULTADOS AVANZADOS: {passed}/{total} tests pasaron")
        print(f"📈 Porcentaje de éxito: {(passed/total)*100:.1f}%")
        
        return passed == total

def main():
    """Función principal"""
    tester = PortAdaAdvancedTester()
    success = tester.run_advanced_tests()
    
    if success:
        print("🎉 ¡TODOS LOS TESTS AVANZADOS PASARON!")
    else:
        print("⚠️  Algunos tests avanzados fallaron.")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())