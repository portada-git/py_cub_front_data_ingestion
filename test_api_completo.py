#!/usr/bin/env python3
"""
Script de prueba completo para verificar todas las funcionalidades del API PortAda
"""

import requests
import json
import time
from pathlib import Path

# Configuración
BASE_URL = "http://localhost:8002/api"
USERNAME = "daniel"
PASSWORD = "test123"

class PortAdaAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        
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
            print(f"✅ Sesión iniciada exitosamente para usuario: {data['user_info']['username']}")
            return True
        else:
            print(f"❌ Error en login: {response.status_code} - {response.text}")
            return False
    
    def test_health(self):
        """Prueba de salud del sistema"""
        print("\n🏥 Probando health check...")
        response = self.session.get(f"{BASE_URL}/health")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Sistema saludable: {data['status']}")
            return True
        else:
            print(f"❌ Error en health check: {response.status_code}")
            return False
    
    def test_known_entities(self):
        """Prueba de entidades conocidas"""
        print("\n🧠 Probando análisis de entidades conocidas...")
        response = self.session.get(f"{BASE_URL}/analysis/known-entities")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Entidades conocidas: {data['total_entities']} entidades encontradas")
            print(f"   Tipos disponibles: {', '.join(data['entity_types'])}")
            return True
        else:
            print(f"❌ Error en entidades conocidas: {response.status_code} - {response.text}")
            return False
    
    def test_pending_files(self):
        """Prueba de archivos pendientes"""
        print("\n📁 Probando análisis de archivos pendientes...")
        response = self.session.get(f"{BASE_URL}/analysis/pending-files")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Archivos pendientes: {data['total_pending']} archivos")
            return True
        else:
            print(f"❌ Error en archivos pendientes: {response.status_code} - {response.text}")
            return False
    
    def test_daily_entries(self):
        """Prueba de análisis de entradas diarias"""
        print("\n📊 Probando análisis de entradas diarias...")
        payload = {
            "publication_name": "DM",
            "start_date": "1903-01-01",
            "end_date": "1903-12-31"
        }
        response = self.session.post(f"{BASE_URL}/analysis/daily-entries", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Análisis de entradas diarias completado")
            print(f"   Total de días analizados: {len(data.get('daily_data', []))}")
            return True
        else:
            print(f"❌ Error en entradas diarias: {response.status_code} - {response.text}")
            return False
    
    def test_duplicates_analysis(self):
        """Prueba de análisis de duplicados"""
        print("\n🔍 Probando análisis de duplicados...")
        payload = {
            "publication_name": "DM",
            "start_date": "1903-01-01",
            "end_date": "1903-12-31"
        }
        response = self.session.post(f"{BASE_URL}/analysis/duplicates", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Análisis de duplicados completado")
            print(f"   Duplicados encontrados: {data.get('total_duplicates', 0)}")
            return True
        else:
            print(f"❌ Error en análisis de duplicados: {response.status_code} - {response.text}")
            return False
    
    def test_missing_dates(self):
        """Prueba de análisis de fechas faltantes"""
        print("\n📅 Probando análisis de fechas faltantes...")
        payload = {
            "publication_name": "DM",
            "start_date": "1903-01-01",
            "end_date": "1903-12-31"
        }
        response = self.session.post(f"{BASE_URL}/analysis/missing-dates", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Análisis de fechas faltantes completado")
            print(f"   Fechas faltantes: {len(data.get('missing_dates', []))}")
            return True
        else:
            print(f"❌ Error en fechas faltantes: {response.status_code} - {response.text}")
            return False
    
    def test_storage_metadata(self):
        """Prueba de metadatos de almacenamiento"""
        print("\n💾 Probando metadatos de almacenamiento...")
        payload = {"data_path": "ship_entries"}
        response = self.session.post(f"{BASE_URL}/analysis/storage-metadata", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Metadatos de almacenamiento obtenidos")
            print(f"   Total de registros: {data.get('total_records', 0)}")
            return True
        else:
            print(f"❌ Error en metadatos de almacenamiento: {response.status_code} - {response.text}")
            return False
    
    def test_process_metadata(self):
        """Prueba de metadatos de proceso"""
        print("\n⚙️ Probando metadatos de proceso...")
        payload = {"process_type": "ingestion"}
        response = self.session.post(f"{BASE_URL}/analysis/process-metadata", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Metadatos de proceso obtenidos")
            print(f"   Procesos encontrados: {len(data.get('processes', []))}")
            return True
        else:
            print(f"❌ Error en metadatos de proceso: {response.status_code} - {response.text}")
            return False
    
    def run_all_tests(self):
        """Ejecuta todas las pruebas"""
        print("🚀 INICIANDO PRUEBAS COMPLETAS DEL API PORTADA")
        print("=" * 60)
        
        # Autenticación
        if not self.login():
            return False
        
        # Lista de pruebas
        tests = [
            self.test_health,
            self.test_known_entities,
            self.test_pending_files,
            self.test_daily_entries,
            self.test_duplicates_analysis,
            self.test_missing_dates,
            self.test_storage_metadata,
            self.test_process_metadata
        ]
        
        # Ejecutar pruebas
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed += 1
                time.sleep(1)  # Pausa entre pruebas
            except Exception as e:
                print(f"❌ Error inesperado en {test.__name__}: {e}")
        
        # Resumen
        print("\n" + "=" * 60)
        print(f"📊 RESUMEN DE PRUEBAS:")
        print(f"   ✅ Exitosas: {passed}/{total}")
        print(f"   ❌ Fallidas: {total - passed}/{total}")
        print(f"   📈 Porcentaje de éxito: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("\n🎉 ¡TODAS LAS PRUEBAS PASARON! El sistema está completamente funcional.")
        else:
            print(f"\n⚠️  {total - passed} pruebas fallaron. Revisar logs para más detalles.")
        
        return passed == total

if __name__ == "__main__":
    tester = PortAdaAPITester()
    success = tester.run_all_tests()
    exit(0 if success else 1)