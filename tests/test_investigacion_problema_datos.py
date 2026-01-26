#!/usr/bin/env python3
"""
Script para investigar el problema de datos duplicados/incorrectos
"""

import requests
import json
import time

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

def investigate_data_problem():
    """Investiga el problema de datos duplicados"""
    print("🔍 INVESTIGANDO PROBLEMA DE DATOS")
    print("=" * 50)
    
    session = login_and_get_session()
    if not session:
        return
    
    # 1. Verificar metadatos de almacenamiento
    print("1. 📊 Verificando metadatos de almacenamiento...")
    storage_response = session.post(
        f"{BASE_URL}/analysis/storage-metadata",
        json={"data_path": "ship_entries"}
    )
    
    if storage_response.status_code == 200:
        storage_data = storage_response.json()
        print(f"   Total registros reportados: {storage_data.get('total_records', 0)}")
        print(f"   Respuesta completa: {json.dumps(storage_data, indent=2)}")
    else:
        print(f"   ❌ Error: {storage_response.status_code}")
    
    # 2. Probar consultas muy específicas
    print("\n2. 🔍 Probando consultas específicas...")
    
    # Consulta muy específica por fecha
    specific_queries = [
        {"publication": "DM", "start_date": "1903-02-01", "end_date": "1903-02-01"},
        {"publication": "DB", "start_date": "1854-04-25", "end_date": "1854-04-25"},
        {"publication": "LP", "start_date": "1852-03-15", "end_date": "1852-03-15"},
        {"publication": "TEST", "start_date": "2026-01-26", "end_date": "2026-01-26"}
    ]
    
    for query in specific_queries:
        print(f"   🔍 Consultando {query['publication']} en {query['start_date']}...")
        response = session.post(f"{BASE_URL}/analysis/daily-entries", json=query)
        
        if response.status_code == 200:
            data = response.json()
            total = data.get('total_entries', 0)
            daily_data = data.get('daily_data', [])
            
            print(f"      📊 Total entradas: {total}")
            print(f"      📅 Días con datos: {len(daily_data)}")
            
            # Mostrar algunos datos si existen
            if daily_data:
                print(f"      📝 Primer día: {daily_data[0]}")
        else:
            print(f"      ❌ Error: {response.status_code}")
    
    # 3. Verificar si el problema está en el backend
    print("\n3. 🔧 Verificando logs del backend...")
    print("   (Revisar logs del proceso backend para ver qué consultas se están ejecutando)")
    
    # 4. Probar consulta sin filtros
    print("\n4. 🌐 Probando consulta sin filtros...")
    response = session.post(
        f"{BASE_URL}/analysis/daily-entries",
        json={"publication": "", "start_date": "1800-01-01", "end_date": "2030-12-31"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"   📊 Total sin filtros: {data.get('total_entries', 0)}")
    else:
        print(f"   ❌ Error sin filtros: {response.status_code}")
    
    # 5. Verificar estructura de archivos en el sistema
    print("\n5. 📁 Verificando estructura de archivos...")
    import os
    data_path = "/tmp/portada_data"
    
    if os.path.exists(data_path):
        print(f"   📂 Directorio base existe: {data_path}")
        
        # Listar contenido
        for root, dirs, files in os.walk(data_path):
            level = root.replace(data_path, '').count(os.sep)
            indent = ' ' * 2 * level
            print(f"{indent}📁 {os.path.basename(root)}/")
            
            subindent = ' ' * 2 * (level + 1)
            for file in files[:5]:  # Solo primeros 5 archivos
                print(f"{subindent}📄 {file}")
            if len(files) > 5:
                print(f"{subindent}... y {len(files) - 5} archivos más")
    else:
        print(f"   ❌ Directorio no existe: {data_path}")

def test_clean_upload():
    """Prueba subir un archivo completamente nuevo y verificar"""
    print("\n🧪 PRUEBA DE SUBIDA LIMPIA")
    print("=" * 40)
    
    session = login_and_get_session()
    if not session:
        return
    
    # Crear archivo con datos únicos
    unique_data = [
        {
            "model_version": "boat_fact-00.00.01",
            "publication_date": "2026-01-26",
            "publication_name": "UNIQUE",
            "publication_edition": "U",
            "news_section": "E",
            "travel_departure_port": "Puerto Único",
            "travel_arrival_port": "Puerto Destino Único",
            "travel_departure_date": "2026-01-25",
            "travel_arrival_date": "2026-01-26",
            "travel_arrival_moment": None,
            "travel_duration_value": "1",
            "travel_duration_unit": "días",
            "travel_port_of_call_list": [],
            "ship_type": "vapor",
            "ship_flag": "único",
            "ship_name": f"Barco Único {int(time.time())}",  # Nombre único con timestamp
            "ship_tons_capacity": "999",
            "ship_tons_unit": "toneladas",
            "master_role": "cap.",
            "master_name": "Capitán Único",
            "ship_agent_name": "Agente Único",
            "crew_number": 99,
            "cargo_list": [
                {
                    "cargo_merchant_name": "Comerciante Único",
                    "cargo": [
                        {
                            "cargo_quantity": "99",
                            "cargo_unit": "cajas únicas",
                            "cargo_commodity": "mercancía única"
                        }
                    ]
                }
            ],
            "quarantine": False,
            "forced_arrival": False,
            "ship_amount": None,
            "ship_origin_area": None,
            "parsed_text": f"Texto único de prueba {int(time.time())}",
            "obs": "Registro único para prueba"
        }
    ]
    
    # Guardar archivo
    unique_filename = f"test_unique_{int(time.time())}.json"
    with open(unique_filename, 'w', encoding='utf-8') as f:
        json.dump(unique_data, f, indent=2, ensure_ascii=False)
    
    print(f"📁 Archivo único creado: {unique_filename}")
    
    # Subir archivo
    with open(unique_filename, 'rb') as f:
        response = session.post(
            f"{BASE_URL}/ingestion/upload",
            files={"file": (unique_filename, f, "application/json")},
            data={"ingestion_type": "extraction_data"}
        )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Archivo subido - Task ID: {data.get('task_id')}")
        
        # Esperar procesamiento
        print("⏳ Esperando procesamiento...")
        time.sleep(15)
        
        # Verificar si aparece en consultas
        print("🔍 Verificando si el archivo único aparece...")
        
        # Consulta específica para UNIQUE
        response = session.post(
            f"{BASE_URL}/analysis/daily-entries",
            json={"publication": "UNIQUE", "start_date": "2026-01-01", "end_date": "2026-12-31"}
        )
        
        if response.status_code == 200:
            data = response.json()
            unique_entries = data.get('total_entries', 0)
            print(f"📊 Entradas para UNIQUE: {unique_entries}")
            
            if unique_entries == 1:
                print("✅ El archivo único se procesó correctamente")
            elif unique_entries > 1:
                print(f"⚠️  Se encontraron {unique_entries} entradas (debería ser 1)")
            else:
                print("❌ No se encontró el archivo único")
        else:
            print(f"❌ Error consultando UNIQUE: {response.status_code}")
    else:
        print(f"❌ Error subiendo archivo: {response.status_code}")
    
    # Limpiar archivo
    import os
    if os.path.exists(unique_filename):
        os.remove(unique_filename)

def main():
    """Función principal"""
    print("🚨 INVESTIGACIÓN DE PROBLEMA DE DATOS DUPLICADOS")
    print("=" * 60)
    
    investigate_data_problem()
    test_clean_upload()
    
    print("\n" + "=" * 60)
    print("📋 CONCLUSIONES:")
    print("1. Si todas las publicaciones devuelven el mismo número:")
    print("   → Hay un problema en el filtrado de consultas")
    print("2. Si hay millones de entradas con pocos archivos subidos:")
    print("   → Puede haber datos preexistentes o duplicación")
    print("3. Revisar logs del backend para ver las consultas SQL reales")

if __name__ == "__main__":
    main()