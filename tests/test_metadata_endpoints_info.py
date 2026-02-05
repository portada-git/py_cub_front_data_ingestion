#!/usr/bin/env python3
"""
Test para verificar los endpoints de metadatos disponibles
y mostrar información detallada sobre su funcionamiento
"""

import requests
import json
from typing import Dict, Any

# Configuración
BASE_URL = "http://localhost:8002"
API_BASE = f"{BASE_URL}/api"

# Colores para output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    """Imprime un encabezado destacado"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(80)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.RESET}\n")

def print_success(message: str):
    """Imprime mensaje de éxito"""
    print(f"{Colors.GREEN}✅ {message}{Colors.RESET}")

def print_error(message: str):
    """Imprime mensaje de error"""
    print(f"{Colors.RED}❌ {message}{Colors.RESET}")

def print_info(message: str):
    """Imprime mensaje informativo"""
    print(f"{Colors.CYAN}ℹ️  {message}{Colors.RESET}")

def print_endpoint(method: str, path: str, description: str):
    """Imprime información de un endpoint"""
    print(f"{Colors.BOLD}{Colors.BLUE}{method:6}{Colors.RESET} {Colors.YELLOW}{path:50}{Colors.RESET} {description}")

def check_endpoint(method: str, path: str, params: Dict = None) -> Dict[str, Any]:
    """Verifica un endpoint y retorna información"""
    url = f"{BASE_URL}{path}"
    try:
        if method == "GET":
            response = requests.get(url, params=params, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=params, timeout=10)
        else:
            return {"status": "unsupported", "code": None}
        
        return {
            "status": "ok" if response.status_code < 500 else "error",
            "code": response.status_code,
            "has_data": response.status_code == 200
        }
    except Exception as e:
        return {"status": "error", "code": None, "error": str(e)}

def main():
    print_header("INFORMACIÓN DE ENDPOINTS DE METADATOS")
    
    # Verificar backend
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Backend conectado: {BASE_URL}")
            print_info(f"API: {data.get('message', 'N/A')}")
            print_info(f"Versión: {data.get('version', 'N/A')}")
        else:
            print_error("Backend no responde correctamente")
            return
    except Exception as e:
        print_error(f"No se puede conectar al backend: {str(e)}")
        return
    
    print_header("ENDPOINTS DE METADATOS DISPONIBLES")
    
    endpoints = [
        {
            "method": "GET",
            "path": "/api/metadata/storage",
            "description": "Obtener metadatos de almacenamiento",
            "params": {"publication": "DM"}
        },
        {
            "method": "GET",
            "path": "/api/metadata/process",
            "description": "Obtener metadatos de procesamiento",
            "params": {"publication": "DM"}
        },
        {
            "method": "GET",
            "path": "/api/metadata/field-lineage",
            "description": "Obtener linaje de campos",
            "params": {"publication": "DM"}
        },
        {
            "method": "GET",
            "path": "/api/metadata/duplicates",
            "description": "Obtener registros duplicados",
            "params": {"publication": "DM"}
        }
    ]
    
    print(f"\n{Colors.BOLD}Verificando endpoints...{Colors.RESET}\n")
    
    results = []
    for endpoint in endpoints:
        print_endpoint(endpoint["method"], endpoint["path"], endpoint["description"])
        
        # Verificar sin parámetros
        result_all = check_endpoint(endpoint["method"], endpoint["path"])
        status_all = "✅" if result_all["status"] == "ok" else "❌"
        code_all = result_all.get("code", "N/A")
        
        # Verificar con parámetros
        result_filtered = check_endpoint(endpoint["method"], endpoint["path"], endpoint.get("params"))
        status_filtered = "✅" if result_filtered["status"] == "ok" else "❌"
        code_filtered = result_filtered.get("code", "N/A")
        
        print(f"  {status_all} Sin filtros: HTTP {code_all}")
        print(f"  {status_filtered} Con filtros: HTTP {code_filtered}")
        
        if result_all.get("has_data"):
            print(f"  {Colors.GREEN}📊 Tiene datos disponibles{Colors.RESET}")
        elif result_all.get("code") == 404:
            print(f"  {Colors.YELLOW}📭 Sin datos (esperado si no hay ingestión){Colors.RESET}")
        
        print()
        
        results.append({
            "endpoint": endpoint["path"],
            "working": result_all["status"] == "ok" and result_filtered["status"] == "ok"
        })
    
    print_header("PARÁMETROS DISPONIBLES")
    
    print(f"{Colors.BOLD}Parámetro 'publication':{Colors.RESET}")
    print("  - Filtra resultados por nombre de publicación")
    print("  - Ejemplo: ?publication=DM")
    print("  - Opcional: si no se proporciona, retorna todos los datos")
    
    print(f"\n{Colors.BOLD}Formato de respuesta:{Colors.RESET}")
    print("  - HTTP 200: Datos encontrados (JSON array)")
    print("  - HTTP 404: No se encontraron datos")
    print("  - HTTP 500: Error del servidor")
    
    print_header("ESTRUCTURA DE DATOS ESPERADA")
    
    print(f"{Colors.BOLD}Storage Metadata:{Colors.RESET}")
    print(json.dumps({
        "stored_log_id": "uuid",
        "publication_name": "string",
        "stored_at": "timestamp",
        "records_count": "integer",
        "file_path": "string"
    }, indent=2))
    
    print(f"\n{Colors.BOLD}Process Metadata:{Colors.RESET}")
    print(json.dumps({
        "process_log_id": "uuid",
        "publication_name": "string",
        "processed_at": "timestamp",
        "records_processed": "integer",
        "status": "string"
    }, indent=2))
    
    print(f"\n{Colors.BOLD}Field Lineage:{Colors.RESET}")
    print(json.dumps({
        "stored_log_id": "uuid",
        "field_name": "string",
        "original_value": "string",
        "transformed_value": "string",
        "transformation_type": "string"
    }, indent=2))
    
    print(f"\n{Colors.BOLD}Duplicates:{Colors.RESET}")
    print(json.dumps({
        "publication": "string",
        "duplicate_count": "integer",
        "records": ["array of duplicate records"]
    }, indent=2))
    
    print_header("RESUMEN")
    
    working = sum(1 for r in results if r["working"])
    total = len(results)
    
    print(f"Endpoints verificados: {total}")
    print(f"Endpoints funcionando: {working}")
    
    if working == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✅ TODOS LOS ENDPOINTS ESTÁN FUNCIONANDO{Colors.RESET}")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}⚠️  ALGUNOS ENDPOINTS NO FUNCIONAN{Colors.RESET}")
    
    print(f"\n{Colors.YELLOW}Nota: Los endpoints retornan 404 cuando no hay datos, lo cual es normal")
    print(f"si aún no se ha realizado ninguna ingestión de datos.{Colors.RESET}\n")

if __name__ == "__main__":
    main()
