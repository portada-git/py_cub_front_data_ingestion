#!/usr/bin/env python3
"""
Script para investigar qué datos hay realmente procesados en el sistema
"""

import requests
import json
import sys

# Configuración
BASE_URL = "http://localhost:8002/api"
USERNAME = "daniel"
PASSWORD = "test123"

def investigate_data():
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

    # 2. Consultar Entidades Conocidas
    print("\n🧠 Consultando Entidades Conocidas (para ver qué publicaciones existen)...")
    try:
        resp = session.get(f"{BASE_URL}/analysis/known-entities")
        if resp.status_code == 200:
            data = resp.json()
            print(f"📊 Total entidades: {data.get('total_entities')}")
            # Ver publicaciones únicas si están listadas
            publications = set()
            for entity in data.get('entities', []):
                if 'publication' in entity:
                    publications.add(entity['publication'])
            if publications:
                print(f"📝 Publicaciones encontradas en entidades: {publications}")
        else:
            print(f"❌ Error entidades: {resp.status_code}")
    except Exception as e:
        print(f"💥 Error: {e}")

    # 3. Consultar Storage Metadata
    print("\n💾 Consultando Storage Metadata (ship_entries)...")
    try:
        resp = session.post(
            f"{BASE_URL}/analysis/storage-metadata",
            json={"data_path": "ship_entries"}
        )
        if resp.status_code == 200:
            data = resp.json()
            print(f"📊 Total registros: {data.get('total_records')}")
            print(f"📅 Rango: {data.get('min_date')} a {data.get('max_date')}")
            print(f"📦 Publicaciones: {data.get('publications')}")
        else:
            print(f"❌ Error storage: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"💥 Error: {e}")

    # 4. Consultar Daily Entries para 'db'
    print("\n📈 Consultando Daily Entries para 'db'...")
    try:
        resp = session.post(
            f"{BASE_URL}/analysis/daily-entries",
            json={"publication": "db"}
        )
        if resp.status_code == 200:
            data = resp.json()
            print(f"📊 Registros diarios para 'db': {len(data.get('daily_counts', []))}")
            if data.get('daily_counts'):
                print(f"📅 Muestra diaria: {data.get('daily_counts')[:5]}")
        else:
            print(f"❌ Error daily-entries: {resp.status_code}")
    except Exception as e:
        print(f"💥 Error: {e}")

if __name__ == "__main__":
    investigate_data()
