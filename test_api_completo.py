#!/usr/bin/env python3
"""
Test completo de todas las funcionalidades de la API PortAda
Prueba todos los endpoints y funcionalidades disponibles
"""

import requests
import json
import time
import os
from typing import Dict, Any, List

# Configuración
BASE_URL = "http://localhost:8002/api"
TEST_USER = {"username": "daniel", "password": "test123"}

class PortAdaAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Registra el resultado de un test"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
    
    def test_health_check(self):
        """Test 1: Health Check"""
        try:
            response = self.session.get(f"{BASE_URL}/health")
            success = response.status_code == 200 and response.json().get("status") == "healthy"
            self.log_test("Health Check", success, f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Health Check", False, str(e))
            return False
    
    def test_cors_check(self):
        """Test 2: CORS Configuration"""
        try:
            response = self.session.get(f"{BASE_URL}/cors-test")
            success = response.status_code == 200 and "CORS is working" in response.json().get("message", "")
            self.log_test("CORS Configuration", success, f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("CORS Configuration", False, str(e))
            return False
    
    def test_authentication(self):
        """Test 3: Authentication System"""
        try:
            # Test login
            response = self.session.post(f"{BASE_URL}/auth/login", json=TEST_USER)
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                self.log_test("User Login", True, f"Token received: {self.token[:20]}...")
                
                # Test token validation
                response = self.session.get(f"{BASE_URL}/health")
                success = response.status_code == 200
                self.log_test("Token Validation", success, f"Authenticated request: {response.status_code}")
                return success
            else:
                self.log_test("User Login", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Authentication System", False, str(e))
            return False
    
    def test_file_upload_extraction_data(self):
        """Test 4: File Upload - Extraction Data"""
        try:
            # Crear archivo de prueba
            test_data = [
                {
                    "model_version": "boat_fact-00.00.01",
                    "publication_date": "2026-01-26",
                    "publication_name": "TEST",
                    "publication_edition": "U",
                    "news_section": "E",
                    "travel_departure_port": "Test Port",
                    "travel_arrival_port": "Destination Port",
                    "travel_departure_date": "2026-01-25",
                    "travel_arrival_date": "2026-01-26",
                    "travel_arrival_moment": "mañana",
                    "travel_duration_value": "1",
                    "travel_duration_unit": "días",
                    "travel_port_of_call_list": [],
                    "ship_type": "vapor",
                    "ship_flag": "test",
                    "ship_name": "Test Ship",
                    "ship_tons_capacity": "1000",
                    "ship_tons_unit": "toneladas",
                    "master_role": "cap.",
                    "master_name": "Test Captain",
                    "ship_agent_name": "Test Agent",
                    "crew_number": 50,
                    "cargo_list": [
                        {
                            "cargo_merchant_name": "Test Merchant",
                            "cargo": [
                                {
                                    "cargo_quantity": "100",
                                    "cargo_unit": "cajas",
                                    "cargo_commodity": "test cargo"
                                }
                            ]
                        }
                    ],
                    "quarantine": False,
                    "forced_arrival": False,
                    "ship_amount": None,
                    "ship_origin_area": None,
                    "parsed_text": "Test entry for API testing",
                    "obs": "API Test Entry"
                }
            ]
            
            # Guardar archivo temporal
            test_file = "test_extraction_data.json"
            with open(test_file, 'w', encoding='utf-8') as f:
                json.dump(test_data, f, ensure_ascii=False, indent=2)
            
            # Subir archivo
            with open(test_file, 'rb') as f:
                files = {'file': (test_file, f, 'application/json')}
                data = {'ingestion_type': 'extraction_data'}
                response = self.session.post(f"{BASE_URL}/ingestion/upload", files=files, data=data)
            
            # Limpiar archivo temporal
            os.remove(test_file)
            
            success = response.status_code == 200 and "task_id" in response.json()
            task_id = response.json().get("task_id") if success else None
            self.log_test("File Upload - Extraction Data", success, 
                         f"Status: {response.status_code}, Task ID: {task_id}")
            
            # Esperar procesamiento
            if success and task_id:
                time.sleep(5)  # Dar tiempo para procesamiento
                
            return success
        except Exception as e:
            self.log_test("File Upload - Extraction Data", False, str(e))
            return False
    
    def test_analysis_endpoints(self):
        """Test 5: Analysis Endpoints"""
        # Endpoints GET
        get_endpoints = [
            ("pending-files", "Pending Files Analysis"),
            ("known-entities", "Known Entities Analysis")
        ]
        
        # Endpoints POST (requieren request body)
        post_endpoints = [
            ("daily-entries", "Daily Entries Analysis", {"publication": "DM", "start_date": "1900-01-01", "end_date": "2026-12-31"}),
            ("duplicates", "Duplicates Analysis", {"limit": 10}),
            ("missing-dates", "Missing Dates Analysis", {"publication": "DM", "start_date": "1900-01-01", "end_date": "2026-12-31"}),
            ("storage-metadata", "Storage Metadata Analysis", {"include_file_details": True}),
            ("process-metadata", "Process Metadata Analysis", {"include_recent_processes": True})
        ]
        
        all_success = True
        
        # Test GET endpoints
        for endpoint, name in get_endpoints:
            try:
                response = self.session.get(f"{BASE_URL}/analysis/{endpoint}")
                success = response.status_code == 200
                if not success:
                    all_success = False
                self.log_test(f"Analysis - {name}", success, f"Status: {response.status_code}")
            except Exception as e:
                self.log_test(f"Analysis - {name}", False, str(e))
                all_success = False
        
        # Test POST endpoints
        for endpoint, name, request_data in post_endpoints:
            try:
                response = self.session.post(f"{BASE_URL}/analysis/{endpoint}", json=request_data)
                success = response.status_code == 200
                if not success:
                    all_success = False
                self.log_test(f"Analysis - {name}", success, f"Status: {response.status_code}")
            except Exception as e:
                self.log_test(f"Analysis - {name}", False, str(e))
                all_success = False
        
        return all_success
    
    def test_analysis_with_filters(self):
        """Test 6: Analysis with Filters"""
        try:
            # Test con filtros de publicación
            request_data = {"publication": "DM", "start_date": "1900-01-01", "end_date": "2026-12-31"}
            response = self.session.post(f"{BASE_URL}/analysis/daily-entries", json=request_data)
            success1 = response.status_code == 200
            
            # Test con filtros de fecha
            request_data = {"start_date": "2026-01-01", "end_date": "2026-01-31"}
            response = self.session.post(f"{BASE_URL}/analysis/missing-dates", json=request_data)
            success2 = response.status_code == 200
            
            # Test duplicates con límite
            request_data = {"limit": 10}
            response = self.session.post(f"{BASE_URL}/analysis/duplicates", json=request_data)
            success3 = response.status_code == 200
            
            success = success1 and success2 and success3
            self.log_test("Analysis with Filters", success, 
                         f"Daily entries: {success1}, Missing dates: {success2}, Duplicates: {success3}")
            return success
        except Exception as e:
            self.log_test("Analysis with Filters", False, str(e))
            return False
    
    def test_data_persistence(self):
        """Test 7: Data Persistence"""
        try:
            # Verificar que los datos persisten después del procesamiento
            request_data = {"include_file_details": True}
            response = self.session.post(f"{BASE_URL}/analysis/storage-metadata", json=request_data)
            if response.status_code == 200:
                data = response.json()
                total_files = data.get("total_files", 0)
                total_records = data.get("total_records", 0)
                
                success = total_files > 0 and total_records > 0
                self.log_test("Data Persistence", success, 
                             f"Files: {total_files}, Records: {total_records}")
                return success
            else:
                self.log_test("Data Persistence", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Data Persistence", False, str(e))
            return False
    
    def test_error_handling(self):
        """Test 8: Error Handling"""
        try:
            # Test archivo inválido
            test_file = "invalid_test.json"
            with open(test_file, 'w') as f:
                f.write("invalid json content")
            
            with open(test_file, 'rb') as f:
                files = {'file': (test_file, f, 'application/json')}
                data = {'ingestion_type': 'extraction_data'}
                response = self.session.post(f"{BASE_URL}/ingestion/upload", files=files, data=data)
            
            os.remove(test_file)
            
            # Debe manejar el error gracefully
            success = response.status_code in [400, 422, 500]  # Error esperado
            self.log_test("Error Handling - Invalid JSON", success, 
                         f"Status: {response.status_code}")
            
            # Test endpoint inexistente
            response = self.session.get(f"{BASE_URL}/nonexistent-endpoint")
            success2 = response.status_code == 404
            self.log_test("Error Handling - 404 Not Found", success2, 
                         f"Status: {response.status_code}")
            
            return success and success2
        except Exception as e:
            self.log_test("Error Handling", False, str(e))
            return False
    
    def test_logout(self):
        """Test 9: Logout"""
        try:
            response = self.session.post(f"{BASE_URL}/auth/logout")
            success = response.status_code in [200, 401]  # 401 si ya expiró
            self.log_test("User Logout", success, f"Status: {response.status_code}")
            
            # Limpiar token
            self.token = None
            if "Authorization" in self.session.headers:
                del self.session.headers["Authorization"]
            
            return success
        except Exception as e:
            self.log_test("User Logout", False, str(e))
            return False
    
    def test_performance(self):
        """Test 10: Performance Test"""
        try:
            start_time = time.time()
            response = self.session.get(f"{BASE_URL}/health")
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000  # en ms
            success = response.status_code == 200 and response_time < 1000  # < 1 segundo
            
            self.log_test("Performance Test", success, 
                         f"Response time: {response_time:.2f}ms")
            return success
        except Exception as e:
            self.log_test("Performance Test", False, str(e))
            return False
    
    def run_all_tests(self):
        """Ejecuta todos los tests"""
        print("🚀 Iniciando tests completos de la API PortAda")
        print("=" * 60)
        
        tests = [
            self.test_health_check,
            self.test_cors_check,
            self.test_authentication,
            self.test_file_upload_extraction_data,
            self.test_analysis_endpoints,
            self.test_analysis_with_filters,
            self.test_data_persistence,
            self.test_error_handling,
            self.test_logout,
            self.test_performance
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            if test():
                passed += 1
            print()  # Línea en blanco entre tests
        
        print("=" * 60)
        print(f"📊 RESULTADOS FINALES: {passed}/{total} tests pasaron")
        print(f"📈 Porcentaje de éxito: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("🎉 ¡TODOS LOS TESTS PASARON! La API está completamente funcional.")
        else:
            print("⚠️  Algunos tests fallaron. Revisar los detalles arriba.")
        
        return passed == total

def main():
    """Función principal"""
    tester = PortAdaAPITester()
    success = tester.run_all_tests()
    
    # Guardar resultados en archivo
    with open("test_results.json", "w", encoding="utf-8") as f:
        json.dump(tester.test_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 Resultados guardados en: test_results.json")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())