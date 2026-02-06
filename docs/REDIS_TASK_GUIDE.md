# Guía de Implementación de Workers con Redis

Esta guía describe cómo crear un servicio (Worker) que consuma tareas de ingestión creadas por la API de PortAda y actualice su estado en Redis.

## 🧠 Conceptos Básicos

El sistema utiliza Redis con dos propósitos principales:

1.  **Cola de Mensajes (Queue)**: Lista que mantiene el orden de procesamiento.
2.  **Base de Datos de Estado (State DB)**: Hashes que almacenan los metadatos y el estado actual de cada archivo.

### Estructura de Claves (Keys)

| Tipo Redis | Clave (Key)            | Descripción                                                   | Creado por        | Consumido por         |
| :--------- | :--------------------- | :------------------------------------------------------------ | :---------------- | :-------------------- |
| **List**   | `files:all`            | **Cola Global**. Contiene los IDs de los archivos pendientes. | API (`ingest.py`) | **Worker**            |
| **List**   | `files:user:<usuario>` | **Historial Usuario**. Lista de IDs subidos por un usuario.   | API (`ingest.py`) | Frontend (Historial)  |
| **Hash**   | `file:<id>`            | **Detalles Tarea**. Metadatos (ruta, estado, timestamp).      | API (`ingest.py`) | **Worker** / Frontend |

### Códigos de Estado (Status)

El campo `status` dentro del Hash `file:<id>` controla el ciclo de vida:

- `0`: **Pendiente** (Inicial)
- `1`: **Procesando** (Prosesado)

---

## 🛠 Comandos Redis para el Worker

Un servicio que procese estos archivos debe seguir este flujo de comandos:

### 1. Obtener la siguiente tarea

Usa `BLPOP` (Blocking Left Pop) para esperar y obtener el siguiente ID de la cola. Esto bloquea la ejecución hasta que haya un elemento, evitando bucles infinitos de consumo de CPU.

```redis
BLPOP files:all 0
```

_Respuesta:_ `["files:all", "<uuid-del-archivo>"]`

### 2. Leer metadatos

Una vez tengas el ID, lee la información del archivo (ruta, tipo, etc.).

```redis
HGETALL file:<uuid-del-archivo>
```

### 3. Marcar como "Procesando"

Antes de empezar el trabajo pesado, actualiza el estado para que se sepa que se está trabajando en él.

```redis
HSET file:<uuid-del-archivo> status 1
```

### 4. Procesar el archivo

Realiza la lógica de negocio (leer JSON, escribir a Delta Lake, etc.).

### 5. Finalizar tarea

Si todo sale bien o mal, actualiza el estado final.

**Éxito:**

```redis
HSET file:<uuid-del-archivo> status 2
```

**Error:**
Puedes añadir un campo extra para el mensaje de error.

```redis
HSET file:<uuid-del-archivo> status -1 error_message "JSON inválido en línea 40"
```

---

## 🐍 Ejemplo de Implementación (Python)

Ver el script `scripts/worker_example.py` para una implementación funcional.

### Boilerplate Básico

```python
import redis
import os

# Conexión
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

def process_file(file_id):
    # 1. Leer datos
    data = r.hgetall(f"file:{file_id}")
    path = data.get("file_path")

    print(f"--> Procesando {path}...")

    # 2. Actualizar estado a PROCESSING
    r.hset(f"file:{file_id}", "status", 0)

    try:
        # SIMULACIÓN DE TRABAJO
        # procesar_archivo_delta(path)
        import time; time.sleep(2) # Simular espera

        # 3. Actualizar estado a DONE
        r.hset(f"file:{file_id}", "status", 1)
        print(f"✅ Terminado {file_id}")

    except Exception as e:
        # 4. Manejo de ERRORES
        r.hset(f"file:{file_id}", mapping={
            "status": -1,
            "error_message": str(e)
        })
        print(f"❌ Error en {file_id}: {e}")

def run_worker():
    print("👷 Worker iniciado. Esperando tareas en 'files:all'...")
    while True:
        # BLPOP retorna una tupla (key, element)
        # timeout=0 espera indefinidamente
        queue, file_id = r.blpop("files:all", timeout=0)

        if file_id:
            process_file(file_id)

if __name__ == "__main__":
    run_worker()
```
