#!/usr/bin/env python3
import redis
import os
import time
import sys
import json

# Configuración desde variables de entorno (compatible con docker-compose)
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

print(f"🔌 Conectando a Redis en {REDIS_HOST}:{REDIS_PORT}...")

try:
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    r.ping()
    print("✅ Conexión exitosa a Redis")
except redis.ConnectionError:
    print("❌ No se pudo conectar a Redis. Asegúrate de que el servicio esté corriendo.")
    sys.exit(1)

def process_task(file_id):
    """
    Simula el procesamiento de una tarea.
    """
    task_key = f"file:{file_id}"
    
    # 1. Recuperar metadatos
    metadata = r.hgetall(task_key)
    
    if not metadata:
        print(f"⚠️  Tarea {file_id} recibida pero no encontrada en Hash. Saltando.")
        return

    filename = metadata.get("filename", "unknown")
    user = metadata.get("user", "unknown")
    
    print(f"📦 [START] Procesando archivo: {filename} (Usuario: {user})")

    # 2. Actualizar estado a PROCESSING (1)
    r.hset(task_key, "status", 1)
    
    try:
        # ------------------------------------------------------------------
        # AQUI INSERTAR LÓGICA DE NEGOCIO REAL
        # Ejemplo: Llamar a DeltaDataLayer, validar JSON, transformar datos...
        # ------------------------------------------------------------------
        
        # Simulamos trabajo
        time.sleep(3) 
        
        if "error" in filename:
            raise Exception("Simulación de error forzado por nombre de archivo")

        # ------------------------------------------------------------------

        # 3. Actualizar estado a COMPLETED (2)
        r.hset(task_key, "status", 2)
        print(f"✅ [DONE] Archivo completado: {filename}")

    except Exception as e:
        # 4. Actualizar estado a ERROR (-1)
        print(f"❌ [ERROR] Falló procesamiento de {filename}: {str(e)}")
        r.hset(task_key, mapping={
            "status": -1,
            "error_message": str(e)
        })

def main():
    queue_name = "files:all"
    print(f"👷 Worker escuchando en la cola: {queue_name}")
    print("   Presiona Ctrl+C para detener.")

    while True:
        try:
            # BLPOP bloquea hasta que hay un elemento. Timeout 0 = infinito.
            # Retorna tupla (nombre_cola, valor)
            result = r.blpop(queue_name, timeout=0)
            
            if result:
                _, file_id = result
                process_task(file_id)
                
        except KeyboardInterrupt:
            print("\n🛑 Deteniendo worker...")
            break
        except Exception as e:
            print(f"💥 Error crítico en loop del worker: {e}")
            time.sleep(5)  # Esperar antes de reintentar si se cae Redis

if __name__ == "__main__":
    main()
