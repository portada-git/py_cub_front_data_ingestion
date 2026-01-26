#!/usr/bin/env python3
"""
Script para carga masiva de todos los datos reales convertidos del DM
Procesa todos los archivos convertidos en lotes para evitar sobrecargar el sistema
"""

import requests
import json
import time
import sys
from pathlib import Path
import glob
from typing import List, Dict, Any

class BulkUploader:
    """Cargador masivo de datos convertidos"""
    
    def __init__(self, base_url: str = "http://localhost:8002/api"):
        self.base_url = base_url
        self.session = None
        self.stats = {
            'files_uploaded': 0,
            'files_failed': 0,
            'total_entries_uploaded': 0,
            'errors': [],
            'processing_times': []
        }
    
    def login(self, username: str = "daniel", password: str = "test123") -> bool:
        """Autenticación en el sistema"""
        try:
            response = requests.post(
                f"{self.base_url}/auth/login",
                json={"username": username, "password": password}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.session = requests.Session()
                self.session.headers.update({
                    "Authorization": f"Bearer {data['access_token']}"
                })
                print(f"✅ Autenticado como: {username}")
                return True
            else:
                print(f"❌ Error de autenticación: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error de conexión: {e}")
            return False
    
    def upload_file(self, file_path: str) -> Dict[str, Any]:
        """Sube un archivo individual"""
        try:
            file_name = Path(file_path).name
            print(f"📤 Subiendo: {file_name}")
            
            # Contar entradas en el archivo
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                entry_count = len(data)
            
            print(f"   📊 Entradas: {entry_count:,}")
            
            # Subir archivo
            start_time = time.time()
            
            with open(file_path, 'rb') as f:
                files = {'file': (file_name, f, 'application/json')}
                data = {'ingestion_type': 'extraction_data'}
                
                response = self.session.post(
                    f"{self.base_url}/ingestion/upload",
                    files=files,
                    data=data
                )
            
            if response.status_code == 200:
                result = response.json()
                task_id = result.get('task_id')
                
                print(f"   ✅ Subido - Task ID: {task_id}")
                
                # Esperar procesamiento
                processing_time = self.wait_for_completion(task_id)
                total_time = time.time() - start_time
                
                self.stats['files_uploaded'] += 1
                self.stats['total_entries_uploaded'] += entry_count
                self.stats['processing_times'].append(total_time)
                
                print(f"   ⏱️  Tiempo total: {total_time:.1f}s")
                
                return {
                    'success': True,
                    'file': file_name,
                    'entries': entry_count,
                    'task_id': task_id,
                    'processing_time': total_time
                }
            else:
                error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
                print(f"   ❌ Error: {error_msg}")
                self.stats['files_failed'] += 1
                self.stats['errors'].append(f"{file_name}: {error_msg}")
                
                return {
                    'success': False,
                    'file': file_name,
                    'error': error_msg
                }
                
        except Exception as e:
            error_msg = str(e)
            print(f"   ❌ Excepción: {error_msg}")
            self.stats['files_failed'] += 1
            self.stats['errors'].append(f"{Path(file_path).name}: {error_msg}")
            
            return {
                'success': False,
                'file': Path(file_path).name,
                'error': error_msg
            }
    
    def wait_for_completion(self, task_id: str, max_wait: int = 300) -> float:
        """Espera a que se complete el procesamiento"""
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                # Verificar estado del task (esto es conceptual, el API actual no tiene endpoint de estado)
                # Por ahora, esperamos un tiempo fijo basado en el tamaño
                time.sleep(30)  # Esperar 30 segundos por defecto
                print(f"   ⏳ Procesamiento completado (estimado)")
                return time.time() - start_time
                
            except Exception as e:
                print(f"   ⚠️  Error verificando estado: {e}")
                time.sleep(10)
        
        print(f"   ⚠️  Timeout esperando completación")
        return time.time() - start_time
    
    def upload_batch(self, file_paths: List[str], batch_delay: int = 60) -> List[Dict]:
        """Sube un lote de archivos con delay entre cada uno"""
        results = []
        
        for i, file_path in enumerate(file_paths):
            print(f"\n📁 Archivo {i+1}/{len(file_paths)}")
            
            result = self.upload_file(file_path)
            results.append(result)
            
            # Delay entre archivos (excepto el último)
            if i < len(file_paths) - 1:
                print(f"   ⏸️  Esperando {batch_delay}s antes del siguiente archivo...")
                time.sleep(batch_delay)
        
        return results

def main():
    """Función principal"""
    print("🚀 CARGA MASIVA DE DATOS REALES DEL DM")
    print("=" * 60)
    
    # Verificar archivos convertidos
    converted_dir = Path(".data/converted")
    if not converted_dir.exists():
        print(f"❌ Directorio no encontrado: {converted_dir}")
        return False
    
    # Buscar archivos convertidos
    converted_files = sorted(glob.glob(str(converted_dir / "*_converted.json")))
    
    if not converted_files:
        print(f"❌ No se encontraron archivos convertidos en {converted_dir}")
        return False
    
    print(f"📁 Archivos encontrados: {len(converted_files)}")
    
    # Agrupar por tipo y década para procesamiento inteligente
    cabotage_files = [f for f in converted_files if 'cabotage' in f]
    traversing_files = [f for f in converted_files if 'traversing' in f]
    
    print(f"   🚢 Cabotaje: {len(cabotage_files)} archivos")
    print(f"   🌊 Travesías: {len(traversing_files)} archivos")
    
    # Crear uploader
    uploader = BulkUploader()
    
    # Autenticar
    if not uploader.login():
        return False
    
    # Estrategia de carga
    print(f"\n📋 ESTRATEGIA DE CARGA:")
    print(f"   1. Procesar archivos en orden cronológico")
    print(f"   2. Delay de 60s entre archivos")
    print(f"   3. Monitoreo de progreso")
    
    # Confirmar antes de proceder
    response = input(f"\n¿Proceder con la carga de {len(converted_files)} archivos? (y/N): ")
    if response.lower() != 'y':
        print("❌ Operación cancelada")
        return False
    
    # Procesar todos los archivos
    print(f"\n🔄 INICIANDO CARGA MASIVA...")
    print("=" * 40)
    
    start_time = time.time()
    results = uploader.upload_batch(converted_files, batch_delay=60)
    total_time = time.time() - start_time
    
    # Mostrar estadísticas finales
    print(f"\n📊 ESTADÍSTICAS FINALES")
    print("=" * 40)
    print(f"✅ Archivos subidos: {uploader.stats['files_uploaded']}")
    print(f"❌ Archivos fallidos: {uploader.stats['files_failed']}")
    print(f"📊 Total entradas: {uploader.stats['total_entries_uploaded']:,}")
    print(f"⏱️  Tiempo total: {total_time/60:.1f} minutos")
    
    if uploader.stats['processing_times']:
        avg_time = sum(uploader.stats['processing_times']) / len(uploader.stats['processing_times'])
        print(f"⏱️  Tiempo promedio por archivo: {avg_time:.1f}s")
    
    # Mostrar errores si los hay
    if uploader.stats['errors']:
        print(f"\n❌ ERRORES ({len(uploader.stats['errors'])}):")
        for error in uploader.stats['errors'][:10]:
            print(f"   • {error}")
        if len(uploader.stats['errors']) > 10:
            print(f"   ... y {len(uploader.stats['errors']) - 10} más")
    
    # Resumen por década
    successful_files = [r for r in results if r['success']]
    if successful_files:
        print(f"\n📅 DATOS CARGADOS POR PERÍODO:")
        decades = {}
        total_entries_by_decade = {}
        
        for result in successful_files:
            file_name = result['file']
            year = int(file_name.split('_')[0])
            decade = (year // 10) * 10
            
            if decade not in decades:
                decades[decade] = 0
                total_entries_by_decade[decade] = 0
            
            decades[decade] += 1
            total_entries_by_decade[decade] += result['entries']
        
        for decade in sorted(decades.keys()):
            print(f"   📆 {decade}s: {decades[decade]} archivos, {total_entries_by_decade[decade]:,} entradas")
    
    # Recomendaciones finales
    print(f"\n🎯 PRÓXIMOS PASOS:")
    if uploader.stats['files_uploaded'] > 0:
        print(f"   ✅ Verificar datos en la interfaz web")
        print(f"   ✅ Ejecutar análisis de calidad de datos")
        print(f"   ✅ Crear visualizaciones históricas")
    
    if uploader.stats['files_failed'] > 0:
        print(f"   ⚠️  Revisar archivos fallidos")
        print(f"   ⚠️  Reintentar carga de archivos con errores")
    
    success_rate = (uploader.stats['files_uploaded'] / len(converted_files)) * 100
    print(f"\n🎉 TASA DE ÉXITO: {success_rate:.1f}%")
    
    return success_rate >= 80

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)