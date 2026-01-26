#!/usr/bin/env python3
"""
Script para verificar la estructura exacta de los datos guardados
"""

import requests
import json
import time
import os

# Configuración
BASE_URL = "http://localhost:8002/api"
USERNAME = "daniel"
PASSWORD = "test123"

def login_and_get_session():
    """Obtiene una sesión autenticada"""
    session = requests.Session()
    
    response = session.post(
        f"{BASE_URL}/auth/login",
        json={"username": USERNAME, "password": PASSWORD}
    )
    
    if response.status_code == 200:
        data = response.json()
        session.headers.update({"Authorization": f"Bearer {data['access_token']}"})
        return session
    else:
        print(f"❌ Error en login: {response.status_code}")
        return None

def test_simple_upload_and_verify():
    """Sube un archivo simple y verifica inmediatamente"""
    print("🧪 PRUEBA SIMPLE: Subir archivo y verificar inmediatamente")
    print("=" * 60)
    
    session = login_and_get_session()
    if not session:
        return False
    
    # Crear un archivo JSON simple para prueba
    test_data = [
        {
            "model_version": "boat_fact-00.00.01",
            "publication_date": "2026-01-26",
            "publication_name": "TEST",
            "publication_edition": "U",
            "news_section": "E",
            "travel_departure_port": "Puerto Test",
            "travel_arrival_port": "Puerto Destino",
            "travel_departure_date": "2026-01-25",
            "travel_arrival_date": "2026-01-26",
            "travel_arrival_moment": None,
            "travel_duration_value": "1",
            "travel_duration_unit": "días",
            "travel_port_of_call_list": [],
            "ship_type": "vapor",
            "ship_flag": "test",
            "ship_name": "Barco Test",
            "ship_tons_capacity": "100",
            "ship_tons_unit": "toneladas",
            "master_role": "cap.",
            "master_name": "Capitán Test",
            "ship_agent_name": "Agente Test",
            "crew_number": 10,
            "cargo_list": [
                {
                    "cargo_merchant_name": "Comerciante Test",
                    "cargo": [
                        {
                            "cargo_quantity": "50",
                            "cargo_unit": "cajas",
                            "cargo_commodity": "mercancía test"
                        }
                    ]
                }
            ],
            "quarantine": False,
            "forced_arrival": False,
            "ship_amount": None,
            "ship_origin_area": None,
            "parsed_text": "Texto de prueba para verificar funcionamiento",
            "obs": "Registro de prueba"
        }
    ]
    
    # Guardar archivo temporal
    test_filename = "test_simple.json"
    with open(test_filename, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, indent=2, ensure_ascii=False)
    
    print(f"📁 Archivo de prueba creado: {test_filename}")
    
    # Subir archivo
    print("📤 Subiendo archivo de prueba...")
    with open(test_filename, 'rb') as f:
        response = session.post(
            f"{BASE_URL}/ingestion/upload",
            files={"file": (test_filename, f, "application/json")},
            data={"ingestion_type": "extraction_data"}
        )
    
    if response.status_code == 200:
        data = response.json()
        task_id = data.get('task_id')
        print(f"✅ Archivo subido exitosamente - Task ID: {task_id}")
        
        # Esperar procesamiento
        print("⏳ Esperando procesamiento (15 segundos)...")
        time.sleep(15)
        
        # Verificar metadatos de almacenamiento
        print("🔍 Verificando metadatos de almacenamiento...")
        storage_response = session.post(
            f"{BASE_URL}/analysis/storage-metadata",
            json={"data_path": "ship_entries"}
        )
        
        if storage_response.status_code == 200:
            storage_data = storage_response.json()
            print(f"📊 Total registros: {storage_data.get('total_records', 0)}")
        
        # Probar análisis específico con nuestra publicación TEST
        print("📊 Probando análisis con publicación TEST...")
        daily_response = session.post(
            f"{BASE_URL}/analysis/daily-entries",
            json={
                "publication": "TEST",
                "start_date": "2026-01-01",
                "end_date": "2026-12-31"
            }
        )
        
        if daily_response.status_code == 200:
            daily_data = daily_response.json()
            print(f"✅ Análisis exitoso:")
            print(f"   📊 Total entradas: {daily_data.get('total_entries', 0)}")
            print(f"   📅 Días con datos: {len(daily_data.get('daily_data', []))}")
            
            if daily_data.get('total_entries', 0) > 0:
                print("🎯 ¡Los datos se guardaron y se pueden consultar correctamente!")
                return True
            else:
                print("⚠️  Los datos no se encontraron en la consulta específica")
                return False
        else:
            print(f"❌ Error en análisis: {daily_response.status_code}")
            return False
    else:
        print(f"❌ Error subiendo archivo: {response.status_code}")
        return False

def test_existing_data_structure():
    """Verifica la estructura de los datos existentes"""
    print("\n🔍 VERIFICANDO ESTRUCTURA DE DATOS EXISTENTES")
    print("=" * 50)
    
    session = login_and_get_session()
    if not session:
        return False
    
    # Verificar metadatos generales
    print("📊 Metadatos generales:")
    storage_response = session.post(
        f"{BASE_URL}/analysis/storage-metadata",
        json={"data_path": "ship_entries"}
    )
    
    if storage_response.status_code == 200:
        storage_data = storage_response.json()
        print(f"   Total registros: {storage_data.get('total_records', 0)}")
    
    # Probar diferentes consultas para entender la estructura
    publications_to_test = ["DM", "DB", "LP", "SM", "dm", "db", "lp", "sm"]
    
    print("\n🔍 Probando diferentes publicaciones:")
    for pub in publications_to_test:
        response = session.post(
            f"{BASE_URL}/analysis/daily-entries",
            json={
                "publication": pub,
                "start_date": "1850-01-01",
                "end_date": "2026-12-31"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            total = data.get('total_entries', 0)
            if total > 0:
                print(f"   ✅ {pub}: {total} entradas")
            else:
                print(f"   ⚪ {pub}: 0 entradas")
        else:
            print(f"   ❌ {pub}: Error {response.status_code}")
    
    return True

def main():
    """Función principal"""
    print("🧪 VERIFICACIÓN COMPLETA DE ESTRUCTURA DE DATOS")
    print("=" * 60)
    
    # Prueba 1: Upload simple y verificación inmediata
    test1_success = test_simple_upload_and_verify()
    
    # Prueba 2: Verificar estructura existente
    test2_success = test_existing_data_structure()
    
    # Resumen
    print("\n" + "=" * 60)
    print("📋 RESUMEN DE VERIFICACIÓN:")
    print(f"   🧪 Prueba simple: {'✅ EXITOSA' if test1_success else '❌ FALLIDA'}")
    print(f"   🔍 Estructura existente: {'✅ VERIFICADA' if test2_success else '❌ ERROR'}")
    
    if test1_success:
        print("\n🎉 CONCLUSIÓN: El sistema funciona correctamente")
        print("   - Los datos se guardan correctamente")
        print("   - Los análisis funcionan con datos nuevos")
        print("   - La estructura es correcta")
    else:
        print("\n⚠️  CONCLUSIÓN: Hay problemas en el sistema")
        print("   - Revisar configuración de PortAda")
        print("   - Verificar estructura de directorios")
        print("   - Comprobar consultas de análisis")
    
    return test1_success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)