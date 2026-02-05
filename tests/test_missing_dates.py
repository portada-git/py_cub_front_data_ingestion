#!/usr/bin/env python3
"""
Test para validar la funcionalidad de Fechas Faltantes (Missing Dates)
"""

import requests
import json
import sys

# Configuración
BASE_URL = "http://localhost:8002/api"
USERNAME = "daniel"
PASSWORD = "test123"

def run_test():
    # Crear sesión
    session = requests.Session()
    
    # 1. Login
    print("🔐 Identificándose...")
    login_response = session.post(
        f"{BASE_URL}/auth/login",
        json={"username": USERNAME, "password": PASSWORD}
    )
    
    if login_response.status_code != 200:
        print(f"❌ Error en login: {login_response.status_code}")
        return
    
    token_data = login_response.json()
    session.headers.update({"Authorization": f"Bearer {token_data['access_token']}"})
    print("✅ Login exitoso")

    # Escenarios de prueba
    escenarios = [
        {
            "nombre": "Búsqueda por publicación (sin rango)",
            "payload": {
                "publication_name": "dm"
            }
        },
        {
            "nombre": "Búsqueda por rango de fechas",
            "payload": {
                "publication_name": "dm",
                "start_date": "1903-01-01",
                "end_date": "1903-01-31"
            }
        },
        {
            "nombre": "Búsqueda con lista de fechas (File-based emulation)",
            "payload": {
                "publication_name": "dm",
                "date_and_edition_list": "1903-01-01,U;1903-01-02,U;1903-01-03,U"
            }
        }
    ]

    for escenario in escenarios:
        print(f"\n🚀 Probando: {escenario['nombre']}")
        print(f"   Payload: {json.dumps(escenario['payload'])}")
        
        try:
            response = session.post(
                f"{BASE_URL}/analysis/missing-dates",
                json=escenario['payload']
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Respuesta recibida (200 OK)")
                print(f"   Tipo de consulta: {data.get('query_type')}")
                print(f"   Total faltantes: {data.get('total_missing')}")
                
                missing = data.get('missing_dates', [])
                if missing:
                    print(f"   Muestra: {missing[:3]}")
                else:
                    print(f"   (No se encontraron fechas faltantes)")
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"   Detalle: {response.text}")
                
        except Exception as e:
            print(f"💥 Excepción: {str(e)}")

if __name__ == "__main__":
    run_test()
