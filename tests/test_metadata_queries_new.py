#!/usr/bin/env python3
"""
Test para probar la nueva forma de consultar metadatos
Backend corriendo en puerto 8002
"""

import requests
import json
from datetime import datetime
from typing import Dict, Any, Optional

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

def print_test(test_name: str):
    """Imprime el nombre del test"""
    print(f"{Colors.BOLD}{Colors.BLUE}🧪 TEST: {test_name}{Colors.RESET}")

def print_success(message: str):
    """Imprime mensaje de éxito"""
    print(f"{Colors.GREEN}✅ {message}{Colors.RESET}")

def print_error(message: str):
    """Imprime mensaje de error"""
    print(f"{Colors.RED}❌ {message}{Colors.RESET}")

def print_warning(message: str):
    """Imprime mensaje de advertencia"""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.RESET}")

def print_info(message: str):
    """Imprime mensaje informativo"""
    print(f"{Colors.CYAN}ℹ️  {message}{Colors.RESET}")

def print_json(data: Any, title: str = "Response"):
    """Imprime JSON formateado"""
    print(f"\n{Colors.YELLOW}{title}:{Colors.RESET}")
    print(json.dumps(data, indent=2, ensure_ascii=False))

def check_backend_health() -> bool:
    """Verifica que el backend esté corriendo"""
    try:
        # Intentar con el endpoint raíz
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Backend está corriendo en {BASE_URL}")
            print_info(f"API: {data.get('message', 'N/A')}")
            print_info(f"Version: {data.get('version', 'N/A')}")
            return True
        else:
            print_error(f"Backend respondió con código {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error(f"No se puede conectar al backend en {BASE_URL}")
        print_info("Asegúrate de que el backend esté corriendo en el puerto 8002")
        return False
    except Exception as e:
        print_error(f"Error al verificar backend: {str(e)}")
        return False

def test_get_storage_metadata(publication: Optional[str] = None) -> Dict[str, Any]:
    """
    Test: Obtener metadatos de almacenamiento
    Endpoint: GET /api/metadata/storage
    """
    print_test("Obtener Metadatos de Almacenamiento")
    
    url = f"{API_BASE}/metadata/storage"
    params = {}
    if publication:
        params['publication'] = publication
        print_info(f"Consultando para publicación: {publication}")
    else:
        print_info("Consultando todos los metadatos de almacenamiento")
    
    try:
        response = requests.get(url, params=params, timeout=30)
        
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print_success("Metadatos obtenidos correctamente")
            
            # Analizar respuesta
            if isinstance(data, list):
                print_info(f"Total de registros: {len(data)}")
                if len(data) > 0:
                    print_json(data[0], "Primer registro (ejemplo)")
                    
                    # Verificar estructura
                    first_record = data[0]
                    expected_fields = ['stored_log_id', 'publication_name', 'stored_at', 
                                     'records_count', 'file_path']
                    missing_fields = [f for f in expected_fields if f not in first_record]
                    
                    if missing_fields:
                        print_warning(f"Campos faltantes: {missing_fields}")
                    else:
                        print_success("Estructura de datos correcta")
                        
                    # Mostrar estadísticas
                    publications = set(r.get('publication_name') for r in data)
                    total_records = sum(r.get('records_count', 0) for r in data)
                    print_info(f"Publicaciones únicas: {len(publications)}")
                    print_info(f"Total de registros almacenados: {total_records}")
                    
            else:
                print_json(data, "Respuesta completa")
                
            return {"success": True, "data": data}
            
        elif response.status_code == 404:
            print_warning("No se encontraron metadatos")
            return {"success": True, "data": []}
            
        else:
            print_error(f"Error en la petición: {response.status_code}")
            print_json(response.json(), "Error response")
            return {"success": False, "error": response.json()}
            
    except requests.exceptions.Timeout:
        print_error("Timeout en la petición (>30s)")
        return {"success": False, "error": "timeout"}
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return {"success": False, "error": str(e)}

def test_get_process_metadata(publication: Optional[str] = None) -> Dict[str, Any]:
    """
    Test: Obtener metadatos de procesamiento
    Endpoint: GET /api/metadata/process
    """
    print_test("Obtener Metadatos de Procesamiento")
    
    url = f"{API_BASE}/metadata/process"
    params = {}
    if publication:
        params['publication'] = publication
        print_info(f"Consultando para publicación: {publication}")
    else:
        print_info("Consultando todos los metadatos de procesamiento")
    
    try:
        response = requests.get(url, params=params, timeout=30)
        
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print_success("Metadatos obtenidos correctamente")
            
            # Analizar respuesta
            if isinstance(data, list):
                print_info(f"Total de registros: {len(data)}")
                if len(data) > 0:
                    print_json(data[0], "Primer registro (ejemplo)")
                    
                    # Verificar estructura
                    first_record = data[0]
                    expected_fields = ['process_log_id', 'publication_name', 'processed_at',
                                     'records_processed', 'status']
                    missing_fields = [f for f in expected_fields if f not in first_record]
                    
                    if missing_fields:
                        print_warning(f"Campos faltantes: {missing_fields}")
                    else:
                        print_success("Estructura de datos correcta")
                        
                    # Mostrar estadísticas
                    publications = set(r.get('publication_name') for r in data)
                    total_processed = sum(r.get('records_processed', 0) for r in data)
                    statuses = {}
                    for r in data:
                        status = r.get('status', 'unknown')
                        statuses[status] = statuses.get(status, 0) + 1
                    
                    print_info(f"Publicaciones únicas: {len(publications)}")
                    print_info(f"Total de registros procesados: {total_processed}")
                    print_info(f"Estados: {statuses}")
                    
            else:
                print_json(data, "Respuesta completa")
                
            return {"success": True, "data": data}
            
        elif response.status_code == 404:
            print_warning("No se encontraron metadatos")
            return {"success": True, "data": []}
            
        else:
            print_error(f"Error en la petición: {response.status_code}")
            print_json(response.json(), "Error response")
            return {"success": False, "error": response.json()}
            
    except requests.exceptions.Timeout:
        print_error("Timeout en la petición (>30s)")
        return {"success": False, "error": "timeout"}
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return {"success": False, "error": str(e)}

def test_get_field_lineage(publication: Optional[str] = None) -> Dict[str, Any]:
    """
    Test: Obtener linaje de campos
    Endpoint: GET /api/metadata/field-lineage
    """
    print_test("Obtener Linaje de Campos")
    
    url = f"{API_BASE}/metadata/field-lineage"
    params = {}
    if publication:
        params['publication'] = publication
        print_info(f"Consultando para publicación: {publication}")
    else:
        print_info("Consultando todo el linaje de campos")
    
    try:
        response = requests.get(url, params=params, timeout=30)
        
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print_success("Linaje obtenido correctamente")
            
            # Analizar respuesta
            if isinstance(data, list):
                print_info(f"Total de registros: {len(data)}")
                if len(data) > 0:
                    print_json(data[0], "Primer registro (ejemplo)")
                    
                    # Verificar estructura
                    first_record = data[0]
                    expected_fields = ['stored_log_id', 'field_name', 'original_value',
                                     'transformed_value', 'transformation_type']
                    missing_fields = [f for f in expected_fields if f not in first_record]
                    
                    if missing_fields:
                        print_warning(f"Campos faltantes: {missing_fields}")
                    else:
                        print_success("Estructura de datos correcta")
                        
                    # Mostrar estadísticas
                    fields = set(r.get('field_name') for r in data)
                    transformations = {}
                    for r in data:
                        trans_type = r.get('transformation_type', 'unknown')
                        transformations[trans_type] = transformations.get(trans_type, 0) + 1
                    
                    print_info(f"Campos únicos: {len(fields)}")
                    print_info(f"Tipos de transformación: {transformations}")
                    
            else:
                print_json(data, "Respuesta completa")
                
            return {"success": True, "data": data}
            
        elif response.status_code == 404:
            print_warning("No se encontró linaje de campos")
            return {"success": True, "data": []}
            
        else:
            print_error(f"Error en la petición: {response.status_code}")
            print_json(response.json(), "Error response")
            return {"success": False, "error": response.json()}
            
    except requests.exceptions.Timeout:
        print_error("Timeout en la petición (>30s)")
        return {"success": False, "error": "timeout"}
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return {"success": False, "error": str(e)}

def test_get_duplicates(publication: Optional[str] = None) -> Dict[str, Any]:
    """
    Test: Obtener duplicados
    Endpoint: GET /api/metadata/duplicates
    """
    print_test("Obtener Duplicados")
    
    url = f"{API_BASE}/metadata/duplicates"
    params = {}
    if publication:
        params['publication'] = publication
        print_info(f"Consultando para publicación: {publication}")
    else:
        print_info("Consultando todos los duplicados")
    
    try:
        response = requests.get(url, params=params, timeout=30)
        
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print_success("Duplicados obtenidos correctamente")
            
            # Analizar respuesta
            if isinstance(data, list):
                print_info(f"Total de registros duplicados: {len(data)}")
                if len(data) > 0:
                    print_json(data[0], "Primer registro (ejemplo)")
                    
                    # Mostrar estadísticas
                    publications = set(r.get('publication') for r in data)
                    print_info(f"Publicaciones con duplicados: {len(publications)}")
                    
            else:
                print_json(data, "Respuesta completa")
                
            return {"success": True, "data": data}
            
        elif response.status_code == 404:
            print_warning("No se encontraron duplicados")
            return {"success": True, "data": []}
            
        else:
            print_error(f"Error en la petición: {response.status_code}")
            print_json(response.json(), "Error response")
            return {"success": False, "error": response.json()}
            
    except requests.exceptions.Timeout:
        print_error("Timeout en la petición (>30s)")
        return {"success": False, "error": "timeout"}
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return {"success": False, "error": str(e)}

def run_all_tests():
    """Ejecuta todos los tests"""
    print_header("TEST DE METADATOS - NUEVA IMPLEMENTACIÓN")
    
    # Verificar backend
    if not check_backend_health():
        return
    
    print("\n")
    
    # Resultados
    results = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "warnings": 0
    }
    
    # Test 1: Storage Metadata (todos)
    print_header("TEST 1: Storage Metadata (Todos)")
    result = test_get_storage_metadata()
    results["total"] += 1
    if result["success"]:
        results["passed"] += 1
    else:
        results["failed"] += 1
    
    # Test 2: Storage Metadata (publicación específica)
    print_header("TEST 2: Storage Metadata (Publicación: DM)")
    result = test_get_storage_metadata(publication="DM")
    results["total"] += 1
    if result["success"]:
        results["passed"] += 1
    else:
        results["failed"] += 1
    
    # Test 3: Process Metadata (todos)
    print_header("TEST 3: Process Metadata (Todos)")
    result = test_get_process_metadata()
    results["total"] += 1
    if result["success"]:
        results["passed"] += 1
    else:
        results["failed"] += 1
    
    # Test 4: Process Metadata (publicación específica)
    print_header("TEST 4: Process Metadata (Publicación: DM)")
    result = test_get_process_metadata(publication="DM")
    results["total"] += 1
    if result["success"]:
        results["passed"] += 1
    else:
        results["failed"] += 1
    
    # Test 5: Field Lineage (todos)
    print_header("TEST 5: Field Lineage (Todos)")
    result = test_get_field_lineage()
    results["total"] += 1
    if result["success"]:
        results["passed"] += 1
    else:
        results["failed"] += 1
    
    # Test 6: Field Lineage (publicación específica)
    print_header("TEST 6: Field Lineage (Publicación: DM)")
    result = test_get_field_lineage(publication="DM")
    results["total"] += 1
    if result["success"]:
        results["passed"] += 1
    else:
        results["failed"] += 1
    
    # Test 7: Duplicates (todos)
    print_header("TEST 7: Duplicates (Todos)")
    result = test_get_duplicates()
    results["total"] += 1
    if result["success"]:
        results["passed"] += 1
    else:
        results["failed"] += 1
    
    # Test 8: Duplicates (publicación específica)
    print_header("TEST 8: Duplicates (Publicación: DM)")
    result = test_get_duplicates(publication="DM")
    results["total"] += 1
    if result["success"]:
        results["passed"] += 1
    else:
        results["failed"] += 1
    
    # Resumen final
    print_header("RESUMEN DE TESTS")
    print(f"{Colors.BOLD}Total de tests:{Colors.RESET} {results['total']}")
    print(f"{Colors.GREEN}✅ Pasados:{Colors.RESET} {results['passed']}")
    print(f"{Colors.RED}❌ Fallidos:{Colors.RESET} {results['failed']}")
    
    if results['failed'] == 0:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 TODOS LOS TESTS PASARON 🎉{Colors.RESET}\n")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}⚠️  ALGUNOS TESTS FALLARON ⚠️{Colors.RESET}\n")

if __name__ == "__main__":
    run_all_tests()
